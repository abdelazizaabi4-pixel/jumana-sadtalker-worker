# Jumana V17.2 Serverless Worker
# يبنى في GitHub Actions ثم يُرفع إلى Docker Hub.
# لا تبنِ هذه الصورة على جهاز ضعيف أو إنترنت غير مستقر.

FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel

WORKDIR /app

RUN apt-get update && apt-get install -y git wget ffmpeg unzip && rm -rf /var/lib/apt/lists/*

COPY requirements_worker.txt /app/requirements_worker.txt
RUN pip install --upgrade pip && pip install -r /app/requirements_worker.txt

# SadTalker داخل الصورة حتى يصبح Worker جاهزًا في RunPod Serverless
RUN git clone https://github.com/OpenTalker/SadTalker.git /app/SadTalker || true

WORKDIR /app/SadTalker
RUN pip install -r requirements.txt || true
RUN pip install numpy==1.23.5 scipy==1.10.1 kornia yacs facexlib gfpgan basicsr || true
RUN bash scripts/download_models.sh || true

WORKDIR /app
COPY handler.py /app/handler.py

ENV JUMANA_WORK=/tmp/jumana_serverless_jobs
ENV JUMANA_RESULTS=/tmp/jumana_results
ENV SADTALKER_DIR=/app/SadTalker
ENV CONDA_SH=/opt/conda/etc/profile.d/conda.sh
ENV CONDA_ENV=base

CMD ["python", "-u", "/app/handler.py"]
