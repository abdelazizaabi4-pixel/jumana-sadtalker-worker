from __future__ import annotations

import os, base64, subprocess, uuid, json, traceback, shutil, time, platform
from pathlib import Path
from typing import Any, Dict

import runpod

VERSION = "V18.7_LONG_WAIT_AND_LIVE_LOGS"
WORKER_NAME = "Jumana V18.7 Long Wait + Live Logs + Deep Diagnostics + SadTalker"
WORK_ROOT = Path(os.environ.get("JUMANA_WORK", "/workspace/jumana_serverless_jobs"))
RESULTS = Path(os.environ.get("JUMANA_RESULTS", "/workspace/results"))
SADTALKER = Path(os.environ.get("SADTALKER_DIR", "/workspace/SadTalker"))
CONDA_SH = os.environ.get("CONDA_SH", "/workspace/miniconda/etc/profile.d/conda.sh")
CONDA_ENV = os.environ.get("CONDA_ENV", "jumana_sadtalker")
MAX_INLINE_VIDEO_MB = int(os.environ.get("JUMANA_MAX_INLINE_VIDEO_MB", "45"))

MOTION_PRESETS = {
    "face_talking_stable": "وجه وفم وكلام فقط",
    "standing_explain_hands": "واقف يشرح بيديه",
    "simple_walk": "يمشي حركة بسيطة",
    "point_right_hand": "يشير بيده اليمنى",
    "point_left_hand": "يشير بيده اليسرى",
    "turn_right_raise_hand": "يلتفت يمينًا ثم يرفع يده",
    "turn_left_explain_hands": "يلتفت يسارًا ثم يشرح بيديه",
    "raise_both_hands_explain": "يرفع يديه قليلًا كأنه يشرح",
    "two_person_scene_listen": "مشهد فيه شخصان: الأول يتكلم والثاني يستمع",
    "two_person_scene_dialogue": "مشهد فيه شخصان: حوار متناوب/تحضير آمن",
    "multi_person_scene_prepare": "تحضير مشهد فيه أشخاص كثيرون",
    "multi_person_speaker_with_audience": "شخص يتكلم أمام مجموعة أشخاص",
    "multi_person_dialogue_circle": "حوار بين عدة أشخاص في مشهد واحد",
}
SUPPORTED_TASKS = ["ping", "diagnostic_output", "sadtalker_video"]
WORK_ROOT.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)

def _safe_tail(text: str | None, n: int = 8000) -> str:
    if not text: return ""
    return str(text)[-n:]

def _list_dir(path: Path, limit: int = 80):
    try:
        if not path.exists(): return {"exists": False, "path": str(path)}
        items=[]
        for p in list(path.iterdir())[:limit]:
            try: items.append({"name": p.name, "type": "dir" if p.is_dir() else "file", "size": p.stat().st_size if p.is_file() else None})
            except Exception: items.append({"name": p.name})
        return {"exists": True, "path": str(path), "items": items}
    except Exception as e:
        return {"exists": False, "path": str(path), "error": str(e)}

def _env_report(stage="start"):
    return {
        "stage": stage,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": VERSION,
        "worker": WORKER_NAME,
        "python": platform.python_version(),
        "cwd": os.getcwd(),
        "work_root": str(WORK_ROOT),
        "results": str(RESULTS),
        "sadtalker_dir": str(SADTALKER),
        "sadtalker_exists": SADTALKER.exists(),
        "conda_sh": CONDA_SH,
        "conda_sh_exists": Path(CONDA_SH).exists(),
        "conda_env": CONDA_ENV,
        "ffmpeg_path": shutil.which("ffmpeg"),
        "python_path": shutil.which("python"),
        "disk_usage_workspace": shutil.disk_usage('/workspace')._asdict() if Path('/workspace').exists() else None,
        "sadtalker_files": _list_dir(SADTALKER, 50),
        "checkpoints": _list_dir(SADTALKER / 'checkpoints', 80),
        "results_files": _list_dir(RESULTS, 80),
    }

def _ok(**kwargs: Any) -> Dict[str, Any]:
    payload = {"ok": True, "worker": WORKER_NAME, "version": VERSION, "output_contract": "always_returns_output_dict", "diagnostic_report": _env_report("ok")}
    payload.update(kwargs)
    return payload

