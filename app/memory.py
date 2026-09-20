"""Genuine Moss text sessions, serial native operations, and bounded visitor isolation."""
import asyncio
from contextlib import asynccontextmanager
import hashlib
import json
import os
from pathlib import Path
import secrets
import time
import uuid

from .bootstrap import load_credentials, load_sdk

ROOT = Path(__file__).resolve().parents[1]
TTL_SECONDS = 3600
MAX_VISITORS = 100
MAX_ADDITIONS = 5


class BusyError(Exception):
    pass


async def finish_native(awaitable):
    # Do not release the serialization lock while an SDK to_thread call still runs.
    task = asyncio.create_task(awaitable)
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        try:
            await task
        finally:
            raise


class MossMemory:
    def __init__(self):
        self.data = json.loads((ROOT / 'data/seed_incidents.json').read_text(encoding='utf-8-sig'))
        self.records = {r['id']: r for r in self.data['incidents']}
        self.lock = asyncio.Lock()
        self.ready = False
        self.error = None
        self.started_at = time.perf_counter()
        self.cold_ready_ms = None
        self.native_calls = 0
        self.visitors = {}
        self.sdk = self.client = self.seed = self.private = None

    async def start(self):
        try:
            if not load_credentials():
                raise RuntimeError('missing_runtime_credentials')
            self.sdk = load_sdk()
            self.client = self.sdk.MossClient(os.environ['MOSS_PROJECT_ID'], os.environ['MOSS_PROJECT_KEY'])
            self.seed = await self.client.session('again-seeds-' + uuid.uuid4().hex, model_id='moss-minilm')
            docs = [self.sdk.DocumentInfo(id=r['id'], text=self.document_text(r)) for r in self.records.values()]
            await self.seed.add_docs(docs)
            self.private = await self.client.session('again-visitors-' + uuid.uuid4().hex, model_id='moss-minilm')
            hits = await self.seed.query('An administrator collector cannot launch an ordinary helper after preflight passed.', self.sdk.QueryOptions(top_k=3, alpha=1.0))
            self.native_calls += 1
            if not hits.docs or self.seed.doc_count != len(self.records):
                raise RuntimeError('readiness_query_failed')
            self.cold_ready_ms = round((time.perf_counter() - self.started_at) * 1000, 3)
            self.ready = True
        except Exception as exc:
            # Native error strings may contain configuration; never return them to public clients.
            self.error = 'Moss could not become ready. Check private server configuration and restart.'
            print('Again startup failed:', type(exc).__name__, flush=True)

    @staticmethod
    def document_text(r):
        return '\n'.join([r['title'], r.get('search_text', ''), 'Stage: ' + r['stage'], *r.get('observations', []), r.get('next_step', '')])

    @asynccontextmanager
    async def serialized(self):
        try:
            await asyncio.wait_for(self.lock.acquire(), 8)
        except asyncio.TimeoutError:
            raise BusyError('The demo is busy. Please retry in a few seconds.') from None
        try:
            await self.expire()
            yield
        finally:
            self.lock.release()

    async def expire(self):
        now = time.monotonic()
        expired = [key for key, value in self.visitors.items() if now - value['last_seen'] > TTL_SECONDS]
        for key in expired:
            visitor = self.visitors[key]
            if visitor['records']:
                await finish_native(self.private.delete_docs(list(visitor['records'])))
            del self.visitors[key]

    def visitor(self, cookie):
        if cookie in self.visitors:
            self.visitors[cookie]['last_seen'] = time.monotonic()
            return cookie, self.visitors[cookie]
        if len(self.visitors) >= MAX_VISITORS:
            raise BusyError('The demo has reached its session limit. Please try later.')
        token = secrets.token_urlsafe(32)
        value = {'id': uuid.uuid4().hex, 'last_seen': time.monotonic(), 'records': {}, 'requests': []}
        self.visitors[token] = value
        return token, value

    def rate_check(self, visitor):
        now = time.monotonic()
        visitor['requests'] = [t for t in visitor['requests'] if now - t < 60]
        if len(visitor['requests']) >= 30:
            raise BusyError('Please wait a minute before sending more demo requests.')
        visitor['requests'].append(now)

    async def retrieve(self, visitor, text):
        start = time.perf_counter()
        seed_hits = await finish_native(self.seed.query(text, self.sdk.QueryOptions(top_k=5, alpha=1.0)))
        self.native_calls += 1
        native_queries = 1
        hits = [{'id': d.id, 'score': float(d.score), 'scope': 'public_seed'} for d in seed_hits.docs if d.id in self.records]
        records = dict(self.records)
        if visitor['records']:
            # Native filtering AND ownership post-check: one visitor never sees another's text/IDs.
            private_hits = await finish_native(self.private.query(text, self.sdk.QueryOptions(top_k=3, alpha=1.0, filter={'visitor_id': visitor['id']})))
            self.native_calls += 1
            native_queries += 1
            own = [{'id': d.id, 'score': float(d.score), 'scope': 'your_session'} for d in private_hits.docs if d.id in visitor['records']]
            records.update(visitor['records'])
            # Scores from distinct native sessions need not be calibrated. Keep each rank explicit.
            # A private hit is offered as a condition-check question, never as verified repair.
            hits = own + hits
        return hits, [records[h['id']] for h in hits], round((time.perf_counter() - start) * 1000, 3), native_queries

    async def teach(self, visitor, data):
        if len(visitor['records']) >= MAX_ADDITIONS:
            raise BusyError('This session already has five memories. Clear them to start again.')
        rid = 'memory_' + uuid.uuid4().hex
        label = 'Fictional demonstration' if data['is_synthetic'] else 'Your reported incident'
        record = {'id': rid, 'title': label + ': ' + data['symptom'][:90], 'search_text': data['symptom'] + ' ' + data['conditions'], 'stage': 'user_reported', 'status': 'synthetic_user_reported' if data['is_synthetic'] else 'user_reported', 'is_synthetic': data['is_synthetic'], 'provenance_class': 'visitor_reported', 'conditions': data['conditions'], 'observations': ['Symptom: ' + data['symptom'], 'Conditions: ' + data['conditions'], 'Attempted action: ' + data['attempted_action'], 'User-reported outcome: ' + data['outcome']], 'failed_attempts': [], 'next_step': 'Compare your current conditions with this user-reported outcome before reusing the action.', 'limits': ['User-reported; not independently verified.', 'Visible only in this browser session; expires after one hour of inactivity or a server restart.'], 'sources': [{'id': rid + '_note', 'document': 'Your session note', 'section': label, 'excerpt': '\n'.join([data['symptom'], data['conditions'], data['attempted_action'], data['outcome']]), 'excerpt_type': 'fictional_note' if data['is_synthetic'] else 'user_report'}]}
        started = time.perf_counter()
        await finish_native(self.private.add_docs([self.sdk.DocumentInfo(id=rid, text=self.document_text(record), metadata={'visitor_id': visitor['id']})]))
        visitor['records'][rid] = record
        return rid, round((time.perf_counter() - started) * 1000, 3)

    async def forget(self, token):
        visitor = self.visitors.get(token)
        if visitor:
            if visitor['records']:
                await finish_native(self.private.delete_docs(list(visitor['records'])))
            del self.visitors[token]
