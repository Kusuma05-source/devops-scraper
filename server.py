import json
import os
import subprocess
import threading
from urllib.parse import urlparse

from flask import Flask, Response, jsonify, request

app = Flask(__name__)
DATA_FILE = os.environ.get("DATA_FILE", "scraped_data.json")
lock = threading.Lock()

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Web Scraper</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 body{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px}
 input{width:70%;padding:10px;font-size:16px} button{padding:10px 16px;font-size:16px;cursor:pointer}
 pre{background:#111;color:#0f0;padding:16px;border-radius:8px;overflow:auto;white-space:pre-wrap}
</style></head><body>
<h2>Puppeteer + Chromium Scraper</h2>
<input id="url" placeholder="https://example.com">
<button onclick="go()">Scrape</button>
<p id="status"></p>
<pre id="out">Loading last result...</pre>
<script>
const out=document.getElementById('out'), st=document.getElementById('status');
fetch('/data').then(r=>r.json()).then(d=>out.textContent=JSON.stringify(d,null,2));
async function go(){
  const u=document.getElementById('url').value.trim();
  if(!u){st.textContent='Enter a URL first';return}
  st.textContent='Scraping... (can take up to a minute)'; out.textContent='';
  try{
    const r=await fetch('/scrape?url='+encodeURIComponent(u));
    const d=await r.json();
    st.textContent=r.ok?'Done':'Failed';
    out.textContent=JSON.stringify(d,null,2);
  }catch(e){st.textContent='Error: '+e}
}
document.getElementById('url').addEventListener('keydown',e=>{if(e.key==='Enter')go()});
</script></body></html>"""


def read_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    return Response(PAGE, mimetype="text/html")


@app.route("/data")
def data():
    try:
        return jsonify(read_data())
    except FileNotFoundError:
        return jsonify({"error": "No scraped data yet. Use /scrape?url=..."}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "scraped data is not valid JSON"}), 500


@app.route("/scrape")
def scrape():
    url = (request.args.get("url") or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return jsonify({"error": "Provide a valid http(s) URL, e.g. /scrape?url=https://example.com"}), 400

    with lock:
        try:
            env = {**os.environ, "OUTPUT_FILE": DATA_FILE}
            result = subprocess.run(
                ["node", "scrape.js", url],
                capture_output=True, text=True, timeout=120, env=env,
            )
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Scraping timed out"}), 504

        if result.returncode != 0:
            msg = (result.stderr or result.stdout).strip()[-500:]
            return jsonify({"error": "Scrape failed", "details": msg}), 500

        try:
            return jsonify(read_data())
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": "Scraper did not produce valid output"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
