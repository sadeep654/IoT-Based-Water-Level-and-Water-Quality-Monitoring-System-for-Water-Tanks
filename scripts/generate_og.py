#!/usr/bin/env python3
"""
OG card generator — stronger wrapping + reserved avatar space (no overlap).
Saves: social_preview.png
"""

import os, argparse
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
    w,h = im.size
    s = min(w,h)
    left = (w-s)//2; top = (h-s)//2
    im = im.crop((left,top,left+s,top+s))
    mask = Image.new("L", (s,s), 0)
    d = ImageDraw.Draw(mask); d.ellipse((0,0,s,s), fill=255)
    out = Image.new("RGBA", (s,s), (0,0,0,0)); out.paste(im,(0,0),mask)
    return out

def draw_github_fallback(draw, gx, gy, size=64):
    r = max(6, size//6)
    draw.rounded_rectangle([gx,gy,gx+size,gy+size], radius=r, fill=(36,41,46))
    f = load_font(FONT_BOLD, max(12,size//2))
    tw, th = measure(draw, "GH", f)
    draw.text((gx + (size-tw)//2, gy + (size-th)//2), "GH", font=f, fill=(255,255,255))

def draw_stats(draw, x, y, font, color):
    items = [("Contributors","1"),("Issues","0"),("Stars","0"),("Forks","0")]
    spacing = 64
    for label, count in items:
        txt = f"{count} {label}"
        draw.text((x,y), txt, font=font, fill=color)
        w,_ = measure(draw, txt, font); x += w + spacing

def render_repo_title(draw, text, left, maxw):
    """
    Try: wrap into up to 3 lines using large font;
    if >3 lines then reduce font and retry; finally truncate if still too big.
    Returns (lines, used_font_size)
    """
    desired_sizes = [64, 56, 48, 40, 32, 28]
    for fs in desired_sizes:
        f = load_font(FONT_BOLD, fs)
        lines = wrap_text_by_width(text, f, maxw, draw)
        if len(lines) <= 3:
            return lines, fs
    # last resort: truncate with smallest font
    f = load_font(FONT_BOLD, desired_sizes[-1])
    # build truncated text to fit maxw * 3 lines
    words = text.split()
    if not words:
        return [""], desired_sizes[-1]
    out = ""
    for w in words:
        test = (out + " " + w).strip()
        # measure if adding would exceed allowed total width (approx 3 lines)
        lines = wrap_text_by_width(test, f, maxw, draw)
        if len(lines) > 3:
            break
        out = test
    # ensure we end with an ellipsis
    if out != text:
        out = out.rstrip() + "…"
    return wrap_text_by_width(out, f, maxw, draw), desired_sizes[-1]

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

    W,H = 1280,640
    BG = (255,255,255); TEXT=(28,32,36); SUB=(98,108,118); STATS=(100,110,124)

    img = Image.new("RGB",(W,H),BG)
    draw = ImageDraw.Draw(img)

    # Avatar/column sizes (bigger reserved right column to avoid overlap)
    avatar_size = 160
    avatar_border = 6
    avatar_padding = 32
    extra_right_margin = 48
    avatar_box_width = avatar_size + avatar_border*2 + avatar_padding + extra_right_margin

    left = 100
    right = W - avatar_box_width - 24
    maxw = right - left

    # fonts
    f_owner = load_font(FONT_REGULAR, 28)
    f_desc = load_font(FONT_REGULAR, 26)
    f_stats = load_font(FONT_REGULAR, 22)

    # parse title
    raw = args.title or "unknown/repo"
    owner = ""; repo = raw
    if "/" in raw:
        owner, repo = raw.split("/",1)

    y = 120
    if owner:
        otext = f"{owner}/"
        draw.text((left,y), otext, font=f_owner, fill=SUB)
        _, oh = measure(draw, otext, f_owner); y += oh + 10

    # Render repo title with robust wrapping, up to 3 lines
    repo_lines, repo_font_size = render_repo_title(draw, repo, left, maxw)
    f_repo = load_font(FONT_BOLD, repo_font_size)
    line_y = y
    total_h = 0
    for line in repo_lines:
        draw.text((left, line_y), line, font=f_repo, fill=TEXT)
        _, lh = measure(draw, line, f_repo)
        line_y += lh + 6
        total_h += lh + 6
    y += total_h + 6

    # description (max 3 lines)
    desc_lines = wrap_text_by_width(args.subtitle or "", f_desc, maxw, draw)[:3]
    for line in desc_lines:
        draw.text((left,y), line, font=f_desc, fill=SUB)
        _, lh = measure(draw, line, f_desc); y += lh + 6

    # stats
    y += 6
    draw_stats(draw, left, y, f_stats, STATS)

    # bottom-left meta
    meta = ""
    if args.author: meta = f"by {args.author}"
    if args.sha: meta = meta + (" • " if meta else "") + args.sha[:7]
    draw.text((left, H-64), meta, font=f_stats, fill=SUB)

    # Place round avatar inside its reserved box (right side)
    avatar_x = W - avatar_box_width + (avatar_padding//2)
    avatar_y = 88
    if os.path.exists(args.logo):
        try:
            a = Image.open(args.logo).convert("RGBA")
            a = crop_circle(a)
            a = a.resize((avatar_size, avatar_size), Image.LANCZOS)
            # border
            bordered = Image.new("RGBA", (avatar_size+avatar_border*2, avatar_size+avatar_border*2), (255,255,255,0))
            mask = Image.new("L", bordered.size, 0)
            md = ImageDraw.Draw(mask)
            md.ellipse([0,0,bordered.size[0]-1,bordered.size[1]-1], fill=255)
            bg = Image.new("RGBA", bordered.size, (255,255,255,255)); bg.putalpha(mask)
            bordered.paste(bg, (0,0), bg)
            bordered.paste(a, (avatar_border, avatar_border), a)
            img.paste(bordered, (avatar_x, avatar_y), bordered)
            print("Placed round avatar at", avatar_x, avatar_y)
        except Exception as e:
            print("Avatar paste error:", e)
    else:
        print("Avatar not found at", args.logo)

    # bottom bar
    bar_h = 18
    split = int(W*0.6)
    draw.rectangle([0,H-bar_h,split,H], fill=(232,76,61))
    draw.rectangle([split,H-bar_h,W,H], fill=(44,111,180))

    # bigger GH icon
    gh_size = 64
    gh_x = W - 24 - gh_size
    gh_y = H - bar_h - gh_size - 8
    placed_gh = False
    if os.path.exists(args.github_mark):
        try:
            g = Image.open(args.github_mark).convert("RGBA")
            g.thumbnail((gh_size, gh_size))
            img.paste(g, (gh_x, gh_y), g); placed_gh = True
            print("Placed github mark at", gh_x, gh_y)
        except Exception as e:
            print("Error placing GH mark:", e)
    if not placed_gh:
        draw_github_fallback(draw, gh_x, gh_y, size=gh_size); print("Drew fallback GH icon at", gh_x, gh_y)

    # save
    img.save(args.output, quality=95)
    print(f"Generated {args.output} | repo_lines: {len(repo_lines)} | repo_font_size: {repo_font_size} | avatar_box_width: {avatar_box_width} | gh_size: {gh_size}")

if __name__ == "__main__":
    main()
