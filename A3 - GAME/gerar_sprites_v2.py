"""Gera o cenário da batalha final: pôr do sol, montanhas, castelo e porta, e a versão NOITE.
Uso (na pasta do jogo):  python ferramentas/gerar_fundo.py
Cria imagens/batalha/fundo_batalha.png, fundo_noite.png e porta.png
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from sistemas import cenario as C  # noqa: E402

W, H = C.LARGURA, C.ALTURA
S = 2  # supersampling
OUT = os.path.join(RAIZ, "imagens", "batalha")


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def grad(stops, t):
    t = min(max(t, 0), 0.9999) * (len(stops) - 1)
    i = int(t)
    return mix(stops[i], stops[i + 1], t - i)


def sc(pts):
    return [(x * S, y * S) for x, y in pts]


def box(x0, y0, x1, y1):
    return [x0 * S, y0 * S, x1 * S, y1 * S]


random.seed(7)
img = Image.new("RGBA", (W * S, H * S))
d = ImageDraw.Draw(img)

# ---------- céu ----------
SKY = [(58, 40, 96), (150, 64, 100), (236, 108, 72), (255, 168, 92), (255, 212, 140)]
for y in range(H * S):
    d.line([(0, y), (W * S, y)], fill=grad(SKY, y / (C.CHAO_Y * S)) + (255,))

# ---------- sol com brilho ----------
SOL = (770, 290)
glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse(box(SOL[0] - 230, SOL[1] - 230, SOL[0] + 230, SOL[1] + 230), fill=(255, 190, 110, 150))
glow = glow.filter(ImageFilter.GaussianBlur(60 * S))
img.alpha_composite(glow)
d = ImageDraw.Draw(img)
for r in range(78, 0, -2):
    t = r / 78
    d.ellipse(box(SOL[0] - r, SOL[1] - r, SOL[0] + r, SOL[1] + r),
              fill=mix((255, 250, 210), (255, 140, 60), t) + (255,))


# ---------- nuvens (poucas) ----------
def nuvem(cx, cy, w, h, alvo=None, c_sombra=(214, 108, 112, 200), c_corpo=(255, 206, 176, 235)):
    alvo = img if alvo is None else alvo
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    partes = [(-0.30, 0.10, 0.45, 0.60), (-0.05, -0.10, 0.50, 0.75), (0.22, 0.05, 0.42, 0.62), (0.00, 0.18, 0.80, 0.45)]
    for ox, oy, pw, ph in partes:  # sombra inferior
        ld.ellipse(box(cx + ox * w - pw * w / 2, cy + oy * h - ph * h / 2 + 6,
                       cx + ox * w + pw * w / 2, cy + oy * h + ph * h / 2 + 6), fill=c_sombra)
    for ox, oy, pw, ph in partes:
        ld.ellipse(box(cx + ox * w - pw * w / 2, cy + oy * h - ph * h / 2,
                       cx + ox * w + pw * w / 2, cy + oy * h + ph * h / 2), fill=c_corpo)
    alvo.alpha_composite(layer.filter(ImageFilter.GaussianBlur(3 * S)))


for cx, cy, w, h in [(190, 120, 300, 70), (520, 70, 240, 54), (890, 150, 280, 60), (1120, 60, 220, 46)]:
    nuvem(cx, cy, w, h)
d = ImageDraw.Draw(img)
ceu_dia = img.copy()   # só o céu: serve para separar o cenário (montanhas, castelo) na versão noturna


# ---------- montanhas e colinas ----------
def silhueta(base, amp, cor, fase, freq=1.0):
    pts = []
    for x in range(0, W + 20, 16):
        y = base - amp * (0.55 * math.sin(x * 0.0042 * freq + fase) + 0.30 * math.sin(x * 0.011 * freq + fase * 2)
                          + 0.15 * math.sin(x * 0.031 * freq + fase * 3))
        pts.append((x, y))
    pts += [(W, C.CHAO_Y + 20), (0, C.CHAO_Y + 20)]
    d.polygon(sc(pts), fill=cor + (255,))


silhueta(470, 70, (150, 84, 122), 0.4)
silhueta(520, 60, (112, 62, 108), 1.7, 1.3)
silhueta(575, 38, (66, 70, 70), 2.9, 1.6)
silhueta(610, 26, (48, 66, 48), 4.1, 2.0)

# pinheiros à esquerda
for px in (40, 98, 170, 240, 300):
    base = C.CHAO_Y + 4
    alt = random.randint(86, 128)
    for k in range(3):
        top = base - alt + k * alt * 0.22
        wid = (alt * 0.30) * (0.55 + 0.25 * k)
        d.polygon(sc([(px, top - 20), (px - wid, top + alt * 0.32), (px + wid, top + alt * 0.32)]),
                  fill=(28, 44, 40, 255))
    d.rectangle(box(px - 4, base - 14, px + 4, base), fill=(40, 30, 28, 255))

# ---------- chão ----------
GR = [(100, 134, 62), (62, 88, 46), (44, 40, 34)]
for y in range(C.CHAO_Y * S, H * S):
    d.line([(0, y), (W * S, y)], fill=grad(GR, (y - C.CHAO_Y * S) / ((H - C.CHAO_Y) * S)) + (255,))
d.line([(0, C.CHAO_Y * S), (W * S, C.CHAO_Y * S)], fill=(255, 214, 130, 255), width=3 * S // 2)
for _ in range(420):
    gx = random.randint(0, W)
    gy = C.CHAO_Y + random.randint(0, 10)
    d.line(sc([(gx, gy), (gx + random.randint(-3, 3), gy - random.randint(3, 8))]), fill=(132, 170, 76, 255), width=S)


# ---------- castelo ----------
def pedra(x0, y0, x1, y1, claro=(184, 154, 152), escuro=(92, 80, 102)):
    for x in range(int(x0 * S), int(x1 * S)):
        d.line([(x, y0 * S), (x, y1 * S)], fill=mix(claro, escuro, (x - x0 * S) / max(1, (x1 - x0) * S)) + (255,))
    tijolo = 16
    for k, y in enumerate(range(int(y0), int(y1), tijolo)):
        d.line(sc([(x0, y), (x1, y)]), fill=(40, 30, 48, 70), width=S)
        off = 0 if k % 2 == 0 else 14
        for x in range(int(x0) + off, int(x1), 28):
            d.line(sc([(x, y), (x, y + tijolo)]), fill=(40, 30, 48, 60), width=S)
    d.rectangle(box(x0, y0, x1, y1), outline=(36, 26, 44, 255), width=2 * S)


def janela(cx, cy, w, h, fundo=(26, 20, 34), moldura=(66, 56, 72)):
    forma = [box(cx - w / 2 - 4, cy - h / 2 - 4, cx + w / 2 + 4, cy - h / 2 + w + 4),
             box(cx - w / 2 - 4, cy - h / 2 + w / 2, cx + w / 2 + 4, cy + h / 2 + 4)]
    d.ellipse(forma[0], fill=moldura + (255,))
    d.rectangle(forma[1], fill=moldura + (255,))
    d.ellipse(box(cx - w / 2, cy - h / 2, cx + w / 2, cy - h / 2 + w), fill=fundo + (255,))
    d.rectangle(box(cx - w / 2, cy - h / 2 + w / 2, cx + w / 2, cy + h / 2), fill=fundo + (255,))


def telhado(pts, claro=(196, 84, 74), escuro=(124, 40, 52)):
    d.polygon(sc(pts), fill=escuro + (255,))
    meio = [pts[0], pts[1], ((pts[1][0] + pts[2][0]) / 2, (pts[1][1] + pts[2][1]) / 2)]
    d.polygon(sc([pts[1], ((pts[0][0] + pts[1][0]) / 2 - 6, pts[0][1] + 2),
                  (pts[1][0] - 2, pts[0][1] + 2)]), fill=claro + (255,))
    d.polygon(sc(pts), outline=(50, 20, 30, 255), width=2 * S)


# muralha atrás
pedra(990, 400, 1280, C.CHAO_Y + 4)
for mx in range(990, 1280, 32):
    pedra(mx, 380, mx + 20, 402, (170, 142, 142), (110, 96, 112))

# torre da esquerda
pedra(990, 262, 1062, C.CHAO_Y + 4)
telhado([(982, 264), (1026, 168), (1070, 264)])
janela(1026, 340, 18, 32)

# torre principal
pedra(1160, 110, 1272, C.CHAO_Y + 4)
telhado([(1146, 114), (1216, 6), (1286, 114)])
d.line(sc([(1216, 6), (1216, -30)]), fill=(60, 40, 40, 255), width=2 * S)
for cx, cy, w, h in C.JANELAS_TORRE:
    janela(cx, cy, w, h)
cx, cy, w, h = C.JANELA_PRINCESA
janela(cx, cy, w, h, fundo=(26, 20, 34), moldura=(88, 74, 80))
d.rectangle(box(cx - 40, cy + h / 2 + 2, cx + 40, cy + h / 2 + 10), fill=(112, 98, 108, 255))  # sacada
d.rectangle(box(cx - 40, cy + h / 2 + 2, cx + 40, cy + h / 2 + 10), outline=(36, 26, 44, 255), width=S)

# portão
px, py, pw, ph = C.PORTA
d.ellipse(box(px - 8, py - 8, px + pw + 8, py + pw + 8), fill=(60, 50, 66, 255))
d.rectangle(box(px - 8, py + pw / 2, px + pw + 8, py + ph + 4), fill=(60, 50, 66, 255))
d.ellipse(box(px, py, px + pw, py + pw), fill=(22, 16, 22, 255))
d.rectangle(box(px, py + pw / 2, px + pw, py + ph + 4), fill=(22, 16, 22, 255))
for yy in range(py + 40, py + ph + 4):  # luz quente no fundo
    t = (yy - (py + 40)) / (ph - 36)
    d.line(sc([(px + 6, yy), (px + pw - 6, yy)]), fill=mix((24, 16, 22), (70, 38, 26), t) + (255,))

# suportes das tochas
for tx, ty in C.TOCHAS:
    d.line(sc([(tx, ty + 6), (tx, ty + 30)]), fill=(50, 38, 34, 255), width=3 * S)
    d.rectangle(box(tx - 5, ty + 2, tx + 5, ty + 8), fill=(70, 56, 50, 255))

# ---------- versão NOITE ----------
def ceu_noturno():
    im = Image.new("RGBA", (W * S, H * S))
    dd = ImageDraw.Draw(im)
    NOITE = [(8, 10, 34), (20, 26, 66), (44, 48, 104), (92, 78, 128), (150, 100, 130)]
    for y in range(H * S):
        dd.line([(0, y), (W * S, y)], fill=grad(NOITE, y / (C.CHAO_Y * S)) + (255,))
    rnd = random.Random(11)  # gerador próprio: não altera o resto do cenário
    for _ in range(300):
        x, y = rnd.randint(0, W), int(rnd.random() ** 1.5 * 430)
        r = rnd.choice((1, 1, 1, 2, 2, 3))
        br = rnd.randint(150, 255)
        dd.ellipse(box(x - r / 2, y - r / 2, x + r / 2, y + r / 2), fill=(br, br, min(255, br + 20), 255))
        if r == 3:
            halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ImageDraw.Draw(halo).ellipse(box(x - 5, y - 5, x + 5, y + 5), fill=(200, 210, 255, 70))
            im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(2 * S)))
            dd = ImageDraw.Draw(im)
    LUA = (800, 170)
    brilho = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(brilho).ellipse(box(LUA[0] - 190, LUA[1] - 190, LUA[0] + 190, LUA[1] + 190), fill=(170, 190, 255, 120))
    im.alpha_composite(brilho.filter(ImageFilter.GaussianBlur(50 * S)))
    dd = ImageDraw.Draw(im)
    dd.ellipse(box(LUA[0] - 58, LUA[1] - 58, LUA[0] + 58, LUA[1] + 58), fill=(238, 238, 222, 255))
    for ox, oy, rr in ((-20, -16, 14), (18, 10, 18), (-8, 26, 9), (26, -24, 8)):
        dd.ellipse(box(LUA[0] + ox - rr, LUA[1] + oy - rr, LUA[0] + ox + rr, LUA[1] + oy + rr), fill=(206, 208, 196, 255))
    for cx, cy, w, h in [(190, 120, 300, 70), (520, 70, 240, 54), (890, 150, 280, 60), (1120, 60, 220, 46)]:
        nuvem(cx, cy, w, h, im, (28, 32, 74, 170), (74, 82, 134, 215))
    return im


def tingir(rgb):
    """Escurece e azula o cenário (tudo que não é céu)."""
    r, g, b = rgb.split()
    r = r.point(lambda v: int(v * 0.30))
    g = g.point(lambda v: int(v * 0.36))
    b = b.point(lambda v: min(255, int(v * 0.55) + 22))
    return Image.merge("RGB", (r, g, b))


def acabamento(base, nome, forca):
    """Vinheta (bordas mais escuras) e grava em imagens/batalha/<nome>."""
    final = base.resize((W, H), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse([-W * 0.18, -H * 0.25, W * 1.18, H * 1.25], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(120))
    sombra = Image.new("RGBA", (W, H), (20, 8, 24, 0))
    sombra.putalpha(mask.point(lambda v: int((255 - v) * forca)))
    final.alpha_composite(sombra)
    final.convert("RGB").save(os.path.join(OUT, nome))


cenario = ImageChops.difference(img.convert("RGB"), ceu_dia.convert("RGB")).convert("L").point(lambda v: 255 if v > 0 else 0)
noite = ceu_noturno().convert("RGB")
noite.paste(tingir(img.convert("RGB")), mask=cenario)
acabamento(noite, "fundo_noite.png", 0.5)

# ---------- vinheta (dia) ----------
acabamento(img, "fundo_batalha.png", 0.55)

# ---------- porta fechada (sobreposição) ----------
PS = 4
pw_, ph_ = C.PORTA[2], C.PORTA[3]
pimg = Image.new("RGBA", (pw_ * PS, ph_ * PS), (0, 0, 0, 0))
pd = ImageDraw.Draw(pimg)
mask_p = Image.new("L", pimg.size, 0)
md = ImageDraw.Draw(mask_p)
md.ellipse([0, 0, pw_ * PS, pw_ * PS], fill=255)
md.rectangle([0, pw_ * PS // 2, pw_ * PS, ph_ * PS], fill=255)
tab = Image.new("RGBA", pimg.size)
td = ImageDraw.Draw(tab)
n_tab = 5
for k in range(n_tab):
    x0 = k * pw_ * PS // n_tab
    x1 = (k + 1) * pw_ * PS // n_tab
    base = mix((128, 84, 48), (84, 52, 32), k / (n_tab - 1))
    td.rectangle([x0, 0, x1, ph_ * PS], fill=base + (255,))
    td.line([(x1, 0), (x1, ph_ * PS)], fill=(40, 24, 16, 255), width=2 * PS)
for fy in (0.38, 0.78):  # ferragens
    yy = int(ph_ * PS * fy)
    td.rectangle([0, yy - 3 * PS, pw_ * PS, yy + 3 * PS], fill=(62, 62, 72, 255))
    for k in range(1, n_tab):
        td.ellipse([k * pw_ * PS // n_tab - 3 * PS, yy - 2 * PS, k * pw_ * PS // n_tab + 3 * PS, yy + 2 * PS],
                   fill=(150, 150, 160, 255))
td.ellipse([pw_ * PS * 0.58, ph_ * PS * 0.56, pw_ * PS * 0.58 + 9 * PS, ph_ * PS * 0.56 + 9 * PS],
           outline=(214, 180, 90, 255), width=2 * PS)
pimg.paste(tab, (0, 0), mask_p)
pd.line([(0, pw_ * PS // 2), (0, ph_ * PS)], fill=(30, 20, 16, 255), width=2 * PS)
pimg.resize((pw_, ph_), Image.LANCZOS).save(os.path.join(OUT, "porta.png"))
print("ok")
