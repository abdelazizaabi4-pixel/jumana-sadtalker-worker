FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel
WORKDIR /workspace
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y git wget ffmpeg unzip libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements_worker.txt /workspace/requirements_worker.txt
RUN pip install --upgrade pip && pip install -r /workspace/requirements_worker.txt
RUN git clone https://github.com/OpenTalker/SadTalker.git /workspace/SadTalker || true
WORKDIR /workspace/SadTalker
RUN pip install -r requirements.txt || true
RUN pip install --force-reinstall numpy==1.23.5 scipy==1.10.1 || true
RUN pip install kornia yacs facexlib gfpgan basicsr imageio-ffmpeg moviepy || true
RUN bash scripts/download_models.sh || true
WORKDIR /workspace
COPY handler.py /workspace/handler.py
ENV SADTALKER_DIR=/workspace/SadTalker
ENV JUMANA_MAX_INLINE_VIDEO_MB=24
ENV JUMANA_WORKER_VERSION=V18.8_HANDLER_OUTPUT_GUARANTEE
CMD ["python", "-u", "/workspace/handler.py"]
