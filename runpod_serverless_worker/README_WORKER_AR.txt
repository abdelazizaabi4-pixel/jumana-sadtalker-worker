# Jumana V17.2 Serverless Worker

هذا المجلد هو Worker الخاص بـ RunPod Serverless.
لا تبنيه على الحاسوب إذا كان Docker يفشل أو الإنترنت ضعيف.
استعمل GitHub Actions الموجود في:

.github/workflows/docker-build.yml

النتيجة النهائية المطلوبة بعد نجاح GitHub Actions:

docker.io/abdelazizaabi/jumana-sadtalker-worker:latest

بعدها فقط ننتقل إلى إنشاء RunPod Serverless Endpoint.
