"""Builds the Hercules app icon (original art, Pillow only).

Output next to this file: hercules_icon_1024.png (master) and hercules.icns (macOS, via sips + iconutil).
Design: round bronze hoplite shield (terracotta face like the hero's tunic, gold star emblem) over a sword, inside a
gold Greek-key frame on a deep navy rounded square (Apple icon grid: 824 px body on a 1024 canvas).
Run: python3 game/icon/make_icon.py   (this folder has a .gdignore: Godot never imports it)
"""
import math, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
S = 4                      # supersampling
N = 1024 * S
NAVY_TOP, NAVY_BOT = (34, 52, 92), (14, 22, 42)
GOLD, GOLD_DARK, GOLD_LIGHT = (214, 164, 64), (150, 104, 34), (246, 214, 132)
TERRA, TERRA_DARK = (166, 66, 44), (112, 38, 26)
STEEL, STEEL_DARK = (214, 222, 230), (128, 140, 154)
INK = (20, 16, 18)


def s(v):
    return int(round(v * S))


def rounded_mask(box, r):
    m = Image.new("L", (N, N), 0)
    ImageDraw.Draw(m).rounded_rectangle([s(c) for c in box], radius=s(r), fill=255)
    return m


def gradient(top, bot):
    g = Image.new("RGB", (1, N))
    for y in range(N):
        t = y / (N - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return g.resize((N, N))


def meander_strip(length, height, color, width):
    """Horizontal Greek-key band (length x height, in final px), drawn at S."""
    im = Image.new("RGBA", (s(length), s(height)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = s(width)
    c = height / 7.0                       # cell size; band = 7 cells high, unit = 7 cells wide
    units = max(1, round(length / (7 * c)))
    u = length / units
    k = u / 7.0
    for i in range(units):
        x0 = i * u
        pts = [(0, 6), (0, 1), (5, 1), (5, 5), (2, 5), (2, 3), (3.5, 3)]
        pts = [(s(x0 + px * k + c * 0.5), s(py * c)) for px, py in pts]
        d.line(pts, fill=color, width=w, joint="curve")
    d.line([(0, s(c * 0.0) + w // 2), (s(length), s(c * 0.0) + w // 2)], fill=color, width=w)
    d.line([(0, s(6 * c)), (s(length), s(6 * c))], fill=color, width=w)
    return im


def star(d, cx, cy, r_in, r_long, r_short, rays, color):
    for i in range(rays):
        a = 2 * math.pi * i / rays - math.pi / 2
        r = r_long if i % 2 == 0 else r_short
        half = math.pi / rays * 0.85
        pts = [(cx + r_in * math.cos(a - half), cy + r_in * math.sin(a - half)),
               (cx + r * math.cos(a), cy + r * math.sin(a)),
               (cx + r_in * math.cos(a + half), cy + r_in * math.sin(a + half))]
        d.polygon([(s(x), s(y)) for x, y in pts], fill=color)
    d.ellipse([s(cx - r_in), s(cy - r_in), s(cx + r_in), s(cy + r_in)], fill=color)


def main():
    canvas = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    body = (100, 100, 924, 924)
    radius = 185
    # soft drop shadow
    sh = rounded_mask((body[0], body[1] + 14, body[2], body[3] + 14), radius).filter(ImageFilter.GaussianBlur(s(18)))
    canvas.paste(Image.new("RGBA", (N, N), (0, 0, 0, 110)), (0, 0), sh)
    # navy body
    canvas.paste(gradient(NAVY_TOP, NAVY_BOT), (0, 0), rounded_mask(body, radius))
    d = ImageDraw.Draw(canvas)
    # gold frame lines + Greek key band
    m = 150; band = 56
    d.rounded_rectangle([s(m), s(m), s(1024 - m), s(1024 - m)], radius=s(120), outline=GOLD, width=s(7))
    inner = m + 26
    L = 1024 - 2 * inner - 2 * band
    strip = meander_strip(L, band, GOLD, 9)
    canvas.alpha_composite(strip, (s(inner + band), s(inner)))
    canvas.alpha_composite(strip.rotate(180), (s(inner + band), s(1024 - inner - band)))
    canvas.alpha_composite(strip.rotate(90, expand=True), (s(inner), s(inner + band)))
    canvas.alpha_composite(strip.rotate(-90, expand=True), (s(1024 - inner - band), s(inner + band)))
    for cx, cy in [(inner, inner), (1024 - inner - band, inner), (inner, 1024 - inner - band),
                   (1024 - inner - band, 1024 - inner - band)]:
        d.rectangle([s(cx + 10), s(cy + 10), s(cx + band - 10), s(cy + band - 10)], outline=GOLD, width=s(9))
        d.rectangle([s(cx + 24), s(cy + 24), s(cx + band - 24), s(cy + band - 24)], fill=GOLD)
    # sword behind the shield (lower left to upper right)
    cx, cy = 512, 524
    ang = math.radians(-45)
    ux, uy = math.cos(ang), math.sin(ang)          # along the blade (towards upper right)
    px, py = -uy, ux                                # across
    def P(a, b):
        return (s(cx + ux * a + px * b), s(cy + uy * a + py * b))
    blade = [P(-150, -22), P(250, -22), P(300, 0), P(250, 22), P(-150, 22)]
    d.polygon(blade, fill=STEEL, outline=INK, width=s(6))
    d.line([P(-150, 0), P(262, 0)], fill=STEEL_DARK, width=s(6))
    d.polygon([P(-170, -70), P(-150, -70), P(-150, 70), P(-170, 70)], fill=GOLD, outline=INK, width=s(6))
    d.polygon([P(-280, -16), P(-170, -16), P(-170, 16), P(-280, 16)], fill=TERRA_DARK, outline=INK, width=s(6))
    d.ellipse([P(-300, 0)[0] - s(26), P(-300, 0)[1] - s(26), P(-300, 0)[0] + s(26), P(-300, 0)[1] + s(26)],
              fill=GOLD, outline=INK, width=s(6))
    # shield
    R = 228
    def circ(r, **kw):
        d.ellipse([s(cx - r), s(cy - r), s(cx + r), s(cy + r)], **kw)
    sh2 = Image.new("L", (N, N), 0)
    ImageDraw.Draw(sh2).ellipse([s(cx - R - 4), s(cy - R + 18), s(cx + R + 4), s(cy + R + 26)], fill=150)
    canvas.paste(Image.new("RGBA", (N, N), (0, 0, 0, 255)), (0, 0), sh2.filter(ImageFilter.GaussianBlur(s(14))))
    d = ImageDraw.Draw(canvas)
    circ(R + 6, fill=INK)
    circ(R, fill=GOLD_DARK)
    circ(R - 10, fill=GOLD)
    circ(R - 34, fill=INK)
    circ(R - 40, fill=TERRA)
    # light band on the upper left of the face (cel look: one hard highlight)
    hl = Image.new("L", (N, N), 0)
    hd = ImageDraw.Draw(hl)
    hd.ellipse([s(cx - R + 40), s(cy - R + 40), s(cx + R - 40), s(cy + R - 40)], fill=255)
    hd.ellipse([s(cx - R + 90), s(cy - R + 100), s(cx + R + 10), s(cy + R + 20)], fill=0)
    canvas.paste(Image.new("RGBA", (N, N), (196, 92, 62, 255)), (0, 0), hl)
    d = ImageDraw.Draw(canvas)
    # dark lower-right band
    sd = Image.new("L", (N, N), 0)
    sdd = ImageDraw.Draw(sd)
    sdd.ellipse([s(cx - R + 40), s(cy - R + 40), s(cx + R - 40), s(cy + R - 40)], fill=255)
    sdd.ellipse([s(cx - R - 20), s(cy - R - 30), s(cx + R - 70), s(cy + R - 80)], fill=0)
    canvas.paste(Image.new("RGBA", (N, N), TERRA_DARK + (255,)), (0, 0), sd)
    d = ImageDraw.Draw(canvas)
    circ(R - 62, outline=GOLD, width=s(8))
    # rivets on the rim
    for i in range(16):
        a = 2 * math.pi * i / 16
        rx, ry = cx + (R - 22) * math.cos(a), cy + (R - 22) * math.sin(a)
        d.ellipse([s(rx - 6), s(ry - 6), s(rx + 6), s(ry + 6)], fill=GOLD_LIGHT, outline=GOLD_DARK, width=s(2))
    # star emblem with an ink edge
    star(d, cx, cy, 44, 132, 96, 16, INK)
    star(d, cx, cy, 38, 124, 88, 16, GOLD)
    d.ellipse([s(cx - 22), s(cy - 22), s(cx + 22), s(cy + 22)], fill=GOLD_LIGHT, outline=GOLD_DARK, width=s(4))
    out = canvas.resize((1024, 1024), Image.LANCZOS)
    png = os.path.join(HERE, "hercules_icon_1024.png")
    out.save(png)
    # icns
    tmp = tempfile.mkdtemp()
    iconset = os.path.join(tmp, "hercules.iconset")
    os.makedirs(iconset)
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            px_ = size * scale
            name = "icon_%dx%d%s.png" % (size, size, "@2x" if scale == 2 else "")
            out.resize((px_, px_), Image.LANCZOS).save(os.path.join(iconset, name))
    icns = os.path.join(HERE, "hercules.icns")
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o", icns], check=True)
    shutil.rmtree(tmp)
    print(png, icns, os.path.getsize(icns))


if __name__ == "__main__":
    main()
