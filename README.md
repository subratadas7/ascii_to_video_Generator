# Stable ASCII Video

Converts video into a high-contrast monochrome ASCII animation while eliminating embedded yellow titles/captions from the original footage.

### Key Features:
- **Clean Output**: Does not introduce any watermark, title, or overlay.
- **Flicker Reduction**: Employs temporal smoothing and deterministic character selection to minimize jitter.
- **Refined Edges**: Restricts punctuation dots to subject contours on a solid black background.

---

## Windows Setup

### 1. Prerequisites
- [Python 3.10+](https://www.python.org/downloads/) installed.
- **Important**: During Python installation, make sure to check **"Add python.exe to PATH"**.

### 2. Setup & Execution

Place your source video in this folder as `input.mp4`, then open **Command Prompt (`cmd`)** or **PowerShell** in the project folder:

#### Using Command Prompt (`cmd`)
```cmd
:: Create a virtual environment
python -m venv .venv

:: Activate the environment
.venv\Scripts\activate

:: Upgrade pip and install requirements
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

:: Convert video
python main.py input.mp4

:: Open the result
start ascii_no_yellow_stable.mp4
```

#### Using PowerShell
```powershell
# Create a virtual environment
python -m venv .venv

# Activate the environment
.venv\Scripts\Activate.ps1

# Upgrade pip and install requirements
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Convert video
python main.py input.mp4

# Open the result
start ascii_no_yellow_stable.mp4
```

> **Tip for PowerShell:** If you encounter `running scripts is disabled on this system`, allow script execution for the current session:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```
> then run `.venv\Scripts\Activate.ps1` again.

---

## macOS & Linux Setup

Place your video in this folder as `input.mp4`, then run:

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the environment
source .venv/bin/activate

# Upgrade pip and install requirements
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Convert video
python main.py input.mp4

# Open the result (macOS)
open ascii_no_yellow_stable.mp4
# On Linux:
# xdg-open ascii_no_yellow_stable.mp4
```

---

## Optional Parameters

You can fine-tune smoothing and edge density:

```bash
python main.py input.mp4 --smoothing 0.30 --edge-dots 0.05
```

- `--smoothing`: Temporal blend factor between frames to reduce flicker (default: `0.25`).
- `--edge-dots`: Density of punctuation dots along high-contrast boundaries (default: `0.04`).

---

## Notes
- Output is generated as `ascii_no_yellow_stable.mp4`.
- The yellow removal specifically targets yellow hue pixels within the central title region so that other objects across the frame remain unaffected.
