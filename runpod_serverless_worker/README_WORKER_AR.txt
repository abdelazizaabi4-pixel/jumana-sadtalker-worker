# Jumana V18.3 Serverless Worker

هذه نسخة Worker واحدة للرفع إلى GitHub مرة واحدة فقط.

المهم فيها:
- ترجع output دائمًا.
- تدعم اختيار الحركة من الواجهة: يمشي، يشير بيده، يشرح، يلتفت، يرفع يده.
- تبقي SadTalker للوجه والكلام.
- تحفظ طبقة الجسم الكامل داخل output حتى لا تضيع اختيارات الحركة.
- تبني Docker tag ثابتًا: `v18-3` بالإضافة إلى `latest`.

الصورة بعد نجاح GitHub Actions:

```text
docker.io/abdelazizaabi/jumana-sadtalker-worker:v18-3
```

استعمل هذا الـ tag في RunPod Endpoint بدل latest حتى لا يختلط عليك القديم بالجديد.
