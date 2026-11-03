#!/usr/bin/env python3
"""Renders crafting-table recipe images (animated GIFs when the dye can change) for the README.

Vanilla textures are read straight from the Minecraft 1.20.1 client jar in the ForgeGradle cache
(run ./gradlew build once first); mod items come from src/main/resources. Block items are drawn
as 3D GUI icons with a small orthographic renderer, flat items as 16x16 sprites.

    python tools/gen_recipe_images.py [path/to/client-extra.jar]
"""
import io
import json
import math
import os
import sys
import zipfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
RES = os.path.join(ROOT, 'src', 'main', 'resources', 'assets')
OUT = os.path.join(ROOT, 'assets', 'recipes')
JAR = os.path.join(os.path.expanduser('~'), '.gradle', 'caches', 'forge_gradle', 'minecraft_repo',
                   'versions', '1.20.1', 'client-extra.jar')
SCALE = 4          # GUI pixels -> image pixels
SS = 4             # supersampling for 3D icons
MOD = 'tacticalcompass'

jar = None


def texture(ref):
    """'minecraft:item/iron_ingot' or 'tacticalcompass:block/relay/atlas_olive' -> RGBA image."""
    ns, path = ref.split(':') if ':' in ref else ('minecraft', ref)
    rel = f'{ns}/textures/{path}.png'
    if ns == 'minecraft':
        img = Image.open(io.BytesIO(jar.read('assets/' + rel)))
    else:
        img = Image.open(os.path.join(RES, rel))
    img = img.convert('RGBA')
    if img.height > img.width:  # animated strip: first frame
        img = img.crop((0, 0, img.width, img.width))
    return img


def flat(ref):
    return texture(ref).resize((16 * SCALE, 16 * SCALE), Image.NEAREST)


# ---------------------------------------------------------------- 3D GUI icons

def rot(v, rx, ry, rz):
    x, y, z = v
    for axis, deg in (('z', rz), ('y', ry), ('x', rx)):  # q = Rx * Ry * Rz, applied right-to-left
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        if axis == 'x':
            y, z = y * c - z * s, y * s + z * c
        elif axis == 'y':
            x, z = x * c + z * s, -x * s + z * c
        else:
            x, y = x * c - y * s, x * s + y * c
    return x, y, z


