from __future__ import annotations

import os, base64, subprocess, uuid, json, traceback, shutil, time, platform, sys
from pathlib import Path
from typing import Any, Dict

import runpod

VERSION = "V18.8_HANDLER_OUTPUT_GUARANTEE"
WORKER_NAME = "Jumana V18.8 Handler Output Guarantee + Criminal Diagnostics"
WORK_ROOT = Path(os.environ.get("JUMANA_WORK", "/workspace/jumana_serverless_jobs"))
RESULTS = Path(os.environ.get("JUMANA_RESULTS", "/workspace/results"))
SADTALKER = Path(os.environ.get("SADTALKER_DIR", "/workspace/SadTalker"))
CONDA_SH = os.environ.get("CONDA_SH", "/workspace/miniconda/etc/profile.d/conda.sh")
CONDA_ENV = os.environ.get("CONDA_ENV", "jumana_sadtalker")
MAX_INLINE_VIDEO_MB = int(os.environ.get("JUMANA_MAX_INLINE_VIDEO_MB", "24"))

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

FACE_ONLY_PRESETS = {"face_talking_stable", "face_talk", "face_only", "talking_face"}
FULL_BODY_PRESETS = set(MOTION_PRESETS) - {"face_talking_stable"}
SUPPORTED_TASKS = ["ping", "diagnostic_output", "sadtalker_video"]
WORK_ROOT.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)


def log(marker: str, **data: Any) -> None:
    try:
        line = {"marker": marker, "version": VERSION, "time": time.strftime("%Y-%m-%d %H:%M:%S"), **data}
        print("JUMANA_DIAG " + json.dumps(line, ensure_ascii=False, default=str), flush=True)
    except Exception:
        print(f"JUMANA_DIAG {marker}", flush=True)


def _safe_tail(text: str | None, n: int = 8000) -> str:
    if not text:
        return ""
    return str(text)[-n:]


def _list_dir(path: Path, limit: int = 80):
    try:
        if not path.exists():
            return {"exists": False, "path": str(path)}
        items=[]
        for p in list(path.iterdir())[:limit]:
            try:
                items.append({"name": p.name, "type": "dir" if p.is_dir() else "file", "size": p.stat().st_size if p.is_file() else None})
            except Exception:
                items.append({"name": p.name})
        return {"exists": True, "path": str(path), "items": items}
    except Exception as e:
        return {"exists": False, "path": str(path), "error": str(e)}


def _env_report(stage="start"):
    return {
        "stage": stage,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": VERSION,
        "worker": WORKER_NAME,
        "output_contract": "RUNPOD_COMPLETED_MUST_CONTAIN_OUTPUT_ALWAYS",
        "python": platform.python_version(),
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "work_root": str(WORK_ROOT),
        "results": str(RESULTS),
        "sadtalker_dir": str(SADTALKER),
        "sadtalker_exists": SADTALKER.exists(),
        "conda_sh": CONDA_SH,
        "conda_sh_exists": Path(CONDA_SH).exists(),
        "conda_env": CONDA_ENV,
        "ffmpeg_path": shutil.which("ffmpeg"),
        "python_path": shutil.which("python"),
        "handler_file": str(Path(__file__).resolve()),
        "handler_file_exists": Path(__file__).exists(),
        "disk_usage_workspace": shutil.disk_usage('/workspace')._asdict() if Path('/workspace').exists() else None,
        "sadtalker_files": _list_dir(SADTALKER, 50),
        "checkpoints": _list_dir(SADTALKER / 'checkpoints', 80),
        "results_files": _list_dir(RESULTS, 80),
    }


def _criminal_report(stage: str, suspect: str, evidence: Dict[str, Any] | None = None, solution_ar: str = "") -> Dict[str, Any]:
    return {
        "stage": stage,
        "primary_suspect": suspect,
        "suspects_ordered_ar": [
            "1) handler.py لم يرجع output بالشكل المطلوب أو لم يبدأ أصلًا.",
            "2) Dockerfile / Start command يشغل ملفًا قديمًا أو مسارًا خطأ.",
            "3) مسار الجسم الكامل اختير قبل أن يكون محرك الجسم الحقيقي جاهزًا.",
            "4) SadTalker أو checkpoints أو ffmpeg ناقص داخل الصورة.",
            "5) جمانة تقرأ output من مفتاح مختلف عن الذي رجعه Worker.",
        ],
        "evidence": evidence or {},
        "solution_ar": solution_ar,
        "env": _env_report(stage),
    }


