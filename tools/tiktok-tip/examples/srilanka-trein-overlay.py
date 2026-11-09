import os, math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
DUR = 34.75
OUT = 'ov4'
os.makedirs(OUT, exist_ok=True)

INTER_B = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
INTER_XB = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
INTER_SB = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
LORA = '/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf'

def font(p, s, bold=False):
    f = ImageFont.truetype(p, s)
    if bold and p == LORA:
        try: f.set_variation_by_name('Bold')
        except Exception: pass
    return f

CREAM = (246, 239, 224)
GOLD = (214, 176, 92)
GREEN = (22, 48, 40)
RED = (200, 45, 45)
OPENG = (120, 190, 120)

sym = {k: Image.open(f'sym/{k}.png').convert('RGBA') for k in ['tuktuk', 'barrier', 'train', 'rails']}

def ease(x):
    x = max(0, min(1, x)); return 1 - (1 - x) ** 3

def back(x):
    x = max(0, min(1, x)); c1 = 1.7; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def alpha_img(im, a):
    if a >= 1: return im
    im = im.copy(); r, g, b, al = im.split()
    al = al.point(lambda v: int(v * a)); im.putalpha(al); return im

def text_center(d, y, txt, f, fill, stroke=0, sfill=(0, 0, 0)):
    w = d.textlength(txt, font=f)
    d.text(((W - w) / 2, y), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)

# ---------- subtitles (real spelling) ----------
SUBS = [
    (3.52, 5.40, 'De beroemde treinrit van Kandy naar Ella'),
    (5.40, 7.40, 'rijdt namelijk niet helemaal.'),
    (7.57, 9.70, 'Na de cycloon van eind 2025'),
    (9.70, 12.55, 'rijdt deze trein nog steeds niet vanaf Kandy.'),
    (12.81, 14.10, 'Zo doe je het wel:'),
    (14.23, 15.90, 'ga over de weg naar Nanu Oya,'),
    (15.90, 17.60, 'bij Nuwara Eliya.'),
    (17.74, 18.85, 'Daar stap je op.'),
    (18.94, 20.20, 'En het mooiste stuk,'),
    (20.20, 22.80, 'door de theeplantages en over deze brug,'),
    (22.93, 24.40, 'is gewoon weer open.'),
    (24.56, 26.70, 'Check de status vlak voor je reis.'),
    (26.84, 27.70, 'Bewaar dit,'),
    (27.70, 29.40, 'en stuur het naar je reismaatje!'),
]
FSUB = font(INTER_B, 56)

def wrap(d, txt, f, maxw):
    words = txt.split(); lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def draw_sub(img, t):
    for a, b, txt in SUBS:
        if a <= t < b:
            d = ImageDraw.Draw(img)
            lines = wrap(d, txt, FSUB, 880)
            y = 1300 - (len(lines) - 1) * 36
            pop = ease((t - a) / 0.12)
            for ln in lines:
                text_center(d, y + (1 - pop) * 10, ln, FSUB, CREAM, 6, (15, 25, 20))
                y += 72

# ---------- hook ----------
F_H1 = font(LORA, 128, True)
F_H2 = font(INTER_XB, 92)

