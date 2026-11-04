#!/usr/bin/env python3
"""
Stable monochrome ASCII video converter.

Features:
- Removes a centered yellow title/text overlay from source frames before conversion.
- Adds no new captions, titles, or graphic overlays.
- Uses a fixed character grid and deterministic character placement.
- Applies mild temporal smoothing to reduce flicker around the subject outline.
- Adds a small number of punctuation marks near the subject's edges only.
- Fully cross-platform: tested and compatible with macOS, Windows, and Linux.
"""

import argparse
import os
import sys
from pathlib import Path

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


def get_font_candidates(custom_font=None):
    """Return an ordered list of font paths to search across macOS, Windows, and Linux."""
    candidates = []
    if custom_font:
        candidates.append(custom_font)

    # macOS system monospace fonts
    candidates.extend([
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/SFMono-Regular.otf",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/Library/Fonts/Courier New.ttf",
    ])

    # Windows system monospace fonts
    windir = os.environ.get("WINDIR", r"C:\Windows")
    candidates.extend([
        os.path.join(windir, "Fonts", "consola.ttf"),
        os.path.join(windir, "Fonts", "lucon.ttf"),
        os.path.join(windir, "Fonts", "cour.ttf"),
        # Pillow fallback name resolution on Windows
        "consola.ttf",
        "lucon.ttf",
        "cour.ttf",
    ])

    # Linux system monospace fonts
    candidates.extend([
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    ])

    return candidates


def load_font(size=13, custom_font=None):
    """Load a suitable monospace TrueType font, or fall back to Pillow's default."""
    for candidate in get_font_candidates(custom_font):
        if os.path.exists(candidate) or not os.path.isabs(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except (OSError, IOError):
                pass
    return ImageFont.load_default()


def create_video_writer(output_path, fps, size):
    """
    Initialize cv2.VideoWriter with cross-platform codec fallback.
    Tries avc1 (H.264) first for native Windows & Mac playback,
    falling back to mp4v if avc1 is unavailable.
    """
    abs_output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_output), exist_ok=True)

    codecs = [
        ("avc1", "H.264 (avc1)"),
        ("mp4v", "MPEG-4 (mp4v)"),
        ("XVID", "XVID"),
    ]

    for fourcc_code, name in codecs:
        fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
        writer = cv2.VideoWriter(abs_output, fourcc, fps, size)
        if writer.isOpened():
            return writer, fourcc_code, name
        writer.release()

    raise RuntimeError(
        f"Could not open video writer for '{output_path}'. "
        "Verify your OpenCV installation supports MP4 output."
    )


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
                  temporal_smoothing=0.22, edge_dots=0.07,
                  remove_yellow=True):
    # Optionally remove yellow title embedded in central area of source footage.
    if remove_yellow:
        cleaned = remove_center_yellow_text(frame_bgr)
    else:
        cleaned = frame_bgr

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

    groups_count = len(CHAR_GROUPS)
    for y in range(rows):
        for x in range(columns):
            value = float(gray[y, x])

            if value >= 38:
                level = int((value / 255.0) * (groups_count - 1))
                level = max(0, min(level, groups_count - 1))
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
                  smoothing=0.22, edge_dots=0.07, remove_yellow=True,
                  custom_font=None):
    clean_input = os.path.normpath(str(input_path))
    if not os.path.isfile(clean_input):
        raise FileNotFoundError(
            f"Input video not found: '{clean_input}'. "
            "Please ensure the file exists or provide its full path."
        )

    cap = cv2.VideoCapture(clean_input)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open '{clean_input}'. Unsupported format or missing codec.")

    source_fps = cap.get(cv2.CAP_PROP_FPS) or fps
    source_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_source_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if source_w <= 0 or source_h <= 0:
        cap.release()
        raise RuntimeError("Could not read video dimensions from input.")

    rows = max(1, int(columns * source_h / source_w * CELL_W / CELL_H))
    size = (columns * CELL_W, rows * CELL_H)

    writer, codec_code, codec_name = create_video_writer(output_path, fps, size)

    frame_step = max(1, round(source_fps / fps))
    font = load_font(custom_font=custom_font)
    previous_gray = None
    source_index = written = 0

    estimated_output_frames = (
        (total_source_frames // frame_step) if total_source_frames > 0 else 0
    )

    print(f"Input:       {os.path.abspath(clean_input)}")
    print(f"Source:      {source_w}x{source_h} @ {source_fps:.2f} FPS ({total_source_frames} frames)")
    print(f"Output:      {os.path.abspath(output_path)}")
    print(f"Target:      {size[0]}x{size[1]} @ {fps:.2f} FPS (Codec: {codec_name})")
    print(f"Grid size:   {columns} cols x {rows} rows")
    print(f"Yellow filter: {'Enabled' if remove_yellow else 'Disabled'}")
    print("-" * 50)

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if source_index % frame_step == 0:
                image, previous_gray = convert_frame(
                    frame, columns, font, previous_gray,
                    smoothing, edge_dots, remove_yellow
                )
                bgr = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
                writer.write(bgr)
                written += 1

                if estimated_output_frames > 0:
                    pct = min(100.0, (written / estimated_output_frames) * 100)
                    print(
                        f"\rRendering: frame {written}/{estimated_output_frames} [{pct:5.1f}%]",
                        end="",
                        flush=True,
                    )
                else:
                    print(f"\rRendering: frame {written}...", end="", flush=True)

            source_index += 1
    finally:
        cap.release()
        writer.release()

    print()  # Newline after carriage return progress

    if written == 0:
        raise RuntimeError("No frames were converted.")

    print("-" * 50)
    print("ASCII video created successfully!")
    print(f"Output saved to: {os.path.abspath(output_path)}")
    print(f"Total rendered frames: {written}")


def main():
    parser = argparse.ArgumentParser(
        description="Cross-platform ASCII video generator with flicker reduction and subtitle removal."
    )
    parser.add_argument("input", nargs="?", default="input.mp4", help="Path to input video (default: input.mp4)")
    parser.add_argument("-o", "--output", default="ascii_no_yellow_stable.mp4", help="Output path (default: ascii_no_yellow_stable.mp4)")
    parser.add_argument("--width", type=int, default=120, help="ASCII grid columns (default: 120)")
    parser.add_argument("--fps", type=float, default=10.0, help="Target framerate (default: 10.0)")
    parser.add_argument("--smoothing", type=float, default=0.22, help="Temporal blend 0.0-0.45 (default: 0.22)")
    parser.add_argument("--edge-dots", type=float, default=0.07, help="Edge punctuation density 0.0-0.30 (default: 0.07)")
    parser.add_argument("--no-yellow-filter", action="store_true", help="Disable removal of yellow text overlay")
    parser.add_argument("--font", type=str, default=None, help="Optional path to custom TTF/OTF font file")
    args = parser.parse_args()

    if (args.width < 30 or args.fps <= 0
            or not 0 <= args.smoothing <= 0.45
            or not 0 <= args.edge_dots <= 0.3):
        parser.error("Invalid width, fps, smoothing, or edge-dots value.")

    try:
        convert_video(
            input_path=args.input,
            output_path=args.output,
            columns=args.width,
            fps=args.fps,
            smoothing=args.smoothing,
            edge_dots=args.edge_dots,
            remove_yellow=not args.no_yellow_filter,
            custom_font=args.font,
        )
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
