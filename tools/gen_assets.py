#!/usr/bin/env python3
"""Generates every model, texture and data file for the Tactical Compass mod.

Models are built from boxes; every face gets its own hand-painted region in a
per-variant texture atlas, so all variants share UV layouts and only the paint
differs. Run from anywhere: python tools/gen_assets.py
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.normpath(os.path.join(HERE, '..', 'src', 'main', 'resources'))
MOD = 'tacticalcompass'
ASSETS = os.path.join(RES, 'assets', MOD)
DATA = os.path.join(RES, 'data')

VARIANTS = {
    'black': dict(name='Black', body=(40, 42, 47), led=(46, 150, 255), camo=None,
                  dyes=('minecraft:black_dye', 'minecraft:black_dye'), led_dye='minecraft:blue_dye'),
    'olive': dict(name='Olive', body=(84, 93, 52), led=(255, 46, 34), camo=None,
                  dyes=('minecraft:green_dye', 'minecraft:green_dye'), led_dye='minecraft:red_dye'),
    'camo': dict(name='Camo', body=(82, 96, 56), led=(60, 255, 96),
                 camo=[(82, 96, 56), (104, 84, 55), (150, 138, 100), (38, 40, 33)],
                 dyes=('minecraft:green_dye', 'minecraft:brown_dye'), led_dye='minecraft:lime_dye'),
}


# ---------------------------------------------------------------- utilities

def out(path, obj):
    path = os.path.join(RES, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='\n') as f:
        json.dump(obj, f, indent=1)


def save_png(img, path):
    path = os.path.join(ASSETS, 'textures', path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def clamp(v):
    return max(0, min(255, int(round(v))))


def shade(c, f):
    return tuple(clamp(x * f) for x in c[:3]) + tuple(c[3:])


def mix(a, b, t):
    return tuple(clamp(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _hash(ix, iy, iz, seed):
    n = (ix * 374761393 + iy * 668265263 + iz * 1442695041 + seed * 2246822519) & 0xffffffff
    n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
    return ((n ^ (n >> 16)) & 0xffff) / 65535.0


def vnoise(x, y, z, seed):
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - ix, y - iy, z - iz
    sx, sy, sz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)

    def lerp(a, b, t):
        return a + (b - a) * t
    c = [[[_hash(ix + i, iy + j, iz + k, seed) for k in (0, 1)] for j in (0, 1)] for i in (0, 1)]
    x00 = lerp(c[0][0][0], c[1][0][0], sx)
    x10 = lerp(c[0][1][0], c[1][1][0], sx)
    x01 = lerp(c[0][0][1], c[1][0][1], sx)
    x11 = lerp(c[0][1][1], c[1][1][1], sx)
    return lerp(lerp(x00, x10, sy), lerp(x01, x11, sy), sz)


def camo_index(p, scale):
    x, y, z = (p[0] / scale, p[1] / scale, p[2] / scale)
    brown = vnoise(x / 2.4, y / 2.4, z / 2.4, 11) * 0.7 + vnoise(x, y, z, 12) * 0.3
    tan = vnoise(x / 1.7 + 30, y / 1.7, z / 1.7, 13) * 0.7 + vnoise(x * 1.5, y * 1.5, z * 1.5, 14) * 0.3
    black = vnoise(x / 1.9 + 60, y / 1.3, z / 1.9, 15) * 0.75 + vnoise(x * 2, y * 2, z * 2, 16) * 0.25
    if black > 0.64:
        return 3
    if tan > 0.66:
        return 2
    if brown > 0.55:
        return 1
    return 0


# 3x5 pixel font
FONT = {
    '0': ['111', '101', '101', '101', '111'], '1': ['010', '110', '010', '010', '111'],
    '2': ['111', '001', '111', '100', '111'], '3': ['111', '001', '111', '001', '111'],
    '4': ['101', '101', '111', '001', '001'], '5': ['111', '100', '111', '001', '111'],
    '6': ['111', '100', '111', '101', '111'], '7': ['111', '001', '010', '010', '010'],
    '8': ['111', '101', '111', '101', '111'], '9': ['111', '101', '111', '001', '111'],
    'A': ['010', '101', '111', '101', '101'], 'B': ['110', '101', '110', '101', '110'],
    'C': ['011', '100', '100', '100', '011'], 'D': ['110', '101', '101', '101', '110'],
    'E': ['111', '100', '110', '100', '111'], 'F': ['111', '100', '110', '100', '100'],
    'G': ['011', '100', '101', '101', '011'], 'H': ['101', '101', '111', '101', '101'],
    'I': ['111', '010', '010', '010', '111'], 'K': ['101', '110', '100', '110', '101'],
    'L': ['100', '100', '100', '100', '111'], 'M': ['10001', '11011', '10101', '10001', '10001'],
    'N': ['1001', '1101', '1011', '1001', '1001'], 'O': ['010', '101', '101', '101', '010'],
    'P': ['110', '101', '110', '100', '100'], 'R': ['110', '101', '110', '101', '101'],
    'S': ['011', '100', '010', '001', '110'], 'T': ['111', '010', '010', '010', '010'],
    'U': ['101', '101', '101', '101', '111'], 'V': ['101', '101', '101', '101', '010'],
    'W': ['10001', '10001', '10101', '11011', '10001'], 'X': ['101', '101', '010', '101', '101'],
    'Y': ['101', '101', '010', '010', '010'], 'Z': ['111', '001', '010', '100', '111'], '-': ['000', '000', '111', '000', '000'],
    ':': ['0', '1', '0', '1', '0'], '.': ['0', '0', '0', '0', '1'], ' ': ['00', '00', '00', '00', '00'],
    '/': ['001', '001', '010', '100', '100'],
}


def text_size(s, sc=1):
    w = sum(len(FONT[ch][0]) + 1 for ch in s) - 1
    return w * sc, 5 * sc


def draw_text(img, x, y, s, color, sc=1, center=False):
    if center:
        w, h = text_size(s, sc)
        x, y = x - w // 2, y - h // 2
    d = ImageDraw.Draw(img)
    cx = x
    for ch in s:
        g = FONT[ch]
        for j, row in enumerate(g):
            for i, bit in enumerate(row):
                if bit == '1':
                    d.rectangle([cx + i * sc, y + j * sc, cx + i * sc + sc - 1, y + j * sc + sc - 1], fill=color)
        cx += (len(g[0]) + 1) * sc


# ------------------------------------------------------------- box modeling

FACES = ['down', 'up', 'north', 'south', 'west', 'east']


class Box:
    def __init__(self, frm, to, mat='body', faces=None, skip=(), fm=None, ext=None, rot=None,
                 emissive=False, decals=None):
        self.frm, self.to = frm, to
        self.mat = mat
        self.faces = [f for f in (faces or FACES) if f not in skip]
        self.fm = fm or {}
        self.ext = ext or {}          # face -> (texture key, uv)
        self.rot = rot
        self.emissive = emissive
        self.decals = decals or []    # functions(face) applied on every face of this box


class Face:
    """One textured face: a pixel region plus the model-space mapping for it."""

    def __init__(self, box, name, D):
        self.box, self.name, self.D = box, name, D
        f, t = box.frm, box.to
        ext = {'up': (t[0] - f[0], t[2] - f[2]), 'down': (t[0] - f[0], t[2] - f[2]),
               'north': (t[0] - f[0], t[1] - f[1]), 'south': (t[0] - f[0], t[1] - f[1]),
               'west': (t[2] - f[2], t[1] - f[1]), 'east': (t[2] - f[2], t[1] - f[1])}[name]
        self.w = max(1, int(round(ext[0] * D)))
        self.h = max(1, int(round(ext[1] * D)))
        self.sx = self.w / max(ext[0], 1e-6)
        self.sy = self.h / max(ext[1], 1e-6)
        self.mat = box.fm.get(name, box.mat)
        self.x = self.y = 0
        self.img = None

    def pos(self, i, j):
        """Model-space point at the centre of texel (i, j)."""
        f, t = self.box.frm, self.box.to
        u, v = (i + 0.5) / self.sx, (j + 0.5) / self.sy
        n = self.name
        if n == 'up':
            return (f[0] + u, t[1], f[2] + v)
        if n == 'down':
            return (f[0] + u, f[1], t[2] - v)
        if n == 'north':
            return (t[0] - u, t[1] - v, f[2])
        if n == 'south':
            return (f[0] + u, t[1] - v, t[2])
        if n == 'west':
            return (f[0], t[1] - v, f[2] + u)
        return (t[0], t[1] - v, t[2] - u)

    def px(self, x, y, z):
        """Model-space point -> pixel coordinate inside this face's region."""
        f, t = self.box.frm, self.box.to
        n = self.name
        if n == 'up':
            a, b = x - f[0], z - f[2]
        elif n == 'down':
            a, b = x - f[0], t[2] - z
        elif n == 'north':
            a, b = t[0] - x, t[1] - y
        elif n == 'south':
            a, b = x - f[0], t[1] - y
        elif n == 'west':
            a, b = z - f[2], t[1] - y
        else:
            a, b = t[2] - z, t[1] - y
        return a * self.sx, b * self.sy

    def plane_rect(self, p0, p1, color, outline=None):
        """Fill the rectangle spanned by two model-space points lying on this face's plane."""
        a = self.px(*p0)
        b = self.px(*p1)
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        d = ImageDraw.Draw(self.img)
        d.rectangle([round(x0), round(y0), round(x1) - 1, round(y1) - 1], fill=color, outline=outline)

    def dot(self, p, r_px, color, hi=None):
        x, y = self.px(*p)
        d = ImageDraw.Draw(self.img)
        d.ellipse([x - r_px, y - r_px, x + r_px - 1, y + r_px - 1], fill=color)
        if hi:
            d.point((round(x - r_px / 2), round(y - r_px / 2)), fill=hi)