def draw_hook(img, t):
    if t >= 3.52: return
    fade = 1 - ease((t - 3.25) / 0.27) if t > 3.25 else 1
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    s = 0.9 + 0.1 * back(t / 0.35)
    # line 1
    text_center(d, 360, 'SRI LANKA?', F_H1, CREAM, 7, (15, 25, 20))
    # line 2 boxes
    for i, ln in enumerate(['BOEK DEZE TREIN', 'NOG NIET']):
        w = d.textlength(ln, font=F_H2); y = 540 + i * 128
        x0 = (W - w) / 2 - 26
        d.rounded_rectangle([x0, y - 8, x0 + w + 52, y + 112], 18, fill=GOLD if i == 1 else GREEN + (235,))
        d.text(((W - w) / 2, y), ln, font=F_H2, fill=GREEN if i == 1 else CREAM)
    if s != 1:
        layer = layer.resize((int(W * s), int(H * s)), Image.LANCZOS)
        nl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        nl.paste(layer, ((W - layer.width) // 2, int(620 - 620 * s)))
        layer = nl
    img.alpha_composite(alpha_img(layer, fade))

# ---------- route panel ----------
PX0, PY0, PX1, PY1 = 50, 270, 1030, 660
LY = 520                       # rail line y
XK, XN, XE = 160, 560, 920     # Kandy, Nanu Oya, Ella
F_ST = font(INTER_B, 36)
F_TAG = font(INTER_XB, 30)
F_PT = font(INTER_XB, 44)

def rails_strip(x0, x1):
    r = sym['rails']; h = 30
    rr = r.resize((int(r.width * h / r.height), h), Image.LANCZOS)
    L = int(x1 - x0); strip = Image.new('RGBA', (max(L, 1), h), (0, 0, 0, 0))
    x = 0
    while x < L:
        strip.paste(rr, (x, 0)); x += rr.width - 4
    return strip

RAIL_A = rails_strip(XK, XN)
RAIL_B = rails_strip(XN, XE)

def scaled(name, w=None, h=None):
    im = sym[name]
    if w: h = int(im.height * w / im.width)
    else: w = int(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)

BARRIER = scaled('barrier', w=220)
TUK = scaled('tuktuk', h=112)
TRAIN = scaled('train', w=215)

def draw_route(img, t):
    T0, T1 = 3.6, 19.7
    if t < T0 or t > T1 + 0.3: return
    a = ease((t - T0) / 0.3) * (1 - ease((t - T1) / 0.3))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.rounded_rectangle([PX0, PY0, PX1, PY1], 34, fill=GREEN + (225,))
    d.text((PX0 + 40, PY0 + 26), 'Kandy  →  Ella', font=F_PT, fill=CREAM)
    # draw rails progressively
    prog = ease((t - 3.8) / 1.0)
    full = XE - XK; cut = XK + prog * full
    la = int(max(0, min(cut, XN) - XK)); lb = int(max(0, cut - XN))
    if la > 0: layer.alpha_composite(RAIL_A.crop((0, 0, la, RAIL_A.height)), (XK, LY - 15))
    if lb > 0: layer.alpha_composite(RAIL_B.crop((0, 0, lb, RAIL_B.height)), (XN, LY - 15))
    # closed tint on segment A
    if t >= 7.6:
        k = ease((t - 7.6) / 0.3)
        tint = Image.new('RGBA', (XN - XK, 30), RED + (int(150 * k),))
        layer.alpha_composite(tint, (XK, LY - 15))
    if t >= 17.75:
        k = ease((t - 17.75) / 0.3)
        tint = Image.new('RGBA', (XE - XN, 30), OPENG + (int(110 * k),))
        layer.alpha_composite(tint, (XN, LY - 15))
    # station dots + labels
    for x, name in [(XK, 'Kandy'), (XN, 'Nanu Oya'), (XE, 'Ella')]:
        if cut >= x - 2:
            d.ellipse([x - 16, LY - 16, x + 16, LY + 16], fill=CREAM, outline=GOLD, width=6)
            w = d.textlength(name, font=F_ST)
            d.text((x - w / 2, LY + 34), name, font=F_ST, fill=CREAM)
    # barrier pops on segment A
    if t >= 7.6:
        s = back((t - 7.6) / 0.35)
        if s > 0.02:
            b = BARRIER.resize((max(1, int(BARRIER.width * s)), max(1, int(BARRIER.height * s))), Image.LANCZOS)
            bx = (XK + XN) // 2 - b.width // 2; by = LY - b.height // 2
            layer.alpha_composite(b, (bx, by))
        tag = 'DICHT'; w = d.textlength(tag, font=F_TAG)
        cx = (XK + XN) / 2
        k = ease((t - 7.9) / 0.25)
        if k > 0:
            d.rounded_rectangle([cx - w / 2 - 16, LY + 88, cx + w / 2 + 16, LY + 132], 12, fill=RED + (int(255 * k),))
            d.text((cx - w / 2, LY + 92), tag, font=F_TAG, fill=(255, 255, 255, int(255 * k)))
    if t >= 17.75:
        k = ease((t - 17.9) / 0.25); tag = 'OPEN'; w = d.textlength(tag, font=F_TAG); cx = (XN + XE) / 2
        d.rounded_rectangle([cx - w / 2 - 16, LY + 88, cx + w / 2 + 16, LY + 132], 12, fill=(60, 140, 70, int(255 * k)))
        d.text((cx - w / 2, LY + 92), tag, font=F_TAG, fill=(255, 255, 255, int(255 * k)))
    # tuktuk drives Kandy -> Nanu Oya (above the line)
    if t >= 14.2:
        p = ease((t - 14.3) / 3.0)
        x = XK + p * (XN - XK) - TUK.width / 2
        bob = math.sin(t * 18) * 2
        tk = alpha_img(TUK, ease((t - 14.2) / 0.2))
        if t > 17.75: tk = alpha_img(TUK, 1 - ease((t - 17.75) / 0.3))
        layer.alpha_composite(tk, (int(x), int(LY - 150 + bob)))
    # train drives Nanu Oya -> Ella
    if t >= 17.75:
        p = ease((t - 17.85) / 1.5)
        x = XN + p * (XE - XN) - TRAIN.width * 0.85
        tr = alpha_img(TRAIN, ease((t - 17.75) / 0.2))
        layer.alpha_composite(tr, (int(x), LY - TRAIN.height - 6))
    img.alpha_composite(alpha_img(layer, a))

# ---------- "weer open" badge ----------
F_BADGE = font(INTER_XB, 60)
def draw_open(img, t):
    a0, a1 = 22.9, 24.5
    if not (a0 <= t <= a1): return
    k = back((t - a0) / 0.3); fade = 1 - ease((t - (a1 - 0.25)) / 0.25)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    txt = 'NANU OYA → ELLA: OPEN'
    w = d.textlength(txt, font=F_BADGE)
    d.rounded_rectangle([(W - w) / 2 - 34, 380, (W + w) / 2 + 34, 500], 24, fill=GOLD)
    d.text(((W - w) / 2, 398), txt, font=F_BADGE, fill=GREEN)
    s = max(0.01, k)
    lay = layer.crop((0, 340, W, 540)).resize((max(1, int(W * s)), max(1, int(200 * s))), Image.LANCZOS)
    img.alpha_composite(alpha_img(lay, fade), ((W - lay.width) // 2, 440 - lay.height // 2))

# ---------- end card ----------
F_E1 = font(LORA, 64, True)
F_E2 = font(INTER_XB, 58)
F_E3 = font(INTER_SB, 40)
def draw_end(img, t):
    if t < 26.9: return
    k = ease((t - 26.9) / 0.4)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.rounded_rectangle([90, 300, 990, 700], 36, fill=GREEN + (232,))
    text_center(d, 345, 'Meer van dit soort tips?', F_E1, CREAM)
    w = d.textlength('GRATIS REISGIDS', font=F_E2)
    d.rounded_rectangle([(W - w) / 2 - 30, 470, (W + w) / 2 + 30, 560], 18, fill=GOLD)
    text_center(d, 482, 'GRATIS REISGIDS', F_E2, GREEN)
    text_center(d, 600, 'link in bio  ·  WayFare Reizen', F_E3, CREAM)
    img.alpha_composite(alpha_img(layer, k), (0, int((1 - k) * 30)))


ANCH=[(0,0),(1.59,1.94),(3.52,5.19),(5.40,7.38),(7.57,10.03),(9.70,12.01),(12.81,15.44),(14.23,17.51),(15.90,20.22),(17.74,22.38),(18.94,23.91),(20.20,24.93),(22.93,27.82),(24.56,28.98),(26.84,30.94),(27.70,31.89),(29.15,33.25),(30.6,34.75)]
def to_old(t):
    for (o0,n0),(o1,n1) in zip(ANCH,ANCH[1:]):
        if n0<=t<=n1: return o0+(t-n0)*(o1-o0)/(n1-n0)
    return ANCH[-1][0]
LOGO_IMG=None
import os as _os
if _os.path.exists('logo.png'):
    _l=Image.open('logo.png').convert('RGBA'); _l=_l.crop(_l.getbbox()); LOGO_IMG=_l.resize((220,int(_l.height*220/_l.width)),Image.LANCZOS)
F_LOGO=font(LORA,40,True)
def draw_logo(img,t_old):
    if t_old<3.4 or t_old>26.8: return
    a=0.8*ease((t_old-3.4)/0.4)*(1-ease((t_old-26.6)/0.2))
    layer=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
    if LOGO_IMG is not None:
        sh=Image.new('RGBA',LOGO_IMG.size,(10,20,15,0)); sh.putalpha(LOGO_IMG.split()[3].point(lambda v:int(v*0.55)))
        sh=sh.filter(ImageFilter.GaussianBlur(6)); layer.alpha_composite(sh,(58,154)); layer.alpha_composite(LOGO_IMG,(56,150))
    else:
        d.text((58,150),'WayFare',font=F_LOGO,fill=CREAM,stroke_width=2,stroke_fill=(15,25,20))
        d.text((60,198),'R E I Z E N',font=font(INTER_SB,20),fill=CREAM,stroke_width=1,stroke_fill=(15,25,20))
    img.alpha_composite(alpha_img(layer,a))

N = int(DUR * FPS)
part = int(sys.argv[1]) if len(sys.argv) > 1 else 0
parts = int(sys.argv[2]) if len(sys.argv) > 2 else 1
for i in range(N):
    if i % parts != part: continue
    t = to_old(i / FPS)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_hook(img, t); draw_route(img, t); draw_open(img, t); draw_end(img, t); draw_sub(img, t); draw_logo(img, t)
    img.save(f'{OUT}/{i:05d}.png', compress_level=1)
