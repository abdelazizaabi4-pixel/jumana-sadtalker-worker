# المرحلة الأولى فقط — بناء Docker image في GitHub بدل الحاسوب

لا تنشئ RunPod Endpoint الآن.
هدف هذه المرحلة فقط أن تحصل في النهاية على Docker image بهذا الشكل:

docker.io/abdelazizaabi/jumana-sadtalker-worker:latest

## 1) افتح GitHub
ادخل إلى github.com وأنشئ حسابًا إذا لم يكن عندك.

## 2) أنشئ مستودعًا جديدًا
اضغط New repository.
الاسم المقترح:

jumana-sadtalker-worker

اجعله Private أو Public كما تريد.

## 3) ارفع ملفات هذه النسخة إلى GitHub
ارفع محتوى مجلد:

JumanaMotionCodeLab_V17_2_CLOUD_BUILD_READY

المهم أن تكون هذه الملفات موجودة في أعلى المستودع:

runpod_serverless_worker/handler.py
runpod_serverless_worker/Dockerfile
runpod_serverless_worker/requirements_worker.txt
.github/workflows/docker-build.yml

## 4) ضع أسرار Docker Hub في GitHub Secrets
في GitHub افتح المستودع ثم:

Settings → Secrets and variables → Actions → New repository secret

أضف السر الأول:
Name:
DOCKERHUB_USERNAME
Value:
abdelazizaabi

أضف السر الثاني:
Name:
DOCKERHUB_TOKEN
Value:
ضع هنا Docker Personal Access Token الجديد

لا تصور التوكن ولا ترسله لأحد.

## 5) شغل البناء
افتح تبويب Actions في GitHub.
اختر:
Build and Push Jumana Serverless Worker
ثم اضغط:
Run workflow

انتظر حتى ينتهي بنجاح.

## 6) النتيجة المطلوبة
بعد النجاح، افتح Docker Hub، ستجد صورة باسم:

abdelazizaabi/jumana-sadtalker-worker

الرابط الذي سنحتاجه في المرحلة الثانية هو:

docker.io/abdelazizaabi/jumana-sadtalker-worker:latest

توقف هنا. لا تنشئ Endpoint حتى تنجح هذه المرحلة.
