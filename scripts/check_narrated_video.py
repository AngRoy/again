"""Check the finalized narrated MP4 in Chrome, including the audio stream."""
import hashlib,json,threading
from datetime import datetime,timezone
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
video=root/'demo/again-demo-narrated.mp4'
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(video.parent),**kw)
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True,args=['--disable-gpu','--autoplay-policy=no-user-gesture-required'])
  page=browser.new_page(viewport={'width':1440,'height':1000})
  page.goto(f'http://127.0.0.1:{server.server_port}/')
  page.set_content('<video controls muted style="width:100%;height:100%"></video>')
  page.locator('video').evaluate('(v,url)=>fetch(url).then(r=>r.blob()).then(b=>{v.src=URL.createObjectURL(b);v.load();})',f'http://127.0.0.1:{server.server_port}/{video.name}')
  page.wait_for_function('Number.isFinite(document.querySelector("video").duration)',timeout=30000)
  meta=page.locator('video').evaluate('(v)=>({duration_s:v.duration,width:v.videoWidth,height:v.videoHeight,error:v.error?{code:v.error.code,message:v.error.message}:null})')
  assert 92.9<=meta['duration_s']<=93.2 and meta['width']==1440 and meta['height']==1000 and meta['error'] is None,meta
  seeks=[]
  for t in [5,25,55,78,90]:
   page.locator('video').evaluate('(v,t)=>new Promise((resolve,reject)=>{v.addEventListener("seeked",()=>resolve(),{once:true});v.addEventListener("error",()=>reject(new Error("decode failed")),{once:true});v.currentTime=t;})',t)
   row=page.locator('video').evaluate('(v)=>({current_time_s:v.currentTime,ready_state:v.readyState,error:v.error?{code:v.error.code,message:v.error.message}:null})')
   assert abs(row['current_time_s']-t)<.2 and row['ready_state']>=2 and row['error'] is None,row
   seeks.append(row)
  page.locator('video').evaluate('(v)=>{v.currentTime=5;return v.play();}')
  page.wait_for_timeout(1200)
  sound=page.locator('video').evaluate('(v)=>{const s=v.captureStream();return {audio_tracks:s.getAudioTracks().map(t=>({kind:t.kind,enabled:t.enabled,ready_state:t.readyState})),decoded_audio_bytes:v.webkitAudioDecodedByteCount??null,decoded_video_bytes:v.webkitVideoDecodedByteCount??null,current_time_s:v.currentTime,paused:v.paused,error:v.error?{code:v.error.code,message:v.error.message}:null}}')
  assert len(sound['audio_tracks'])==1 and sound['audio_tracks'][0]['ready_state']=='live' and sound['paused'] is False and sound['current_time_s']>5.5 and sound['error'] is None,sound
  assert sound['decoded_audio_bytes'] is not None and sound['decoded_audio_bytes']>0,sound
  browser.close()
 report={'status':'passed','checked_utc':datetime.now(timezone.utc).isoformat(),'file':video.name,'bytes':video.stat().st_size,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'metadata':meta,'decoded_seek_checks':seeks,'audio_playback':sound,'scope':'Actual completed MP4 loaded into Chrome from a full local Blob; exact five seek positions, moving playback, live audio track and decoded audio bytes verified. Audio levels are a separate FFmpeg check. No external calls or footage changes.'}
 (root/'demo/narrated_video_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report))
finally:server.shutdown();server.server_close()
