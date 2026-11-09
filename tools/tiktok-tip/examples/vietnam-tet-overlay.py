import os, math, sys, datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
DUR = 32.4
OUT = 'ov'
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

CREAM = (246, 239, 224); GOLD = (214, 176, 92); GREEN = (22, 48, 40)
RED = (200, 45, 45); OPENG = (70, 150, 85); DARK = (15, 25, 20)

def ease(x):
    x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def back(x):
    x = max(0, min(1, x)); c1 = 1.7; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def alpha_img(im, a):
    if a >= 1: return im
    im = im.copy(); al = im.split()[3].point(lambda v: int(v * max(0, a))); im.putalpha(al); return im
def text_center(d, y, txt, f, fill, stroke=0, sfill=DARK, cx=W/2):
    w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
def scaled(im, w=None, h=None):
    if w: h = int(im.height * w / im.width)
    else: w = int(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)
def pop_paste(layer, im, cx, cy, s, a=1.0, rot=0):
    if s <= 0.02 or a <= 0: return
    i = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if rot: i = i.rotate(rot, resample=Image.BICUBIC, expand=True)
    layer.alpha_composite(alpha_img(i, a), (int(cx - i.width / 2), int(cy - i.height / 2)))

S = {k: Image.open(f'sym/{k}.png').convert('RGBA') for k in ['flag', 'flagwave', 'lantern', 'scooter']}
LANT = scaled(S['lantern'], h=210)
LANT_S = scaled(S['lantern'], h=70)
SCOOT = scaled(S['scooter'], h=120)
FLAG = scaled(S['flag'], w=96)

