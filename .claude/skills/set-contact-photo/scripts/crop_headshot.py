#!/usr/bin/env python3
"""Crop a square headshot out of a photo for use as a contact picture.

Usage:
    crop_headshot.py SOURCE OUT.jpg --box X0 Y0 X1 Y1 [--size 1024]

The box is given either as fractions of the frame (0.0 to 1.0) or as pixels.
The box is squared from its top edge so foreheads are never cut, then resized.
If Pillow is not installed, an equivalent `sips` command (macOS built-in) is
printed so the crop can still be done on the Mac.
"""
import argparse
import sys


def parse_box(vals, w, h):
    x0, y0, x1, y1 = vals
    if all(0.0 <= v <= 1.0 for v in vals):
        x0, x1 = x0 * w, x1 * w
        y0, y1 = y0 * h, y1 * h
    x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    if x1 <= x0 or y1 <= y0:
        sys.exit("box is empty after clamping to the image")
    side = min(x1 - x0, y1 - y0)
    # Square from the top edge, centred horizontally.
    cx = (x0 + x1) // 2
    sx0 = max(0, min(w - side, cx - side // 2))
    return sx0, y0, sx0 + side, y0 + side


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("out")
    ap.add_argument("--box", nargs=4, type=float, required=True, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--quality", type=int, default=92)
    a = ap.parse_args()

    try:
        from PIL import Image
    except ImportError:
        # Without Pillow we can't read the dimensions; fractions need them.
        if all(0.0 <= v <= 1.0 for v in a.box):
            print("Pillow missing and box is fractional. Get the size with:\n"
                  f"  sips -g pixelWidth -g pixelHeight {a.source}\n"
                  "then rerun with a pixel box, or run:")
            print(f"  python3 -m pip install pillow")
            sys.exit(2)
        x0, y0, x1, y1 = (int(v) for v in a.box)
        side = min(x1 - x0, y1 - y0)
        print("Pillow missing. Equivalent macOS command:")
        print(f"  sips --cropOffset {y0} {x0} -c {side} {side} {a.source} --out {a.out} && "
              f"sips -z {a.size} {a.size} -s format jpeg {a.out} --out {a.out}")
        sys.exit(2)

    im = Image.open(a.source)
    im = im.convert("RGB")
    box = parse_box(a.box, im.width, im.height)
    out = im.crop(box).resize((a.size, a.size), Image.LANCZOS)
    out.save(a.out, "JPEG", quality=a.quality)
    print(f"{a.out}: cropped {box} from {im.width}x{im.height} -> {a.size}x{a.size}")


if __name__ == "__main__":
    main()