def corners(face, f, t):
    x0, y0, z0 = f
    x1, y1, z1 = t
    return {  # TL, TR, BR, BL in texture space
        'up': [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        'down': [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
        'north': [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
        'south': [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
        'west': [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
        'east': [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
    }[face]


NORMALS = {'up': (0, 1, 0), 'down': (0, -1, 0), 'north': (0, 0, -1), 'south': (0, 0, 1),
           'west': (-1, 0, 0), 'east': (1, 0, 0)}


def _unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


L0, L1 = _unit((0.2, 1.0, -0.7)), _unit((-0.2, 1.0, 0.7))


def render_model(model, size=16 * SCALE):
    """Orthographic GUI render of a block-model dict (elements + textures + display.gui)."""
    gui = model.get('display', {}).get('gui', {'rotation': [30, 225, 0], 'scale': [0.625] * 3})
    rx, ry, rz = gui['rotation']
    sc = gui['scale'][0]
    texmap = model['textures']
    cache = {}

    def tex(key):
        while key.startswith('#'):
            key = texmap[key[1:]]
        if key not in cache:
            cache[key] = texture(key)
        return cache[key]

    W = size * SS
    canvas = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    polys = []
    for el in model['elements']:
        f, t = el['from'], el['to']
        emissive = 'forge_data' in el
        for face, fd in el['faces'].items():
            n = rot(NORMALS[face], rx, ry, rz)
            if n[2] <= 1e-4:
                continue
            pts = []
            for p in corners(face, f, t):
                q = rot(((p[0] - 8) / 16, (p[1] - 8) / 16, (p[2] - 8) / 16), rx, ry, rz)
                pts.append((W / 2 + q[0] * sc * W, W / 2 - q[1] * sc * W, q[2]))
            depth = sum(p[2] for p in pts) / 4
            light = 1.0 if emissive else min(1.0, 0.4 + 0.6 * (max(0, sum(a * b for a, b in zip(n, L0))) +
                                                            max(0, sum(a * b for a, b in zip(n, L1)))))
            polys.append((depth, pts, fd, light))
    for depth, pts, fd, light in sorted(polys, key=lambda p: p[0]):
        img = tex(fd['texture'])
        u0, v0, u1, v1 = fd.get('uv', [0, 0, 16, 16])
        tw, th = img.size
        a, b = (u0 * tw / 16, v0 * th / 16), (u1 * tw / 16, v1 * th / 16)
        src = img.crop((int(min(a[0], b[0])), int(min(a[1], b[1])),
                        max(int(min(a[0], b[0])) + 1, int(round(max(a[0], b[0])))),
                        max(int(min(a[1], b[1])) + 1, int(round(max(a[1], b[1]))))))
        if b[0] < a[0]:
            src = src.transpose(Image.FLIP_LEFT_RIGHT)
        if b[1] < a[1]:
            src = src.transpose(Image.FLIP_TOP_BOTTOM)
        if light < 1.0:
            r, g, bb, al = src.split()
            r, g, bb = (ch.point(lambda c, k=light: int(c * k)) for ch in (r, g, bb))
            src = Image.merge('RGBA', (r, g, bb, al))
        (x0, y0, _), (x1, y1, _), _, (x3, y3, _) = pts
        sw, sh = src.size
        # inverse affine: output (X,Y) -> source (u,v), from TL, TR, BL
        ax, ay, bx, by = (x1 - x0) / sw, (y1 - y0) / sw, (x3 - x0) / sh, (y3 - y0) / sh
        det = ax * by - bx * ay
        if abs(det) < 1e-9:
            continue
        ia, ib, id_, ie = by / det, -bx / det, -ay / det, ax / det
        data = (ia, ib, -(ia * x0 + ib * y0), id_, ie, -(id_ * x0 + ie * y0))
        warped = src.transform((W, W), Image.AFFINE, data, resample=Image.NEAREST)
        mask = Image.new('L', (W, W), 0)
        ImageDraw.Draw(mask).polygon([(p[0], p[1]) for p in pts], fill=255)
        alpha = Image.composite(warped.getchannel('A'), Image.new('L', (W, W), 0), mask)
        warped.putalpha(alpha)
        canvas.alpha_composite(warped)
    return canvas.resize((size, size), Image.LANCZOS)


def mod_model(path):
    with open(os.path.join(RES, MOD, 'models', path + '.json')) as fh:
        return json.load(fh)


IRON_BLOCK = {'textures': {'all': 'minecraft:block/iron_block'},
              'display': {'gui': {'rotation': [30, 225, 0], 'scale': [0.625] * 3}},
              'elements': [{'from': [0, 0, 0], 'to': [16, 16, 16],
                            'faces': {f: {'texture': '#all'} for f in NORMALS}}]}


# ---------------------------------------------------------------- crafting grid

def panel():
    gui = Image.open(io.BytesIO(jar.read('assets/minecraft/textures/gui/container/crafting_table.png'))).convert('RGBA')
    top = gui.crop((0, 0, 176, 79))
    bottom = gui.crop((0, 162, 176, 166))
    p = Image.new('RGBA', (176, 83))
    p.paste(top, (0, 0))
    p.paste(bottom, (0, 79))
    return p.resize((176 * SCALE, 83 * SCALE), Image.NEAREST)


SLOT = [(30 + 18 * (i % 3), 17 + 18 * (i // 3)) for i in range(9)]
RESULT = (124, 35)


def frame(grid, result):
    img = panel()
    for i, icon in enumerate(grid):
        if icon is not None:
            x, y = SLOT[i]
            img.alpha_composite(icon, (x * SCALE, y * SCALE))
    img.alpha_composite(result, (RESULT[0] * SCALE, RESULT[1] * SCALE))
    return img


def save_gif(frames, name, ms=1000):
    os.makedirs(OUT, exist_ok=True)
    rgb = [f.convert('RGB') for f in frames]
    path = os.path.join(OUT, name)
    if len(rgb) == 1:
        rgb[0].save(path.replace('.gif', '.png'))
        return
    pal = [f.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE) for f in rgb]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=ms, loop=0, disposal=1)


def main():
    global jar
    jar = zipfile.ZipFile(sys.argv[1] if len(sys.argv) > 1 else JAR)
    iron = flat('minecraft:item/iron_ingot')
    redstone = flat('minecraft:item/redstone')
    compass = flat('minecraft:item/compass_16')
    torch = flat('minecraft:block/redstone_torch')
    iron_block = render_model(IRON_BLOCK)
    dyes = {d: flat(f'minecraft:item/{d}_dye') for d in ('green', 'black', 'brown')}
    tc = {v: flat(f'{MOD}:item/compass/icon_{v}') for v in ('olive', 'black', 'camo')}
    relay = {v: render_model(mod_model(f'item/comms_relay_{v}')) for v in ('olive', 'black', 'camo')}
    steps = [(None, 'olive'), ('green', 'olive'), ('black', 'black'), ('brown', 'camo')]

    save_gif([frame([dyes.get(d), iron, redstone, iron, compass, iron, None, iron, None], tc[v])
              for d, v in steps], 'tactical_compass.gif')
    save_gif([frame([dyes.get(d), compass, torch, None, iron_block, None, None, None, None], relay[v])
              for d, v in steps], 'comms_relay.gif')
    swaps = [('olive', 'black', 'black'), ('black', 'brown', 'camo'), ('camo', 'green', 'olive')]
    save_gif([frame([None, None, None, tc[a], dyes[d], None, None, None, None], tc[b]) for a, d, b in swaps] +
             [frame([None, None, None, relay[a], dyes[d], None, None, None, None], relay[b]) for a, d, b in swaps],
             'redye.gif')
    print('wrote', OUT)


if __name__ == '__main__':
    main()
