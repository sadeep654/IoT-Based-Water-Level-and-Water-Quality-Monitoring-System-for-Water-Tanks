#!/usr/bin/env python3
"""
OG card generator — with round avatar + bigger GitHub mark + bottom bar.
Saves: social_preview.png
"""

import os
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageOps

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def measure(draw, text, font):
    try:
        b = draw.textbbox((0,0), text, font=font)
        return b[2]-b[0], b[3]-b[1]
    except Exception:
        try:
            return font.getsize(text)
        except Exception:
            return (len(text)*6, 20)

def wrap_text(text, font, max_w, draw):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = cur + (" " if cur else "") + w
        w_px, _ = measure(draw, test, font)
        if w_px <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_stats(draw, x, y, font, color):
    items = [("Contributors", "1"), ("Issues", "0"), ("Stars", "0"), ("Forks", "0")]
    spacing = 64
    for label, count in items:
        text = f"{count} {label}"
        draw.text((x, y), text, font=font, fill=color)
        w, _ = measure(draw, text, font)
        x += w + spacing

def crop_circle(im):
    """Returns a perfectly circular cropped version of the image."""
    w, h = im.size
    size = min(w, h)
    im = im.crop(((w - size) // 2, (h - size) // 2, (w + size) // 2, (h + size) // 2))  # square
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0,0,size,size), fill=255)
    output = Image.new("RGBA", (size, size), (0,0,0,0))
    output.paste(im, (0,0), mask)
    return output

def draw_github_fallback(draw, gx, gy, size=48):
    """Draw fallback GH icon if github-mark.png missing."""
    r = size // 6
    rect = [gx, gy, gx + size, gy + size]
    draw.rounded_rectangle(rect, radius=r, fill=(36, 41, 46))
    f = load_font(FONT_BOLD, size//2)
    tw, th = measure(draw, "GH", f)
    tx = gx + (size - tw)//2
    ty = gy + (size - th)//2
    draw.text((tx, ty), "GH", font=f, fill=(255,255,255))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="social_preview.png")
    ap.add_argument("--title", default="username/repo")
    ap.add_argument("--subtitle", default="A project description.")
    ap.add_argument("--author", default="")
    ap.add_argument("--sha", default="")
    ap.add_argument("--logo", default="assets/brand-logo.png")
    ap.add_argument("--github-mark", default="assets/github-mark.png")
    args = ap.parse_args()

    W, H = 1280, 640
    BG = (255,255,255)
    TEXT = (28,32,36)
    SUB = (98,108,118)
    STATS = (100,110,124)

    img = Image.new("RGB", (W,H), BG)
    draw = ImageDraw.Draw(img)

    left = 100
    right = W - 260
    maxw = right - left

    raw = args.title or "unknown/repo"
    if "/" in raw:
        owner, repo = raw.split("/", 1)
    else:
        owner, repo = "", raw

    f_owner = load_font(FONT_REGULAR, 28)
    f_repo = load_font(FONT_BOLD, 64)
    f_desc = load_font(FONT_REGULAR, 26)
    f_stats = load_font(FONT_REGULAR, 22)

    # Owner
    y = 120
    if owner:
        draw.text((left, y), f"{owner}/", font=f_owner, fill=SUB)
        _, oh = measure(draw, f"{owner}/", f_owner)
        y += oh + 10

    # Repo (shrink as needed)
    rw, rh = measure(draw, repo, f_repo)
    if rw > maxw:
        for s in range(64, 28, -2):
            f_repo = load_font(FONT_BOLD, s)
            rw, rh = measure(draw, repo, f_repo)
            if rw <= maxw:
                break
    draw.text((left, y), repo, font=f_repo, fill=TEXT)
    y += rh + 18

    # Description
    lines = wrap_text(args.subtitle, f_desc, maxw, draw)[:3]
    for line in lines:
        draw.text((left, y), line, font=f_desc, fill=SUB)
        _, lh = measure(draw, line, f_desc)
        y += lh + 6

    # Stats
    y += 18
    draw_stats(draw, left, y, f_stats, STATS)

    # Meta bottom-left
    meta = ""
    if args.author:
        meta = f"by {args.author}"
    if args.sha:
        meta += f" • {args.sha[:7]}"
    draw.text((left, H-64), meta, font=f_stats, fill=SUB)

    # Round avatar (top-right)
    if os.path.exists(args.logo):
        try:
            avatar = Image.open(args.logo).convert("RGBA")
            avatar = crop_circle(avatar)
            avatar = avatar.resize((180,180), Image.LANCZOS)

            # Optional white border
            border = ImageOps.expand(avatar, border=6, fill="white")

            # Position
            ax = W - 260 + (260 - border.size[0])//2
            ay = 100
            img.paste(border, (ax, ay), border)

        except Exception as e:
            print("Avatar error:", e)

    # Bottom color bar
    bar_h = 18
    draw.rectangle([0, H-bar_h, int(W*0.6), H], fill=(232,76,61))   # red
    draw.rectangle([int(W*0.6), H-bar_h, W, H], fill=(44,111,180)) # blue

    # Bigger GitHub icon
    gh_size = 48
    gx = W - 48 - gh_size
    gy = H - bar_h - gh_size - 12

    if os.path.exists(args.github_mark):
        try:
            gh = Image.open(args.github_mark).convert("RGBA")
            gh.thumbnail((gh_size, gh_size))
            img.paste(gh, (gx, gy), gh)
        except:
            draw_github_fallback(draw, gx, gy, size=gh_size)
    else:
        draw_github_fallback(draw, gx, gy, size=gh_size)

    # Save final image
    img.save(args.output, quality=95)
    print("Generated", args.output)

if __name__ == "__main__":
    main()
