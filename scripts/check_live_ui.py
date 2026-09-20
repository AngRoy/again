"""Verify live seed recall, clarification, memory-off and responsive evidence UI.
No teaching, forgetting, credentials, mocked API, or invented measurements.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]

def run(base, chrome, output, explicit_preflight=False):
    output.mkdir(parents=True,exist_ok=True)
    responses=[]; errors=[]; checks=[]
    def capture(response):
        if '/api/recall' in response.url and response.request.method=='POST':
            try:
                responses.append({'http_status':response.status,'request':response.request.post_data_json,'response':response.json()})
                (output/'live_responses.json').write_text(json.dumps(responses,indent=2)+'\n',encoding='utf-8')
            except Exception as exc:
                errors.append('Response inspection failed: '+type(exc).__name__)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=chrome,headless=True,args=['--disable-gpu'])
        context=browser.new_context(viewport={'width':1440,'height':1080},reduced_motion='reduce')
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',capture)
        page.goto(base,wait_until='networkidle',timeout=60000)
        expect(page.locator('#health-label')).to_have_text('Moss ready',timeout=30000)
        expect(page.locator('#try-example')).to_be_enabled()
        page.screenshot(path=str(output/'live_desktop_initial.png'),full_page=True)
        checks.append('public UI reports genuine backend readiness')
        page.locator('#try-example').click()
        assert not responses
        page.locator('#recall-button').click()
        expect(page.locator('#result-panel')).to_have_attribute('data-state','matched',timeout=45000)
        assert responses[-1]['response']['matched_id']=='elevated_controller_worker_launch_denied'
        assert responses[-1]['response']['native_query_count']>0
        expect(page.locator('#result-content .status-badge')).to_have_text('Partially resolved')
        assert page.locator('.attempt').count()==2
        page.locator('#result-content .source-link').first.click()
        expect(page.locator('.source-excerpt[open] blockquote').first).to_contain_text('Both passed Administrator preflight')
        page.locator('#metrics-panel summary').click()
        expect(page.locator('#metrics-content')).to_contain_text('Native query calls:')
        responses[-1]['browser_visible_metrics']=page.locator('#metrics-content').inner_text()
        page.screenshot(path=str(output/'live_desktop_recall.png'),full_page=True)
        checks.append('lead incident retrieved genuinely; partial status, failed attempts, source excerpt and real metrics visible')
        page.locator('#example-select').select_option(label='A System32 prompt does not prove administrator privileges')
        if explicit_preflight:
            page.locator('#condition-preset').select_option('The controller token is not Administrator.')
        page.locator('#recall-button').click()
        expect(page.locator('.result-headline')).to_have_text('A System32 prompt does not prove administrator privileges',timeout=45000)
        assert responses[-1]['response']['matched_id']=='trace_controller_not_elevated'
        checks.append('administrator-preflight example retrieves a different applicable action')
        page.locator('#example-select').select_option(label='Same error, missing stage')
        page.locator('#recall-button').click()
        expect(page.locator('#result-panel')).to_have_attribute('data-state','clarify',timeout=45000)
        checks.append('ambiguous access-denied input requests clarification')
        page.locator('#memory-enabled').uncheck();page.locator('#recall-button').click()
        expect(page.locator('#result-panel')).to_have_attribute('data-state','memory_off',timeout=45000)
        assert responses[-1]['response']['native_query_count']==0
        assert not responses[-1]['response']['retrieved']
        expect(page.locator('#evidence-panel')).to_be_hidden()
        checks.append('memory-off response reports zero native queries and no retrieved records')
        page.set_viewport_size({'width':390,'height':844});page.reload(wait_until='networkidle')
        expect(page.locator('#try-example')).to_be_enabled()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(output/'live_mobile_initial.png'),full_page=True)
        page.locator('#try-example').click();page.locator('#recall-button').click()
        expect(page.locator('#result-panel')).to_have_attribute('data-state','matched',timeout=45000)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        responses[-1]['browser_visible_metrics']=page.locator('#metrics-content').inner_text()
        page.screenshot(path=str(output/'live_mobile_recall.png'),full_page=True)
        checks.append('390px live mobile initial/recall pages have no horizontal overflow')
        browser.close()
    assert not errors,errors
    result={'status':'passed','base_url':base,'checked_utc':datetime.now(timezone.utc).isoformat(),'scope':'Actual public-browser requests to the deployed backend; seed recall only. No teaching or deletion performed.','explicit_preflight_condition':explicit_preflight,'checks':checks,'page_errors':errors,'recall_requests':responses}
    (output/'live_ui_check.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'passed','checks':checks,'page_errors':errors,'requests':len(responses),'output':str(output)}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True);p.add_argument('--chrome',default=r'C:\Program Files\Google\Chrome\Application\chrome.exe');p.add_argument('--output',type=Path,default=ROOT/'tests/live_artifacts');p.add_argument('--explicit-preflight-condition',action='store_true');a=p.parse_args();run(a.url,a.chrome,a.output,a.explicit_preflight_condition)
