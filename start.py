#!/usr/bin/env python3
"""
SparkDownloader — Social Media Downloader
Termux Web Downloader | localhost:6969
"""

import os
import sys
import subprocess

# ─── Auto-install & permission check (runs before Flask import) ───────────────

REQUIRED_PIP = ["flask", "yt-dlp"]
REQUIRED_BIN = ["ffmpeg", "yt-dlp"]


def _pip_installed(pkg):
    import importlib
    name = pkg.replace("-", "_")
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def _bin_exists(binary):
    import shutil
    return shutil.which(binary) is not None


def check_and_setup():
    print("\n⚡ SparkDownloader — Pre-flight Check")
    print("─" * 40)

    # 1. Storage permission
    storage_path = os.path.expanduser("~/storage")
    if not os.path.exists(storage_path):
        print("  [!] Storage permission not granted.")
        print("  → Running: termux-setup-storage")
        try:
            subprocess.run(["termux-setup-storage"], check=True)
            print("  [✓] Storage permission granted")
        except Exception as e:
            print(f"  [✗] Failed: {e}")
            print("  → Please run 'termux-setup-storage' manually and restart.")
            sys.exit(1)
    else:
        print("  [✓] Storage permission OK")

    # 2. pip packages
    for pkg in REQUIRED_PIP:
        if _pip_installed(pkg):
            print(f"  [✓] {pkg}")
        else:
            print(f"  [~] Installing {pkg}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", pkg],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  [✓] {pkg} installed")
            else:
                print(f"  [✗] Failed to install {pkg}:")
                print(result.stderr[-300:])
                sys.exit(1)

    # 3. system binaries (ffmpeg, yt-dlp binary)
    for binary in REQUIRED_BIN:
        if _bin_exists(binary):
            print(f"  [✓] {binary} (binary)")
        else:
            if binary == "ffmpeg":
                print("  [~] Installing ffmpeg via pkg...")
                result = subprocess.run(
                    ["pkg", "install", "-y", "ffmpeg"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    print("  [✓] ffmpeg installed")
                else:
                    print("  [✗] Could not install ffmpeg. Run: pkg install ffmpeg")
                    sys.exit(1)
            elif binary == "yt-dlp":
                # yt-dlp installed via pip — check if it's on PATH
                ytdlp_pip = os.path.join(
                    os.path.dirname(sys.executable), "yt-dlp"
                )
                if os.path.exists(ytdlp_pip):
                    print("  [✓] yt-dlp (via pip bin)")
                else:
                    print("  [~] Installing yt-dlp binary...")
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--quiet", "yt-dlp"],
                        check=True
                    )
                    print("  [✓] yt-dlp installed")

    print("─" * 40)
    print("  All checks passed. Starting server...\n")


check_and_setup()

# ─── Now safe to import ───────────────────────────────────────────────────────

import threading
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DOWNLOAD_DIR = os.path.expanduser("~/storage/downloads/SparkDownloader")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# { dl_id: { status, progress, stage, log, filename, error } }
downloads: dict = {}
# Thread pool limiter — max 4 concurrent downloads
_semaphore = threading.Semaphore(4)

# ─── HTML ─────────────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>SparkDownloader</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:       #08080e;
  --surface:  #0f0f18;
  --card:     #13131f;
  --border:   #1e1e30;
  --border2:  #2a2a40;
  --accent:   #7c3aed;
  --accent-h: #9d5cf6;
  --glow:     rgba(124,58,237,.25);
  --text:     #ddddf0;
  --muted:    #55556e;
  --muted2:   #888899;
  --ok:       #22c55e;
  --err:      #f87171;
  --warn:     #fbbf24;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  min-height: 100svh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 36px 16px 48px;
  -webkit-font-smoothing: antialiased;
}

/* ── Header ── */
.header {
  text-align: center;
  margin-bottom: 40px;
  user-select: none;
}
.wordmark {
  font-size: 1.7rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
  color: var(--text);
}
.wordmark em {
  font-style: normal;
  color: var(--accent-h);
}
.tagline {
  margin-top: 7px;
  font-size: 0.75rem;
  color: var(--muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

/* ── Card ── */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 22px;
  width: 100%;
  max-width: 500px;
  margin-bottom: 14px;
}

/* ── Input ── */
.url-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}
.url-input {
  flex: 1;
  background: var(--surface);
  border: 1.5px solid var(--border2);
  border-radius: 10px;
  color: var(--text);
  font-size: 0.92rem;
  padding: 13px 15px;
  outline: none;
  transition: border-color .18s, box-shadow .18s;
  min-width: 0;
}
.url-input::placeholder { color: var(--muted); }
.url-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--glow);
}