def _fail(message: str, **kwargs: Any) -> Dict[str, Any]:
    payload = {"ok": False, "error": str(message), "worker": WORKER_NAME, "version": VERSION, "output_contract": "always_returns_output_dict", "diagnostic_report": _env_report(kwargs.get('stage','failure'))}
    payload.update(kwargs)
    return payload

def _write_b64(data: str, path: Path) -> None:
    try: path.write_bytes(base64.b64decode(data))
    except Exception as e: raise RuntimeError(f"فشل فك base64 وحفظ الملف {path.name}: {e}")

def _run(cmd: str, timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-lc", cmd], check=True, text=True, capture_output=True, timeout=timeout)

def _encode_video(video_path: Path) -> Dict[str, Any]:
    size_mb = video_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_INLINE_VIDEO_MB:
        return _fail("تم إنتاج الفيديو لكن حجمه أكبر من حد الإرجاع المباشر داخل RunPod output.", stage="encode_video", video_created=True, video_path=str(video_path), video_size_mb=round(size_mb, 2), hint_ar="قلل مدة الصوت أو ارفع حد JUMANA_MAX_INLINE_VIDEO_MB أو أضف رفع S3/Drive في V19.")
    return _ok(message="تم إنتاج الفيديو بنجاح.", video_base64=base64.b64encode(video_path.read_bytes()).decode("ascii"), video_filename=video_path.name, video_size_mb=round(size_mb, 2))

def _extract_body_layer(inp: Dict[str, Any]) -> Dict[str, Any]:
    body_layer = inp.get("v18_body_layer") or {}
    if not isinstance(body_layer, dict): body_layer = {"raw": str(body_layer)}
    preset = body_layer.get("motion_preset") or "face_talking_stable"
    body_layer["motion_preset"] = preset
    body_layer["movement_ar"] = body_layer.get("movement_ar") or MOTION_PRESETS.get(preset, "حركة غير معروفة")
    return body_layer

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    stage = "received"
    job_id = str(uuid.uuid4())[:8]
    try:
        inp = event.get("input") or {}
        task = inp.get("task") or ("diagnostic_output" if inp.get("prompt") else "sadtalker_video")
        if task in {"ping", "diagnostic_output"}:
            return _ok(task="ping", message=inp.get("message", "pong"), supports=SUPPORTED_TASKS, motion_presets=MOTION_PRESETS, important_ar="إذا ظهر هذا output فهذا يعني أن Worker V18.7 يعمل فعلًا.")
        if task != "sadtalker_video":
            return _fail(f"Unknown task: {task}", stage="task_check", supported_tasks=SUPPORTED_TASKS)
        body_layer = _extract_body_layer(inp)
        stage = "validate_input"
        if not inp.get("image_base64"):
            return _fail("image_base64 is required", stage=stage, missing="image_base64", body_layer=body_layer)
        if not inp.get("audio_base64"):
            return _fail("audio_base64 is required. استعمل صوتك المسجل الآن.", stage=stage, missing="audio_base64", body_layer=body_layer, hint_ar="اختر ملف صوت mp3 أو wav أو m4a من البرنامج.")
        if not SADTALKER.exists():
            return _fail(f"SadTalker not found at {SADTALKER}", stage="check_sadtalker", body_layer=body_layer, hint_ar="Docker image لا تحتوي SadTalker. راجع Dockerfile أو استعمل صورة تحتوي SadTalker داخل /workspace/SadTalker.")
        stage = "prepare_files"
        job = WORK_ROOT / job_id; job.mkdir(parents=True, exist_ok=True)
        image = job / "source_image.png"; image2 = job / "second_person.png"; audio_in = job / "audio_input"; audio_wav = job / "audio.wav"; out_txt = job / "last_video.txt"
        (job / "request_debug.json").write_text(json.dumps({k: ("<base64>" if "base64" in k else v) for k, v in inp.items()}, ensure_ascii=False, indent=2), encoding="utf-8")
        _write_b64(inp["image_base64"], image)
        second_person_received = False
        if inp.get("image2_base64"):
            _write_b64(inp["image2_base64"], image2); second_person_received = True
        extra_people_saved=[]; extra_people = inp.get("extra_people") or []
        if not isinstance(extra_people, list): extra_people=[]
        for idx, person in enumerate(extra_people, start=2):
            if not isinstance(person, dict) or not person.get("image_base64"): continue
            p_path = job / f"person_{idx}.png"; _write_b64(person["image_base64"], p_path)
            extra_people_saved.append({"index": idx, "image": str(p_path), "role_ar": person.get("role_ar") or "شخص في المشهد", "image_name": person.get("image_name") or p_path.name})
        _write_b64(inp["audio_base64"], audio_in)
        preset = body_layer.get("motion_preset") or "face_talking_stable"
        two_person_mode = preset in {"two_person_scene_listen", "two_person_scene_dialogue"}
        multi_person_mode = preset.startswith("multi_person") or bool(extra_people_saved)
        scene_people=[{"index":1,"role_ar":body_layer.get("person1_role_ar","المتكلم الرئيسي"),"image":str(image),"speaker":True}]
        if second_person_received: scene_people.append({"index":2,"role_ar":body_layer.get("person2_role_ar","المستمع"),"image":str(image2),"speaker":False})
        scene_people.extend(extra_people_saved)
        scene_manifest={"version":VERSION,"person_count":len(scene_people),"two_person_mode":two_person_mode,"multi_person_mode":multi_person_mode,"people":scene_people,"motion_preset":preset,"merge_strategy_ar":"SadTalker للوجه والكلام الآن، ومحرك الجسم الكامل الحقيقي طبقة لاحقة."}
        (job / "scene_manifest.json").write_text(json.dumps(scene_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        stage = "run_sadtalker"
        cmd = f'''set -e
if [ -f "{CONDA_SH}" ]; then source "{CONDA_SH}"; conda activate "{CONDA_ENV}" || true; fi
ffmpeg -y -i "{audio_in}" -ar 16000 -ac 1 "{audio_wav}"
cd "{SADTALKER}"
mkdir -p "{RESULTS}"
python inference.py \
  --driven_audio "{audio_wav}" \
  --source_image "{image}" \
  --result_dir "{RESULTS}" \
  --checkpoint_dir "{SADTALKER}/checkpoints" \
  --still \
  --preprocess full \
  --size 256
find "{RESULTS}" -type f -name "*.mp4" -printf "%T@ %p\n" | sort -n | tail -1 | cut -d" " -f2- > "{out_txt}"
'''
        (job / "run_command.sh").write_text(cmd, encoding="utf-8")
        proc = _run(cmd, timeout=int(inp.get("timeout", 3600)))
        stage = "find_video"
        video_text = out_txt.read_text(encoding="utf-8", errors="ignore").strip()
        if not video_text:
            return _fail("SadTalker انتهى لكن لم يتم العثور على ملف MP4 في مجلد النتائج.", stage=stage, job_id=job_id, body_layer=body_layer, results_dir=str(RESULTS), stdout_tail=_safe_tail(proc.stdout), stderr_tail=_safe_tail(proc.stderr), job_dir=str(job), results_files=_list_dir(RESULTS, 120))
        video_path = Path(video_text)
        if not video_path.exists():
            return _fail("Video path was returned but file does not exist.", stage=stage, job_id=job_id, body_layer=body_layer, video_path=str(video_path), stdout_tail=_safe_tail(proc.stdout), stderr_tail=_safe_tail(proc.stderr))
        encoded = _encode_video(video_path)
        encoded.update({"job_id":job_id,"task":task,"body_layer":body_layer,"body_layer_status":"face_talking_video_produced__real_body_engine_pending","body_layer_engine_real":False,"two_person_mode":two_person_mode,"multi_person_mode":multi_person_mode,"scene_manifest":scene_manifest,"motion_preset":preset,"stdout_tail":_safe_tail(proc.stdout,2000),"stderr_tail":_safe_tail(proc.stderr,2000),"job_dir":str(job)})
        return encoded
    except subprocess.CalledProcessError as e:
        return _fail("SadTalker failed أثناء التنفيذ.", stage=stage, returncode=e.returncode, stdout_tail=_safe_tail(e.stdout), stderr_tail=_safe_tail(e.stderr))
    except subprocess.TimeoutExpired as e:
        return _fail("انتهت مهلة تنفيذ SadTalker داخل Worker.", stage=stage, stdout_tail=_safe_tail(getattr(e,"stdout","")), stderr_tail=_safe_tail(getattr(e,"stderr","")))
    except Exception as e:
        return _fail(str(e), stage=stage, traceback_tail=_safe_tail(traceback.format_exc()))

runpod.serverless.start({"handler": handler})
