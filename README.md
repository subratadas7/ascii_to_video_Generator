# Stable ASCII Video — Yellow Title Removed

This version:
- Removes yellow title/text already embedded in the central area of the source video.
- Does not add any new text, title, caption, or overlay.
- Uses stable character placement and mild temporal smoothing to reduce flicker.
- Keeps punctuation sparse and near the subject's edges.
- Keeps the background black.

## macOS setup

Place your video in this folder as `input.mp4`, then run:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py input.mp4
```

Output: `ascii_no_yellow_stable.mp4`

Open it:

```bash
open ascii_no_yellow_stable.mp4
```

Optional:
```bash
python main.py input.mp4 --smoothing 0.30 --edge-dots 0.05
```

The yellow removal is limited to yellow pixels in the central title area. If
your source clip has other important yellow content in that area, it may also
be removed. The subject still moves naturally with the original footage;
smoothing only reduces frame-to-frame flicker.
