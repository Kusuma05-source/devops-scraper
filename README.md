# Dockerized Web Scraper (Node.js + Puppeteer → Python Flask)

A multi-stage Docker build:

1. **Scraper stage** (`node:18-slim`): installs Chromium, runs `scrape.js` with Puppeteer, writes `scraped_data.json`.
2. **Hosting stage** (`python:3.10-slim`): copies only the JSON and serves it with Flask on port 5000.

The final image contains no Node.js, Chromium, or Puppeteer, so it stays lean.

## Project structure

```
.
├── Dockerfile
├── scrape.js
├── server.py
├── package.json
├── requirements.txt
└── README.md
```

## Build

The URL is scraped **at build time** and passed with `--build-arg`:

```bash
docker build --build-arg SCRAPE_URL=https://example.com -t scraper-app .
```

If `SCRAPE_URL` is not given, it defaults to `https://example.com`.

## Run

```bash
docker run -p 5000:5000 scraper-app
```

## Access the data

Open http://localhost:5000/ , type any URL in the box and click **Scrape**. The container runs Puppeteer + Chromium, saves `scraped_data.json`, and Flask displays it as JSON.

Endpoints: `/` (UI), `/scrape?url=<URL>` (scrape + JSON), `/data` (last scraped JSON), `/health`.

### Alternative access

Open http://localhost:5000/ in a browser, or:

```bash
curl http://localhost:5000/
```

Example response:

```json
{
  "title": "Example Domain",
  "first_heading": "Example Domain",
  "meta_description": null,
  "link_count": 1,
  "url": "https://example.com",
  "scraped_at": "2026-10-24T10:00:00.000Z"
}
```

A health check is available at `/health`.

## Scrape a different site

Rebuild with a new URL:

```bash
docker build --build-arg SCRAPE_URL=https://news.ycombinator.com -t scraper-app .
docker run -p 5000:5000 scraper-app
```

## Run the scraper locally (without Docker)

```bash
npm install
SCRAPE_URL=https://example.com node scrape.js
# or
node scrape.js https://example.com
```

(Set `PUPPETEER_EXECUTABLE_PATH` to your Chrome/Chromium path if needed.)

## Notes

- Puppeteer's bundled Chromium download is skipped (`PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true`); the apt-installed Chromium is used.
- Chromium runs with `--no-sandbox` since it runs as root in the container.
- If the scrape fails (bad URL, timeout), the build fails with an error message.
