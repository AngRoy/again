"""Verify the recorded WebM is playable in installed Chrome; no external requests."""
import argparse
from datetime import datetime, timezone
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

def run(video, chrome, output):
    video=video.resolve();output=output.resolve()
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(video.parent),**kwargs)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chrome,headless=True,args=['--disable-gpu'])
            page=browser.new_page(viewport={'width':1440,'height':1000})
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            page.set_content('<video controls muted style="width:100%;height:100%"></video>')
            page.locator('video').evaluate('(v,url)=>fetch(url).then(r=>r.blob()).then(blob=>{v.src=URL.createObjectURL(blob);v.load();})',f'http://127.0.0.1:{server.server_port}/{video.name}')
            page.wait_for_function('document.querySelector("video") && Number.isFinite(document.querySelector("video").duration)',timeout=30000)
            metadata=page.locator('video').evaluate('(v)=>{v.pause();return {duration_s:v.duration,width:v.videoWidth,height:v.videoHeight,ready_state:v.readyState,error:v.error?{code:v.error.code,message:v.error.message}:null}}')
            assert metadata['duration_s']>80 and metadata['width']>0 and metadata['height']>0 and metadata['error'] is None
            seeks=[]
            for seconds in [5,25,55,78,87]:
                page.locator('video').evaluate('(v,t)=>new Promise((resolve,reject)=>{v.addEventListener("seeked",()=>resolve(),{once:true});v.addEventListener("error",()=>reject(new Error("video decode failed")),{once:true});v.currentTime=t;})',seconds)
                item=page.locator('video').evaluate('(v)=>({current_time_s:v.currentTime,ready_state:v.readyState,error:v.error?{code:v.error.code,message:v.error.message}:null})')
                assert item['ready_state']>=2 and item['error'] is None and abs(item['current_time_s']-seconds)<0.2,item
                seeks.append(item)
            browser.close()
        result={'status':'passed','checked_utc':datetime.now(timezone.utc).isoformat(),'scope':'Chrome loaded the actual local WebM and decoded seeks at five timestamps; no external queries, recompression or retiming.','file':video.name,'bytes':video.stat().st_size,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'metadata':metadata,'decoded_seek_checks':seeks,'verification_note':'The complete local file was fetched into a Blob before seeking, avoiding HTTP Range support requirements; actual current times are asserted against requested timestamps.'}
        output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
    finally:server.shutdown();server.server_close()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('video',type=Path);p.add_argument('--chrome',default=r'C:\Program Files\Google\Chrome\Application\chrome.exe');p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.video,a.chrome,a.output)
