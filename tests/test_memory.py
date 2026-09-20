"""Mutation cancellation and rollback contracts; no native worker or credentials."""
import asyncio
from types import SimpleNamespace
import pytest
from app.memory import MossMemory, BusyError, MAX_ADDITIONS

PAYLOAD={'symptom':'Fictional browser refuses connection','conditions':'Server is ready on port 3001',
         'attempted_action':'Opened the reported URL','outcome':'A fictional result','is_synthetic':True}


def setup():
    memory=MossMemory()
    memory.sdk=SimpleNamespace(DocumentInfo=lambda **kwargs:SimpleNamespace(**kwargs))
    token,visitor=memory.visitor(None)
    return memory,token,visitor


def test_repeated_cancellation_keeps_lock_and_commits_owner_before_propagating():
    async def run():
        memory,token,visitor=setup()
        native=set(); inserted=asyncio.Event(); release=asyncio.Event()
        async def add_docs(docs):
            native.update(d.id for d in docs); inserted.set()
            await release.wait()
            return len(docs),0
        async def delete_docs(ids):
            native.difference_update(ids);return len(ids)
        memory.private=SimpleNamespace(add_docs=add_docs,delete_docs=delete_docs)
        async def transaction():
            async with memory.serialized():
                return await memory.teach(visitor,PAYLOAD)
        task=asyncio.create_task(transaction())
        await inserted.wait()
        task.cancel();await asyncio.sleep(0)
        task.cancel();await asyncio.sleep(0)
        held=memory.lock.locked() and not task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):await task
        assert held
        assert not memory.lock.locked()
        assert native==set(visitor['records']) and len(native)==1
        assert not visitor['cleanup_ids']
        await memory.forget(token)
        assert not native and token not in memory.visitors
    asyncio.run(run())


@pytest.mark.parametrize('result',[(0,0),(0,1),(2,0)])
def test_nonexact_native_insert_count_rolls_back_and_never_claims_success(result):
    async def run():
        memory,_,visitor=setup();native=set()
        async def add_docs(docs):
            native.update(d.id for d in docs);return result
        async def delete_docs(ids):native.difference_update(ids);return len(ids)
        memory.private=SimpleNamespace(add_docs=add_docs,delete_docs=delete_docs)
        with pytest.raises(RuntimeError,match='native_insert_count_mismatch'):
            await memory.teach(visitor,PAYLOAD)
        assert not native and not visitor['records'] and not visitor['cleanup_ids']
    asyncio.run(run())


def test_partial_native_failure_rolls_back_inserted_id():
    async def run():
        memory,_,visitor=setup();native=set()
        async def add_docs(docs):
            native.update(d.id for d in docs);raise RuntimeError('native mutation failed')
        async def delete_docs(ids):native.difference_update(ids);return len(ids)
        memory.private=SimpleNamespace(add_docs=add_docs,delete_docs=delete_docs)
        with pytest.raises(RuntimeError):await memory.teach(visitor,PAYLOAD)
        assert not native and not visitor['records'] and not visitor['cleanup_ids']
    asyncio.run(run())


def test_failed_rollback_remains_owned_bounded_and_removable():
    async def run():
        memory,token,visitor=setup();native=set()
        async def add_docs(docs):
            native.update(d.id for d in docs);raise RuntimeError('native mutation failed')
        async def delete_failure(ids):raise RuntimeError('native deletion failed')
        memory.private=SimpleNamespace(add_docs=add_docs,delete_docs=delete_failure)
        for _ in range(MAX_ADDITIONS):
            with pytest.raises(RuntimeError):await memory.teach(visitor,PAYLOAD)
        assert native==visitor['cleanup_ids'] and len(native)==MAX_ADDITIONS
        assert not visitor['records']
        with pytest.raises(BusyError):await memory.teach(visitor,PAYLOAD)
        async def delete_success(ids):native.difference_update(ids);return len(ids)
        memory.private.delete_docs=delete_success
        await memory.forget(token)
        assert not native and token not in memory.visitors
    asyncio.run(run())


def test_cancelled_forget_completes_deletion_and_owner_removal():
    async def run():
        memory,token,visitor=setup();visitor['records']['one']={'id':'one'}
        native={'one'};inside=asyncio.Event();release=asyncio.Event()
        async def delete_docs(ids):
            native.difference_update(ids);inside.set();await release.wait();return len(ids)
        memory.private=SimpleNamespace(delete_docs=delete_docs)
        task=asyncio.create_task(memory.forget(token));await inside.wait();task.cancel()
        await asyncio.sleep(0);release.set()
        with pytest.raises(asyncio.CancelledError):await task
        assert not native and token not in memory.visitors
    asyncio.run(run())
