"""Policy and API checks use isolated fakes; live Moss checks are recorded separately."""
import json
from pathlib import Path
import pytest
from app.policy import analyze, decide

DATA=json.loads((Path(__file__).resolve().parents[1]/'data/seed_incidents.json').read_text(encoding='utf-8-sig'))
RECORDS=DATA['incidents']
BYID={r['id']:r for r in RECORDS}

def run(text, ids, stage=None, conditions=''):
    c=analyze(RECORDS,text,conditions,stage)
    c['permission_error']='access is denied' in text.lower()
    return decide([BYID[i] for i in ids],c)


def test_worker_launch_requires_retrieved_incident_and_actual_conditions():
    query='LaunchUnelevated says Access is denied. Administrator preflight passed and using the RunAs popup did not help.'
    result=run(query,['trace_controller_not_elevated','elevated_controller_worker_launch_denied'])
    assert result['state']=='matched'
    assert result['matched_id']=='elevated_controller_worker_launch_denied'
    assert len(result['failed_attempts'])==2
    assert 'ordinary coordinator' in result['next_step']
    assert run(query,['numpy_first_query_commit_jump'])['state']=='no_match'


def test_same_error_at_administrator_stage_does_not_select_worker_fix():
    result=run('WPR Access is denied. The controller token is not elevated.',['elevated_controller_worker_launch_denied','trace_controller_not_elevated'],stage='administrator_preflight')
    assert result['state']=='matched'
    assert result['matched_id']=='trace_controller_not_elevated'


def test_missing_stage_asks_instead_of_recommending_elevation():
    result=run('Access is denied. What now?',['trace_controller_not_elevated','elevated_controller_worker_launch_denied'])
    assert result['state']=='clarify'
    assert not result['failed_attempts']


def test_contradictory_current_admin_facts_require_clarification():
    result=run('Administrator preflight passed, but controller_windows_administrator=false.',['elevated_controller_worker_launch_denied','trace_controller_not_elevated'])
    assert result['state']=='clarify'
    assert result['headline']=='These conditions conflict'


def test_native_import_requires_order_not_only_error_word():
    result=run('Moss DLL initialization fails on Windows.',['moss_torch_import_order'])
    assert result['state']=='clarify'
    result=run('My native retrieval engine crashes only after I import PyTorch.',['moss_torch_import_order'])
    assert result['state']=='matched'


def test_unknown_input_abstains_even_when_moss_returns_candidates():
    assert run('How do I roast broccoli for dinner?',list(BYID))['state']=='no_match'


def test_actual_outcome_status_is_never_upgraded():
    assert BYID['elevated_controller_worker_launch_denied']['status']=='partially_resolved'
    assert BYID['controller_startup_confirmation_missing']['status']=='unresolved'
    assert BYID['numpy_first_query_commit_jump']['status']=='diagnosed'
    assert DATA['synthetic_teaching_example']['id'] not in BYID


def test_empty_retrieval_cannot_emit_a_fix():
    assert run('Administrator preflight passed, LaunchUnelevated Access is denied',[])['state']=='no_match'


@pytest.mark.parametrize('platform', ['Linux', 'Ubuntu', 'macOS'])
def test_explicit_other_os_does_not_reuse_windows_native_repair(platform):
    result=run('The native SDK DLL initialization fails after I import PyTorch.', ['moss_torch_import_order'], conditions='The failing host is running '+platform)
    assert result['state']=='clarify'
    assert result['headline']=='Check the affected environment'
    assert result['matched_id'] is None
    assert not result['failed_attempts']


def test_mixed_host_descriptions_need_environment_clarification():
    result=run('Windows WPR Access is denied on Linux. The controller token is not elevated.', ['trace_controller_not_elevated'], stage='administrator_preflight')
    assert result['headline']=='Check the affected environment'


def test_explicit_matching_os_and_negated_other_os_preserve_verified_case():
    result=run('Moss DLL initialization fails after I import PyTorch on Windows, not Linux.', ['moss_torch_import_order'])
    assert result['state']=='matched'
    assert result['matched_id']=='moss_torch_import_order'


def test_platform_word_alone_cannot_turn_unrelated_history_into_a_diagnosis():
    assert run('How do I cook broccoli on Linux?',list(BYID))['state']=='no_match'