/* Paste button */
.paste-btn {
  background: var(--surface);
  border: 1.5px solid var(--border2);
  border-radius: 10px;
  color: var(--muted2);
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0 14px;
  white-space: nowrap;
  transition: color .15s, border-color .15s;
  flex-shrink: 0;
}
.paste-btn:hover { color: var(--text); border-color: var(--accent); }

/* ── Options ── */
.options-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}
.select-box {
  background: var(--surface);
  border: 1.5px solid var(--border2);
  border-radius: 9px;
  color: var(--text);
  font-size: 0.85rem;
  padding: 10px 12px;
  outline: none;
  cursor: pointer;
  width: 100%;
  transition: border-color .15s;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2355556e' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 30px;
}
.select-box:focus { border-color: var(--accent); }

/* ── Button ── */
.dl-btn {
  width: 100%;
  background: var(--accent);
  border: none;
  border-radius: 10px;
  color: #fff;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  padding: 14px;
  transition: background .18s, opacity .18s, transform .1s;
  position: relative;
  overflow: hidden;
}
.dl-btn::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,.08) 0%, transparent 60%);
  pointer-events: none;
}
.dl-btn:hover:not(:disabled) { background: var(--accent-h); transform: translateY(-1px); }
.dl-btn:active:not(:disabled) { transform: translateY(0); }
.dl-btn:disabled { opacity: .45; cursor: not-allowed; }

/* ── Progress ── */
.progress-wrap {
  display: none;
  margin-top: 16px;
}
.progress-wrap.show { display: block; }
.progress-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.76rem;
  color: var(--muted2);
  margin-bottom: 7px;
}
.bar-bg {
  height: 4px;
  background: var(--border2);
  border-radius: 99px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-h));
  border-radius: 99px;
  width: 0%;
  transition: width .5s cubic-bezier(.4,0,.2,1);
}

/* ── Log ── */
.log-area {
  display: none;
  margin-top: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 11px 14px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.79rem;
  line-height: 1.75;
  color: var(--muted2);
  max-height: 120px;
  overflow-y: auto;
}
.log-area.show { display: block; }
.log-line { display: block; }
.log-ok   { color: var(--ok); }
.log-err  { color: var(--err); }
.log-warn { color: var(--warn); }

/* ── Chips ── */
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 18px;
}
.chip {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 99px;
  color: var(--muted);
  font-size: 0.72rem;
  padding: 3px 11px;
  letter-spacing: 0.01em;
}

