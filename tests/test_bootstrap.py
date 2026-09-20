from app.bootstrap import load_credentials


def test_private_allowlist_and_existing_environment_precedence(tmp_path,monkeypatch):
    p=tmp_path/'.env.local'
    p.write_text('MOSS_PROJECT_ID=fictional-id\nMOSS_PROJECT_KEY="fictional-key"\nUNRELATED_TEST_VALUE=do-not-load\n')
    monkeypatch.setenv('AGAIN_ENV_FILE',str(p))
    monkeypatch.setenv('MOSS_PROJECT_ID','already-set')
    monkeypatch.delenv('MOSS_PROJECT_KEY',raising=False)
    monkeypatch.delenv('UNRELATED_TEST_VALUE',raising=False)
    assert load_credentials()
    import os
    assert os.environ['MOSS_PROJECT_ID']=='already-set'
    assert os.environ['MOSS_PROJECT_KEY']=='fictional-key'
    assert 'UNRELATED_TEST_VALUE' not in os.environ


def test_missing_credentials_report_only_false(tmp_path,monkeypatch):
    monkeypatch.setenv('AGAIN_ENV_FILE',str(tmp_path/'absent'))
    monkeypatch.delenv('MOSS_PROJECT_ID',raising=False)
    monkeypatch.delenv('MOSS_PROJECT_KEY',raising=False)
    assert load_credentials() is False
