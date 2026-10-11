FROM docker.io/library/node@sha256:0e5f906573693feaa1e21057ebdcfdb5bd5021f050b2dc7c9deceb629c7da2a8
USER root
RUN rm -f /etc/apt/sources.list.d/debian.sources && printf '%s\n' 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261001T000000Z/ bookworm main' > /etc/apt/sources.list && apt-get update && apt-get install -y --no-install-recommends python3 python3-numpy python3-pil python3-fonttools tesseract-ocr strace imagemagick unzip fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 libxkbcommon0 && rm -rf /var/lib/apt/lists/*
COPY ffmpeg.tar.xz /tmp/ffmpeg.tar.xz
RUN echo 'abda8d77ce8309141f83ab8edf0596834087c52467f6badf376a6a2a4c87cf67  /tmp/ffmpeg.tar.xz' | sha256sum -c - && mkdir -p /opt/tools/bin /opt/tools/license && tar -xJf /tmp/ffmpeg.tar.xz -C /tmp && cp /tmp/ffmpeg-7.0.2-amd64-static/ffmpeg /tmp/ffmpeg-7.0.2-amd64-static/ffprobe /opt/tools/bin/ && cp /tmp/ffmpeg-7.0.2-amd64-static/GPLv3.txt /opt/tools/license/ && rm -rf /tmp/ffmpeg* && /opt/tools/bin/ffmpeg -version && node --version
RUN userdel node && rm -rf /home/node
COPY chrome.zip /tmp/chrome.zip
RUN echo 'ad115a7498a17f53f6ed0914458326c6516addc756224db14c32184a9b1ab078  /tmp/chrome.zip' | sha256sum -c - && unzip -q /tmp/chrome.zip -d /opt/tools && rm /tmp/chrome.zip && /opt/tools/chrome-linux64/chrome --version
COPY package.json package-lock.json /opt/tools/
RUN HOME=/tmp/npm-home npm ci --prefix /opt/tools --ignore-scripts --no-audit --no-fund --registry=https://registry.npmjs.org && rm -rf /tmp/npm-home && python3 -c 'import PIL, fontTools' && node -e 'console.log(require("/opt/tools/node_modules/puppeteer-core/package.json").version)'
