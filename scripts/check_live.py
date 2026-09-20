"""Check the deployed Again build using only public seeds and a fictional teaching note."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import statistics
import time
import httpx


def check(base_url, output):
    a=httpx.Client(base_url=base_url, timeout=90, follow_redirects=True)
    b=httpx.Client(base_url=base_url, timeout=90, follow_redirects=True)
    health=a.get('/api/health');health.raise_for_status();health=health.json()
    if not health.get('ready'):raise RuntimeError('Live Moss readiness has not passed')
    records=[]
    def recall(name, query, expected_state, expected_id=None, client=a, **extra):
        started=time.perf_counter();response=client.post('/api/recall',json={'query':query,**extra});elapsed=(time.perf_counter()-started)*1000
        result=response.json()
        passed=response.is_success and result.get('state')==expected_state and (expected_id is None or result.get('matched_id')==expected_id)
        records.append({'check':name,'passed':passed,'http_status':response.status_code,'http_roundtrip_ms':round(elapsed,3),'response':result})
        Path(output).parent.mkdir(parents=True,exist_ok=True)
        Path(output).write_text(json.dumps({'status':'in_progress','base_url':base_url,'records':records},indent=2)+'\n',encoding='utf-8')
        return result
    recall('lead_worker_launch','LaunchUnelevated says Access is denied. Administrator preflight passed and using the RunAs popup did not help.','matched','elevated_controller_worker_launch_denied')
    recall('paraphrase_worker','My elevated trace collector cannot spawn its normal-permission helper. What have we already tried?','matched','elevated_controller_worker_launch_denied')
    recall('button_preflight_example','My PowerShell prompt is in System32, but administrator_preflight says false.','matched','trace_controller_not_elevated',stage='administrator_preflight')
    recall('different_preflight_stage','WPR returned Access is denied. The controller token is not elevated.','matched','trace_controller_not_elevated',stage='administrator_preflight')
    recall('paraphrase_native_order','My native retrieval engine crashes only after I import PyTorch.','matched','moss_torch_import_order')
    recall('paraphrase_ram','My extraction stops immediately because it cannot meet the RAM preflight.','matched','extraction_ram_preflight')
    recall('ambiguous_error','Access is denied. What should I try next?','clarify')
    recall('unrelated_input','How do I roast broccoli for dinner?','no_match')
    off=recall('memory_off','LaunchUnelevated says Access is denied after administrator preflight passed.','memory_off',memory_enabled=False)
    records[-1]['passed'] &= off['native_query_count']==0 and not off['retrieved'] and not off['evidence']
    payload={'symptom':'The browser refuses the connection at localhost:3000.','conditions':'The terminal says the development server is ready at localhost:3001.','attempted_action':'Refreshing localhost:3000 did not help; I opened the reported localhost:3001 URL.','outcome':'Fictional demonstration: the page loaded at localhost:3001.','is_synthetic':True}
    response=a.post('/api/teach',json=payload);response.raise_for_status();taught=response.json();rid=taught['id']
    records.append({'check':'teach_native_index','passed':taught.get('indexed') is True,'response':taught})
    learned=recall('taught_paraphrase','My server says it is running, but an old browser tab refuses the connection.','clarify',rid)
    records[-1]['passed'] &= rid in [r['id'] for r in learned.get('retrieved', [])]
    other=recall('different_visitor_isolation','My server says it is running, but an old browser tab refuses the connection.','no_match',client=b)
    records[-1]['passed'] &= rid not in [r['id'] for r in other.get('retrieved', [])]
    recall('unrelated_after_teaching','How do I roast broccoli for dinner?','no_match')
    response=a.post('/api/forget');response.raise_for_status()
    forgotten=recall('forget_native_delete','My server says it is running, but an old browser tab refuses the connection.','no_match')
    records[-1]['passed'] &= rid not in [r['id'] for r in forgotten.get('retrieved', [])]
    query_times=[r['response']['timings']['moss_query_ms'] for r in records if r.get('response',{}).get('native_query_count',0)>0]
    report={'measured_utc':datetime.now(timezone.utc).isoformat(),'base_url':base_url,'status':'passed' if all(r['passed'] for r in records) else 'failed','checks_passed':sum(r['passed'] for r in records),'checks_total':len(records),'health':health,'query_including_embedding_ms':{'median':statistics.median(query_times),'min':min(query_times),'max':max(query_times),'n':len(query_times)},'method':'Sequential public-safe live API checks; each timing is real. Conditional/private requests may issue two native queries; this is a functional diagnostic, not a throughput benchmark. HTTP roundtrip is from the validation machine, not a browser timer.','records':records}
    Path(output).parent.mkdir(parents=True,exist_ok=True);Path(output).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('base_url','status','checks_passed','checks_total','query_including_embedding_ms')}))
    for r in records:
        if not r['passed']:print('Failed:',r['check'],'state=',r['response'].get('state'),'match=',r['response'].get('matched_id'))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base-url',required=True);parser.add_argument('--output',default='measurements/live_checks.json');args=parser.parse_args();raise SystemExit(check(args.base_url,args.output))
