#!/usr/bin/env python3
"""
InstaDown - Social Media Downloader
Termux Web Downloader | localhost:69
Supports: Instagram, YouTube, TikTok, Facebook, Twitter/X and more
"""

import os
import sys
import json
import threading
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Download folder - Termux shared storage
DOWNLOAD_DIR = os.path.expanduser("~/storage/downloads/InstaDown")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Track active downloads
downloads = {}

HTML = """<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>InstaDown</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg: #0a0a0f;
    --surface: #13131a;
    --card: #1a1a24;
    --border: #2a2a3a;
    --accent: #7c3aed;
    --accent2: #a855f7;
    --glow: rgba(124, 58, 237, 0.3);
    --text: #e8e8f0;
    --muted: #6b6b8a;
    --success: #22c55e;
    --error: #ef4444;
    --warn: #f59e0b;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 16px;
  }

  .header {
    text-align: center;
    margin-bottom: 32px;
  }

  .logo {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a855f7, #7c3aed, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
  }

  .logo span {
    font-weight: 300;
    font-size: 1.6rem;
  }

  .subtitle {
    color: var(--muted);
    font-size: 0.85rem;
    margin-top: 6px;
  }

  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    width: 100%;
    max-width: 520px;
    margin-bottom: 16px;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .url-input {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    color: var(--text);
    font-size: 0.95rem;
    padding: 14px 16px;
    width: 100%;
    transition: border-color 0.2s;
    outline: none;
  }

  .url-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--glow);
  }

  .url-input::placeholder { color: var(--muted); }

  .options-row {
    display: flex;
    gap: 10px;
  }

  .select-box {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    color: var(--text);
    font-size: 0.9rem;
    padding: 11px 14px;
    flex: 1;
    outline: none;
    cursor: pointer;
  }

  .select-box:focus { border-color: var(--accent); }

  .btn {
    border: none;
    border-radius: 10px;
    cursor: pointer;
    font-size: 0.95rem;
    font-weight: 600;
    padding: 13px 22px;
    transition: all 0.2s;
    width: 100%;
  }

  .btn-primary {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: #fff;
    box-shadow: 0 4px 15px var(--glow);
  }

  .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
  .btn-primary:active { transform: translateY(0); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

  .status-box {
    display: none;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    font-size: 0.88rem;
    line-height: 1.6;
    color: var(--muted);
    max-height: 180px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .status-box.active { display: block; }

  .progress-bar {
    display: none;
    height: 4px;
    background: var(--border);
    border-radius: 99px;
    overflow: hidden;
    margin-top: 8px;
  }

  .progress-bar.active { display: block; }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    border-radius: 99px;
    width: 0%;
    transition: width 0.4s ease;
  }

  .badge {
    display: inline-block;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
  }

  .badge-success { background: rgba(34, 197, 94, 0.15); color: var(--success); }
  .badge-error { background: rgba(239, 68, 68, 0.15); color: var(--error); }
  .badge-warn { background: rgba(245, 158, 11, 0.15); color: var(--warn); }

  .support-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
  }

  .chip {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 99px;
    font-size: 0.78rem;
    color: var(--muted);
    padding: 4px 12px;
  }

  .divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 16px 0;
  }

  .section-label {
    font-size: 0.8rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
  }

  .history-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 240px;
    overflow-y: auto;
  }

  .history-item {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.83rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
  }

  .history-item .filename {
    color: var(--text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
  }

  footer {
    color: var(--muted);
    font-size: 0.78rem;
    margin-top: 24px;
    text-align: center;
  }
</style>
</head>
<body>

<div class="header">
  <div class="logo">Insta<span>Down</span></div>
  <div class="subtitle">Termux Video Downloader &bull; localhost:6969</div>
</div>

<div class="card">
  <div class="input-group">
    <input class="url-input" id="urlInput" type="url"
      placeholder="https://www.instagram.com/reel/... বা যেকোনো URL">

    <div class="options-row">
      <select class="select-box" id="qualitySelect">
        <option value="best">Best Quality</option>
        <option value="bestvideo+bestaudio">Video + Audio (best)</option>
        <option value="bestaudio">Audio Only (mp3)</option>
        <option value="worst">Smallest Size</option>
      </select>
      <select class="select-box" id="formatSelect">
        <option value="mp4">MP4</option>
        <option value="mkv">MKV</option>
        <option value="mp3">MP3</option>
        <option value="webm">WebM</option>
      </select>
    </div>

    <button class="btn btn-primary" id="dlBtn" onclick="startDownload()">
      ⬇ Download
    </button>
  </div>

  <div class="progress-bar" id="progressBar">
    <div class="progress-fill" id="progressFill"></div>
  </div>

  <div class="status-box" id="statusBox"></div>

  <div class="support-chips">
    <span class="chip">📸 Instagram</span>
    <span class="chip">▶ YouTube</span>
    <span class="chip">🎵 TikTok</span>
    <span class="chip">📘 Facebook</span>
    <span class="chip">🐦 Twitter/X</span>
    <span class="chip">+ আরো অনেক</span>
  </div>
</div>

<div class="card">
  <div class="section-label">📁 Downloaded Files</div>
  <div class="history-list" id="historyList">
    <div style="color: var(--muted); font-size: 0.85rem; text-align: center; padding: 12px 0;">
      এখনো কোনো ফাইল ডাউনলোড হয়নি
    </div>
  </div>
</div>

<footer>
  Files save হচ্ছে: ~/storage/downloads/InstaDown/<br>
  Powered by yt-dlp &bull; Made for Termux
</footer>

<script>
let pollInterval = null;

function log(msg, type='info') {
  const box = document.getElementById('statusBox');
  box.classList.add('active');
  const colors = { info: '#6b6b8a', success: '#22c55e', error: '#ef4444', warn: '#f59e0b' };
  const color = colors[type] || colors.info;
  box.innerHTML += `<span style="color:${color}">${msg}</span>\n`;
  box.scrollTop = box.scrollHeight;
}

function setProgress(pct) {
  document.getElementById('progressBar').classList.add('active');
  document.getElementById('progressFill').style.width = pct + '%';
}

function resetUI() {
  document.getElementById('progressBar').classList.remove('active');
  document.getElementById('progressFill').style.width = '0%';
  document.getElementById('statusBox').innerHTML = '';
  document.getElementById('statusBox').classList.remove('active');
}

async function startDownload() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { alert('URL দাও আগে!'); return; }

  const quality = document.getElementById('qualitySelect').value;
  const format = document.getElementById('formatSelect').value;

  resetUI();
  document.getElementById('dlBtn').disabled = true;
  log('⏳ Download শুরু হচ্ছে...', 'warn');
  setProgress(10);

  try {
    const resp = await fetch('/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, quality, format })
    });
    const data = await resp.json();

    if (data.id) {
      log('🔄 Processing... ID: ' + data.id, 'info');
      pollStatus(data.id);
    } else {
      log('❌ Error: ' + (data.error || 'Unknown'), 'error');
      document.getElementById('dlBtn').disabled = false;
    }
  } catch(e) {
    log('❌ Request failed: ' + e.message, 'error');
    document.getElementById('dlBtn').disabled = false;
  }
}

function pollStatus(id) {
  let dots = 0;
  pollInterval = setInterval(async () => {
    try {
      const resp = await fetch('/status/' + id);
      const data = await resp.json();

      if (data.progress) setProgress(data.progress);
      if (data.log) log(data.log, 'info');

      if (data.status === 'done') {
        clearInterval(pollInterval);
        setProgress(100);
        log('✅ Download সম্পন্ন! ফাইল: ' + data.filename, 'success');
        document.getElementById('dlBtn').disabled = false;
        document.getElementById('urlInput').value = '';
        loadHistory();
      } else if (data.status === 'error') {
        clearInterval(pollInterval);
        log('❌ Error: ' + data.error, 'error');
        document.getElementById('dlBtn').disabled = false;
      }
    } catch(e) {}
  }, 1500);
}

async function loadHistory() {
  try {
    const resp = await fetch('/files');
    const data = await resp.json();
    const list = document.getElementById('historyList');

    if (!data.files || data.files.length === 0) {
      list.innerHTML = '<div style="color: var(--muted); font-size: 0.85rem; text-align: center; padding: 12px 0;">কোনো ফাইল নেই</div>';
      return;
    }

    list.innerHTML = data.files.reverse().slice(0, 20).map(f => `
      <div class="history-item">
        <span class="filename">📄 ${f.name}</span>
        <span style="color:var(--muted);font-size:0.78rem;white-space:nowrap">${f.size}</span>
      </div>
    `).join('');
  } catch(e) {}
}

// Load history on start
loadHistory();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url", "").strip()
    quality = data.get("quality", "best")
    fmt = data.get("format", "mp4")

    if not url:
        return jsonify({"error": "URL দাও"}), 400

    import uuid, time
    dl_id = str(uuid.uuid4())[:8]
    downloads[dl_id] = {
        "status": "running",
        "progress": 10,
        "log": None,
        "filename": None,
        "error": None
    }

    threading.Thread(target=run_download, args=(dl_id, url, quality, fmt), daemon=True).start()
    return jsonify({"id": dl_id})

def run_download(dl_id, url, quality, fmt):
    try:
        output_template = os.path.join(DOWNLOAD_DIR, "%(title).60s.%(ext)s")
        cmd = ["yt-dlp", "--no-playlist", "-o", output_template]

        if fmt == "mp3":
            cmd += ["-x", "--audio-format", "mp3"]
        else:
            if quality == "bestaudio":
                cmd += ["-x", "--audio-format", "mp3"]
            elif quality == "best":
                cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]
            else:
                cmd += ["-f", quality]
            cmd += ["--merge-output-format", fmt]

        cmd += [
            "--progress",
            "--no-warnings",
            "--newline",
            url
        ]

        downloads[dl_id]["log"] = "yt-dlp চালু হচ্ছে..."
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        last_filename = None
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            # Parse progress
            if "[download]" in line:
                if "%" in line:
                    try:
                        pct_str = line.split("%")[0].split()[-1]
                        pct = float(pct_str.replace(",", "."))
                        downloads[dl_id]["progress"] = min(int(pct), 95)
                        downloads[dl_id]["log"] = line
                    except:
                        downloads[dl_id]["log"] = line
                elif "Destination:" in line:
                    last_filename = line.split("Destination:")[-1].strip()
                    downloads[dl_id]["log"] = "📥 " + os.path.basename(last_filename)
                else:
                    downloads[dl_id]["log"] = line

            elif "[Merger]" in line or "[ffmpeg]" in line:
                downloads[dl_id]["log"] = "🔧 Processing..."
                downloads[dl_id]["progress"] = 90

            elif "has already been downloaded" in line:
                downloads[dl_id]["log"] = "⚠️ Already downloaded"

        process.wait()

        if process.returncode == 0:
            # Find the downloaded file
            filename = None
            if last_filename and os.path.exists(last_filename):
                filename = os.path.basename(last_filename)
            else:
                files = sorted(Path(DOWNLOAD_DIR).iterdir(), key=os.path.getmtime, reverse=True)
                if files:
                    filename = files[0].name

            downloads[dl_id]["status"] = "done"
            downloads[dl_id]["progress"] = 100
            downloads[dl_id]["filename"] = filename or "file"
        else:
            downloads[dl_id]["status"] = "error"
            downloads[dl_id]["error"] = "yt-dlp failed. URL check করো।"

    except FileNotFoundError:
        downloads[dl_id]["status"] = "error"
        downloads[dl_id]["error"] = "yt-dlp পাওয়া গেলো না! `pip install yt-dlp` চালাও।"
    except Exception as e:
        downloads[dl_id]["status"] = "error"
        downloads[dl_id]["error"] = str(e)

@app.route("/status/<dl_id>")
def status(dl_id):
    if dl_id not in downloads:
        return jsonify({"status": "error", "error": "Not found"}), 404
    return jsonify(downloads[dl_id])

@app.route("/files")
def list_files():
    try:
        files = []
        for f in sorted(Path(DOWNLOAD_DIR).iterdir(), key=os.path.getmtime, reverse=True):
            if f.is_file():
                size = f.stat().st_size
                if size >= 1024**2:
                    size_str = f"{size/1024**2:.1f} MB"
                elif size >= 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                files.append({"name": f.name, "size": size_str})
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"files": [], "error": str(e)})

def check_deps():
    missing = []
    for pkg in ["flask", "yt_dlp"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg.replace("_", "-"))
    return missing

if __name__ == "__main__":
    print("\n" + "="*45)
    print("  🔮 InstaDown - Termux Downloader")
    print("="*45)

    missing = check_deps()
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"   Run: pip install {' '.join(missing)}")
        sys.exit(1)

    print(f"\n📁 Save folder: {DOWNLOAD_DIR}")
    print(f"🌐 Open browser: http://localhost:6969")
    print(f"\n   Ctrl+C দিয়ে বন্ধ করো\n")
    print("="*45 + "\n")

    app.run(host="0.0.0.0", port=6969, debug=False)
