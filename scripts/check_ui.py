"""Browser contract checks with explicit mocked API fixtures, never a live retrieval benchmark.
Run with the dev Playwright dependency and an existing Chrome installation.
Screenshots carry a visible TEST FIXTURE watermark and must not be used as demo evidence.
"""
import argparse
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def run(chrome, output):
    output.mkdir(parents=True, exist_ok=True)
    corpus = json.loads((ROOT / 'data/seed_incidents.json').read_text(encoding='utf-8'))
    records = {r['id']: r for r in corpus['incidents']}
    lead = records['elevated_controller_worker_launch_denied']
    second = records['trace_controller_not_elevated']
    requests = []
    errors = []
    checks = []
    taught = False

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)
        def do_GET(self):
            if self.path == '/':
                self.path = '/static/index.html'
            return super().do_GET()
        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'

    def route_api(route):
        nonlocal taught
        path = route.request.url.split('/api/', 1)[1]
        body = route.request.post_data_json if route.request.method == 'POST' else None
        requests.append({'path': path, 'body': body})
        if path == 'health':
            data = {'status': 'ready', 'ready': True, 'seed_count': 7, 'teaching_enabled': True, 'cold_ready_ms': 1234.5, 'model': 'moss-minilm', 'message': 'MOCKED TEST FIXTURE: no real Moss query.'}
        elif path == 'examples':
            data = {'examples': [{'id': r['id'], 'label': r['title'], 'query': r['demo_queries'][0], 'stage': r['stage'], 'conditions': ''} for r in [lead, second]], 'stages': [], 'teaching_example': {'symptom': 'The browser refuses localhost:3000.', 'conditions': 'Terminal is ready at localhost:3001.', 'attempted_action': 'I opened the reported port 3001 URL.', 'outcome': 'Fictional: the page loaded.', 'is_synthetic': True}}
        elif path == 'recall':
            if 'unavailable test' in body['query']:
                route.fulfill(status=503, content_type='application/json', body=json.dumps({'detail': 'Fixture service unavailable.'}))
                return
            if not body['memory_enabled']:
                data = {'state': 'memory_off', 'headline': 'History is unavailable with memory off', 'next_step': 'Enable memory to retrieve recorded attempts and evidence. No retrieval query was made.', 'evidence': [], 'retrieved': [], 'timings': {'moss_query_ms': 0, 'api_ms': .2}, 'native_query_count': 0}
            elif body['stage'] == 'administrator_preflight':
                data = matched(second)
            elif not body['stage']:
                data = {'state': 'clarify', 'headline': 'The failure stage matters', 'next_step': 'Which stage failed: administrator preflight or ordinary-worker launch?', 'evidence': [lead | {'applicable': False}], 'retrieved': [{'id': lead['id'], 'score': .8}], 'timings': {'moss_query_ms': 1.5, 'api_ms': 2}, 'native_query_count': 1}
            else:
                data = matched(lead)
            if '<img' in body['query']:
                data['next_step'] = body['query']
        elif path == 'teach':
            taught = True
            data = {'ok': True, 'id': 'fixture-user-1', 'indexed': True, 'message': 'TEST FIXTURE: indexing simulated.'}
        elif path == 'forget':
            taught = False
            data = {'ok': True, 'message': 'Your session memories were removed.'}
        else:
            route.fulfill(status=404, content_type='application/json', body='{"detail":"Unknown fixture route"}')
            return
        route.fulfill(status=200, content_type='application/json', body=json.dumps(data))

    def matched(record):
        return {'state': 'matched', 'headline': record['title'], 'next_step': record['next_step'], 'what_matches': ['Stage: ' + record['stage']], 'failed_attempts': record['failed_attempts'], 'evidence': [record | {'applicable': True}], 'retrieved': [{'id': record['id'], 'score': .925}], 'matched_id': record['id'], 'timings': {'moss_query_ms': 1.5, 'api_ms': 2}, 'native_query_count': 1}

    def screenshot(page, name):
        page.evaluate("""() => { if (!document.getElementById('test-watermark')) { const b=document.createElement('div'); b.id='test-watermark'; b.textContent='UI TEST FIXTURE / NO LIVE RETRIEVAL'; b.style.cssText='position:fixed;bottom:0;left:0;right:0;padding:7px;text-align:center;background:#692a24;color:white;z-index:9999;font:11px monospace'; document.body.append(b); } }""")
        page.screenshot(path=str(output / name), full_page=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chrome, headless=True, args=['--disable-gpu'])
            context = browser.new_context(viewport={'width': 1440, 'height': 1080}, reduced_motion='reduce')
            context.route('**/api/**', route_api)
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base)
            expect(page.locator('#health-label')).to_have_text('Moss ready')
            expect(page.locator('#try-example')).to_be_enabled()
            assert not [x for x in requests if x['path'] == 'recall']
            page.keyboard.press('Tab')
            expect(page.locator('.skip-link')).to_be_focused()
            assert page.locator('.skip-link').evaluate('(el)=>getComputedStyle(el).opacity') == '1'
            page.keyboard.press('Tab')
            assert page.locator('.skip-link').evaluate('(el)=>getComputedStyle(el).opacity') == '0'
            checks.append('keyboard skip link is visible only when focused')
            screenshot(page, 'ui_fixture_desktop_empty.png')
            checks.append('initial render and health; no automatic recall')
            page.locator('#try-example').click()
            expect(page.locator('#query')).to_have_value(lead['demo_queries'][0])
            assert not [x for x in requests if x['path'] == 'recall']
            page.locator('#query').press('Control+Enter')
            expect(page.locator('#result-panel')).to_have_attribute('data-state', 'matched')
            expect(page.locator('#result-content .status-badge')).to_have_text('Partially resolved')
            assert page.locator('.attempt').count() == 2
            assert requests[-1]['body']['stage'] == 'unelevated_worker_ready'
            checks.append('example fills only; keyboard recall; actual response status and attempts')
            page.locator('#result-content .source-link').first.click()
            assert page.locator('.source-excerpt[open]').count() >= 1
            expect(page.locator('.source-excerpt[open] blockquote').first).to_contain_text('Both passed Administrator preflight')
            page.locator('#metrics-panel summary').click()
            expect(page.locator('#metrics-content')).to_contain_text('Native query calls: 1')
            expect(page.locator('#metrics-content')).to_contain_text(lead['id'])
            screenshot(page, 'ui_fixture_desktop_recall.png')
            checks.append('source links open excerpts; query/API/browser timing and returned IDs')
            page.locator('#stage').select_option('administrator_preflight')
            expect(page.locator('#result-stale')).to_be_visible()
            page.locator('#recall-button').click()
            expect(page.locator('.result-headline')).to_have_text(second['title'])
            checks.append('stage change is sent and old result is marked stale')
            page.locator('#stage').select_option('')
            page.locator('#recall-button').click()
            expect(page.locator('#result-panel')).to_have_attribute('data-state', 'clarify')
            expect(page.locator('#context-details')).to_have_attribute('open', '')
            checks.append('clarification opens context without inventing a fix')
            page.locator('#memory-enabled').uncheck()
            page.locator('#recall-button').click()
            expect(page.locator('#result-panel')).to_have_attribute('data-state', 'memory_off')
            assert requests[-1]['body']['memory_enabled'] is False
            expect(page.locator('#evidence-panel')).to_be_hidden()
            checks.append('memory-off request disables retrieval in contract and removes previous evidence')
            page.locator('#memory-enabled').check()
            page.locator('#stage').select_option('unelevated_worker_ready')
            attack = '<img src=x onerror="window.XSS_TEST=1"> access denied'
            page.locator('#query').fill(attack)
            page.locator('#recall-button').click()
            expect(page.locator('.next-step p')).to_have_text(attack)
            assert page.locator('#result-content img').count() == 0
            assert page.evaluate('window.XSS_TEST') is None
            checks.append('HTML-shaped response text renders inertly')
            page.locator('#teach-panel > summary').click()
            page.locator('#fill-teaching').click()
            expect(page.locator('#teach-synthetic')).to_be_checked()
            page.locator('#teach-button').click()
            expect(page.locator('#teach-message')).to_contain_text('Fictional / user reported')
            assert taught and any(x['path'] == 'teach' and x['body']['is_synthetic'] is True for x in requests)
            checks.append('fictional teaching payload and indexed confirmation; no verified-success label')
            page.locator('#recall-taught').click()
            expect(page.locator('#query')).to_have_value('')
            expect(page.locator('#query')).to_be_focused()
            page.locator('#forget-button').click()
            expect(page.locator('#teach-message')).to_contain_text('removed')
            assert not taught
            expect(page.locator('#result-empty')).to_be_visible()
            checks.append('paraphrase prompt uses new input; forgetting clears stale session evidence')
            page.locator('#query').fill('unavailable test')
            page.locator('#recall-button').click()
            expect(page.locator('#recall-error')).to_have_text('Fixture service unavailable.')
            expect(page.locator('#recall-button')).to_be_enabled()
            checks.append('failed service request shows error and allows retry without fabricated result')
            page.set_viewport_size({'width': 390, 'height': 844})
            page.reload()
            expect(page.locator('#try-example')).to_be_enabled()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            screenshot(page, 'ui_fixture_mobile_empty.png')
            page.locator('#try-example').click(); page.locator('#recall-button').click()
            expect(page.locator('#result-panel')).to_have_attribute('data-state', 'matched')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            screenshot(page, 'ui_fixture_mobile_recall.png')
            checks.append('390px mobile layout has no horizontal overflow before and after recall')
            browser.close()
        assert not errors, errors
        result = {'status': 'passed', 'scope': 'Mocked API browser contract checks only; no genuine Moss queries, deployment verification, or performance measurements.', 'checks': checks, 'page_errors': errors, 'screenshot_policy': 'All screenshots visibly watermarked TEST FIXTURE; not demo evidence.'}
        (output / 'ui_check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result))
    finally:
        server.shutdown(); server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chrome', default=r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    parser.add_argument('--output', type=Path, default=ROOT / 'tests/artifacts')
    args = parser.parse_args()
    run(args.chrome, args.output)
