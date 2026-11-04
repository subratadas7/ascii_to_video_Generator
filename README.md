# Stable ASCII Video

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://www.python.org/downloads/)
[![Platform: macOS | Windows | Linux](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)]()

Convert videos into high-contrast monochrome ASCII animations with temporal stabilization to eliminate flicker. Features an intelligent filter to automatically remove central yellow title/text overlays from source footage without affecting surrounding content.

Fully cross-platform: tested and compatible with **Windows**, **macOS**, and **Linux**.

---

## Key Features

- **Cross-Platform Compatibility**: Automatically discovers system monospace fonts on Windows (`Consolas`, `Lucida Console`), macOS (`Menlo`, `SF Mono`), and Linux (`DejaVu Sans Mono`).
- **H.264 (avc1) / MPEG-4 (mp4v) Codec Support**: Encodes with codecs supported natively by Windows Media Player, macOS QuickTime, and modern web browsers.
- **Clean Output**: Does not introduce any watermark, title, or overlay.
- **Smart Yellow Title Removal**: Automatically isolates and inpaints centered yellow subtitle/title text from frames before conversion. Can be toggled on/off via `--no-yellow-filter`.
- **Flicker Reduction & Edge Control**: Uses deterministic character mapping, mild temporal blending, and sparse punctuation dots along object contours to eliminate jitter.
- **Live Terminal Progress**: Clean single-line progress indicator showing frame count and percentage.

---

## Getting Started

### 1. Windows Setup

#### Prerequisites:
- Download & install [Python 3.10+](https://www.python.org/downloads/).
- **Important**: In the installer, check the box: **"Add python.exe to PATH"**.

#### Running in Command Prompt (`cmd`):
```cmd
:: 1. Navigate to the project directory
cd Ascii_Generator

:: 2. Create virtual environment
python -m venv .venv

:: 3. Activate virtual environment
.venv\Scripts\activate

:: 4. Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

:: 5. Run conversion (uses input.mp4 by default)
python main.py input.mp4

:: 6. Open the generated ASCII video
start ascii_no_yellow_stable.mp4
```

#### Running in PowerShell:
```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 3. Run conversion
python main.py input.mp4

# 4. Open the result
start ascii_no_yellow_stable.mp4
```

> **PowerShell execution policy note:** If you see `running scripts is disabled on this system`, enable script execution for your session by running:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```
> then run `.venv\Scripts\Activate.ps1` again.

---

### 2. macOS & Linux Setup

Place your video in the project directory as `input.mp4` (or specify any file path):

```bash
# 1. Create virtual environment
python3 -m venv .venv

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4. Run conversion
python main.py input.mp4

# 5. Play video
# macOS:
open ascii_no_yellow_stable.mp4
# Linux:
# xdg-open ascii_no_yellow_stable.mp4
```

---

## CLI Options & Customization

```bash
python main.py [input] [options]
```

| Argument | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `input` | Positional | `input.mp4` | Path to the source video file (MP4, MOV, AVI, etc.) |
| `-o`, `--output` | String | `ascii_no_yellow_stable.mp4` | Destination output file path |
| `--width` | Integer | `120` | ASCII character grid columns (higher = more detail) |
| `--fps` | Float | `10.0` | Framerate of the rendered video |
| `--smoothing` | Float | `0.22` | Temporal blend factor (0.0 to 0.45) to reduce flicker |
| `--edge-dots` | Float | `0.07` | Density of sparse edge punctuation (0.0 to 0.30) |
| `--no-yellow-filter` | Flag | `False` | Disable the central yellow subtitle/title removal filter |
| `--font` | String | `None` | Path to a custom `.ttf` or `.otf` font file |

### Examples:

1. **Convert standard video without yellow subtitle filtering:**
   ```bash
   python main.py my_video.mp4 --no-yellow-filter -o output.mp4
   ```

2. **Higher resolution ASCII output at 15 FPS:**
   ```bash
   python main.py input.mp4 --width 160 --fps 15.0
   ```

3. **Maximum stability / smoothing for high-noise footage:**
   ```bash
   python main.py input.mp4 --smoothing 0.35 --edge-dots 0.04
   ```

4. **Use a custom monospace font:**
   ```bash
   python main.py input.mp4 --font /path/to/my-font.ttf
   ```

---

## Project Structure

```
Ascii_Generator/
├── main.py              # Core ASCII rendering engine & CLI
├── requirements.txt     # Python dependencies (OpenCV, Pillow, NumPy)
├── .gitignore           # Git ignore rules for virtual environments & media
├── .gitattributes       # Cross-platform LF/CRLF line ending normalization
├── LICENSE              # MIT License
└── README.md            # Documentation & setup guide
```

---

## License

This project is licensed under the [MIT License](LICENSE) — see the LICENSE file for details.
