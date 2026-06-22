# ⚡ SparkDownloader

A minimal, self-hosted social media downloader that runs locally on **Termux** via a web UI. Paste a link, pick a format, download — no accounts, no ads, no tracking.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white)](https://python.org)
[![Platform: Termux](https://img.shields.io/badge/Platform-Termux-1f425f)](https://termux.dev)

---

## Features

- **One-tap paste & download** — clean mobile-first UI at `localhost:6969`
- **Video & audio** — MP4 (best / 720p / 480p) or MP3 extraction
- **Multithreaded** — up to 4 concurrent downloads, each in its own thread
- **Auto-setup** — checks and installs all dependencies on first run
- **Supported sites** — YouTube, Instagram, TikTok, Facebook, Twitter/X, and [1000+ more](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) via yt-dlp

---

## Requirements

| Dependency | How it's installed |
|---|---|
| Python 3.10+ | Pre-installed in Termux |
| `flask` | Auto-installed by script |
| `yt-dlp` | Auto-installed by script |
| `ffmpeg` | Auto-installed via `pkg` |
| Termux storage permission | Auto-granted by script |

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/devfahim00/SparkDownloader.git
cd SparkDownloader

# 2. Run — dependencies install automatically on first launch
python start.py
```

Then open **`http://localhost:6969`** in your browser.

> Files are saved to `~/storage/downloads/SparkDownloader/`

---

## Usage

1. Copy a video URL (YouTube, Instagram, TikTok, etc.)
2. Open `http://localhost:6969`
3. Paste the URL → choose format & quality → tap **Download**
4. Find the file in `~/storage/downloads/SparkDownloader/`

---

## Project Structure

```
SparkDownloader/
├── start.py        # Main script — server + auto-setup
└── README.md
```

---

## License

This project is licensed under the **GNU General Public License v3.0**.

You are free to use, modify, and distribute this software under the terms of the GPL-3.0. Any derivative work must also be distributed under the same license.

See the [LICENSE](LICENSE) file or visit [gnu.org/licenses/gpl-3.0](https://www.gnu.org/licenses/gpl-3.0) for the full license text.

---

## Disclaimer

This tool is intended for downloading content you have the right to download (your own content, public domain, or content explicitly allowed by the platform's terms). The author is not responsible for any misuse.