# ---------- subtitles ----------
SUBS = [
    (7.28, 8.40, 'Dan is het Tet,'), (8.48, 10.30, 'het Vietnamese nieuwjaar.'),
    (10.46, 12.35, 'Van 4 tot en met 10 februari'), (12.38, 13.15, 'is het feest.'),
    (13.28, 15.60, 'Veel winkels en restaurants gaan dan dicht'),
    (15.76, 17.95, 'en treinen, bussen en hotels'), (18.06, 20.40, 'zitten vol en worden een stuk duurder.'),
    (20.66, 21.50, 'Mijn tip:'), (21.60, 23.35, 'kom in de twee weken ervoor.'),
    (23.44, 25.00, 'Dan zie je de bloemenmarkten'), (25.00, 26.02, 'en de versierde straten'),
    (26.04, 27.95, 'en is alles nog gewoon open.'),
    (28.14, 29.92, 'Stuur dit eventjes naar je reismaatje'), (29.94, 31.30, 'en sla even op.'),
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
            d = ImageDraw.Draw(img); lines = wrap(d, txt, FSUB, 880)
            y = 1300 - (len(lines) - 1) * 36; pop = ease((t - a) / 0.12)
            for ln in lines:
                text_center(d, y + (1 - pop) * 10, ln, FSUB, CREAM, 6); y += 72

# ---------- hook ----------
F_H1 = font(LORA, 112, True); F_H2 = font(INTER_XB, 88)
def draw_hook(img, t):
    if t >= 4.75: return
    fade = 1 - ease((t - 4.5) / 0.25) if t > 4.5 else 1
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    # hanging lanterns swinging
    for cx, ph in [(150, 0), (930, 1.3)]:
        sw = math.sin(t * 2.2 + ph) * 6
        d.line([(cx, 0), (cx, 60)], fill=GOLD, width=3)
        pop_paste(layer, LANT, cx, 60 + LANT.height / 2, 1, 1, sw)
    text_center(d, 420, 'VIETNAM', F_H1, CREAM, 7)
    text_center(d, 545, 'IN FEBRUARI?', F_H1, CREAM, 7)
    ln = 'CHECK DEZE DATUM'; w = d.textlength(ln, font=F_H2); y = 710
    d.rounded_rectangle([(W - w) / 2 - 28, y - 8, (W + w) / 2 + 28, y + 108], 18, fill=GOLD)
    d.text(((W - w) / 2, y), ln, font=F_H2, fill=GREEN)
    s = 0.9 + 0.1 * back(t / 0.35)
    if s != 1:
        layer = layer.resize((int(W * s), int(H * s)), Image.LANCZOS)
        nl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); nl.paste(layer, ((W - layer.width) // 2, int(560 - 560 * s))); layer = nl
    img.alpha_composite(alpha_img(layer, fade))

# ---------- date card ----------
F_D1 = font(INTER_XB, 150); F_D2 = font(LORA, 64, True); F_D3 = font(INTER_SB, 40)
def draw_date(img, t):
    a0, a1 = 4.72, 10.35
    if not (a0 <= t <= a1): return
    fade = 1 - ease((t - (a1 - 0.3)) / 0.3)
    s = back((t - a0) / 0.35)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    # calendar page
    x0, y0, x1, y1 = 230, 330, 850, 860
    d.rounded_rectangle([x0, y0, x1, y1], 40, fill=CREAM)
    d.rounded_rectangle([x0, y0, x1, y0 + 150], 40, fill=RED)
    d.rectangle([x0, y0 + 110, x1, y0 + 150], fill=RED)
    text_center(d, y0 + 30, 'FEBRUARI 2027', font(INTER_XB, 64), (255, 255, 255), cx=(x0 + x1) / 2)
    text_center(d, y0 + 175, '6', font(INTER_XB, 280), GREEN, cx=(x0 + x1) / 2)
    text_center(d, y0 + 470, 'zaterdag', F_D3, GREEN, cx=(x0 + x1) / 2)
    for rx in (x0 + 130, x1 - 130):
        d.rounded_rectangle([rx - 14, y0 - 30, rx + 14, y0 + 30], 10, fill=GOLD)
    # Tet label from 7.96
    k = ease((t - 7.96) / 0.3)
    if k > 0:
        lab = 'Tet: Vietnamees nieuwjaar'; w = d.textlength(lab, font=F_D2)
        d.rounded_rectangle([(W - w) / 2 - 30, 905, (W + w) / 2 + 30, 1010], 22, fill=GREEN + (int(235 * k),))
        d.text(((W - w) / 2, 918), lab, font=F_D2, fill=CREAM + (int(255 * k),))
        pop_paste(layer, LANT_S, (W + w) / 2 + 20, 905, back((t - 8.0) / 0.35), k, math.sin(t * 3) * 8)
    big = layer.resize((max(1, int(W * s)), max(1, int(H * s))), Image.LANCZOS)
    nl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); nl.paste(big, ((W - big.width) // 2, int(640 - 640 * s)))
    img.alpha_composite(alpha_img(nl, fade))

# ---------- calendar strip ----------
DAYS = [datetime.date(2027, 1, 20) + datetime.timedelta(i) for i in range(23)]  # 20 jan .. 11 feb
PX0, PY0, PX1, PY1 = 40, 270, 1040, 700
CX0 = 70; CW = (1010 - CX0) / len(DAYS); CY = 420; CH = 70
F_NUM = font(INTER_B, 26); F_MON = font(INTER_XB, 28); F_TAG = font(INTER_XB, 34); F_PT = font(INTER_XB, 44)
def xr(d0, d1):
    i0 = DAYS.index(d0); i1 = DAYS.index(d1)
    return CX0 + i0 * CW, CX0 + (i1 + 1) * CW
def draw_cal(img, t):
    T0, T1 = 10.40, 23.35
    if t < T0 or t > T1 + 0.3: return
    a = ease((t - T0) / 0.3) * (1 - ease((t - T1) / 0.3))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.rounded_rectangle([PX0, PY0, PX1, PY1], 34, fill=GREEN + (228,))
    d.text((PX0 + 36, PY0 + 24), 'Januari  →  februari 2027', font=F_PT, fill=CREAM)
    d.text((CX0, CY - 44), 'JAN', font=F_MON, fill=GOLD)
    fx, _ = xr(datetime.date(2027, 2, 1), datetime.date(2027, 2, 1)); d.text((fx, CY - 44), 'FEB', font=F_MON, fill=GOLD)
    # red Tet range 4-10 feb
    if t >= 10.9:
        k = ease((t - 10.9) / 0.7)
        rx0, rx1 = xr(datetime.date(2027, 2, 4), datetime.date(2027, 2, 10))
        d.rounded_rectangle([rx0, CY - 6, rx0 + (rx1 - rx0) * k, CY + CH + 6], 14, fill=RED)
    # green best range 22 jan - 3 feb
    if t >= 21.6:
        k = ease((t - 21.6) / 0.9)
        gx0, gx1 = xr(datetime.date(2027, 1, 22), datetime.date(2027, 2, 3))
        d.rounded_rectangle([gx0, CY - 6, gx0 + (gx1 - gx0) * k, CY + CH + 6], 14, fill=OPENG)
    for i, dd in enumerate(DAYS):
        x = CX0 + i * CW
        if dd.day == 1 and i > 0: d.line([(x, CY - 10), (x, CY + CH + 10)], fill=GOLD, width=3)
        tx = str(dd.day); w = d.textlength(tx, font=F_NUM)
        d.text((x + CW / 2 - w / 2, CY + CH / 2 - 15), tx, font=F_NUM, fill=CREAM)
    # Tet day marker (6 feb)
    if t >= 10.9:
        mx0, mx1 = xr(datetime.date(2027, 2, 6), datetime.date(2027, 2, 6))
        pop_paste(layer, LANT_S, (mx0 + mx1) / 2, CY - 50, back((t - 11.4) / 0.35), 1, math.sin(t * 3) * 8)
    # tags under red bar
    rx0, rx1 = xr(datetime.date(2027, 2, 4), datetime.date(2027, 2, 10)); rcx = (rx0 + rx1) / 2
    tags = []
    if t >= 11.5: tags.append(('TET', 11.5))
    if t >= 14.9: tags.append(('VEEL DICHT', 14.9))
    if t >= 19.3: tags.append(('VOL & DUURDER', 19.3))
    ty = CY + CH + 24
    for txt, st in tags:
        k = ease((t - st) / 0.25); w = d.textlength(txt, font=F_TAG)
        cx = min(max(rcx, w / 2 + 70), 1010 - w / 2 - 10)
        d.rounded_rectangle([cx - w / 2 - 16, ty, cx + w / 2 + 16, ty + 50], 12, fill=RED + (int(255 * k),))
        d.text((cx - w / 2, ty + 5), txt, font=F_TAG, fill=(255, 255, 255, int(255 * k))); ty += 60
    if t >= 21.9:
        gx0, gx1 = xr(datetime.date(2027, 1, 22), datetime.date(2027, 2, 3)); gcx = (gx0 + gx1) / 2
        k = ease((t - 21.9) / 0.25); txt = 'BESTE PERIODE'; w = d.textlength(txt, font=F_TAG)
        d.rounded_rectangle([gcx - w / 2 - 16, CY + CH + 24, gcx + w / 2 + 16, CY + CH + 74], 12, fill=OPENG + (int(255 * k),))
        d.text((gcx - w / 2, CY + CH + 29), txt, font=F_TAG, fill=(255, 255, 255, int(255 * k)))
        # scooter rides along the green range
        p = ease((t - 21.7) / 1.4)
        sx = gx0 + 60 + p * (gx1 - gx0 - 260)
        pop_paste(layer, SCOOT, sx, CY - 62 + math.sin(t * 16) * 2, 1, ease((t - 21.6) / 0.2))
    img.alpha_composite(alpha_img(layer, a))

# ---------- best period badge ----------
F_BADGE = font(INTER_XB, 54)
def draw_badge(img, t):
    a0, a1 = 23.45, 27.9
    if not (a0 <= t <= a1): return
    k = back((t - a0) / 0.3); fade = 1 - ease((t - (a1 - 0.25)) / 0.25)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    l1 = 'BESTE PERIODE'; l2 = '22 JAN T/M 3 FEB'
    w = max(d.textlength(l1, font=F_TAG), d.textlength(l2, font=F_BADGE))
    d.rounded_rectangle([(W - w) / 2 - 36, 330, (W + w) / 2 + 36, 500], 26, fill=GOLD)
    text_center(d, 348, l1, F_TAG, GREEN); text_center(d, 400, l2, F_BADGE, GREEN)
    pop_paste(layer, FLAG, (W + w) / 2 + 30, 335, 0.8, 1)
    s = max(0.01, k)
    lay = layer.crop((0, 280, W, 560)).resize((max(1, int(W * s)), max(1, int(280 * s))), Image.LANCZOS)
    img.alpha_composite(alpha_img(lay, fade), ((W - lay.width) // 2, 420 - lay.height // 2))

# ---------- end card ----------
F_E1 = font(LORA, 64, True); F_E2 = font(INTER_XB, 58); F_E3 = font(INTER_SB, 40)
def draw_end(img, t):
    if t < 28.1: return
    k = ease((t - 28.1) / 0.4)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.rounded_rectangle([90, 300, 990, 700], 36, fill=GREEN + (232,))
    text_center(d, 345, 'Meer van dit soort tips?', F_E1, CREAM)
    w = d.textlength('GRATIS REISGIDS', font=F_E2)
    d.rounded_rectangle([(W - w) / 2 - 30, 470, (W + w) / 2 + 30, 560], 18, fill=GOLD)
    text_center(d, 482, 'GRATIS REISGIDS', F_E2, GREEN)
    text_center(d, 600, 'link in bio  ·  WayFare Reizen', F_E3, CREAM)
    img.alpha_composite(alpha_img(layer, k), (0, int((1 - k) * 30)))

# ---------- logo ----------
_l = Image.open('logo.png').convert('RGBA'); _l = _l.crop(_l.getbbox())
LOGO = _l.resize((220, int(_l.height * 220 / _l.width)), Image.LANCZOS)
SH = Image.new('RGBA', LOGO.size, (10, 20, 15, 0)); SH.putalpha(LOGO.split()[3].point(lambda v: int(v * 0.55))); SH = SH.filter(ImageFilter.GaussianBlur(6))
def draw_logo(img, t):
    if t < 4.6 or t > 28.2: return
    a = 0.8 * ease((t - 4.6) / 0.4) * (1 - ease((t - 28.0) / 0.2))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); layer.alpha_composite(SH, (58, 154)); layer.alpha_composite(LOGO, (56, 150))
    img.alpha_composite(alpha_img(layer, a))

def frame(t):
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_hook(img, t); draw_date(img, t); draw_cal(img, t); draw_badge(img, t); draw_end(img, t); draw_sub(img, t); draw_logo(img, t)
    return img

if __name__ == '__main__':
    N = int(DUR * FPS)
    part = int(sys.argv[1]); parts = int(sys.argv[2])
    for i in range(N):
        if i % parts != part: continue
        frame(i / FPS).save(f'{OUT}/{i:05d}.png', compress_level=1)