def _output(**kwargs: Any) -> Dict[str, Any]:
    payload = {
        "ok": True,
        "worker": WORKER_NAME,
        "version": VERSION,
        "output_contract": "always_returns_output_dict_v18_8",
        "handler_started": True,
        "diagnostic_report": _env_report("ok"),
    }
    payload.update(kwargs)
    log("RETURNING_OUTPUT", ok=payload.get("ok"), keys=list(payload.keys()), stage=payload.get("stage"))
    return payload


def _fail(message: str, **kwargs: Any) -> Dict[str, Any]:
    suspect = kwargs.pop("suspect", "unknown")
    solution_ar = kwargs.pop("solution_ar", "افتح RunPod Logs واقرأ JUMANA_DIAG، ثم راجع diagnostic_report لمعرفة المرحلة.")
    return _output(ok=False, error=str(message), stage=kwargs.get("stage", "failure"), criminal_report=_criminal_report(kwargs.get("stage", "failure"), suspect, kwargs, solution_ar), **kwargs)


def _write_b64(data: str, path: Path) -> None:
    try:
        path.write_bytes(base64.b64decode(data))
    except Exception as e:
        raise RuntimeError(f"فشل فك base64 وحفظ الملف {path.name}: {e}")


def _run(cmd: str, timeout: int = 1800) -> subprocess.CompletedProcess:
    log("SUBPROCESS_START", timeout=timeout, cmd_head=cmd[:600])
    proc = subprocess.run(["bash", "-lc", cmd], check=True, text=True, capture_output=True, timeout=timeout)
    log("SUBPROCESS_DONE", returncode=proc.returncode, stdout_tail=_safe_tail(proc.stdout, 700), stderr_tail=_safe_tail(proc.stderr, 700))
    return proc


def _encode_video(video_path: Path) -> Dict[str, Any]:
    size_mb = video_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_INLINE_VIDEO_MB:
        return _fail(
            "تم إنتاج الفيديو لكن حجمه أكبر من حد الإرجاع المباشر داخل RunPod output.",
            stage="encode_video",
            suspect="output_size_limit",
            solution_ar="قلل مدة الصوت أو استعمل رفع S3/Drive في نسخة لاحقة. تم إنتاج الفيديو داخل Worker لكن لا يمكن إرجاعه base64 لأنه كبير.",
            video_created=True,
            video_path=str(video_path),
            video_size_mb=round(size_mb, 2),
            max_inline_video_mb=MAX_INLINE_VIDEO_MB,
        )
    return _output(message="تم إنتاج الفيديو بنجاح.", video_base64=base64.b64encode(video_path.read_bytes()).decode("ascii"), video_filename=video_path.name, video_size_mb=round(size_mb, 2))


def _extract_body_layer(inp: Dict[str, Any]) -> Dict[str, Any]:
    body_layer = inp.get("v18_body_layer") or {}
    if not isinstance(body_layer, dict):
        body_layer = {"raw": str(body_layer)}
    preset = body_layer.get("motion_preset") or inp.get("motion_preset") or "face_talking_stable"
    body_layer["motion_preset"] = preset
    body_layer["movement_ar"] = body_layer.get("movement_ar") or MOTION_PRESETS.get(preset, "حركة غير معروفة")
    return body_layer


def _is_full_body_request(body_layer: Dict[str, Any], inp: Dict[str, Any]) -> bool:
    preset = body_layer.get("motion_preset") or "face_talking_stable"
    requested = str(inp.get("mode") or inp.get("task_mode") or "").lower()
    if preset in FULL_BODY_PRESETS:
        return True
    if "full" in requested or "body" in requested or "person" in requested:
        return True
    if inp.get("image2_base64") or inp.get("extra_people"):
        return True
    return False


