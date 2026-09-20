"""Package only the standalone repository's tracked, public-safe submission files."""
from pathlib import Path
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
import subprocess
from urllib.parse import quote,quote_plus
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PRIVATE_NAMES={'MOSS_PROJECT_ID','MOSS_PROJECT_KEY','RENDER_API_KEY','HF_TOKEN','GITHUB_TOKEN','GH_TOKEN'}


def package(output,private_env=None):
    git=['git','-c','safe.directory='+ROOT.as_posix()]
    if subprocess.check_output(git+['status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip():
        raise RuntimeError('Commit the final public files before packaging; tracked worktree changes remain')
    names=[n for n in subprocess.check_output(git+['ls-files','-z'],cwd=ROOT).decode().split('\0') if n]
    required={'README.md','PRD.md','ARCHITECTURE.md','architecture.png','architecture.svg','DEMO_AND_SUBMISSION.md','SUBMISSION_READY.md','requirements.txt','.env.example','Dockerfile','render.yaml','app/main.py','app/memory.py','data/seed_incidents.json','measurements/live_checks.json','measurements/app_tests.xml','demo/again-demo.webm'}
    if not required <= set(names):raise RuntimeError('Commit the complete public submission before packaging: '+str(sorted(required-set(names))))
    values={os.environ[k] for k in PRIVATE_NAMES if os.environ.get(k)}
    if private_env:
        for line in Path(private_env).read_text(encoding='utf-8-sig').splitlines():
            key,sep,value=line.strip().partition('=')
            if sep and key in PRIVATE_NAMES and value.strip():
                value=value.strip()
                if len(value)>1 and value[0]==value[-1] and value[0] in ('\"',"'"):value=value[1:-1]
                values.add(value)
    variants={v.encode('utf-8') for value in values for v in (value,quote(value,safe=''),quote_plus(value),json.dumps(value)[1:-1])}
    records={};payload={}
    for name in names:
        p=Path(name)
        if p.name.startswith('.env') and p.name!='.env.example':raise RuntimeError('Private environment file in public selection')
        if p.parts[0] in ('.git','.venv','.runtime','logs') or any(part in p.parts for part in ('raw','previous_take','final_take','__pycache__')):raise RuntimeError('Private/runtime/duplicate capture selected: '+name)
        if p.suffix in ('.etl','.safetensors','.bin','.npz'):raise RuntimeError('Research/model artifact selected: '+name)
        data=(ROOT/name).read_bytes()
        if any(v in data for v in variants):raise RuntimeError('Configured-secret scanner rejected a selected file: '+name)
        payload[name]=data;records[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'source_commit':subprocess.check_output(git+['rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'deployed_app':'https://again-fl36.onrender.com','public_repository':'https://github.com/AngRoy/again','scope':'Standalone Again app and five submission artifacts; excludes research archives, credentials, virtualenv and raw duplicate captures.','members':records,'configured_secret_scan_passed':True}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(payload.items()):z.writestr(name,data)
        z.writestr('submission_manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None:raise RuntimeError('Archive CRC verification failed')
        for name,meta in records.items():
            data=z.read(name)
            if len(data)!=meta['bytes'] or hashlib.sha256(data).hexdigest()!=meta['sha256']:raise RuntimeError('Archive member verification failed: '+name)
    result={'archive_name':output.name,'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'members':len(records)+1,'verified':True,'configured_secret_scan_passed':True,'source_commit':manifest['source_commit']}
    output.with_suffix('.verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--private-env');a=parser.parse_args();package(a.output,a.private_env)
