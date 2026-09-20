import asyncio
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app import main
from app.memory import MossMemory, BusyError, MAX_ADDITIONS


class FakeOptions:
    def __init__(self, **kwargs):self.__dict__.update(kwargs)


class FakeDocs:
    def __init__(self, **kwargs):self.__dict__.update(kwargs)


class FakeSession:
    def __init__(self, hits=None):self.hits=hits or [];self.queries=[];self.added=[];self.deleted=[]
    async def query(self,text,options):
        self.queries.append((text,options))
        return SimpleNamespace(docs=[SimpleNamespace(id=k,score=1.0) for k in self.hits])
    async def add_docs(self,docs):self.added.extend(docs);return len(docs),0
    async def delete_docs(self,ids):self.deleted.extend(ids);return len(ids)


@pytest.fixture
def memory(monkeypatch):
    m=MossMemory();m.ready=True
    m.sdk=SimpleNamespace(QueryOptions=FakeOptions,DocumentInfo=FakeDocs)
    m.seed=FakeSession(['elevated_controller_worker_launch_denied','trace_controller_not_elevated'])
    m.private=FakeSession()
    monkeypatch.setattr(main,'memory',m)
    return m


def test_memory_off_really_makes_no_native_query(memory):
    c=TestClient(main.app)
    r=c.post('/api/recall',json={'query':'Access is denied','memory_enabled':False})
    assert r.status_code==200 and r.json()['native_query_count']==0
    assert not memory.seed.queries and not memory.private.queries
    assert not r.json()['evidence']


def test_recalls_only_retrieved_applicable_evidence(memory):
    c=TestClient(main.app)
    r=c.post('/api/recall',json={'query':'LaunchUnelevated Access is denied. Administrator preflight passed.'})
    assert r.status_code==200
    assert r.json()['matched_id']=='elevated_controller_worker_launch_denied'
    assert r.json()['native_query_count']==1
    assert len(memory.seed.queries)==1
    assert memory.seed.queries[0][1].alpha==1.0
    assert 'httponly' in r.headers['set-cookie'].lower()
    assert all('MOSS_PROJECT_KEY' not in str(v) for v in r.json().values())


def test_input_limits_and_cross_site_rejection(memory):
    c=TestClient(main.app)
    assert c.post('/api/recall',json={'query':'x'*4001}).status_code==422
    assert c.post('/api/recall',json={'query':'Access is denied','surprise':1}).status_code==422
    assert c.post('/api/recall',content=b'x'*17000,headers={'content-type':'application/json'}).status_code==413
    assert c.post('/api/recall',json={'query':'Access is denied'},headers={'sec-fetch-site':'cross-site'}).status_code==403
    assert not memory.seed.queries


def test_private_native_filter_and_ownership_defense(memory):
    async def run():
        a,va=memory.visitor(None);b,vb=memory.visitor(None)
        va['records']['own']={'id':'own'};vb['records']['other']={'id':'other'}
        memory.private.hits=['other','own']
        hits,records,_,calls=await memory.retrieve(va,'a public-safe test query')
        assert calls==2
        assert memory.private.queries[0][1].filter=={'$and':[{'field':'visitor_id','condition':{'$eq':va['id']}}]}
        assert 'other' not in [r['id'] for r in hits]
        assert 'other' not in [r['id'] for r in records]
    asyncio.run(run())


def test_teach_is_private_bounded_and_forget_deletes_native_docs(memory):
    a=TestClient(main.app);b=TestClient(main.app)
    payload={'symptom':'Fictional browser error','conditions':'Server uses a different port','attempted_action':'Opened the advertised server URL','outcome':'Fictional page loaded','is_synthetic':True}
    ids=[]
    for _ in range(MAX_ADDITIONS):
        r=a.post('/api/teach',json=payload);assert r.status_code==200;ids.append(r.json()['id'])
    assert a.post('/api/teach',json=payload).status_code==429
    memory.private.hits=ids
    rb=b.post('/api/recall',json={'query':'Fictional browser error'}).json()
    assert not any(r['id'] in ids for r in rb['retrieved'])
    assert not memory.private.queries
    assert a.post('/api/forget').status_code==200
    assert set(memory.private.deleted)==set(ids)
    assert not a.cookies.get('again_session')


def test_expiration_deletes_native_docs_before_removing_owner(memory):
    async def run():
        token,visitor=memory.visitor(None)
        visitor['records']['expired']={'id':'expired'};visitor['last_seen']-=3601
        await memory.expire()
        assert token not in memory.visitors
        assert memory.private.deleted==['expired']
    asyncio.run(run())


def test_unready_never_returns_fake_retrieval(memory):
    memory.ready=False
    c=TestClient(main.app)
    assert c.get('/api/health').json()['ready'] is False
    assert c.post('/api/recall',json={'query':'Access is denied'}).status_code==503
    assert not memory.seed.queries
