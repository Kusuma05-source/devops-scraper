# ---------- Stage 1: Node.js scraper (build stage) ----------
FROM node:18-bookworm-slim AS scraper

RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium \
      fonts-liberation \
      fonts-noto-color-emoji \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY scrape.js ./

# Initial scrape at build time (default URL, override with --build-arg)
ARG SCRAPE_URL=https://example.com
ENV SCRAPE_URL=${SCRAPE_URL}
RUN node scrape.js

# ---------- Stage 2: Python web server (final) ----------
FROM python:3.10-slim-bookworm

# Chromium is needed at runtime so users can scrape new URLs from the browser
RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium \
      fonts-liberation \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Node binary + scraper deps copied from stage 1 (no npm/apt build tools in final)
COPY --from=scraper /usr/local/bin/node /usr/local/bin/node

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=scraper /app/node_modules ./node_modules
COPY --from=scraper /app/package.json ./package.json
COPY --from=scraper /app/scrape.js ./scrape.js
COPY --from=scraper /app/scraped_data.json ./scraped_data.json
COPY server.py ./

EXPOSE 5000
CMD ["python", "server.py"]
