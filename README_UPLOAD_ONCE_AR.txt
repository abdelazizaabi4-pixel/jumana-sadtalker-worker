V18.6 Deep Diagnostics — ارفع هذا المجلد مرة واحدة فقط

ارفع محتوى هذا المجلد إلى GitHub.
المهم:
runpod_serverless_worker/handler.py
runpod_serverless_worker/Dockerfile
runpod_serverless_worker/requirements_worker.txt
.github/workflows/docker-build.yml

بعد الرفع شغّل GitHub Actions، ثم في RunPod غيّر Container image إلى:
docker.io/abdelazizaabi/jumana-sadtalker-worker:v18-6

إذا فشل الإنتاج بعد ذلك، ستحصل على تقرير كامل داخل data/diagnostics في برنامج جمانة.
