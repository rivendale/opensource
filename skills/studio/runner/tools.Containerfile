FROM docker.io/library/node@sha256:0e5f906573693feaa1e21057ebdcfdb5bd5021f050b2dc7c9deceb629c7da2a8
USER root
RUN rm -f /etc/apt/sources.list.d/debian.sources && printf '%s\n' 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261001T000000Z/ bookworm main' > /etc/apt/sources.list && apt-get update && apt-get install -y --no-install-recommends python3 python3-numpy tesseract-ocr strace imagemagick && rm -rf /var/lib/apt/lists/*
COPY ffmpeg.tar.xz /tmp/ffmpeg.tar.xz
RUN echo 'abda8d77ce8309141f83ab8edf0596834087c52467f6badf376a6a2a4c87cf67  /tmp/ffmpeg.tar.xz' | sha256sum -c - && mkdir -p /opt/tools/bin /opt/tools/license && tar -xJf /tmp/ffmpeg.tar.xz -C /tmp && cp /tmp/ffmpeg-7.0.2-amd64-static/ffmpeg /tmp/ffmpeg-7.0.2-amd64-static/ffprobe /opt/tools/bin/ && cp /tmp/ffmpeg-7.0.2-amd64-static/GPLv3.txt /opt/tools/license/ && rm -rf /tmp/ffmpeg* && /opt/tools/bin/ffmpeg -version && node --version
RUN userdel node && rm -rf /home/node