/* ── Files card ── */
.card-label {
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 12px;
}
.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 260px;
  overflow-y: auto;
}
.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 13px;
  gap: 10px;
}
.file-name {
  font-size: 0.82rem;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.file-size {
  font-size: 0.73rem;
  color: var(--muted);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.empty { color: var(--muted); font-size: 0.83rem; text-align: center; padding: 18px 0; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 99px; }
</style>
</head>
<body>

<header class="header">
  <div class="wordmark">⚡ Spark<em>DL</em></div>
  <div class="tagline">Social Media Downloader</div>
</header>

<!-- Main card -->
<div class="card">

  <div class="url-row">
    <input class="url-input" id="urlInput" type="url"
      placeholder="Paste a link — YouTube, Instagram, TikTok…" autocomplete="off" autocorrect="off">
    <button class="paste-btn" onclick="pasteUrl()">Paste</button>
  </div>

  <div class="options-row">
    <select class="select-box" id="typeSelect">
      <option value="video">Video (MP4)</option>
      <option value="audio">Audio (MP3)</option>
    </select>
    <select class="select-box" id="qualitySelect">
      <option value="best">Best quality</option>
      <option value="good">720p</option>
      <option value="low">480p / small</option>
    </select>
  </div>

  <button class="dl-btn" id="dlBtn" onclick="startDownload()">Download</button>

  <div class="progress-wrap" id="progressWrap">
    <div class="progress-meta">
      <span id="stageLabel">Starting…</span>
      <span id="pctLabel">0%</span>
    </div>
    <div class="bar-bg"><div class="bar-fill" id="barFill"></div></div>
  </div>

  <div class="log-area" id="logArea"></div>

  <div class="chips">
    <span class="chip">YouTube</span>
    <span class="chip">Instagram</span>
    <span class="chip">TikTok</span>
    <span class="chip">Facebook</span>
    <span class="chip">Twitter / X</span>
    <span class="chip">+ 1000 more</span>
  </div>
</div>

<!-- Files card -->
<div class="card">
  <div class="card-label">Downloaded files</div>
  <div class="file-list" id="fileList"><div class="empty">No files yet</div></div>
</div>

<script>
// ── Helpers ──────────────────────────────────────────────────────────────────

async function pasteUrl() {
  try {
    const text = await navigator.clipboard.readText();
    document.getElementById('urlInput').value = text.trim();
  } catch {
    document.getElementById('urlInput').focus();
  }
}

function setProgress(pct, stage) {
  const wrap = document.getElementById('progressWrap');
  wrap.classList.add('show');
  document.getElementById('barFill').style.width = pct + '%';
  document.getElementById('pctLabel').textContent = pct + '%';
  if (stage) document.getElementById('stageLabel').textContent = stage;
}

function addLog(text, type) {
  // Only show: Starting download, Download started, Done, Error
  const allowed = [
    { key: 'starting', cls: 'log-warn',  prefix: '' },
    { key: 'started',  cls: 'log-warn',  prefix: '' },
    { key: 'done',     cls: 'log-ok',    prefix: '' },
    { key: 'error',    cls: 'log-err',   prefix: '' },
    { key: 'failed',   cls: 'log-err',   prefix: '' },
  ];
  const lower = text.toLowerCase();
  let cls = null;
  for (const rule of allowed) {
    if (lower.includes(rule.key)) { cls = rule.cls; break; }
  }
  // type override
  if (type === 'ok')  cls = 'log-ok';
  if (type === 'err') cls = 'log-err';

  if (!cls) return; // skip anything not in the allowed list

  const area = document.getElementById('logArea');
  area.classList.add('show');
  const span = document.createElement('span');
  span.className = 'log-line ' + cls;
  span.textContent = text;
  area.appendChild(span);
  area.scrollTop = area.scrollHeight;
}

function resetUI() {
  const wrap = document.getElementById('progressWrap');
  wrap.classList.remove('show');
  document.getElementById('barFill').style.width = '0%';
  document.getElementById('pctLabel').textContent = '0%';
  document.getElementById('stageLabel').textContent = 'Starting…';
  const area = document.getElementById('logArea');
  area.innerHTML = '';
  area.classList.remove('show');
}

// ── Download ─────────────────────────────────────────────────────────────────

async function startDownload() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { document.getElementById('urlInput').focus(); return; }

  const type    = document.getElementById('typeSelect').value;
  const quality = document.getElementById('qualitySelect').value;

  resetUI();
  document.getElementById('dlBtn').disabled = true;
  addLog('Starting download…', 'warn');
  setProgress(5, 'Connecting…');

  try {
    const resp = await fetch('/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, type, quality })
    });
    const data = await resp.json();

    if (data.id) {
      addLog('Download started', 'warn');
      pollStatus(data.id);
    } else {
      addLog('Error: ' + (data.error || 'Unknown'), 'err');
      document.getElementById('dlBtn').disabled = false;
    }
  } catch (e) {
    addLog('Error: ' + e.message, 'err');
    document.getElementById('dlBtn').disabled = false;
  }
}

let pollTimer = null;

function pollStatus(id) {
  pollTimer = setInterval(async () => {
    try {
      const resp = await fetch('/status/' + id);
      const data = await resp.json();

      if (data.progress != null) setProgress(data.progress, data.stage || undefined);

      if (data.status === 'done') {
        clearInterval(pollTimer);
        setProgress(100, 'Complete');
        addLog('Done — ' + data.filename, 'ok');
        document.getElementById('dlBtn').disabled = false;
        document.getElementById('urlInput').value = '';
        loadFiles();
      } else if (data.status === 'error') {
        clearInterval(pollTimer);
        addLog('Error: ' + data.error, 'err');
        document.getElementById('dlBtn').disabled = false;
      }
    } catch (_) {}
  }, 1000);
}

// ── File list ─────────────────────────────────────────────────────────────────

async function loadFiles() {
  try {
    const resp = await fetch('/files');
    const { files } = await resp.json();
    const list = document.getElementById('fileList');
    if (!files || files.length === 0) {
      list.innerHTML = '<div class="empty">No files yet</div>';
      return;
    }
    list.innerHTML = files.slice(0, 30).map(f => `
      <div class="file-item">
        <span class="file-name">${f.name}</span>
        <span class="file-size">${f.size}</span>
      </div>`).join('');
  } catch (_) {}
}

