#!/usr/bin/env python3
"""
SparkDownloader - Social Media Downloader
Termux Web Downloader | localhost:6969
Supports: Instagram, YouTube, TikTok, Facebook, Twitter/X and more
"""

import os
import sys
import threading
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DOWNLOAD_DIR = os.path.expanduser("~/storage/downloads/SparkDownloader")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

downloads = {}

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SparkDownloader</title>
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
  .header { text-align: center; margin-bottom: 32px; }
  .logo {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a855f7, #7c3aed, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
  }
  .logo span { font-weight: 300; }
  .subtitle { color: var(--muted); font-size: 0.82rem; margin-top: 6px; }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    width: 100%;
    max-width: 520px;
    margin-bottom: 16px;
  }
  .input-group { display: flex; flex-direction: column; gap: 12px; }
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
  .url-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--glow); }
  .url-input::placeholder { color: var(--muted); }
  .options-row { display: flex; gap: 10px; }
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
  .progress-wrap { display: none; margin-top: 10px; }
  .progress-wrap.active { display: block; }
  .progress-label {
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
  }
  .progress-bar {
    height: 5px;
    background: var(--border);
    border-radius: 99px;
    overflow: hidden;
  }
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    border-radius: 99px;
    width: 0%;
    transition: width 0.4s ease;
  }
  .status-box {
    display: none;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.85rem;
    line-height: 1.7;
    color: var(--muted);
    max-height: 160px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
    margin-top: 10px;
    font-family: monospace;
  }
  .status-box.active { display: block; }
  .support-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
  .chip {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 99px;
    font-size: 0.76rem;
    color: var(--muted);
    padding: 4px 12px;
  }
  .section-label {
    font-size: 0.78rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
  }
  .history-list { display: flex; flex-direction: column; gap: 8px; max-height: 260px; overflow-y: auto; }
  .history-item {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.82rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
  }
  .history-item .fname { color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
  .empty-state { color: var(--muted); font-size: 0.85rem; text-align: center; padding: 16px 0; }
  footer { color: var(--muted); font-size: 0.76rem; margin-top: 24px; text-align: center; line-height: 1.8; }
</style>
</head>
<body>

<div class="header">
  <div class="logo">⚡ Spark<span>Downloader</span></div>
  <div class="subtitle">Social Media Downloader &bull; localhost:6969</div>
</div>

<div class="card">
  <div class="input-group">
    <input class="url-input" id="urlInput" type="url"
      placeholder="Paste URL — Instagram, YouTube, TikTok, Facebook...">

    <div class="options-row">
      <select class="select-box" id="typeSelect" onchange="onTypeChange()">
        <option value="video">Video (MP4)</option>
        <option value="audio">Audio Only (MP3)</option>
      </select>
      <select class="select-box" id="qualitySelect">
        <option value="best">Best Quality</option>
        <option value="good">720p</option>
        <option value="low">480p / Smallest</option>
      </select>
    </div>

    <button class="btn btn-primary" id="dlBtn" onclick="startDownload()">
      ⬇&nbsp; Download
    </button>
  </div>

  <div class="progress-wrap" id="progressWrap">
    <div class="progress-label">
      <span id="progressText">Downloading...</span>
      <span id="progressPct">0%</span>
    </div>
    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
  </div>
  <div class="status-box" id="statusBox"></div>

  <div class="support-chips">
    <span class="chip">📸 Instagram</span>
    <span class="chip">▶ YouTube</span>
    <span class="chip">🎵 TikTok</span>
    <span class="chip">📘 Facebook</span>
    <span class="chip">🐦 Twitter / X</span>
    <span class="chip">+ more</span>
  </div>
</div>

<div class="card">
  <div class="section-label">📁 Downloaded Files</div>
  <div class="history-list" id="historyList">
    <div class="empty-state">No files yet</div>
  </div>
</div>

<footer>
  Saved to: ~/storage/downloads/SparkDownloader/<br>
  Powered by yt-dlp &bull; SparkDownloader v1.0
</footer>

<script>
let pollInterval = null;

function onTypeChange() {
  // nothing needed for now — backend handles it
}

function log(msg, color) {
  const box = document.getElementById('statusBox');
  box.classList.add('active');
  box.innerHTML += `<span style="color:${color||'#6b6b8a'}">${msg}</span>\n`;
  box.scrollTop = box.scrollHeight;
}

function setProgress(pct, label) {
  document.getElementById('progressWrap').classList.add('active');
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('progressPct').textContent = pct + '%';
  if (label) document.getElementById('progressText').textContent = label;
}

function resetUI() {
  document.getElementById('progressWrap').classList.remove('active');
  document.getElementById('progressFill').style.width = '0%';
  document.getElementById('progressPct').textContent = '0%';
  document.getElementById('progressText').textContent = 'Downloading...';
  document.getElementById('statusBox').innerHTML = '';
  document.getElementById('statusBox').classList.remove('active');
}

async function startDownload() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { alert('Please paste a URL first!'); return; }

  const type = document.getElementById('typeSelect').value;
  const quality = document.getElementById('qualitySelect').value;

  resetUI();
  document.getElementById('dlBtn').disabled = true;
  log('Starting download...', '#f59e0b');
  setProgress(5, 'Connecting...');

  try {
    const resp = await fetch('/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, type, quality })
    });
    const data = await resp.json();

    if (data.id) {
      pollStatus(data.id);
    } else {
      log('Error: ' + (data.error || 'Unknown error'), '#ef4444');
      document.getElementById('dlBtn').disabled = false;
    }
  } catch(e) {
    log('Request failed: ' + e.message, '#ef4444');
    document.getElementById('dlBtn').disabled = false;
  }
}