class Model:
    def __init__(self, boxes):
        self.boxes = boxes


def pack(models, D, width):
    faces = []
    seen = set()
    for m in models:
        for b in m.boxes:
            if id(b) in seen:
                continue
            seen.add(id(b))
            b.face_objs = {}
            for n in b.faces:
                if n in b.ext:
                    continue
                fo = Face(b, n, D)
                b.face_objs[n] = fo
                faces.append(fo)
    order = sorted(faces, key=lambda f: (-f.h, -f.w))
    x = y = shelf = 0
    for f in order:
        if x + f.w + 2 > width:
            x, y, shelf = 0, y + shelf, 0
        f.x, f.y = x + 1, y + 1
        x += f.w + 2
        shelf = max(shelf, f.h + 2)
    height = 1
    while height < y + shelf:
        height *= 2
    return faces, (width, height)


# ---------------------------------------------------------------- materials

def material(mat, pal, p, rnd, camo_scale):
    j = rnd.randint(-4, 4)
    if mat == 'body':
        base = pal['camo'][camo_index(p, camo_scale)] if pal['camo'] else pal['body']
        return tuple(clamp(c + j) for c in base) + (255,)
    if mat == 'body_dark':
        base = pal['camo'][camo_index(p, camo_scale)] if pal['camo'] else pal['body']
        return tuple(clamp(c * 0.72 + j) for c in base) + (255,)
    table = {
        'dark': (30, 31, 34), 'rubber': (22, 22, 24), 'metal': (92, 95, 100), 'steel': (150, 154, 160),
        'alu': (168, 172, 176), 'well': (24, 25, 28), 'band': (13, 13, 15), 'panel': (46, 48, 52),
        'white': (222, 222, 212), 'foam': (64, 64, 66), 'brass': (170, 140, 70),
    }
    if mat in table:
        jj = j if mat not in ('band', 'well') else j // 2
        if mat in ('metal', 'steel', 'alu'):  # brushed: streaks along u
            jj = j + int(6 * (_hash(int(p[1] * 37), int(p[0] * 3 + p[2] * 3), 0, 9) - 0.5))
        if mat == 'foam':
            jj = rnd.randint(-10, 10)
        return tuple(clamp(c + jj) for c in table[mat]) + (255,)
    if mat == 'clear':
        return (0, 0, 0, 0)
    raise ValueError(mat)


def paint(models, faces, size, pal, camo_scale, seed):
    atlas = Image.new('RGBA', size, (0, 0, 0, 0))
    for fo in faces:
        rnd = random.Random(seed + fo.x * 7919 + fo.y)
        img = Image.new('RGBA', (fo.w, fo.h))
        px = img.load()
        for j in range(fo.h):
            for i in range(fo.w):
                px[i, j] = material(fo.mat, pal, fo.pos(i, j), rnd, camo_scale)
        fo.img = img
        if fo.mat != 'clear':
            # bevel: light top/left edge, dark bottom/right edge
            if fo.h >= 4:
                for i in range(fo.w):
                    px[i, 0] = shade(px[i, 0], 1.18)
                    px[i, fo.h - 1] = shade(px[i, fo.h - 1], 0.74)
            if fo.w >= 4:
                for j in range(fo.h):
                    px[0, j] = shade(px[0, j], 1.1)
                    px[fo.w - 1, j] = shade(px[fo.w - 1, j], 0.8)
        for decal in fo.box.decals:
            decal(fo, pal)
        atlas.paste(fo.img, (fo.x, fo.y))
        # bleed edges into the 1px gutter so mipmaps/filtering never show seams
        for i in range(fo.w):
            atlas.putpixel((fo.x + i, fo.y - 1), fo.img.getpixel((i, 0)))
            atlas.putpixel((fo.x + i, fo.y + fo.h), fo.img.getpixel((i, fo.h - 1)))
        for j in range(-1, fo.h + 1):
            jj = min(max(j, 0), fo.h - 1)
            atlas.putpixel((fo.x - 1, fo.y + j), fo.img.getpixel((0, jj)))
            atlas.putpixel((fo.x + fo.w, fo.y + j), fo.img.getpixel((fo.w - 1, jj)))
    return atlas


def r4(v):
    return round(v, 4)