def _scene_manifest(job: Path, inp: Dict[str, Any], image: Path, image2: Path, body_layer: Dict[str, Any]) -> Dict[str, Any]:
    preset = body_layer.get("motion_preset") or "face_talking_stable"
    second_person_received = False
    if inp.get("image2_base64"):
        _write_b64(inp["image2_base64"], image2)
        second_person_received = True
    extra_people_saved=[]
    extra_people = inp.get("extra_people") or []
    if not isinstance(extra_people, list):
        extra_people=[]
    for idx, person in enumerate(extra_people, start=2):
        if not isinstance(person, dict) or not person.get("image_base64"):
            continue
        p_path = job / f"person_{idx}.png"
        _write_b64(person["image_base64"], p_path)
        extra_people_saved.append({"index": idx, "image": str(p_path), "role_ar": person.get("role_ar") or "شخص في المشهد", "image_name": person.get("image_name") or p_path.name})
    two_person_mode = preset in {"two_person_scene_listen", "two_person_scene_dialogue"}
    multi_person_mode = preset.startswith("multi_person") or bool(extra_people_saved)
    scene_people=[{"index":1,"role_ar":body_layer.get("person1_role_ar","المتكلم الرئيسي"),"image":str(image),"speaker":True}]
    if second_person_received:
        scene_people.append({"index":2,"role_ar":body_layer.get("person2_role_ar","المستمع"),"image":str(image2),"speaker":False})
    scene_people.extend(extra_people_saved)
    manifest={"version":VERSION,"person_count":len(scene_people),"two_person_mode":two_person_mode,"multi_person_mode":multi_person_mode,"people":scene_people,"motion_preset":preset,"merge_strategy_ar":"V18.8 يمنع output فارغ. الوجه والكلام عبر SadTalker. الجسم الكامل يرجع full_body_engine_not_ready إلى أن نركب محركًا حقيقيًا."}
    (job / "scene_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _run_sadtalker(inp: Dict[str, Any], body_layer: Dict[str, Any], job: Path) -> Dict[str, Any]:
    stage = "validate_input"
    if not inp.get("image_base64"):
        return _fail("image_base64 is required", stage=stage, suspect="client_payload_missing_image", solution_ar="اختر صورة قبل الضغط على الإنتاج.", missing="image_base64", body_layer=body_layer)
    if not inp.get("audio_base64"):
        return _fail("audio_base64 is required. استعمل صوتك المسجل الآن.", stage=stage, suspect="client_payload_missing_audio", solution_ar="اختر ملف صوت mp3 أو wav أو m4a من البرنامج.", missing="audio_base64", body_layer=body_layer)
    if not SADTALKER.exists():
        return _fail(f"SadTalker not found at {SADTALKER}", stage="check_sadtalker", suspect="docker_image_missing_sadtalker", solution_ar="Docker image لا تحتوي SadTalker. راجع Dockerfile أو build log.", body_layer=body_layer)

    image = job / "source_image.png"
    image2 = job / "second_person.png"
    audio_in = job / "audio_input"
    audio_wav = job / "audio.wav"
    out_txt = job / "last_video.txt"
    (job / "request_debug.json").write_text(json.dumps({k: ("<base64>" if "base64" in k else v) for k, v in inp.items()}, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_b64(inp["image_base64"], image)
    _write_b64(inp["audio_base64"], audio_in)
    scene_manifest = _scene_manifest(job, inp, image, image2, body_layer)
    log("FILES_READY", job=str(job), image_size=image.stat().st_size, audio_size=audio_in.stat().st_size, body_layer=body_layer)

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
    video_text = out_txt.read_text(encoding="utf-8", errors="ignore").strip() if out_txt.exists() else ""
    if not video_text:
        return _fail("SadTalker انتهى لكن لم يتم العثور على ملف MP4 في مجلد النتائج.", stage="find_video", suspect="sadtalker_no_mp4", solution_ar="افتح stdout_tail و stderr_tail. غالبًا checkpoints ناقصة أو inference لم ينتج ملفًا.", job_dir=str(job), body_layer=body_layer, results_dir=str(RESULTS), stdout_tail=_safe_tail(proc.stdout), stderr_tail=_safe_tail(proc.stderr), results_files=_list_dir(RESULTS, 120))
    video_path = Path(video_text)
    if not video_path.exists():
        return _fail("Video path was returned but file does not exist.", stage="find_video", suspect="video_path_missing", solution_ar="راجع مجلد results داخل Worker أو طريقة find command.", job_dir=str(job), body_layer=body_layer, video_path=str(video_path), stdout_tail=_safe_tail(proc.stdout), stderr_tail=_safe_tail(proc.stderr))
    encoded = _encode_video(video_path)
    encoded.update({"job_id": job.name, "task": "sadtalker_video", "body_layer": body_layer, "body_layer_status": "face_talking_video_produced", "body_layer_engine_real": False, "scene_manifest": scene_manifest, "motion_preset": body_layer.get("motion_preset"), "stdout_tail": _safe_tail(proc.stdout, 2000), "stderr_tail": _safe_tail(proc.stderr, 2000), "job_dir": str(job), "stage": "success"})
    return encoded


def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    log("HANDLER_START", event_keys=list((event or {}).keys()))
    stage = "received"
    job_id = str(uuid.uuid4())[:8]
    job = WORK_ROOT / job_id
    try:
        job.mkdir(parents=True, exist_ok=True)
        inp = (event or {}).get("input") or {}
        log("JOB_RECEIVED", job_id=job_id, input_keys=list(inp.keys()), task=inp.get("task"), mode=inp.get("mode"), task_mode=inp.get("task_mode"))
        task = inp.get("task") or ("diagnostic_output" if inp.get("prompt") else "sadtalker_video")
        if task in {"ping", "diagnostic_output"}:
            return _output(task="ping", stage="ping", message=inp.get("message", "pong"), supports=SUPPORTED_TASKS, motion_presets=MOTION_PRESETS, important_ar="إذا ظهر هذا output فهذا يعني أن Worker V18.8 يعمل فعلًا وأن handler.py يرجع output.")
        if task != "sadtalker_video":
            return _fail(f"Unknown task: {task}", stage="task_check", suspect="client_sent_unknown_task", solution_ar="عدّل جمانة لترسل task=sadtalker_video أو ping فقط.", supported_tasks=SUPPORTED_TASKS)

        body_layer = _extract_body_layer(inp)
        log("MODE_SELECTED", job_id=job_id, task=task, body_layer=body_layer)
        if _is_full_body_request(body_layer, inp):
            return _fail(
                "full_body_engine_not_ready: مسار الجسم الكامل لم يركب بمحرك حقيقي بعد. SadTalker يعمل للوجه والفم والكلام فقط.",
                stage="full_body_gate",
                suspect="full_body_engine_layer_not_ready",
                solution_ar="استعمل الآن خيار: وجه وكلام فقط. ثم نركب محرك جسم حقيقي منفصل مثل AnimateAnyone/MusePose/DWpose لاحقًا، ولا نخلطه مع SadTalker داخل نفس الطلب.",
                body_layer=body_layer,
                available_now="face_talking_stable",
                requested_motion=body_layer.get("motion_preset"),
            )
        return _run_sadtalker(inp, body_layer, job)
    except subprocess.CalledProcessError as e:
        log("EXCEPTION_CALLED_PROCESS", stage=stage, returncode=e.returncode, stdout_tail=_safe_tail(e.stdout), stderr_tail=_safe_tail(e.stderr))
        return _fail("SadTalker failed أثناء التنفيذ.", stage=stage, suspect="sadtalker_process_failed", solution_ar="اقرأ stderr_tail. غالبًا مشكلة checkpoints أو مكتبة ناقصة أو ffmpeg/input.", returncode=e.returncode, stdout_tail=_safe_tail(e.stdout), stderr_tail=_safe_tail(e.stderr))
    except subprocess.TimeoutExpired as e:
        log("EXCEPTION_TIMEOUT", stage=stage)
        return _fail("انتهت مهلة تنفيذ SadTalker داخل Worker.", stage=stage, suspect="worker_execution_timeout", solution_ar="ارفع Execution timeout في RunPod أو قلل مدة الصوت.", stdout_tail=_safe_tail(getattr(e, "stdout", "")), stderr_tail=_safe_tail(getattr(e, "stderr", "")))
    except Exception as e:
        log("EXCEPTION_GENERIC", stage=stage, error=str(e), traceback_tail=_safe_tail(traceback.format_exc(), 1500))
        return _fail(str(e), stage=stage, suspect="handler_exception", solution_ar="افتح RunPod Logs وابحث عن JUMANA_DIAG EXCEPTION_GENERIC، ثم أرسل traceback_tail.", traceback_tail=_safe_tail(traceback.format_exc()))


log("HANDLER_MODULE_LOADED", file=__file__)
runpod.serverless.start({"handler": handler})