function pollStatus(id) {
  pollInterval = setInterval(async () => {
    try {
      const resp = await fetch('/status/' + id);
      const data = await resp.json();

      if (data.progress) setProgress(data.progress, data.stage || 'Downloading...');
      if (data.log) log(data.log, '#6b6b8a');

      if (data.status === 'done') {
        clearInterval(pollInterval);
        setProgress(100, 'Complete!');
        log('✅ Done! File: ' + data.filename, '#22c55e');
        document.getElementById('dlBtn').disabled = false;
        document.getElementById('urlInput').value = '';
        loadHistory();
      } else if (data.status === 'error') {
        clearInterval(pollInterval);
        log('❌ ' + data.error, '#ef4444');
        document.getElementById('dlBtn').disabled = false;
      }
    } catch(e) {}
  }, 1200);
}

async function loadHistory() {
  try {
    const resp = await fetch('/files');
    const data = await resp.json();
    const list = document.getElementById('historyList');
    if (!data.files || data.files.length === 0) {
      list.innerHTML = '<div class="empty-state">No files yet</div>';
      return;
    }
    list.innerHTML = data.files.slice(0, 25).map(f => `
      <div class="history-item">
        <span class="fname">📄 ${f.name}</span>
        <span style="color:var(--muted);font-size:0.76rem;white-space:nowrap">${f.size}</span>
      </div>
    `).join('');
  } catch(e) {}
}

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
    dl_type = data.get("type", "video")   # "video" or "audio"
    quality = data.get("quality", "best") # "best", "good", "low"

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    import uuid
    dl_id = str(uuid.uuid4())[:8]
    downloads[dl_id] = {
        "status": "running",
        "progress": 5,
        "stage": "Starting...",
        "log": None,
        "filename": None,
        "error": None
    }

    threading.Thread(
        target=run_download,
        args=(dl_id, url, dl_type, quality),
        daemon=True
    ).start()

    return jsonify({"id": dl_id})


