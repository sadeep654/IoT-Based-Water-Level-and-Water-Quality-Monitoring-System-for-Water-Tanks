#!/usr/bin/env python3
"""
OG card generator — improved layout to avoid avatar overlap and increase GH icon.
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

def wrap_text_by_width(text, font, max_w, draw):
    """Wrap into lines that fit max_w."""
    words = text.split()
    if not words:
        return []
    lines = []
    cur = words[0]
    for w in words[1:]:
        test = cur + " " + w
        w_px, _ = measure(draw, test, font)
        if w_px <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines

def crop_circle(im):
    w, h = im.size
    size = min(w, h)
    left = (w - size) // 2
    top = (h - size) // 2
    im = im.crop((left, top, left + size, top + size))
    mask = Image.new("L", (size, size), 0)
    drawm = ImageDraw.Draw(mask)
    drawm.ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0,0,0,0))
    out.paste(im, (0,0), mask)
    return out

def draw_stats(draw, x, y, font, color):
    items = [("Contributors", "1"), ("Issues", "0"), ("Stars", "0"), ("Forks", "0")]
    spacing = 64
    for label, count in items:
        text = f"{count} {label}"
        draw.text((x, y), text, font=font, fill=color)
        w, _ = measure(draw, text, font)
        x += w + spacing

def draw_github_fallback(draw, gx, gy, size=64):
    r = size // 6
    rect = [gx, gy, gx + size, gy + size]
    draw.rounded_rectangle(rect, radius=r, fill=(36,41,46))
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

    # avatar sizing / reserved area
    avatar_size = 160         # circle avatar diameter
    avatar_border = 6         # white ring
    avatar_padding = 24       # gap between avatar box and right edge
    avatar_box_width = avatar_size + avatar_border*2 + avatar_padding

    left = 100
    right = W - avatar_box_width - 40   # leave 40px extra margin
    maxw = right - left

    # fonts
    f_owner = load_font(FONT_REGULAR, 28)
    f_repo = load_font(FONT_BOLD, 64)
    f_desc = load_font(FONT_REGULAR, 26)
    f_stats = load_font(FONT_REGULAR, 22)

    # parse title
    raw = args.title or "unknown/repo"
    if "/" in raw:
        owner, repo = raw.split("/",1)
    else:
        owner, repo = "", raw

    # layout start
    y = 120
    if owner:
        owner_text = f"{owner}/"
        draw.text((left, y), owner_text, font=f_owner, fill=SUB)
        _, oh = measure(draw, owner_text, f_owner)
        y += oh + 10

    # Repo title needs to fit into maxw with up to 2 lines.
    # Try with current font; if too wide, attempt reduce size then wrap.
    def render_repo_text(x, y, repo_text):
        # try initial size; if too wide, wrap into two lines or reduce font
        font_size = 64
        for attempt in range(6):  # progressively smaller
            font_try = load_font(FONT_BOLD, font_size)
            w, h = measure(draw, repo_text, font_try)
            if w <= maxw:
                draw.text((x,y), repo_text, font=font_try, fill=TEXT)
                return h, font_try
            # try wrapping into up to 2 lines with this font
            lines = wrap_text_by_width(repo_text, font_try, maxw, draw)
            if len(lines) <= 2:
                # draw lines
                line_y = y
                total_h = 0
                for line in lines:
                    draw.text((x, line_y), line, font=font_try, fill=TEXT)
                    _, lh = measure(draw, line, font_try)
                    line_y += lh + 6
                    total_h += lh + 6
                return total_h, font_try
            font_size -= 6
            if font_size < 28:
                break
        # fallback: hard truncate to fit
        font_try = load_font(FONT_BOLD, 28)
        # chop characters until fits
        text = repo_text
        while True:
            w, h = measure(draw, text + "…", font_try)
            if w <= maxw or len(text) <= 6:
                break
            text = text[:-4]
        draw.text((x,y), text + "…", font=font_try, fill=TEXT)
        return h, font_try

    repo_h, used_repo_font = render_repo_text(left, y, repo)
    y += repo_h + 12

    # description wrap (3 lines max)
    desc_lines = wrap_text_by_width(args.subtitle or "", f_desc, maxw, draw)[:3]
    for line in desc_lines:
        draw.text((left, y), line, font=f_desc, fill=SUB)
        _, lh = measure(draw, line, f_desc)
        y += lh + 6

    # stats
    y += 8
    draw_stats(draw, left, y, f_stats, STATS)

    # bottom-left meta
    meta = ""
    if args.author:
        meta = f"by {args.author}"
    if args.sha:
        meta = meta + (" • " if meta else "") + args.sha[:7]
    draw.text((left, H-64), meta, font=f_stats, fill=SUB)

    # place avatar inside reserved box (top-right region)
    # compute avatar's top-left corner so it's centered in its reserved column
    avatar_x = W - avatar_box_width + avatar_padding//2
    avatar_y = 92   # similar top margin
    if os.path.exists(args.logo):
        try:
            avatar = Image.open(args.logo).convert("RGBA")
            avatar = crop_circle(avatar)
            avatar = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)
            # white border (create a layer)
            bordered = Image.new("RGBA", (avatar_size + avatar_border*2, avatar_size + avatar_border*2), (255,255,255,0))
            mask = Image.new("L", (avatar_size + avatar_border*2, avatar_size + avatar_border*2), 0)
            md = ImageDraw.Draw(mask)
            md.ellipse((0,0, avatar_size + avatar_border*2 -1, avatar_size + avatar_border*2 -1), fill=255)
            # paste white background then avatar
            bg = Image.new("RGBA", bordered.size, (255,255,255,255))
            bg.putalpha(mask)
            bordered.paste(bg, (0,0), bg)
            bordered.paste(avatar, (avatar_border, avatar_border), avatar)
            img.paste(bordered, (avatar_x, avatar_y), bordered)
            print("Placed round avatar at", avatar_x, avatar_y)
        except Exception as e:
            print("Avatar paste error:", e)
    else:
        print("Avatar not found at", args.logo)

    # bottom color bar
    bar_h = 18
    split = int(W * 0.6)
    draw.rectangle([0, H-bar_h, split, H], fill=(232,76,61))
    draw.rectangle([split, H-bar_h, W, H], fill=(44,111,180))

    # github mark (bigger)
    gh_size = 64
    gh_x = W - 24 - gh_size
    gh_y = H - bar_h - gh_size - 8
    gh_placed = False
    if os.path.exists(args.github_mark):
        try:
            gh = Image.open(args.github_mark).convert("RGBA")
            gh.thumbnail((gh_size, gh_size))
            img.paste(gh, (gh_x, gh_y), gh)
            gh_placed = True
            print("Placed github mark at", gh_x, gh_y)
        except Exception as e:
            print("Error placing GH mark:", e)

    if not gh_placed:
        draw_github_fallback(draw, gh_x, gh_y, size=gh_size)
        print("Drew fallback GH icon at", gh_x, gh_y)

    # save
    img.save(args.output, quality=95)
    print("Generated", args.output, "| avatar_box_width:", avatar_box_width, "| gh_size:", gh_size)

if __name__ == "__main__":
    main()
