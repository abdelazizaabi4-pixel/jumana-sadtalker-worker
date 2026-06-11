from __future__ import annotations
import os, base64, subprocess, uuid
from pathlib import Path
import runpod
WORK_ROOT=Path(os.environ.get('JUMANA_WORK','/tmp/jumana_serverless_jobs'))
RESULTS=Path(os.environ.get('JUMANA_RESULTS','/tmp/jumana_results'))
SADTALKER=Path(os.environ.get('SADTALKER_DIR','/app/SadTalker'))
CONDA_SH=os.environ.get('CONDA_SH','/opt/conda/etc/profile.d/conda.sh')
CONDA_ENV=os.environ.get('CONDA_ENV','base')
WORK_ROOT.mkdir(parents=True, exist_ok=True); RESULTS.mkdir(parents=True, exist_ok=True)
def _write_b64(data,path): path.write_bytes(base64.b64decode(data))
def _run(cmd,timeout=1800): return subprocess.run(['bash','-lc',cmd],check=True,text=True,capture_output=True,timeout=timeout)
def handler(event):
    inp=event.get('input') or {}; task=inp.get('task') or 'sadtalker_video'
    if task=='ping': return {'ok':True,'name':'Jumana V17 Serverless Worker','message':inp.get('message','pong')}
    if task!='sadtalker_video': return {'error':'Unknown task: '+str(task)}
    if not inp.get('image_base64'): return {'error':'image_base64 is required'}
    job_id=str(uuid.uuid4())[:8]; job=WORK_ROOT/job_id; job.mkdir(parents=True, exist_ok=True)
    image=job/'source_image.png'; audio_in=job/'audio_input'; audio_wav=job/'audio.wav'; out_txt=job/'last_video.txt'
    _write_b64(inp['image_base64'], image)
    if inp.get('audio_base64'): _write_b64(inp['audio_base64'], audio_in)
    else: return {'error':'audio_base64 is required in this V17 worker. Use your recorded voice for now.'}
    if not SADTALKER.exists(): return {'error':f'SadTalker not found at {SADTALKER}. Build the worker image with SadTalker or set SADTALKER_DIR.'}
    cmd=f'''set -e
if [ -f "{CONDA_SH}" ]; then source "{CONDA_SH}"; conda activate "{CONDA_ENV}" || true; fi
ffmpeg -y -i "{audio_in}" -ar 16000 -ac 1 "{audio_wav}"
cd "{SADTALKER}"
mkdir -p "{RESULTS}"
python inference.py --driven_audio "{audio_wav}" --source_image "{image}" --result_dir "{RESULTS}" --checkpoint_dir "{SADTALKER}/checkpoints" --still --preprocess full --size 256
find "{RESULTS}" -type f -name "*.mp4" | sort | tail -1 > "{out_txt}"
'''
    try:
        _run(cmd, timeout=int(inp.get('timeout',1800)))
        video_path=Path(out_txt.read_text().strip())
        if not video_path.exists(): return {'error':'Video file was not created'}
        return {'ok':True,'job_id':job_id,'video_base64':base64.b64encode(video_path.read_bytes()).decode('ascii')}
    except subprocess.CalledProcessError as e:
        return {'error':'SadTalker failed','stdout':e.stdout[-4000:],'stderr':e.stderr[-4000:]}
    except Exception as e: return {'error':str(e)}
runpod.serverless.start({'handler':handler})