loadFiles();
</script>
</body>
</html>"""


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/download", methods=["POST"])
def download():
    data = request.json or {}
    url     = data.get("url", "").strip()
    dl_type = data.get("type", "video")
    quality = data.get("quality", "best")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    dl_id = str(uuid.uuid4())[:8]
    downloads[dl_id] = {
        "status":   "running",
        "progress": 5,
        "stage":    "Starting…",
        "log":      None,
        "filename": None,
        "error":    None,
    }

    t = threading.Thread(
        target=_worker,
        args=(dl_id, url, dl_type, quality),
        daemon=True,
    )
    t.start()

    return jsonify({"id": dl_id})


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
                sz = f.stat().st_size
                if sz >= 1 << 20:
                    s = f"{sz / (1 << 20):.1f} MB"
                elif sz >= 1 << 10:
                    s = f"{sz / (1 << 10):.1f} KB"
                else:
                    s = f"{sz} B"
                files.append({"name": f.name, "size": s})
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"files": [], "error": str(e)})


# ─── Worker ──────────────────────────────────────────────────────────────────

def _worker(dl_id: str, url: str, dl_type: str, quality: str):
    """Runs inside a daemon thread; semaphore limits concurrency to 4."""
    with _semaphore:
        _run_download(dl_id, url, dl_type, quality)


def _run_download(dl_id: str, url: str, dl_type: str, quality: str):
    d = downloads[dl_id]
    try:
        out_tmpl = os.path.join(DOWNLOAD_DIR, "%(title).80s.%(ext)s")

        # Resolve yt-dlp binary: try system PATH first, then pip-installed location
        import shutil as _shutil
        ytdlp_bin = "yt-dlp"
        if not _shutil.which("yt-dlp"):
            candidate = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
            if os.path.exists(candidate):
                ytdlp_bin = candidate

        # Resolve ffmpeg path (Termux default)
        ffmpeg_bin = "ffmpeg"
        termux_ffmpeg = "/data/data/com.termux/files/usr/bin/ffmpeg"
        if os.path.exists(termux_ffmpeg):
            ffmpeg_bin = termux_ffmpeg

        cmd = [
            ytdlp_bin,
            "--no-playlist",
            "-o", out_tmpl,
            "--newline",
            "--no-warnings",
            "--ffmpeg-location", ffmpeg_bin,
        ]

        if dl_type == "audio":
            cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
        else:
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

        d["stage"] = "Fetching info…"
        d["progress"] = 8

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        last_filename = None

        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            if "[download]" in line:
                if "Destination:" in line:
                    last_filename = line.split("Destination:")[-1].strip()
                    d["stage"] = "Downloading…"
                elif "%" in line:
                    try:
                        pct = float(line.split("%")[0].split()[-1].replace(",", "."))
                        d["progress"] = max(10, min(int(pct * 0.85), 88))
                        d["stage"] = "Downloading…"
                    except Exception:
                        pass
            elif any(k in line for k in ("[Merger]", "[ffmpeg]", "Merging")):
                d["stage"] = "Merging…"
                d["progress"] = 92
            elif "[ExtractAudio]" in line or "Converting" in line:
                d["stage"] = "Converting…"
                d["progress"] = 92

        process.wait()

        if process.returncode == 0:
            filename = _resolve_filename(last_filename)
            d["status"]   = "done"
            d["progress"] = 100
            d["filename"] = filename or "file"
        else:
            d["status"] = "error"
            d["error"]  = "Download failed — check the URL and try again."

    except FileNotFoundError:
        d["status"] = "error"
        d["error"]  = "yt-dlp not found. Run: pip install yt-dlp"
    except Exception as e:
        d["status"] = "error"
        d["error"]  = str(e)


def _resolve_filename(last_filename: str | None) -> str | None:
    """Best-effort: find the file yt-dlp actually wrote."""
    if last_filename:
        stem = Path(last_filename).stem
        candidates = list(Path(DOWNLOAD_DIR).glob(f"{stem}.*"))
        if candidates:
            return max(candidates, key=os.path.getmtime).name

    files = sorted(Path(DOWNLOAD_DIR).iterdir(), key=os.path.getmtime, reverse=True)
    if files:
        return files[0].name
    return None


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"  Save folder : {DOWNLOAD_DIR}")
    print(f"  Open        : http://localhost:6969\n")
    app.run(host="0.0.0.0", port=6969, debug=False, threaded=True)