def run_download(dl_id, url, dl_type, quality):
    try:
        output_template = os.path.join(DOWNLOAD_DIR, "%(title).80s.%(ext)s")

        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-o", output_template,
            "--newline",
            "--no-warnings",
            "--ffmpeg-location", "/data/data/com.termux/files/usr/bin/ffmpeg",
        ]

        if dl_type == "audio":
            # Audio only — single file, no merge needed
            cmd += [
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",
            ]
        else:
            # Video — download best mp4 that already has audio, avoid separate streams when possible
            if quality == "best":
                fmt = "bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            elif quality == "good":
                fmt = "bestvideo[height<=720][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]"
            else:
                fmt = "bestvideo[height<=480][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/worst[ext=mp4]/worst"

            cmd += [
                "-f", fmt,
                "--merge-output-format", "mp4",
                "--postprocessor-args", "ffmpeg:-c:v copy -c:a aac",
            ]

        cmd.append(url)

        downloads[dl_id]["log"] = "yt-dlp started"
        downloads[dl_id]["stage"] = "Fetching info..."

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

            if "[download]" in line:
                if "Destination:" in line:
                    last_filename = line.split("Destination:")[-1].strip()
                    downloads[dl_id]["stage"] = "Downloading..."
                    downloads[dl_id]["log"] = "Saving: " + os.path.basename(last_filename)
                elif "%" in line:
                    try:
                        pct_str = line.split("%")[0].split()[-1].replace(",", ".")
                        pct = float(pct_str)
                        downloads[dl_id]["progress"] = max(5, min(int(pct * 0.85), 88))
                        downloads[dl_id]["stage"] = "Downloading..."
                    except:
                        pass
                elif "has already been downloaded" in line:
                    downloads[dl_id]["log"] = "Already downloaded"
            elif "[Merger]" in line or "[ffmpeg]" in line or "Merging" in line:
                downloads[dl_id]["stage"] = "Merging video & audio..."
                downloads[dl_id]["progress"] = 92
                downloads[dl_id]["log"] = "Merging..."
            elif "[ExtractAudio]" in line or "Destination" in line:
                downloads[dl_id]["stage"] = "Converting..."
                downloads[dl_id]["progress"] = 90

        process.wait()

        if process.returncode == 0:
            # Find newest file in output dir
            filename = None
            if last_filename:
                # yt-dlp may change extension after merge/convert
                stem = Path(last_filename).stem
                candidates = list(Path(DOWNLOAD_DIR).glob(f"{stem}.*"))
                if candidates:
                    filename = max(candidates, key=os.path.getmtime).name

            if not filename:
                files = sorted(Path(DOWNLOAD_DIR).iterdir(), key=os.path.getmtime, reverse=True)
                if files:
                    filename = files[0].name

            downloads[dl_id]["status"] = "done"
            downloads[dl_id]["progress"] = 100
            downloads[dl_id]["filename"] = filename or "downloaded file"
        else:
            downloads[dl_id]["status"] = "error"
            downloads[dl_id]["error"] = "yt-dlp failed. Check the URL and try again."

    except FileNotFoundError:
        downloads[dl_id]["status"] = "error"
        downloads[dl_id]["error"] = "yt-dlp not found. Run: pip install yt-dlp"
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
                if size >= 1024 ** 2:
                    size_str = f"{size / 1024 ** 2:.1f} MB"
                elif size >= 1024:
                    size_str = f"{size / 1024:.1f} KB"
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
    print("\n" + "=" * 45)
    print("  ⚡ SparkDownloader v1.0")
    print("=" * 45)

    missing = check_deps()
    if missing:
        print(f"\n  Missing packages: {', '.join(missing)}")
        print(f"  Run: pip install {' '.join(missing)}")
        sys.exit(1)

    print(f"\n  Save folder : {DOWNLOAD_DIR}")
    print(f"  Open browser: http://localhost:6969")
    print(f"\n  Press Ctrl+C to stop\n")
    print("=" * 45 + "\n")

    app.run(host="0.0.0.0", port=6969, debug=False)
