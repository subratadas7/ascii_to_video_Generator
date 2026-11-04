#!/usr/bin/env python3
"""
Stable monochrome ASCII video converter.

Features:
- Removes a centered yellow title/text overlay from source frames before conversion.
- Adds no new captions, titles, or graphic overlays.
- Uses a fixed character grid and deterministic character placement.
- Applies mild temporal smoothing to reduce flicker around the subject outline.
- Adds a small number of punctuation marks near the subject's edges only.
"""

import argparse
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

CHAR_GROUPS = [
    ".,:",
    ";'`",
    "1|!i",
    "7r2t",
    "f()[]",
    "zxcvnm",
    "23456789",
    "abBDEHKMPR",
    "W@#%&",
]

CELL_W = 9
CELL_H = 16


def load_font(size=13):
    font_candidates = (
        # macOS
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        # Windows
        "consola.ttf",
        "cour.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    )
    for path in font_candidates:
        if os.path.exists(path) or not os.path.isabs(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def remove_center_yellow_text(frame_bgr):
    """
    Remove yellow text embedded in the source video, limited to the central
    title area so ordinary yellow objects elsewhere in the frame are untouched.
    """
    h, w = frame_bgr.shape[:2]
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    # OpenCV hue range for yellow; saturation/value thresholds ignore whites.
    yellow = cv2.inRange(
        hsv,
        np.array([15, 75, 105], dtype=np.uint8),
        np.array([42, 255, 255], dtype=np.uint8),
    )

    # Restrict removal to the central title zone where the supplied overlay sits.
    region = np.zeros((h, w), dtype=np.uint8)
    x1, x2 = int(w * 0.15), int(w * 0.85)
    y1, y2 = int(h * 0.30), int(h * 0.72)
    region[y1:y2, x1:x2] = 255
    mask = cv2.bitwise_and(yellow, region)

    # Expand slightly to catch anti-aliased edges of the lettering.
    kernel = np.ones((5, 5), dtype=np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    if cv2.countNonZero(mask) == 0:
        return frame_bgr

    # Inpaint reconstructs the small area from nearby background/ASCII detail.
    return cv2.inpaint(frame_bgr, mask, 5, cv2.INPAINT_TELEA)


def stable_choice(group, x, y):
    """Repeatable character choice for each grid location; no random flicker."""
    index = (x * 37 + y * 61 + x * y * 7) % len(group)
    return group[index]


def convert_frame(frame_bgr, columns, font, previous_gray,
                  temporal_smoothing=0.22, edge_dots=0.07):
    # Remove the yellow title that is already present in the source footage.
    cleaned = remove_center_yellow_text(frame_bgr)

    rgb = cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB)
    source = Image.fromarray(rgb)
    rows = max(
        1,
        int(columns * source.height / source.width * CELL_W / CELL_H),
    )
    small = source.resize((columns, rows), Image.Resampling.LANCZOS)
    gray = np.asarray(small.convert("L"), dtype=np.float32)

    # Mild temporal smoothing stabilizes the silhouette without freezing motion.
    if previous_gray is not None and previous_gray.shape == gray.shape:
        gray = (
            (1.0 - temporal_smoothing) * gray
            + temporal_smoothing * previous_gray
        )

    # Moderate brightness/contrast adjustment; keep black negative space.
    gray = np.clip((gray - 15.0) * 1.22 + 12.0, 0, 255)
    gray = np.power(gray / 255.0, 0.90) * 255.0

    subject = (gray >= 38).astype(np.uint8)
    kernel = np.ones((3, 3), dtype=np.uint8)
    expanded = cv2.dilate(subject, kernel, iterations=1)
    eroded = cv2.erode(subject, kernel, iterations=1)
    edge_band = expanded > eroded

    canvas = Image.new(
        "RGB", (columns * CELL_W, rows * CELL_H), (0, 0, 0)
    )
    draw = ImageDraw.Draw(canvas)

    for y in range(rows):
        for x in range(columns):
            value = float(gray[y, x])

            if value >= 38:
                level = int((value / 255.0) * (len(CHAR_GROUPS) - 1))
                level = max(0, min(level, len(CHAR_GROUPS) - 1))
                char = stable_choice(CHAR_GROUPS[level], x, y)
                shade = int(185 + (value / 255.0) * 70)
                shade = max(180, min(255, shade))
            elif edge_band[y, x] and edge_dots > 0:
                # Fixed sparse punctuation near the subject's edge.
                pattern = (x * 13 + y * 29 + x * y) % 1000
                if pattern >= int(edge_dots * 1000):
                    continue
                char = stable_choice(".,:", x, y)
                shade = 165
            else:
                continue

            draw.text(
                (x * CELL_W, y * CELL_H),
                char,
                font=font,
                fill=(shade, shade, shade),
            )

    return canvas, gray


def convert_video(input_path, output_path, columns=120, fps=10.0,
                  smoothing=0.22, edge_dots=0.07):
    if not os.path.isfile(input_path):
        raise FileNotFoundError(
            f"Input video not found: {input_path}. "
            "Put it in this folder or provide its full path."
        )

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError("Could not open video. Try MP4, MOV, or AVI.")

    source_fps = cap.get(cv2.CAP_PROP_FPS) or fps
    source_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if source_w <= 0 or source_h <= 0:
        cap.release()
        raise RuntimeError("Could not read video dimensions.")

    rows = max(1, int(columns * source_h / source_w * CELL_W / CELL_H))
    size = (columns * CELL_W, rows * CELL_H)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    writer = cv2.VideoWriter(
        output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, size
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError("Could not create output MP4.")

    frame_step = max(1, round(source_fps / fps))
    font = load_font()
    previous_gray = None
    source_index = written = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if source_index % frame_step == 0:
                image, previous_gray = convert_frame(
                    frame, columns, font, previous_gray,
                    smoothing, edge_dots
                )
                bgr = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
                writer.write(bgr)
                written += 1
                if written % 25 == 0:
                    print(f"Rendering: {written} frames...", flush=True)
            source_index += 1
    finally:
        cap.release()
        writer.release()

    if written == 0:
        raise RuntimeError("No frames were converted.")

    print("\nASCII video created successfully!")
    print("Output:", os.path.abspath(output_path))
    print(f"Frames: {written} | Resolution: {size[0]}x{size[1]}")
    print("Yellow center text removal: enabled")
    print("New title/caption overlay: none")


def main():
    parser = argparse.ArgumentParser(
        description="Stable ASCII video; remove centered yellow title, add no overlay."
    )
    parser.add_argument("input", nargs="?", default="input.mp4")
    parser.add_argument("-o", "--output", default="ascii_no_yellow_stable.mp4")
    parser.add_argument("--width", type=int, default=120)
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--smoothing", type=float, default=0.22)
    parser.add_argument("--edge-dots", type=float, default=0.07)
    args = parser.parse_args()

    if (args.width < 30 or args.fps <= 0
            or not 0 <= args.smoothing <= 0.45
            or not 0 <= args.edge_dots <= 0.3):
        parser.error("Invalid width, fps, smoothing, or edge-dots value.")

    try:
        convert_video(
            args.input, args.output, args.width, args.fps,
            args.smoothing, args.edge_dots
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
