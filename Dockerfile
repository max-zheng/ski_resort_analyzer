FROM public.ecr.aws/lambda/python:3.11

# Install ffmpeg for Mt Hood Meadows HLS streams
RUN yum install -y git tar xz && \
    curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz -o /tmp/ffmpeg.tar.xz && \
    tar -xf /tmp/ffmpeg.tar.xz -C /tmp && \
    mv /tmp/ffmpeg-*-static/ffmpeg /usr/local/bin/ && \
    rm -rf /tmp/ffmpeg* && \
    yum clean all

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and ensure readable
COPY lambda_handler.py resort_analyzer.py utils.py ./
COPY webcam_downloader/ ./webcam_downloader/
COPY image_utils/ ./image_utils/
RUN chmod -R 755 ${LAMBDA_TASK_ROOT}

CMD ["lambda_handler.handler"]
