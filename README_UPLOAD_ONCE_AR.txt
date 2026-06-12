V18.8 Handler Output Guarantee — ارفع هذا المجلد مرة واحدة فقط

ارفع محتوى هذا المجلد إلى GitHub.
المهم:
runpod_serverless_worker/handler.py
runpod_serverless_worker/Dockerfile
runpod_serverless_worker/requirements_worker.txt
.github/workflows/docker-build.yml

بعد الرفع شغّل GitHub Actions، ثم في RunPod غيّر Container image إلى:
docker.io/abdelazizaabi/jumana-sadtalker-worker:v18-8

ما الجديد في V18.8:
1. handler.py يطبع في Logs دائمًا:
   HANDLER_MODULE_LOADED
   HANDLER_START
   JOB_RECEIVED
   MODE_SELECTED
   RETURNING_OUTPUT
2. يمنع RunPod من أن ينتهي COMPLETED بدون output قدر الإمكان.
3. إذا وقع خطأ يرجع output فيه:
   ok=false
   error
   stage
   criminal_report
   solution_ar
4. إذا اختار المستخدم الجسم الكامل قبل تركيب محرك جسم حقيقي، يرجع:
   full_body_engine_not_ready
   بدل أن يصمت أو يرجع output فارغ.
5. Dockerfile يشغل handler.py صراحة:
   CMD ["python", "-u", "/workspace/handler.py"]

اختبار سريع بعد التحديث:
RunPod Requests أو curl أرسل ping. إذا ظهر output وفيه version=V18.8 فالعامل صحيح.
