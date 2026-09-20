"""Add a synthetic voiceover to the verified real demo; never retime its footage.
Requires edge-tts==7.2.8 and imageio-ffmpeg==0.6.0 (editing only).
Public narration text is sent to Microsoft's online speech endpoint; no credentials are loaded.
"""
import asyncio,hashlib,json,subprocess,wave
from datetime import datetime,timezone
from pathlib import Path
import edge_tts,imageio_ffmpeg,numpy as np
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'demo/narration_work';WORK.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
VOICE='en-US-AriaNeural'
SEGMENTS=[
 (2.2,12.8,"Ever fixed the same error twice? Again remembers what you've tried, so you can pick up where you left off."),
 (15.0,24.0,"Here, the administrator check already passed. The problem is starting the worker. Again brings back the earlier failed attempts."),
 (24.5,33.0,"It keeps the outcome honest: worker startup was fixed, but the later trace was still unresolved."),
 (33.5,41.8,"Same error, different situation. If the administrator check failed, the next step changes. Context matters."),
 (42.3,49.6,"Switch memory off, and there's no pretend answer. Again says the history isn't available."),
 (50.0,60.0,"Now let's teach it something. In this fictional example, the browser is using the wrong port."),
 (61.0,68.0,"Save what you tried and what happened. Moss indexes the note for your browser session."),
 (68.5,80.5,"Next time, ask in your own words. Moss finds the note, and Again asks whether those same conditions apply."),
 (81.8,88.5,"You can inspect the sources, retrieved IDs, and real timings. No mystery answers."),
 (89.0,92.8,"Again. Stop repeating failed fixes."),
]
def run(cmd):
 r=subprocess.run(cmd,capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr[-2500:])
 return r
async def generate():
 sem=asyncio.Semaphore(3)
 async def one(i,text):
  path=WORK/f'{i:02}.mp3'
  fingerprint=hashlib.sha256((VOICE+'|'+text).encode()).hexdigest()
  marker=WORK/f'{i:02}.text.sha256'
  if path.exists() and marker.exists() and marker.read_text()==fingerprint:return
  async with sem:
   await edge_tts.Communicate(text,VOICE,rate='+0%').save(str(path))
   marker.write_text(fingerprint)
 await asyncio.gather(*(one(i,text) for i,(_,_,text) in enumerate(SEGMENTS)))
asyncio.run(generate())
rate=48000;mix=np.zeros(93*rate,dtype=np.float32);records=[]
for i,(start,end,text) in enumerate(SEGMENTS):
 src=WORK/f'{i:02}.mp3';raw=WORK/f'{i:02}.wav'
 run([FF,'-y','-i',str(src),'-ac','1','-ar',str(rate),str(raw)])
 with wave.open(str(raw),'rb') as w:samples=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
 # Remove only silent TTS padding. The screen recording is unchanged.
 active=np.flatnonzero(np.abs(samples)>0.002)
 if len(active):samples=samples[max(0,int(active[0])-int(.06*rate)):min(len(samples),int(active[-1])+int(.12*rate))]
 original_seconds=len(samples)/rate;slot=end-start
 factor=max(1.0,original_seconds/slot)
 if factor>1.18:raise RuntimeError(f'Narration segment {i} needs a shorter script: {original_seconds:.2f}s for {slot:.2f}s')
 if factor>1:
  trim=WORK/f'{i:02}-trim.wav'
  with wave.open(str(trim),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((samples*32767).astype(np.int16).tobytes())
  paced=WORK/f'{i:02}-paced.wav';run([FF,'-y','-i',str(trim),'-af',f'atempo={factor:.6f}','-ac','1','-ar',str(rate),str(paced)])
  with wave.open(str(paced),'rb') as w:samples=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
  samples=samples[:round(slot*rate)]
 at=round(start*rate);mix[at:at+len(samples)]+=samples
 records.append({'start_s':start,'end_s':round(start+len(samples)/rate,3),'text':text,'speech_pacing_factor':round(factor,6),'original_speech_s':round(original_seconds,3)})
voice=WORK/'voiceover.wav'
with wave.open(str(voice),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((np.clip(mix,-1,1)*32767).astype(np.int16).tobytes())
source=ROOT/'demo/again-demo.webm';target=ROOT/'demo/again-demo-narrated.mp4'
run([FF,'-y','-i',str(source),'-i',str(voice),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','20','-threads','4','-pix_fmt','yuv420p','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','160k','-ar','48000','-movflags','+faststart','-t','93',str(target)])
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
(ROOT/'demo/narration.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f"{stamp(r['start_s'])} --> {stamp(r['end_s'])}\n{r['text']}" for r in records)+'\n',encoding='utf-8')
report={'created_utc':datetime.now(timezone.utc).isoformat(),'file':target.name,'voice':VOICE,'voice_type':'Synthetic speech; not a human recording','speech_service':'Microsoft Edge online speech via edge-tts7.2.8; public script only','footage':'Original genuine 93-second screen recording; H.264 transcode, no footage retiming or result alteration','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'duration_s':93,'audio':'AAC160k,48kHz,normalized to-16LUFS target/-1.5dBTP','segments':records}
(ROOT/'demo/narration_metadata.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['file','bytes','sha256','duration_s','voice']},indent=2))