def model_json(model, size, textures, extra=None):
    W, H = size
    elements = []
    for b in model.boxes:
        el = {'from': [r4(v) for v in b.frm], 'to': [r4(v) for v in b.to], 'faces': {}}
        if b.rot:
            el['rotation'] = b.rot
        for n in b.faces:
            if n in b.ext:
                key, uv = b.ext[n]
                el['faces'][n] = {'uv': uv, 'texture': key}
            else:
                fo = b.face_objs[n]
                el['faces'][n] = {'uv': [r4(fo.x * 16 / W), r4(fo.y * 16 / H),
                                         r4((fo.x + fo.w) * 16 / W), r4((fo.y + fo.h) * 16 / H)],
                                  'texture': '#0'}
        if b.emissive:
            el['shade'] = False
            el['forge_data'] = {'block_light': 15, 'sky_light': 15, 'ambient_occlusion': False}
        elements.append(el)
    j = {'textures': textures, 'elements': elements}
    if extra:
        j = {**extra, **j}
    return j


# ================================================================ COMPASS

CD = 16  # texels per model unit on the compass


def d_seam(fo, pal):
    """Two-piece shell seam + corner rivets on the base sides."""
    if fo.name in ('north', 'south', 'west', 'east'):
        c = shade(fo.img.getpixel((fo.w // 2, fo.h // 2)), 0.6)
        y = round(fo.h * 0.5)
        ImageDraw.Draw(fo.img).line([(1, y), (fo.w - 2, y)], fill=c)
        ImageDraw.Draw(fo.img).line([(1, y + 1), (fo.w - 2, y + 1)], fill=shade(c, 1.6))


def d_base_top(fo, pal):
    if fo.name != 'up':
        return
    # dial well inside the bezel
    fo.plane_rect((4.25, 2, 4.75), (11.75, 2, 12.25), (22, 23, 26, 255))
    for (x, z) in ((4.85, 5.35), (11.15, 5.35), (4.85, 11.65), (11.15, 11.65)):
        fo.dot((x, 2, z), 3, (90, 92, 96, 255), (160, 160, 160, 255))
        cx, cy = fo.px(x, 2, z)
        ImageDraw.Draw(fo.img).line([(cx - 2, cy), (cx + 1, cy)], fill=(40, 40, 42, 255))
    # hinge-side shelf print: a little north arrow and model number
    x, y = fo.px(8, 2, 3.2)
    draw_text(fo.img, round(x), round(y), 'TC-7', (200, 200, 190, 255), 2, center=True)


def d_bottom(fo, pal):
    if fo.name != 'down':
        return
    d = ImageDraw.Draw(fo.img)
    base = fo.img.getpixel((fo.w // 2, fo.h // 2))
    for k in range(6, fo.h - 6, 6):
        d.line([(10, k), (fo.w - 11, k)], fill=shade(base, 0.7))
        d.line([(10, k + 1), (fo.w - 11, k + 1)], fill=shade(base, 1.25))
    x, y = fo.px(8, 0, 8)
    d.rectangle([x - 34, y - 10, x + 33, y + 9], fill=shade(base, 0.85))
    draw_text(fo.img, round(x), round(y), 'LENSATIC', (190, 190, 180, 255), 2, center=True)


def d_bezel(fo, pal):
    if fo.name != 'up':
        return
    white = (225, 225, 215, 255)
    # lubber index on the far bar
    if fo.box.frm[2] < 4.5:
        x, y = fo.px(8, 2.6, 4.75)
        ImageDraw.Draw(fo.img).polygon([(x - 6, y - 10), (x + 5, y - 10), (x, y - 1)], fill=white)
        for dx in (-2.5, 2.5):
            x2, _ = fo.px(8 + dx, 2.6, 4.4)
            ImageDraw.Draw(fo.img).line([(x2, 2), (x2, fo.h - 3)], fill=(150, 150, 140, 255))
    elif fo.box.frm[2] > 12:
        x, y = fo.px(9.9, 2.6, 12.9)
        draw_text(fo.img, round(x), round(y), 'LINK', white, 2, center=True)
        fo.plane_rect((10.95, 2.6, 12.5), (11.95, 2.6, 13.25), (12, 12, 14, 255), outline=(70, 70, 74, 255))
        x, y = fo.px(5.6, 2.6, 12.9)
        draw_text(fo.img, round(x), round(y), 'MAG N', (170, 170, 160, 255), 2, center=True)


def d_ruler(fo, pal):
    if fo.name not in ('west', 'up'):
        return
    d = ImageDraw.Draw(fo.img)
    tick = (215, 215, 205, 255)
    if fo.name == 'west':
        n = 0
        for i in range(4, fo.w - 3, 4):
            ln = fo.h * (0.55 if n % 5 == 0 else 0.3)
            d.line([(i, 2), (i, 2 + ln)], fill=tick)
            n += 1
    else:
        for i in range(4, fo.h - 3, 8):
            d.point((fo.w // 2, i), fill=tick)


def d_lid_outer(fo, pal):
    if fo.name != 'up':
        return
    base = fo.img.getpixel((fo.w // 2, fo.h // 2))
    dk, lt = shade(base, 0.66), shade(base, 1.3)
    # embossed border panel
    for (p0, p1) in (((3.7, 3.85, 4.6), (12.3, 3.85, 4.7)), ((3.7, 3.85, 13.3), (12.3, 3.85, 13.4)),
                     ((3.7, 3.85, 4.6), (3.8, 3.85, 13.4)), ((12.2, 3.85, 4.6), (12.3, 3.85, 13.4))):
        fo.plane_rect(p0, p1, dk)
    for (x, z) in ((4.3, 5.2), (11.7, 5.2), (4.3, 12.8), (11.7, 12.8)):
        fo.dot((x, 3.85, z), 3, shade(base, 0.8), lt)
    # stamped emblem: compass rose
    cx, cy = fo.px(8, 3.85, 6.6)
    d = ImageDraw.Draw(fo.img)
    d.ellipse([cx - 18, cy - 18, cx + 17, cy + 17], outline=dk, width=2)
    d.polygon([(cx, cy - 24), (cx + 5, cy), (cx, cy + 24), (cx - 5, cy)], fill=dk)
    d.polygon([(cx - 24, cy), (cx, cy - 5), (cx + 24, cy), (cx, cy + 5)], fill=dk)
    d.polygon([(cx, cy - 24), (cx + 5, cy), (cx - 5, cy)], fill=lt)
    x, y = fo.px(8, 3.85, 9.2)
    draw_text(fo.img, round(x), round(y), 'TACTICAL', dk, 2, center=True)


def d_lid_inner(fo, pal):
    if fo.name != 'down':
        return
    base = fo.img.getpixel((fo.w // 2, fo.h // 2))
    dk = shade(base, 0.7)
    # luminous sighting dots either side of the window
    for x in (5.2, 10.8):
        fo.dot((x, 2.6, 10.25), 3, (210, 230, 200, 255))
    # recessed LED time display (digits are drawn live by the renderer)
    fo.plane_rect((4.3, 2.6, 4.25), (11.7, 2.6, 6.75), (36, 38, 42, 255))
    fo.plane_rect((4.45, 2.6, 4.4), (11.55, 2.6, 6.6), (5, 6, 7, 255))
    x, y = fo.px(8, 2.6, 7.3)
    draw_text(fo.img, round(x), round(y), 'TIME', dk, 2, center=True)


def d_band(fo, pal):
    if fo.name != 'down':
        return
    for x in (4.0, 12.0):
        fo.dot((x, 2, 3.0), 3, (70, 72, 76, 255), (140, 140, 140, 255))


def d_popup(fo, pal):
    if fo.name == 'down':
        fo.plane_rect((6.4, 2.75, 12.6), (9.6, 2.75, 13.5), (6, 7, 8, 255), outline=(38, 38, 42, 255))


def d_glass(fo, pal):
    d = ImageDraw.Draw(fo.img)
    wire = (24, 24, 24, 255)
    x, _ = fo.px(8, 0, 0)
    _, y = fo.px(0, 0, 10.25) if fo.name in ('up', 'down') else (0, 0)
    d.line([(round(x) - 1, 0), (round(x) - 1, fo.h)], fill=wire, width=2)
    d.line([(0, round(y) - 1), (fo.w, round(y) - 1)], fill=wire, width=2)
    # faint edge of the lens
    d.rectangle([0, 0, fo.w - 1, fo.h - 1], outline=(200, 210, 220, 70))


def d_needle(fo, pal):
    img = Image.new('RGBA', (fo.w * 4, fo.h * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def P(x, z):
        a, b = fo.px(x, 0, z)
        return a * 4, b * 4
    tipN, tipS, l, r = P(8, 5.3), P(8, 11.7), P(7.55, 8.5), P(8.45, 8.5)
    d.polygon([tipS, l, tipN, r], fill=(235, 235, 228, 255))  # white outline
    shrink = lambda p, c, k: (c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k)
    c = P(8, 8.5)
    d.polygon([shrink(tipN, c, 0.95), shrink(l, c, 0.75), shrink(r, c, 0.75)], fill=(214, 36, 28, 255))
    d.polygon([shrink(tipS, c, 0.95), shrink(l, c, 0.75), shrink(r, c, 0.75)], fill=(18, 18, 20, 255))
    d.line([shrink(tipN, c, 0.9), c], fill=(255, 110, 90, 255), width=2)
    fo.img = img.resize((fo.w, fo.h), Image.LANCZOS)
    a = fo.img.getchannel('A').point(lambda v: 255 if v > 110 else 0)
    fo.img.putalpha(a)


def compass_models():
    M = []
    base = [
        Box((3, 0, 2.5), (13, 2, 13.5), decals=[d_seam, d_base_top, d_bottom]),
        Box((3.5, 0, 2), (12.5, 2, 2.5), skip=('south',), decals=[d_seam]),
        Box((3.5, 0, 13.5), (12.5, 2, 14), skip=('north',), decals=[d_seam]),
        # bezel
        Box((3.5, 2, 4), (12.5, 2.6, 4.75), fm={'south': 'dark'}, decals=[d_bezel]),
        Box((3.5, 2, 12.25), (12.5, 2.6, 13.5), fm={'north': 'dark'}, decals=[d_bezel]),
        Box((3.5, 2, 4.75), (4.25, 2.6, 12.25), skip=('north', 'south'), fm={'east': 'dark'}),
        Box((11.75, 2, 4.75), (12.5, 2.6, 12.25), skip=('north', 'south'), fm={'west': 'dark'}),
        # hinge knuckles
        Box((3.1, 1.3, 1.3), (4.5, 2.7, 2.7), 'metal'),
        Box((3.1, 1.3, 1.3), (4.5, 2.7, 2.7), 'metal', rot={'origin': [8, 2, 2], 'axis': 'x', 'angle': 45}),
        Box((11.5, 1.3, 1.3), (12.9, 2.7, 2.7), 'metal'),
        Box((11.5, 1.3, 1.3), (12.9, 2.7, 2.7), 'metal', rot={'origin': [8, 2, 2], 'axis': 'x', 'angle': 45}),
        # thumb loop
        Box((6, 0.6, 14), (6.8, 1.4, 15.6), 'metal', skip=('north',)),
        Box((9.2, 0.6, 14), (10, 1.4, 15.6), 'metal', skip=('north',)),
        Box((6.8, 0.6, 14.8), (9.2, 1.4, 15.6), 'metal', skip=('west', 'east')),
        # side ruler
        Box((2.4, 0.2, 2.5), (3, 1.8, 13.5), 'rubber', skip=('east',), decals=[d_ruler]),
        # pivot cap
        Box((7.7, 2, 8.2), (8.3, 2.4, 8.8), 'steel', skip=('down',)),
    ]
    lid_b = [d_lid_outer, d_lid_inner]
    lid = [
        Box((3, 2, 2), (13, 3.85, 4), 'band', decals=[d_band]),
        Box((3, 2.6, 4), (13, 3.85, 8.5), skip=('north',), decals=lid_b),
        Box((3, 2.6, 8.5), (6.5, 3.85, 12), skip=('north', 'south'), fm={'east': 'dark'}, decals=lid_b),
        Box((9.5, 2.6, 8.5), (13, 3.85, 12), skip=('north', 'south'), fm={'west': 'dark'}, decals=lid_b),
        Box((6, 2.6, 12), (10, 3.85, 12.5), skip=('west', 'east'), fm={'north': 'dark', 'south': 'dark'}, decals=lid_b),
        Box((3, 2.6, 12), (6, 3.85, 13.5), skip=('north',), fm={'east': 'dark'}, decals=lid_b),
        Box((3.5, 2.6, 13.5), (6, 3.85, 14), skip=('north',), fm={'east': 'dark'}, decals=lid_b),
        Box((10, 2.6, 12), (13, 3.85, 13.5), skip=('north',), fm={'west': 'dark'}, decals=lid_b),
        Box((10, 2.6, 13.5), (12.5, 3.85, 14), skip=('north',), fm={'west': 'dark'}, decals=lid_b),
        Box((6.5, 3.2, 8.5), (9.5, 3.25, 12), 'clear', faces=['up', 'down'], decals=[d_glass]),
        Box((4.6, 1.3, 1.3), (11.4, 2.7, 2.7), 'metal'),
        Box((4.6, 1.3, 1.3), (11.4, 2.7, 2.7), 'metal', rot={'origin': [8, 2, 2], 'axis': 'x', 'angle': 45}),
        Box((2.4, 2.7, 4.3), (3, 3.75, 13.3), 'rubber', skip=('east',), decals=[d_ruler]),
    ]
    popup = [
        Box((6, 2.75, 12.5), (10, 3.6, 13.6), 'band', decals=[d_popup]),
        Box((6, 2.75, 13.6), (7.8, 3.6, 14), 'band', skip=('north',)),
        Box((8.2, 2.75, 13.6), (10, 3.6, 14), 'band', skip=('north',)),
        Box((6.1, 2.85, 10.9), (6.45, 3.5, 12.5), 'steel', skip=('south',)),
        Box((9.55, 2.85, 10.9), (9.9, 3.5, 12.5), 'steel', skip=('south',)),
    ]
    needle = [Box((7.55, 2.16, 5.3), (8.45, 2.22, 11.7), 'clear', faces=['up', 'down'], decals=[d_needle])]
    card = [Box((4.4, 2.02, 4.9), (11.6, 2.08, 12.1), faces=['up'], ext={'up': ('#card', [0, 0, 16, 16])})]
    return {'base': Model(base), 'lid': Model(lid), 'popup': Model(popup), 'needle': Model(needle), 'card': Model(card)}


def compass_card(pal):
    S = 1024
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2
    d.ellipse([4, 4, S - 5, S - 5], fill=(70, 72, 76, 255))
    d.ellipse([150, 150, S - 151, S - 151], fill=(78, 80, 84, 255))
    d.ellipse([4, 4, S - 5, S - 5], outline=(30, 30, 32, 255), width=10)
    white = (236, 236, 226, 255)
    for deg in range(0, 360, 5):
        a = math.radians(deg)
        ln, wd = (78, 10) if deg % 30 == 0 else (54, 7) if deg % 10 == 0 else (32, 5)
        r0 = 500
        d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)),
                (c + (r0 - ln) * math.sin(a), c - (r0 - ln) * math.cos(a))], fill=white, width=wd)

    def stamp(s, deg, r, sc, col):
        w, h = text_size(s, sc)
        t = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0))
        draw_text(t, 4, 4, s, col, sc)
        t = t.rotate(-deg, resample=Image.BICUBIC, expand=True)
        a = math.radians(deg)
        x, y = c + r * math.sin(a), c - r * math.cos(a)
        img.alpha_composite(t, (int(x - t.width / 2), int(y - t.height / 2)))

    led = pal['led'] + (255,)
    for deg in range(0, 360, 30):
        if deg % 90:
            stamp(str(deg), deg, 360, 9, white)
    for deg, ch in ((0, 'N'), (90, 'E'), (180, 'S'), (270, 'W')):
        stamp(ch, deg, 350, 15, led if ch == 'N' else white)
    # luminous north marker
    d.polygon([(c, 18), (c - 34, 96), (c + 34, 96)], fill=led)
    # inner crosshair & range ring
    grey = (120, 122, 126, 255)
    d.ellipse([c - 160, c - 160, c + 160, c + 160], outline=grey, width=5)
    d.line([(c, c - 230), (c, c + 230)], fill=grey, width=4)
    d.line([(c - 230, c), (c + 230, c)], fill=grey, width=4)
    img = img.resize((256, 256), Image.LANCZOS)
    a = img.getchannel('A').point(lambda v: 255 if v > 100 else 0)
    img.putalpha(a)
    return img


def compass_icon(pal):
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body, led = pal['body'], pal['led']
    out_c = shade(body, 0.45)
    if pal['camo']:
        body = pal['camo'][0]
    # lid
    d.rounded_rectangle([5, 0, 27, 13], 3, fill=body + (255,), outline=out_c + (255,))
    d.rectangle([15, 0, 16, 6], fill=(0, 0, 0, 0))
    d.line([(15, 0), (15, 6)], fill=out_c + (255,))
    d.line([(16, 0), (16, 6)], fill=(230, 230, 230, 255))
    d.rectangle([13, 6, 18, 10], outline=out_c + (255,), fill=(0, 0, 0, 0))
    d.line([(15, 7), (15, 9)], fill=(230, 230, 230, 255))
    d.line([(14, 8), (17, 8)], fill=(230, 230, 230, 255))
    # band with LED time
    d.rectangle([4, 13, 28, 19], fill=(12, 12, 14, 255), outline=(0, 0, 0, 255))
    draw_text(img, 8, 14, '00', led + (255,), 1)
    d.point((15, 15), fill=led + (255,))
    d.point((15, 17), fill=led + (255,))
    draw_text(img, 17, 14, '00', led + (255,), 1)
    # base
    d.rounded_rectangle([5, 19, 27, 30], 3, fill=body + (255,), outline=out_c + (255,))
    d.rounded_rectangle([8, 20, 24, 29], 2, fill=(74, 76, 80, 255), outline=(30, 30, 32, 255))
    d.line([(11, 27), (16, 24)], fill=(20, 20, 22, 255), width=1)
    d.line([(16, 24), (21, 21)], fill=(220, 40, 30, 255), width=1)
    d.point((21, 21), fill=(255, 90, 70, 255))
    d.rectangle([14, 30, 18, 31], fill=(110, 112, 116, 255), outline=(40, 40, 42, 255))
    # rulers
    for y0, y1 in ((1, 12), (20, 29)):
        d.rectangle([2, y0, 4, y1], fill=(24, 24, 26, 255))
        for y in range(y0 + 1, y1, 2):
            d.point((4, y), fill=(200, 200, 190, 255))
    if pal['camo']:
        px = img.load()
        for y in range(32):
            for x in range(32):
                if px[x, y][:3] == body:
                    px[x, y] = pal['camo'][camo_index((x * 0.5, y * 0.5, 3), 1.0)] + (255,)
    return img


# ================================================================ RELAY

RD = 8


def d_case_sides(fo, pal):
    if fo.name in ('north', 'south', 'west', 'east') and fo.h > 12:
        base = fo.img.getpixel((fo.w // 2, fo.h // 2))
        d = ImageDraw.Draw(fo.img)
        for k in range(6, fo.w - 6, 10):
            d.rectangle([k, 4, k + 3, fo.h - 5], fill=shade(base, 0.82))
            d.line([(k, 4), (k, fo.h - 5)], fill=shade(base, 1.2))
        d.line([(0, 2), (fo.w, 2)], fill=shade(base, 0.6))


def d_case_front(fo, pal):
    if fo.name != 'north':
        return
    d_case_sides(fo, pal)
    x, y = fo.px(8, 3.4, 0)
    d = ImageDraw.Draw(fo.img)
    d.rectangle([x - 18, y - 4, x + 17, y + 4], fill=(205, 205, 195, 255), outline=(30, 30, 30, 255))
    draw_text(fo.img, round(x), round(y), 'RLY-9', (30, 30, 30, 255), 1, center=True)


def d_panel(fo, pal):
    if fo.name != 'up':
        return
    d = ImageDraw.Draw(fo.img)
    white = (210, 210, 200, 255)
    for (x, z, s) in ((8.6, 8.6, 'PWR'), (9.6, 8.6, 'TX'), (10.6, 8.6, 'RX'), (12.0, 8.6, 'ANT')):
        px, py = fo.px(x, 0, z)
        draw_text(fo.img, round(px), round(py), s, white, 1, center=True)
    for z in (11.6, 12.3):
        a = fo.px(8.2, 0, z)
        b = fo.px(13.4, 0, z)
        d.line([a, b], fill=(70, 72, 78, 255))
    for (x, z) in ((2.5, 8.5), (13.5, 8.5), (2.5, 12.5), (13.5, 12.5)):
        fo.dot((x, 0, z), 2, (110, 110, 116, 255))


def d_keys(fo, pal):
    if fo.name != 'up':
        return
    d = ImageDraw.Draw(fo.img)
    rows = 5
    x0, x1 = 2, fo.w - 2
    y0, y1 = 2, fo.h - 2
    kh = (y1 - y0) / rows
    for r in range(rows):
        n = 13 if r < 4 else 7
        kw = (x1 - x0) / n
        for k in range(n):
            if r == 4 and k == 3:
                continue
            ax, ay = x0 + k * kw, y0 + r * kh
            bx, by = ax + kw - 1, ay + kh - 1
            if r == 4 and k == 2:
                bx += kw
            d.rectangle([ax, ay, bx, by], fill=(44, 45, 48, 255))
            d.line([(ax, ay), (bx, ay)], fill=(70, 72, 76, 255))
            d.point((round(ax + 1), round(ay + 1)), fill=(150, 150, 150, 255))


def d_radio(fo, pal):
    d = ImageDraw.Draw(fo.img)
    if fo.name == 'north':
        x, y = fo.px(4.4, 4.15, 0)
        draw_text(fo.img, round(x), round(y), 'PRC-7', (30, 30, 34, 255), 1, center=True)
        for xx in (3.2, 4.0, 4.8, 5.6):
            fo.dot((xx, 3.98, 0), 2, (40, 40, 44, 255))
        fo.plane_rect((2.8, 5.4, 0), (7.4, 5.5, 0), (120, 124, 128, 255))
    elif fo.name == 'up':
        for k in range(3, fo.w - 3, 4):
            d.line([(k, 3), (k, fo.h - 4)], fill=(130, 134, 140, 255))


def d_lid_back(fo, pal):
    if fo.name == 'south':
        base = fo.img.getpixel((fo.w // 2, fo.h // 2))
        d = ImageDraw.Draw(fo.img)
        dk, lt = shade(base, 0.75), shade(base, 1.2)
        d.rectangle([10, 10, fo.w - 11, fo.h - 11], outline=dk, width=3)
        d.rectangle([13, 13, fo.w - 14, fo.h - 14], outline=lt, width=1)
        for k in range(24, fo.w - 24, 12):
            d.line([(k, 20), (k, fo.h - 21)], fill=dk, width=3)
    elif fo.name == 'up':
        # closed-lid top view uses the same decal path through 'up'
        d_lid_back_top(fo)


def d_lid_back_top(fo):
    base = fo.img.getpixel((fo.w // 2, fo.h // 2))
    d = ImageDraw.Draw(fo.img)
    dk, lt = shade(base, 0.75), shade(base, 1.2)
    if fo.w > 40 and fo.h > 40:
        d.rectangle([10, 10, fo.w - 11, fo.h - 11], outline=dk, width=3)
        d.rectangle([13, 13, fo.w - 14, fo.h - 14], outline=lt, width=1)
        for k in range(24, fo.w - 24, 12):
            d.line([(k, 20), (k, fo.h - 21)], fill=dk, width=3)


def d_bezel_buttons(fo, pal):
    if fo.name != 'north':
        return
    d = ImageDraw.Draw(fo.img)
    if fo.w < fo.h:  # side bars: buttons
        for k in range(6, fo.h - 4, 9):
            d.rectangle([2, k, fo.w - 3, k + 5], fill=(52, 52, 56, 255), outline=(14, 14, 14, 255))
    elif fo.box.frm[1] < 7:  # bottom bar: maker label
        x, y = fo.w // 2, fo.h // 2
        draw_text(fo.img, x, y, 'TACNET', (110, 110, 110, 255), 1, center=True)


def relay_models():
    """Relay parts, in the 'open' pose. The lid hinges on (y=4.5, z=14) and the antenna on
    (y=6.2, z=11.3); both are animated by the block entity renderer."""
    base = [
        Box((1, 0, 2.5), (15, 3.5, 14), fm={'up': 'panel'}, decals=[d_case_front, d_case_sides]),
        Box((1, 3.5, 2.5), (15, 4.5, 3.3), skip=('down',), fm={'south': 'body_dark'}),
        Box((1, 3.5, 13.2), (15, 4.5, 14), skip=('down',), fm={'north': 'body_dark'}),
        Box((1, 3.5, 3.3), (1.8, 4.5, 13.2), skip=('down', 'north', 'south'), fm={'east': 'body_dark'}),
        Box((14.2, 3.5, 3.3), (15, 4.5, 13.2), skip=('down', 'north', 'south'), fm={'west': 'body_dark'}),
        # latches, handle, power socket, base hinge knuckles, status LED
        Box((2.8, 2.2, 2.0), (4.6, 4.3, 2.5), 'metal', skip=('south',)),
        Box((11.4, 2.2, 2.0), (13.2, 4.3, 2.5), 'metal', skip=('south',)),
        Box((5.4, 1.6, 1.1), (10.6, 2.3, 1.8), 'rubber'),
        Box((5.4, 1.6, 1.8), (6.2, 2.6, 2.5), 'rubber', skip=('south',)),
        Box((9.8, 1.6, 1.8), (10.6, 2.6, 2.5), 'rubber', skip=('south',)),
        Box((0.4, 1.4, 6.0), (1.0, 2.8, 8.0), 'metal', skip=('east',)),
        Box((0.1, 1.8, 6.6), (0.4, 2.4, 7.4), 'brass', skip=('east',)),
        Box((4.4, 4.0, 13.5), (5.4, 5.0, 14.5), 'metal'),
        Box((10.6, 4.0, 13.5), (11.6, 5.0, 14.5), 'metal'),
        Box((13.0, 3.0, 2.45), (13.6, 3.5, 2.5), faces=['north'], ext={'north': ('#blink', [4, 4, 12, 12])}, emissive=True),
    ]
    interior = [
        Box((2.4, 3.5, 3.8), (10.2, 4.05, 7.6), 'rubber', skip=('down',), decals=[d_keys]),
        Box((10.8, 3.5, 4.0), (13.6, 4.0, 7.4), 'panel', skip=('down',)),
        Box((11.8, 4.0, 5.2), (12.6, 4.9, 6.0), 'rubber', skip=('down',)),
        Box((11.95, 4.9, 5.35), (12.45, 5.1, 5.85), 'metal', skip=('down',)),
        Box((2.2, 3.5, 8.2), (13.8, 3.75, 12.8), 'panel', skip=('down',), decals=[d_panel]),
        Box((2.6, 3.75, 8.6), (7.6, 5.6, 12.4), 'alu', skip=('down',), decals=[d_radio]),
        Box((3.2, 4.6, 8.25), (4.0, 5.3, 8.6), 'rubber', skip=('south',)),
        Box((4.4, 4.6, 8.25), (5.2, 5.3, 8.6), 'rubber', skip=('south',)),
        Box((5.8, 4.3, 8.55), (7.2, 5.3, 8.6), faces=['north'], ext={'north': ('#lcd', [0, 4, 16, 12])}, emissive=True),
        *[b for x in (8.4, 9.4, 10.4) for b in (
            Box((x, 3.75, 9.1), (x + 0.4, 4.1, 9.5), 'metal', skip=('down',)),
            Box((x + 0.13, 4.1, 9.2), (x + 0.27, 4.75, 9.34), 'steel', skip=('down',)),
        )],
        Box((8.4, 3.76, 10.2), (8.8, 3.86, 10.6), faces=['up'], ext={'up': ('#led', [4, 4, 12, 12])}, emissive=True),
        Box((9.4, 3.76, 10.2), (9.8, 3.86, 10.6), faces=['up'], ext={'up': ('#blink', [4, 4, 12, 12])}, emissive=True),
        Box((10.4, 3.76, 10.2), (10.8, 3.86, 10.6), faces=['up'], ext={'up': ('#blink2', [4, 4, 12, 12])}, emissive=True),
        Box((11.6, 3.75, 9.0), (12.4, 4.5, 9.8), 'steel', skip=('down',)),
        Box((12.6, 3.75, 9.0), (13.4, 4.5, 9.8), 'steel', skip=('down',)),
        Box((11.85, 4.5, 9.25), (12.15, 4.75, 9.55), 'brass', skip=('down',)),
        Box((12.8, 4.5, 9.2), (13.2, 4.9, 13.2), 'rubber'),
        Box((6.2, 5.6, 10.8), (7.2, 6.0, 11.8), 'rubber', skip=('down',)),
    ]
    antenna = [
        # sized so that, folded flat about (y=6.1, z=11.3), nothing pokes out of the closed lid
        Box((6.5, 6.0, 11.1), (6.9, 6.35, 11.5), 'metal', skip=('down',)),
        Box((6.55, 6.35, 11.15), (6.85, 14.5, 11.45), 'rubber', skip=('down',)),
        Box((6.5, 14.5, 11.1), (6.9, 14.7, 11.5), 'rubber'),
    ]
    lid = [
        Box((1, 4.5, 14), (15, 16, 15.9), fm={'north': 'foam'}, decals=[d_lid_back, d_case_sides]),
        Box((2.2, 14.6, 13.4), (13.8, 15.6, 14), 'rubber', skip=('south',)),
        Box((2.2, 6.0, 13.4), (13.8, 7.0, 14), 'rubber', skip=('south',), decals=[d_bezel_buttons]),
        Box((2.2, 7.0, 13.4), (3.2, 14.6, 14), 'rubber', skip=('south', 'up', 'down'), decals=[d_bezel_buttons]),
        Box((12.8, 7.0, 13.4), (13.8, 14.6, 14), 'rubber', skip=('south', 'up', 'down'), decals=[d_bezel_buttons]),
        Box((3.2, 7.0, 13.8), (12.8, 14.6, 13.85), faces=['north'], ext={'north': ('#screen', [0, 1.9, 16, 14.1])}, emissive=True),
        Box((2.2, 4.0, 13.5), (4.2, 5.0, 14.5), 'metal'),
        Box((11.8, 4.0, 13.5), (13.8, 5.0, 14.5), 'metal'),
        Box((1.2, 8.0, 13.6), (1.6, 8.6, 14), faces=['north', 'up'], ext={'north': ('#led', [4, 4, 12, 12]), 'up': ('#led', [4, 4, 12, 12])}, emissive=True),
    ]
    return {'base': Model(base + interior), 'lid': Model(lid), 'antenna': Model(antenna),
            'full': Model(base + interior + lid + antenna)}


def relay_screen(pal):
    led = pal['led']
    N, S = 16, 128
    sheet = Image.new('RGBA', (S, S * N), (0, 0, 0, 255))
    rnd = random.Random(7)
    blips = [(rnd.uniform(0, 360), rnd.uniform(8, 34)) for _ in range(5)]
    lines = [rnd.randint(8, 52) for _ in range(40)]
    for f in range(N):
        img = Image.new('RGBA', (S, S), (4, 8, 6, 255))
        d = ImageDraw.Draw(img)
        dim = mix((4, 8, 6), led, 0.25)
        mid = mix((4, 8, 6), led, 0.55)
        # status bar (rows 14..22) - visible band is rows ~15..113
        d.rectangle([2, 16, S - 3, 25], fill=mix((4, 8, 6), led, 0.18))
        draw_text(img, 5, 18, 'LINK OK', led, 1)
        draw_text(img, S - 30, 18, 'CH 07', led, 1)
        # radar
        cx, cy, r = 44, 66, 38
        for rr in (r, r * 2 // 3, r // 3):
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=dim)
        d.line([(cx - r, cy), (cx + r, cy)], fill=dim)
        d.line([(cx, cy - r), (cx, cy + r)], fill=dim)
        sweep = f * 360 / N
        for k in range(12):
            a = math.radians(sweep - k * 3)
            d.line([(cx, cy), (cx + r * math.sin(a), cy - r * math.cos(a))], fill=mix((4, 8, 6), led, 1 - k / 12))
        for (ba, br) in blips:
            age = (sweep - ba) % 360
            if age < 200:
                c = mix((4, 8, 6), led, 1 - age / 200)
                a = math.radians(ba)
                x, y = cx + br * math.sin(a), cy - br * math.cos(a)
                d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=c)
        # data column
        for k in range(9):
            w = lines[(k + f) % len(lines)]
            y = 32 + k * 8
            d.rectangle([90, y, 90 + min(w, 34), y + 3], fill=mid if k % 3 else led)
        # bottom bars
        for k in range(10):
            h = 4 + int(10 * abs(math.sin(f * 0.7 + k)))
            d.rectangle([6 + k * 12, 110 - h, 12 + k * 12, 110], fill=mid)
        sheet.paste(img, (0, f * S))
    return sheet


def led_tex(pal, frames=1, phase=0):
    led = pal['led']
    img = Image.new('RGBA', (16, 16 * frames))
    for f in range(frames):
        on = (f + phase) % frames == 0
        for y in range(16):
            for x in range(16):
                dd = math.hypot(x - 7.5, y - 7.5) / 8
                c = mix(led, (255, 255, 255), max(0, 0.6 - dd)) if on else mix((10, 10, 10), led, 0.22)
                img.putpixel((x, f * 16 + y), c + (255,))
    return img


def lcd_tex(pal):
    img = Image.new('RGBA', (32, 32), (6, 10, 8, 255))
    draw_text(img, 3, 11, '07', pal['led'], 2)
    draw_text(img, 18, 13, '25W', mix((6, 10, 8), pal['led'], 0.7), 1)
    return img


# ================================================================ main

def main():
    # ---------- compass
    cm = compass_models()
    order = ['base', 'lid', 'popup', 'needle', 'card']
    faces, size = pack([cm[k] for k in order], CD, 1024)
    print('compass atlas', size)
    for v, pal in VARIANTS.items():
        atlas = paint([cm[k] for k in order], faces, size, pal, 1.2, 1)
        save_png(atlas, f'item/compass/atlas_{v}.png')
        save_png(compass_card(pal), f'item/compass/card_{v}.png')
        save_png(compass_icon(pal), f'item/compass/icon_{v}.png')
        tex = {'0': f'{MOD}:item/compass/atlas_{v}', 'card': f'{MOD}:item/compass/card_{v}',
               'particle': f'{MOD}:item/compass/icon_{v}'}
        for k in order:
            out(f'assets/{MOD}/models/item/compass/{k}_{v}.json', model_json(cm[k], size, tex))
        out(f'assets/{MOD}/models/item/compass/icon_{v}.json',
            {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{MOD}:item/compass/icon_{v}'}})
        tp = {'rotation': [90, 0, 0], 'translation': [0, 1.5, 1.0], 'scale': [0.3, 0.3, 0.3]}
        ident = {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [1, 1, 1]}
        out(f'assets/{MOD}/models/item/tactical_compass_{v}.json', {
            'parent': 'builtin/entity', 'gui_light': 'front',
            'textures': {'particle': f'{MOD}:item/compass/icon_{v}'},
            'display': {
                'thirdperson_righthand': tp, 'thirdperson_lefthand': tp,
                'firstperson_righthand': ident, 'firstperson_lefthand': ident, 'gui': ident,
                'ground': {'rotation': [0, 0, 0], 'translation': [0, 2, 0], 'scale': [0.5, 0.5, 0.5]},
                'fixed': {'rotation': [90, 0, 0], 'translation': [0, 0, 0], 'scale': [1, 1, 1]},
                'head': {'rotation': [0, 0, 0], 'translation': [0, 6, 0], 'scale': [1, 1, 1]},
            }})

    # ---------- relay
    rm = relay_models()
    parts = ['base', 'lid', 'antenna', 'full']
    faces, size = pack([rm[k] for k in parts], RD, 512)
    print('relay atlas', size)
    for v, pal in VARIANTS.items():
        atlas = paint([rm[k] for k in parts], faces, size, pal, 2.0, 2)
        save_png(atlas, f'block/relay/atlas_{v}.png')
        save_png(relay_screen(pal), f'block/relay/screen_{v}.png')
        out(f'assets/{MOD}/textures/block/relay/screen_{v}.png.mcmeta', {'animation': {'frametime': 2}})
        save_png(led_tex(pal), f'block/relay/led_{v}.png')
        save_png(led_tex(pal, 2), f'block/relay/blink_{v}.png')
        out(f'assets/{MOD}/textures/block/relay/blink_{v}.png.mcmeta', {'animation': {'frametime': 10}})
        save_png(led_tex(pal, 3, 1), f'block/relay/blink2_{v}.png')
        out(f'assets/{MOD}/textures/block/relay/blink2_{v}.png.mcmeta', {'animation': {'frametime': 6}})
        save_png(lcd_tex(pal), f'block/relay/lcd_{v}.png')
        part = Image.new('RGBA', (16, 16), (pal['camo'][0] if pal['camo'] else pal['body']) + (255,))
        save_png(part, f'block/relay/particle_{v}.png')
        tex = {'0': f'{MOD}:block/relay/atlas_{v}', 'screen': f'{MOD}:block/relay/screen_{v}',
               'led': f'{MOD}:block/relay/led_{v}', 'blink': f'{MOD}:block/relay/blink_{v}',
               'blink2': f'{MOD}:block/relay/blink2_{v}', 'lcd': f'{MOD}:block/relay/lcd_{v}',
               'particle': f'{MOD}:block/relay/particle_{v}'}
        name = f'comms_relay_{v}'
        extra = {'parent': 'minecraft:block/block', 'render_type': 'minecraft:cutout', 'ambientocclusion': False}
        out(f'assets/{MOD}/models/block/{name}.json', model_json(rm['base'], size, tex, extra))
        out(f'assets/{MOD}/models/block/relay/lid_{v}.json', model_json(rm['lid'], size, tex))
        out(f'assets/{MOD}/models/block/relay/antenna_{v}.json', model_json(rm['antenna'], size, tex))
        # held like a block (stonecutter scale) but turned so the open case faces the holder
        tp_r = {'rotation': [70, 180, 0], 'translation': [0, 2.5, 0], 'scale': [0.375, 0.375, 0.375]}
        tp_l = {'rotation': [70, 180, 0], 'translation': [0, 2.5, 0], 'scale': [0.375, 0.375, 0.375]}
        item_display = {'display': {
            'thirdperson_righthand': tp_r, 'thirdperson_lefthand': tp_l,
            'firstperson_righthand': {'rotation': [15, 160, 0], 'translation': [0, 1, 0], 'scale': [0.4, 0.4, 0.4]},
            'firstperson_lefthand': {'rotation': [15, 200, 0], 'translation': [0, 1, 0], 'scale': [0.4, 0.4, 0.4]},
            'gui': {'rotation': [30, 205, 0], 'translation': [0, 0, 0], 'scale': [0.625, 0.625, 0.625]},
        }}
        out(f'assets/{MOD}/models/item/{name}.json', model_json(rm['full'], size, tex, {**extra, **item_display}))
        variants = {}
        for facing, y in (('north', 0), ('east', 90), ('south', 180), ('west', 270)):
            m = {'model': f'{MOD}:block/{name}'}
            if y:
                m['y'] = y
            variants[f'facing={facing}'] = m
        out(f'assets/{MOD}/blockstates/{name}.json', {'variants': variants})
        out(f'data/{MOD}/loot_tables/blocks/{name}.json', {
            'type': 'minecraft:block',
            'pools': [{'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': f'{MOD}:{name}'}],
                       'conditions': [{'condition': 'minecraft:survives_explosion'}]}]})
        d1, d2 = pal['dyes']
        out(f'data/{MOD}/recipes/tactical_compass_{v}.json', {
            'type': 'minecraft:crafting_shaped', 'category': 'equipment',
            'pattern': ['AIB', 'ICI', 'LRL'],
            'key': {'A': {'item': d1}, 'B': {'item': d2}, 'I': {'item': 'minecraft:iron_ingot'},
                    'C': {'item': 'minecraft:compass'}, 'L': {'item': pal['led_dye']},
                    'R': {'item': 'minecraft:redstone'}},
            'result': {'item': f'{MOD}:tactical_compass_{v}', 'count': 1}})
        out(f'data/{MOD}/recipes/{name}.json', {
            'type': 'minecraft:crafting_shaped', 'category': 'redstone',
            'pattern': ['ATB', 'IRI', 'ILI'],
            'key': {'A': {'item': d1}, 'B': {'item': d2}, 'I': {'item': 'minecraft:iron_ingot'},
                    'T': {'item': 'minecraft:lightning_rod'}, 'R': {'item': 'minecraft:redstone_block'},
                    'L': {'item': pal['led_dye']}},
            'result': {'item': f'{MOD}:{name}', 'count': 1}})

    out('data/minecraft/tags/blocks/mineable/pickaxe.json',
        {'replace': False, 'values': [f'{MOD}:comms_relay_{v}' for v in VARIANTS]})
    lang = {'itemGroup.tacticalcompass': 'Tactical Compass'}
    for v, pal in VARIANTS.items():
        lang[f'item.{MOD}.tactical_compass_{v}'] = f"Tactical Compass ({pal['name']})"
        lang[f'block.{MOD}.comms_relay_{v}'] = f"Communications Relay ({pal['name']})"
    out(f'assets/{MOD}/lang/en_us.json', lang)
    led_px = Image.new('RGBA', (4, 4), (255, 255, 255, 255))
    save_png(led_px, 'misc/led.png')


if __name__ == '__main__':
    main()
