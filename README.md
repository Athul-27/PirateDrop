<p align="center">
  <img src="assets/icon.ico" width="96" alt="PirateDrop icon" />
</p>

<h1 align="center">PirateDrop</h1>

<p align="center">
  <b>Simple. Secure. File Sharing.</b><br>
  A polished desktop app that wraps the <a href="https://github.com/schollz/croc">croc</a> CLI for peer-to-peer file transfers — no terminal required.
</p>

---

## Features

- **Send files & folders** — pick via dialog or drag & drop, queue multiple transfers
- **Direct or Stored mode** — instant peer-to-peer, or upload an encrypted copy to getcroc.com with custom expiration (30m–2w) and download count (1–20)
- **Receive anything** — paste a share code, link, or store token; pick a destination folder
- **Live progress** — real percentages, speed and ETA parsed from croc output (never fabricated)
- **Cancel anytime** — graceful termination with bounded force-kill cleanup
- **Transfer history** — last 200 transfers stored locally in `%APPDATA%\PirateDrop\history.json`
- **Neo-Brutalist UI** — pure black-and-white, high-contrast, monospace share codes, Windows scaling friendly
- **croc bundled** — the croc v11.5.4 executable is packaged inside the app; no separate install

## Download

Grab the latest `PirateDrop.exe` from the [Releases page](https://github.com/Athul-27/PirateDrop/releases).

> **Note:** this is a one-file PyInstaller build. Windows SmartScreen or antivirus may warn on first run — this is a common false positive for new executables; you can choose "More info" → "Run anyway".

## Usage

1. **Open** PirateDrop — the app checks that croc is available on startup
2. **Send**: switch to SEND, pick files or a folder, press **SEND FILES**, share the code with the receiver
3. **Receive**: switch to RECEIVE, paste the code/link/token, choose a destination folder, press **RECEIVE FILES**

**Security basics:**
- Anyone with the code/link can download the transfer — share only with people you trust
- Stored transfers upload an encrypted copy to getcroc.com
- Share codes and links are kept in your local history; clear it from the HISTORY tab if needed

## Build from source

Requirements: **Windows**, **Python 3.12+**

```powershell
git clone https://github.com/Athul-27/PirateDrop.git
cd PirateDrop
pip install -r requirements.txt

# run in development
python app.py

# build the standalone executable -> dist\PirateDrop.exe
.\build.ps1
```

`build.ps1` cleans `build/` and `dist/`, generates the icon if missing, and runs PyInstaller with `app.spec` (bundles `croc.exe` + `assets/icon.ico`).

## Tests

```powershell
# unit suite (mocked croc processes, offscreen Qt) — 48 tests
python -m pytest

# real end-to-end transfer with the bundled croc (requires network)
python -m pytest --run-integration
```

## Project structure

```
PirateDrop/
├── app.py              # entry point
├── app.spec            # PyInstaller build spec
├── build.ps1           # clean + build script
├── croc.exe            # bundled croc CLI v11.5.4
├── assets/             # app icon
├── ui/                 # PySide6 screens (Send, Receive, History, Settings) + styles
├── services/           # croc wrapper, progress parser, config, history
├── scripts/            # icon generator
├── tests/              # pytest suite
└── docs/               # implementation plan + croc integration notes
```

## Tech stack

| Component | Choice |
|---|---|
| Language | Python 3.12 |
| GUI | PySide6 (Qt for Python) |
| Transfer engine | croc CLI v11.5.4 (bundled) |
| Packaging | PyInstaller (one-file, windowed) |
| Testing | pytest |

## Known limitations

- **Windows-only**
- Network-dependent — needs a reachable relay or direct connection (croc's `--no-local` flag may help on restrictive networks)
- Progress parsing is version-dependent on croc's output format
- Send and Receive screens run independently — one send and one receive can be active at the same time
