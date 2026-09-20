"""Record the real public Again app with captions and genuine live requests.
No mocked responses, narration audio, playback retiming, or fabricated numbers.
Requires Playwright and its FFmpeg helper. Output is a captioned WebM.
Run only after live teaching/retrieval readiness has been verified.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
CAPTIONS=[
    'Again remembers what happened, so a familiar error does not send you back to a failed fix.',
    'This is a real recorded incident. The administrator check passed, but starting the ordinary worker failed.',
    'Two earlier attempts failed at the same stage. The source excerpts stay attached to the next step.',
    'Worker startup was repaired. The later trace was still unresolved. Again preserves that distinction.',
    'The same error at administrator preflight calls for a different action. Conditions matter.',
    'With memory off, Again makes zero retrieval queries. Past outcomes are honestly unavailable.',
    'Now a fictional teaching example: the browser uses port 3000, but the server reports port 3001.',
    'This outcome is saved as user reported and indexed by Moss, only for this browser session.',
    'Ask in different words. A live Moss query can recover the newly recorded outcome.',
    'Inspect the returned IDs and actual timings. Query embedding, backend time and browser time stay separate.',
    'Again. Stop repeating failed fixes.'
]

def run(base, chrome, output):
    output.mkdir(parents=True,exist_ok=True)
    events=[]; responses=[]; errors=[]; started=time.monotonic(); video=None
    def mark(kind, **fields): events.append({'elapsed_s':round(time.monotonic()-started,3),'kind':kind,**fields})
    def hold_until(seconds):
        left=seconds-(time.monotonic()-started)
        if left>0: page.wait_for_timeout(left*1000)
    def caption(index):
        value=CAPTIONS[index]
        page.evaluate("""text => { let box=document.getElementById('demo-caption'); if (!box) { box=document.createElement('div'); box.id='demo-caption'; box.setAttribute('role','note'); Object.assign(box.style,{position:'fixed',left:'50%',bottom:'22px',transform:'translateX(-50%)',width:'min(990px,90vw)',padding:'14px 20px',background:'rgba(12,20,14,.96)',color:'#f0f0df',border:'1px solid #5a7545',borderRadius:'10px',zIndex:'10000',font:'16px/1.5 Segoe UI,Arial,sans-serif',textAlign:'center',boxShadow:'0 8px 40px #0008',pointerEvents:'none'});document.body.append(box);}box.textContent=text;}""",value)
        mark('caption',index=index,text=value)
    def capture(response):
        if response.request.method=='POST' and any('/api/'+name in response.url for name in ['recall','teach']):
            try:
                data={'endpoint':response.url.split('/api/',1)[1],'http_status':response.status,'request':response.request.post_data_json,'response':response.json()}
                responses.append(data);mark('api_response',endpoint=data['endpoint'],http_status=data['http_status'])
                (output/'demo_api_evidence.json').write_text(json.dumps(responses,indent=2)+'\n',encoding='utf-8')
            except Exception as exc:errors.append(type(exc).__name__)
    def wait_recall(state=None):
        if state:expect(page.locator('#result-panel')).to_have_attribute('data-state',state,timeout=45000)
        else:expect(page.locator('#result-content')).to_be_visible(timeout=45000)
        expect(page.locator('#recall-button')).to_be_enabled(timeout=45000)
    result={'status':'incomplete','base_url':base,'recorded_utc':datetime.now(timezone.utc).isoformat(),'scope':'Real browser interactions with the public backend. Captions only; no audio narration, mocks, edited latency, or playback retiming.'}
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chrome,headless=True,args=['--disable-gpu'])
            context=browser.new_context(viewport={'width':1440,'height':1000},record_video_dir=str(output/'raw'),record_video_size={'width':1440,'height':1000},reduced_motion='reduce')
            page=context.new_page();video=page.video;page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',capture)
            page.goto(base,wait_until='networkidle',timeout=60000)
            expect(page.locator('#health-label')).to_have_text('Moss ready',timeout=30000)
            expect(page.locator('#try-example')).to_be_enabled()
            started=time.monotonic();caption(0);hold_until(6)
            page.locator('#try-example').click();caption(1);hold_until(12)
            page.locator('#recall-button').click();wait_recall('matched')
            lead=responses[-1]['response'];assert lead['matched_id']=='elevated_controller_worker_launch_denied' and lead['native_query_count']>0
            page.locator('#result-content').scroll_into_view_if_needed();caption(2);hold_until(21)
            page.locator('#result-content .source-link').first.click()
            page.locator('.source-excerpt[open]').first.evaluate("el => el.scrollIntoView({block:'center'})")
            caption(3)
            page.screenshot(path=str(output/'again-live-evidence.png'),full_page=False);hold_until(30)
            page.locator('#example-select').select_option(label='A System32 prompt does not prove administrator privileges')
            page.locator('#recall-button').click();wait_recall('matched')
            assert responses[-1]['response']['matched_id']=='trace_controller_not_elevated'
            page.locator('#result-content').scroll_into_view_if_needed();caption(4);hold_until(39)
            page.locator('#memory-enabled').uncheck();page.locator('#recall-button').click();wait_recall('memory_off')
            assert responses[-1]['response']['native_query_count']==0
            page.locator('#metrics-panel summary').click();page.locator('#metrics-panel').scroll_into_view_if_needed();caption(5);hold_until(47)
            page.locator('#teach-panel > summary').click();page.locator('#fill-teaching').click();caption(6)
            expect(page.locator('#teach-synthetic')).to_be_checked();page.locator('#teach-form').scroll_into_view_if_needed();hold_until(57)
            page.locator('#teach-button').click();expect(page.locator('#recall-taught')).to_be_visible(timeout=60000)
            saved=next(r for r in reversed(responses) if r['endpoint']=='teach')['response'];assert saved['indexed'] is True
            caption(7);hold_until(65)
            page.locator('#recall-taught').click()
            if not page.locator('#query').input_value():
                page.locator('#query').fill('My server says it is running, but an old browser tab refuses the connection.')
                page.locator('#conditions').fill('The terminal reports the development server ready at localhost:3001, while the old browser tab uses localhost:3000.')
            expect(page.locator('#memory-enabled')).to_be_checked();caption(8);hold_until(71)
            page.locator('#recall-button').click();wait_recall()
            recalled=responses[-1]['response'];assert recalled['native_query_count']>0 and any(row['id']==saved['id'] for row in recalled['retrieved'])
            assert any(row['id']==saved['id'] and row.get('is_synthetic') for row in recalled['evidence'])
            page.locator('#result-content').evaluate("el => el.scrollIntoView({block:'center'})")
            page.screenshot(path=str(output/'again-live-taught-memory.png'),full_page=False);hold_until(79)
            if page.locator('#metrics-panel').get_attribute('open') is None:page.locator('#metrics-panel summary').click()
            page.locator('#metrics-panel').scroll_into_view_if_needed();caption(9)
            page.screenshot(path=str(output/'again-live-teach-recall.png'),full_page=False);hold_until(88)
            page.locator('#page-title').scroll_into_view_if_needed();caption(10);hold_until(90)
            assert not errors,errors
            mark('finished')
            context.close();video.save_as(str(output/'again-demo.webm'));browser.close()
        result.update({'status':'passed','recording_run_elapsed_s':round(time.monotonic()-started,3),'planned_action_duration_s':90,'video':'again-demo.webm','teaching_is_synthetic':True,'new_incident_id':saved['id'],'native_recalled_new_id':True,'events':events,'page_errors':errors})
    except Exception as exc:
        result.update({'status':'failed','error_type':type(exc).__name__,'error':str(exc),'events':events,'page_errors':errors})
        raise
    finally:
        (output/'demo_recording.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':result['status'],'output':str(output),'events':len(events)}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True);p.add_argument('--chrome',default=r'C:\Program Files\Google\Chrome\Application\chrome.exe');p.add_argument('--output',type=Path,default=ROOT/'demo');a=p.parse_args();run(a.url,a.chrome,a.output)
