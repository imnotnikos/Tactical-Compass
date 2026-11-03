#!/usr/bin/env python3
"""Generates assets/icon.png (512x512) and assets/social-preview.png (1280x640) in the imNikos
project style: pixel-art subject with dark outline on a rounded gradient tile, banner with heavy
title, two-line pitch, outlined pills and a by-line."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'assets'))
FONTS = 'C:/Windows/Fonts/'

OLIVE = (92, 104, 54)
OLIVE_HI = (122, 136, 76)
OLIVE_LO = (62, 72, 36)
LED = (255, 52, 38)
OUTLINE = (16, 18, 12, 255)

DIGITS = {'0': ['111', '101', '101', '101', '111'], '2': ['111', '001', '111', '100', '111'],
          '4': ['101', '101', '111', '001', '001'], '5': ['111', '100', '111', '001', '111']}


def digits(img, x, y, s, color):
    for ch in s:
        if ch == ':':
            img.putpixel((x, y + 1), color)
            img.putpixel((x, y + 3), color)
            x += 2
            continue
        for j, row in enumerate(DIGITS[ch]):
            for i, b in enumerate(row):
                if b == '1':
                    img.putpixel((x + i, y + j), color)
        x += 4


def compass_sprite():
    """48x48 pixel-art open tactical compass, olive body with red LEDs."""
    img = Image.new('RGBA', (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def body(x0, y0, x1, y1, r=2):
        d.rounded_rectangle([x0, y0, x1, y1], r, fill=OLIVE + (255,))
        d.line([(x0 + 1, y0), (x1 - 1, y0)], fill=OLIVE_HI + (255,))
        d.line([(x0, y0 + 1), (x0, y1 - 1)], fill=OLIVE_HI + (255,))
        d.rectangle([x1 - 1, y0 + 1, x1, y1 - 1], fill=OLIVE_LO + (255,))
        d.line([(x0 + 1, y1), (x1 - 1, y1)], fill=OLIVE_LO + (255,))

    # heading module popping out of the lid, with lit heading
    d.rectangle([18, 0, 30, 6], fill=(22, 22, 24, 255))
    d.rectangle([19, 1, 29, 5], fill=(8, 8, 9, 255))
    digits(img, 19, 1, '245', LED + (255,))
    # lid with sight window + crosshair
    body(12, 6, 37, 21)
    d.rectangle([20, 9, 29, 16], fill=(26, 28, 20, 255))
    d.rectangle([21, 10, 28, 15], fill=(150, 196, 210, 255))
    d.rectangle([21, 10, 28, 11], fill=(196, 228, 236, 255))
    d.line([(24, 10), (24, 15)], fill=(30, 30, 30, 255))
    d.line([(21, 12), (28, 12)], fill=(30, 30, 30, 255))
    for x, y in ((15, 9), (34, 9), (15, 18), (34, 18)):
        img.putpixel((x, y), (150, 160, 110, 255))
    # rulers on the left edge
    for y0, y1 in ((7, 20), (29, 44)):
        d.rectangle([9, y0, 11, y1], fill=(26, 26, 28, 255))
        for y in range(y0 + 1, y1, 2):
            img.putpixel((11, y), (215, 215, 205, 255))
    # LED time band
    d.rectangle([11, 21, 38, 27], fill=(14, 14, 16, 255))
    d.rectangle([15, 22, 34, 26], fill=(6, 6, 7, 255))
    digits(img, 16, 22, '00:00', LED + (255,))
    # hinge knuckles
    for x0 in (13, 21, 32):
        d.rectangle([x0, 27, x0 + 3, 28], fill=(130, 134, 138, 255))
    # base with dial
    body(12, 28, 37, 45)
    d.rounded_rectangle([15, 30, 34, 43], 2, fill=(30, 31, 34, 255))
    d.ellipse([18, 30, 31, 43], fill=(104, 106, 110, 255))
    d.ellipse([19, 31, 30, 42], fill=(86, 88, 92, 255))
    for a in range(0, 360, 30):
        r = math.radians(a)
        x, y = 24.5 + 5.4 * math.sin(r), 36.5 - 5.4 * math.cos(r)
        img.putpixel((round(x), round(y)), (230, 230, 220, 255))
    img.putpixel((24, 31), LED + (255,))
    d.line([(24, 37), (29, 32)], fill=(225, 40, 30, 255), width=1)
    d.line([(24, 37), (20, 41)], fill=(14, 14, 16, 255), width=1)
    img.putpixel((29, 32), (255, 120, 100, 255))
    img.putpixel((24, 36), (190, 190, 190, 255))
    # thumb loop
    d.rectangle([21, 45, 28, 47], fill=(120, 124, 128, 255))
    d.rectangle([23, 45, 26, 46], fill=(0, 0, 0, 0))

    # 1px dark outline around everything
    px = img.load()
    out = img.copy()
    op = out.load()
    for y in range(48):
        for x in range(48):
            if px[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 48 and 0 <= ny < 48 and px[nx, ny][3] > 0:
                        op[x, y] = OUTLINE
                        break
    return out


def gradient(size, c0, c1):
    w, h = size
    g = Image.new('RGB', size)
    gp = g.load()
    for y in range(h):
        for x in range(w):
            t = min(1.0, max(0.0, (x / w) * 0.45 + (y / h) * 0.55))
            gp[x, y] = tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))
    return g


def tactical_overlay(img, step, alpha, rings_center=None, rings=()):
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    w, h = img.size
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=(255, 255, 255, alpha))
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=(255, 255, 255, alpha))
    if rings_center:
        cx, cy = rings_center
        for r in rings:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, alpha * 2), width=2)
    return Image.alpha_composite(img.convert('RGBA'), ov)


def sprite_with_shadow(sprite, scale):
    big = sprite.resize((sprite.width * scale, sprite.height * scale), Image.NEAREST)
    pad = 40
    canvas = Image.new('RGBA', (big.width + pad * 2, big.height + pad * 2), (0, 0, 0, 0))
    shadow = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 150), (pad + 6, pad + 12), big)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    glow = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    glow.paste(LED + (60,), (pad, pad), big)
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas = Image.alpha_composite(canvas, glow)
    canvas.alpha_composite(big, (pad, pad))
    return canvas, pad


def make_icon(sprite):
    S = 512
    tile = gradient((S, S), (110, 126, 64), (40, 50, 24))
    tile = tactical_overlay(tile, 32, 10, (S // 2, S // 2 + 10), (120, 190, 260))
    rnd = random.Random(4)
    d = ImageDraw.Draw(tile)
    for _ in range(14):
        x, y = rnd.randint(30, S - 30), rnd.randint(30, S - 30)
        s = rnd.choice((4, 6))
        d.rectangle([x, y, x + s, y + s], fill=(255, 255, 255, rnd.randint(40, 90)))
    art, pad = sprite_with_shadow(sprite, 9)
    tile.alpha_composite(art, ((S - art.width) // 2, (S - art.height) // 2 + 2))
    # rounded app-icon mask with a soft inner rim
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], 92, fill=255)
    rim = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(rim).rounded_rectangle([3, 3, S - 4, S - 4], 90, outline=(255, 255, 255, 40), width=4)
    tile = Image.alpha_composite(tile, rim)
    tile.putalpha(mask)
    return tile


def pill(d, x, y, text, font, fg, outline):
    tw = d.textlength(text, font=font)
    w, h = tw + 44, 46
    d.rounded_rectangle([x, y, x + w, y + h], h // 2, outline=outline, width=2, fill=(0, 0, 0, 60))
    d.text((x + 22, y + h / 2), text, font=font, fill=fg, anchor='lm')
    return x + w + 14


def make_preview(icon):
    W, H = 1280, 640
    bg = gradient((W, H), (26, 34, 18), (78, 94, 46))
    bg = tactical_overlay(bg, 40, 9, (300, 330), (240, 330, 420))
    ic = icon.resize((360, 360), Image.LANCZOS)
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 140), (106, 152), ic)
    bg = Image.alpha_composite(bg, shadow.filter(ImageFilter.GaussianBlur(16)))
    bg.alpha_composite(ic, (100, 140))
    d = ImageDraw.Draw(bg)
    title = ImageFont.truetype(FONTS + 'seguibl.ttf', 78)
    body = ImageFont.truetype(FONTS + 'segoeui.ttf', 31)
    pf = ImageFont.truetype(FONTS + 'seguisb.ttf', 22)
    foot = ImageFont.truetype(FONTS + 'segoeui.ttf', 23)
    x = 540
    d.text((x, 228), 'Tactical Compass', font=title, fill=(255, 255, 255), anchor='ls')
    d.text((x, 292), 'A flip-up military compass with LED time & heading.', font=body, fill=(226, 232, 214), anchor='ls')
    d.text((x, 338), 'Link it to comms relays. No GUIs, all on the model.', font=body, fill=(226, 232, 214), anchor='ls')
    pills = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pills)
    px = x
    for t in ('Forge 1.20.1', 'Java 17', 'Multiplayer'):
        px = pill(pd, px, 388, t, pf, (240, 244, 230, 255), (210, 222, 180, 255))
    bg = Image.alpha_composite(bg, pills)
    d = ImageDraw.Draw(bg)
    d.text((x, 562), 'by imNikos \u00b7 github.com/imnotnikos', font=foot, fill=(196, 206, 180), anchor='ls')
    return bg.convert('RGB')


def main():
    os.makedirs(OUT, exist_ok=True)
    sprite = compass_sprite()
    icon = make_icon(sprite)
    icon.save(os.path.join(OUT, 'icon.png'))
    make_preview(icon).save(os.path.join(OUT, 'social-preview.png'))
    # in-game mod list logo (referenced from mods.toml)
    icon.resize((256, 256), Image.LANCZOS).save(os.path.join(HERE, '..', 'src', 'main', 'resources', 'logo.png'))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
