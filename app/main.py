"""Again: an evidence-backed troubleshooting memory, with genuine Moss retrieval."""
import asyncio
from contextlib import asynccontextmanager
import re
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .memory import MossMemory, BusyError, ROOT
from .policy import analyze, decide

memory = MossMemory()


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(memory.start())
    yield
    if not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title='Again', version='1.0.0', lifespan=lifespan, docs_url=None, redoc_url=None)
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')


@app.middleware('http')
async def limits(request, call_next):
    if request.method == 'POST':
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail': 'Use the form on this app to submit a request.'}, status_code=403)
        try:
            if int(request.headers.get('content-length', '0')) > 16384:
                return JSONResponse({'detail': 'Input is too large.'}, status_code=413)
        except ValueError:
            return JSONResponse({'detail': 'Invalid request length.'}, status_code=400)
        chunks = []
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > 16384:
                return JSONResponse({'detail': 'Input is too large.'}, status_code=413)
            chunks.append(chunk)
        request._body = b''.join(chunks)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store' if request.url.path.startswith('/api/') else 'no-cache'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'self' https://huggingface.co; form-action 'self'"
    return response


class Recall(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    query: str = Field(min_length=3, max_length=4000)
    stage: str | None = Field(default=None, max_length=80)
    conditions: str = Field(default='', max_length=1200)
    memory_enabled: bool = True


class Teach(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    symptom: str = Field(min_length=5, max_length=1200)
    conditions: str = Field(min_length=5, max_length=1200)
    attempted_action: str = Field(min_length=5, max_length=1200)
    outcome: str = Field(min_length=5, max_length=1200)
    is_synthetic: bool = False


def require_ready():
    if not memory.ready:
        raise HTTPException(503, memory.error or 'Moss is warming up. Please try again shortly.')


def set_cookie(response, token, request):
    response.set_cookie('again_session', token, httponly=True, samesite='lax', max_age=3600, secure=request.url.scheme == 'https' or request.headers.get('x-forwarded-proto') == 'https')


@app.exception_handler(BusyError)
async def busy_handler(request, exc):
    return JSONResponse({'detail': str(exc)}, status_code=429)


@app.get('/')
async def index():
    return FileResponse(ROOT / 'static/index.html')


@app.get('/api/health')
async def health():
    return {'status': 'ready' if memory.ready else ('error' if memory.error else 'starting'), 'ready': memory.ready, 'model': 'moss-minilm', 'seed_count': len(memory.records), 'teaching_enabled': True, 'cold_ready_ms': memory.cold_ready_ms, 'message': memory.error or ('Genuine Moss text retrieval is ready.' if memory.ready else 'Warming the Moss embedding model.'), 'storage': 'Ephemeral, visitor-isolated additions; one hour of inactivity or restart.', 'version': '1.0.0'}


@app.get('/api/ready')
async def ready():
    return JSONResponse({'ready': memory.ready, 'model': 'moss-minilm'}, status_code=200 if memory.ready else 503)


@app.get('/api/examples')
async def examples():
    order = ['elevated_controller_worker_launch_denied', 'trace_controller_not_elevated', 'moss_torch_import_order', 'numpy_first_query_commit_jump', 'extraction_ram_preflight']
    rows = [{'id': k, 'label': memory.records[k]['title'], 'query': memory.records[k]['demo_queries'][0], 'stage': memory.records[k]['stage'], 'conditions': ''} for k in order]
    rows.append({'id': 'ambiguous', 'label': 'Same error, missing stage', 'query': 'Access is denied. What should I try next?', 'stage': '', 'conditions': ''})
    return {'examples': rows, 'stages': [{'value': r['stage'], 'label': r['stage'].replace('_', ' ').capitalize()} for r in memory.records.values()], 'teaching_example': {'symptom': 'The browser refuses the connection at localhost:3000.', 'conditions': 'The terminal says the development server is ready at localhost:3001.', 'attempted_action': 'Refreshing the old localhost:3000 tab did not help. I opened the terminal\'s reported localhost:3001 URL.', 'outcome': 'Fictional demonstration: the page loaded at localhost:3001.', 'is_synthetic': True, 'recall_query': 'My server says it is running, but an old browser tab refuses the connection.'}}


@app.post('/api/recall')
async def recall(data: Recall, request: Request, response: Response):
    started = time.perf_counter()
    if not data.memory_enabled:
        return {'state': 'memory_off', 'headline': 'History is unavailable with memory off', 'next_step': 'Enable memory to retrieve recorded attempts and evidence. No retrieval query was made.', 'what_matches': [], 'failed_attempts': [], 'evidence': [], 'retrieved': [], 'matched_id': None, 'timings': {'moss_query_ms': 0, 'api_ms': round((time.perf_counter()-started)*1000, 3)}, 'native_query_count': 0}
    require_ready()
    if data.stage and data.stage not in {r['stage'] for r in memory.records.values()}:
        raise HTTPException(422, 'Choose a listed stage or leave it unspecified.')
    try:
        async with memory.serialized():
            token, visitor = memory.visitor(request.cookies.get('again_session'))
            memory.rate_check(visitor)
            hits, records, query_ms, calls = await memory.retrieve(visitor, data.query + ('\nCurrent conditions: ' + data.conditions if data.conditions else '') + ('\nFailure stage: ' + data.stage if data.stage else ''))
            context = analyze(list(memory.records.values()), data.query, data.conditions, data.stage)
            context['permission_error'] = bool(re.search(r'access\s+(?:is\s+)?denied|permission\s+denied|0x80070005', data.query, re.I))
            result = decide(records, context)
            evidence = [{k: v for k, v in r.items() if k in ('id','title','status','stage','observations','limits','sources','is_synthetic','conditions')} | {'applicable': result['state'] == 'matched' and result['matched_id'] == r['id']} for r in records]
            set_cookie(response, token, request)
            return {**result, 'evidence': evidence, 'retrieved': hits, 'native_query_count': calls, 'timings': {'moss_query_ms': query_ms, 'api_ms': round((time.perf_counter()-started)*1000, 3)}, 'timing_note': 'Moss query includes text embedding; scores are native ranking values, not confidence probabilities.'}
    except BusyError:
        raise
    except Exception as exc:
        print('Again recall failed:', type(exc).__name__, flush=True)
        raise HTTPException(503, 'The retrieval service could not complete this query. Please retry.') from None


@app.post('/api/teach')
async def teach(data: Teach, request: Request, response: Response):
    require_ready()
    started = time.perf_counter()
    try:
        async with memory.serialized():
            token, visitor = memory.visitor(request.cookies.get('again_session'))
            memory.rate_check(visitor)
            rid, index_ms = await memory.teach(visitor, data.model_dump())
            set_cookie(response, token, request)
            return {'ok': True, 'id': rid, 'status': 'user_reported', 'message': 'Indexed with Moss for this browser session. Try recalling it in different words.', 'indexed': True, 'timings': {'index_ms': index_ms, 'api_ms': round((time.perf_counter()-started)*1000, 3)}}
    except BusyError:
        raise
    except Exception as exc:
        print('Again teaching failed:', type(exc).__name__, flush=True)
        raise HTTPException(503, 'Moss could not index this memory. Nothing has been claimed as saved.') from None


@app.post('/api/forget')
async def forget(request: Request, response: Response):
    require_ready()
    async with memory.serialized():
        await memory.forget(request.cookies.get('again_session'))
    response.delete_cookie('again_session')
    return {'ok': True, 'message': 'Your session memories were removed.'}
