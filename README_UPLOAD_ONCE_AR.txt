V18.7 Long Wait + Live Logs — ارفع هذا المجلد مرة واحدة فقط

ارفع محتوى هذا المجلد إلى GitHub.
المهم:
runpod_serverless_worker/handler.py
runpod_serverless_worker/Dockerfile
runpod_serverless_worker/requirements_worker.txt
.github/workflows/docker-build.yml

بعد الرفع شغّل GitHub Actions، ثم في RunPod غيّر Container image إلى:
docker.io/abdelazizaabi/jumana-sadtalker-worker:v18-7

ما الجديد:
- جمانة تنتظر 60 دقيقة بدل أن تفشل بسرعة.
- تحفظ Request ID في تقرير التشخيص.
- تحفظ status_history.json و runpod_live_status.log و timeout_summary.json.
- تعرض: IN_QUEUE / IN_PROGRESS / COMPLETED / FAILED.
- عند انتهاء المهلة تخبرك آخر حالة ومدة الانتظار ومكان فحص Logs.
