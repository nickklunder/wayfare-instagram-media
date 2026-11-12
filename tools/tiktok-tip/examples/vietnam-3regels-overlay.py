import os, sys, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------- config ----------------
W, H, FPS = 1080, 1920, 30
CFG = json.load(open(os.environ.get('CFG', 'timing.json')))
T = CFG['T']            # section times
WORDS = CFG['words']    # [[word, start, end], ...] (ondertitel-spelling)
DUR = CFG['dur']
OUT = os.environ.get('OUT', 'ov')
os.makedirs(OUT, exist_ok=True)

INTER_BL = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
INTER_XB = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
INTER_B = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
LORA = '/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf'
_fc = {}
def font(p, s):
    k = (p, s)
    if k not in _fc:
        f = ImageFont.truetype(p, s)
        if p == LORA:
            try: f.set_variation_by_name('Bold')
            except Exception: pass
        _fc[k] = f
    return _fc[k]

CREAM = (246, 239, 224); GOLD = (214, 176, 92); GREEN = (22, 48, 40)
RED = (200, 45, 45); OPENG = (70, 150, 85); DARK = (12, 22, 18)

def clamp(x): return max(0.0, min(1.0, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def back(x):
    x = clamp(x); c1 = 2.2; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def alpha_img(im, a):
    if a >= 1: return im
    im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * max(0, a)))); return im

def shadowed(im, r=10, off=(0, 8), op=150):
    pad = r * 3
    base = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    a = im.split()[3].point(lambda v: v * op // 255)
    blk = Image.new('RGBA', im.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.alpha_composite(blk, (pad + off[0], pad + off[1]))
    sh = sh.filter(ImageFilter.GaussianBlur(r))
    base.alpha_composite(sh); base.alpha_composite(im, (pad, pad))
    return base

def paste_c(layer, im, cx, cy, s=1.0, a=1.0, rot=0):
    if s <= 0.02 or a <= 0.01: return
    i = im if abs(s - 1) < 1e-3 else im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if rot: i = i.rotate(rot, resample=Image.BICUBIC, expand=True)
    layer.alpha_composite(alpha_img(i, a), (int(cx - i.width / 2), int(cy - i.height / 2)))

def text_img(txt, f, fill, stroke=0, sfill=DARK, pad=0):
    d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    l, t, r, b = d0.textbbox((0, 0), txt, font=f, stroke_width=stroke)
    im = Image.new('RGBA', (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im

def pill(txt, f, bg, fg, padx=34, pady=18, radius=None, outline=None):
    ti = text_img(txt, f, fg)
    w, h = ti.width + padx * 2, ti.height + pady * 2
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius or h // 2, fill=bg, outline=outline, width=4 if outline else 0)
    im.alpha_composite(ti, (padx, pady))
    return im

# ---------------- static assets ----------------
SYM = '/home/claude/wayfare-instagram-media/tools/tiktok-tip/symbols/vietnam/'
LOGO = Image.open('/home/claude/wayfare-instagram-media/2026/brand/logo-creme-tiktok.png').convert('RGBA')
LOGO = LOGO.resize((220, int(LOGO.height * 220 / LOGO.width)), Image.LANCZOS)
LOGO = shadowed(alpha_img(LOGO, 0.85), r=6, off=(0, 3), op=120)
FLAG = Image.open(SYM + 'flag.png').convert('RGBA').resize((92, 92), Image.LANCZOS)

# hook
H1 = shadowed(text_img('VIETNAM', font(LORA, 150), CREAM, 6), r=14, op=170)
H1b = shadowed(text_img('2027', font(LORA, 150), GOLD, 6), r=14, op=170)
H2 = shadowed(pill('3 NIEUWE REGELS', font(INTER_BL, 76), GOLD, GREEN, padx=40, pady=22, radius=18), r=12)
H3 = shadowed(pill('#3 KOST TOT $190', font(INTER_BL, 64), RED, CREAM, padx=36, pady=20, radius=16, outline=CREAM), r=12)

# tracker
TR_LABELS = ['VISUM', 'QR-KAART', 'VAPE']
def tracker_pill(i, state):
    f = font(INTER_BL, 34)
    lab = f'{i+1}  {TR_LABELS[i]}'
    if state == 'active': return pill(lab, f, GOLD, GREEN, padx=26, pady=14)
    if state == 'done':   return pill(lab, f, (22, 48, 40, 235), CREAM, padx=26, pady=14, outline=GOLD)
    return pill(lab, f, (12, 22, 18, 150), (246, 239, 224, 150), padx=26, pady=14)
TRP = {(i, s): shadowed(tracker_pill(i, s), r=6, off=(0, 3), op=110) for i in range(3) for s in ('idle', 'active', 'done')}

# section headers
def section_header(n, title, col=CREAM):
    num = Image.new('RGBA', (150, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(num)
    d.ellipse((0, 0, 149, 149), fill=GOLD, outline=CREAM, width=5)
    ni = text_img(str(n), font(INTER_BL, 96), GREEN)
    num.alpha_composite(ni, ((150 - ni.width) // 2, (150 - ni.height) // 2 - 2))
    tl = [text_img(t, font(INTER_BL, 70), col, 7) for t in title]
    tw = max(t.width for t in tl); th = sum(t.height for t in tl) + 10 * (len(tl) - 1)
    im = Image.new('RGBA', (150 + 28 + tw, max(150, th)), (0, 0, 0, 0))
    im.alpha_composite(num, (0, (im.height - 150) // 2))
    y = (im.height - th) // 2
    for t in tl: im.alpha_composite(t, (178, y)); y += t.height + 10
    return shadowed(im, r=14, op=170)
SEC = {
    1: section_header(1, ['GEEN VISUM', 'NODIG']),
    2: section_header(2, ['GRATIS', 'AANKOMSTKAART']),
    3: section_header(3, ['VAPE =', 'VERBODEN']),
}
# stickers
ST = {
    'eur0': shadowed(pill('€0', font(INTER_BL, 110), OPENG, CREAM, padx=40, pady=14, radius=26, outline=CREAM), r=12),
    'nep': shadowed(pill('PAS OP: NEPSITES', font(INTER_BL, 56), RED, CREAM, padx=32, pady=18, radius=14, outline=CREAM), r=12),
    '45': shadowed(pill('45 DAGEN · VAKANTIE', font(INTER_BL, 46), (22, 48, 40, 240), GOLD, padx=30, pady=16, radius=14, outline=GOLD), r=10),
    '72': shadowed(pill('PAS 72 UUR VOOR JE LANDT', font(INTER_BL, 50), GOLD, GREEN, padx=32, pady=18, radius=14), r=12),
    'qr': None,
    '190': shadowed(pill('BOETE TOT $190', font(INTER_BL, 72), RED, CREAM, padx=40, pady=22, radius=18, outline=CREAM), r=14),
    'kwijt': shadowed(pill('+ JE VAPE KWIJT', font(INTER_BL, 50), (22, 48, 40, 240), CREAM, padx=30, pady=16, radius=14, outline=RED), r=10),
}
def qr_icon(sz=230):
    im = Image.new('RGBA', (sz, sz), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, sz - 1, sz - 1), 28, fill=CREAM, outline=GOLD, width=8)
    m = 26; cell = (sz - 2 * m) / 9
    import random; rnd = random.Random(7)
    grid = [[rnd.random() < 0.5 for _ in range(9)] for _ in range(9)]
    def finder(x, y):
        for i in range(3):
            for j in range(3): grid[y + j][x + i] = True
    for (x, y) in [(0, 0), (6, 0), (0, 6)]: finder(x, y)
    for y in range(9):
        for x in range(9):
            if grid[y][x]:
                d.rectangle((m + x * cell, m + y * cell, m + (x + 1) * cell - 1, m + (y + 1) * cell - 1), fill=GREEN)
    for (x, y) in [(0, 0), (6, 0), (0, 6)]:
        d.rectangle((m + (x + 1) * cell, m + (y + 1) * cell, m + (x + 2) * cell - 1, m + (y + 2) * cell - 1), fill=CREAM)
    return shadowed(im.rotate(-6, resample=Image.BICUBIC, expand=True), r=14)
ST['qr'] = qr_icon()

# CTA
CTA1 = shadowed(text_img('WELKE WIST JIJ', font(LORA, 92), CREAM, 6), r=12, op=170)
CTA1b = shadowed(text_img('NOG NIET?', font(LORA, 92), GOLD, 6), r=12, op=170)
def num_btn(n):
    im = Image.new('RGBA', (170, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 169, 169), 40, fill=GOLD, outline=CREAM, width=6)
    t = text_img(str(n), font(INTER_BL, 110), GREEN)
    im.alpha_composite(t, ((170 - t.width) // 2, (170 - t.height) // 2 - 4))
    return shadowed(im, r=12)
BTN = [num_btn(i) for i in (1, 2, 3)]
def typ_label():
    t = text_img('TYP HET IN DE REACTIES', font(INTER_BL, 50), CREAM, 6)
    im = Image.new('RGBA', (t.width, t.height + 70), (0, 0, 0, 0)); im.alpha_composite(t, (0, 0))
    d = ImageDraw.Draw(im); cx = t.width // 2; y0 = t.height + 12
    d.polygon([(cx - 26, y0), (cx + 26, y0), (cx, y0 + 50)], fill=GOLD, outline=DARK)
    return shadowed(im, r=10)
TYP = typ_label()

# end card
def end_card():
    w, h = 900, 520
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(22, 48, 40, 238), outline=GOLD, width=4)
    y = 54
    for txt, f, c in [('Ken je iemand die vapet?', font(LORA, 64), CREAM), ('STUUR DIT DOOR', font(INTER_BL, 76), GOLD)]:
        ti = text_img(txt, f, c); im.alpha_composite(ti, ((w - ti.width) // 2, y)); y += ti.height + 30
    y += 26
    gp = pill('GRATIS REISGIDS', font(INTER_BL, 54), GOLD, GREEN, padx=36, pady=18, radius=14)
    im.alpha_composite(gp, ((w - gp.width) // 2, y)); y += gp.height + 26
    ti = text_img('link in bio  ·  WayFare Reizen', font(INTER_B, 38), CREAM)
    im.alpha_composite(ti, ((w - ti.width) // 2, y))
    return shadowed(im, r=18, op=160)
END = end_card()

# ---------------- subtitles (karaoke chunks) ----------------
def make_chunks(words, maxw=3, maxc=20):
    chunks, cur = [], []
    for w in words:
        if w[1] < T['s1'] - 0.05: continue      # geen ondertitels tijdens de hook
        cur.append(w)
        txt = ' '.join(x[0] for x in cur)
        end_sent = w[0][-1] in '.?!:'
        if len(cur) >= maxw or len(txt) >= maxc or end_sent:
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        st = c[0][1]; en = c[-1][2]
        nxt = chunks[i + 1][0][1] if i + 1 < len(chunks) else en + 0.6
        out.append((st, min(nxt, en + 0.6), c))
    return out
CHUNKS = make_chunks(WORDS)
SUBF = font(INTER_BL, 68)
def sub_img(chunk, t):
    parts = []
    for w, s, e in chunk:
        active = s - 0.03 <= t < e + 0.08
        parts.append(text_img(w.upper(), SUBF, GOLD if active else CREAM, 8))
    sp = 20
    tw = sum(p.width for p in parts) + sp * (len(parts) - 1); th = max(p.height for p in parts)
    if tw > 880:
        # twee regels
        half = len(parts) // 2 + len(parts) % 2
        rows = [parts[:half], parts[half:]]
    else:
        rows = [parts]
    rw = [sum(p.width for p in r) + sp * (len(r) - 1) for r in rows]
    im = Image.new('RGBA', (max(rw), th * len(rows) + 10 * (len(rows) - 1)), (0, 0, 0, 0))
    y = 0
    for r, wdt in zip(rows, rw):
        x = (im.width - wdt) // 2
        for p in r: im.alpha_composite(p, (x, y + (th - p.height))); x += p.width + sp
        y += th + 10
    return shadowed(im, r=10, off=(0, 6), op=150)

# ---------------- frame ----------------
def frame(n):
    t = n / FPS
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    s1, s2, s3, cta, endc = T['s1'], T['s2'], T['s3'], T['cta'], T['end']

    # flash bij elke nieuwe sectie
    for ts in (s1, s2, s3, cta):
        dt = t - ts
        if 0 <= dt < 0.16:
            L.alpha_composite(Image.new('RGBA', (W, H), (255, 250, 240, int(150 * (1 - dt / 0.16)))))

    if t < s1:  # ---- HOOK ----
        k = clamp(t / 0.25)
        sc = 0.92 + 0.08 * back(k)
        paste_c(L, H1, W / 2, 560, sc)
        paste_c(L, H1b, W / 2, 715, sc)
        k2 = clamp((t - 0.12) / 0.3)
        paste_c(L, H2, W / 2, 880, 0.8 + 0.2 * back(k2), 1.0 if t > 0 else 1.0, rot=-2)
        if t >= T['hook190']:
            k3 = (t - T['hook190']) / 0.3
            wob = 4 * math.sin((t - T['hook190']) * 9) * max(0, 1 - (t - T['hook190']) / 1.2)
            paste_c(L, H3, W / 2, 1065, back(k3) * 1.0, 1, rot=5 + wob)
        paste_c(L, FLAG, W / 2, 420, 0.9 + 0.1 * back(k))
    else:
        # logo
        L.alpha_composite(LOGO, (56 - 18, 150 - 18))
        # tracker
        if t < cta:
            cur = 0 if t < s2 else (1 if t < s3 else 2)
            ws = [TRP[(i, 'active' if i == cur else ('done' if i < cur else 'idle'))] for i in range(3)]
            gap = 6; tot = sum(w.width for w in ws) + gap * 2
            x = (W - tot) / 2 + 40
            for i, w in enumerate(ws):
                tsec = (s1, s2, s3)[i]
                sc = 1.0 + (0.12 * (1 - ease((t - tsec) / 0.35)) if i == cur else 0)
                paste_c(L, w, x + w.width / 2, 300, sc)
                x += w.width + gap
        # sectie-headers
        for sec, ts, te in ((1, s1, s2), (2, s2, s3), (3, s3, cta)):
            if ts <= t < te:
                k = (t - ts) / 0.35
                paste_c(L, SEC[sec], W / 2, 500, 0.6 + 0.4 * back(k), ease(k * 2))
        # stickers
        def sticker(key, ts, te, cx, cy, rot):
            if ts <= t < te:
                k = (t - ts) / 0.3
                paste_c(L, ST[key], cx, cy, back(k), 1, rot=rot)
        S = T['st']
        sticker('eur0', S['eur0'], s2, W / 2 + 230, 850, 8)
        sticker('45', S['45'], s2, W / 2 - 40, 700, -3)
        sticker('nep', S['nep'], s2, W / 2 - 60, 990, -4)
        sticker('72', S['72'], s3, W / 2, 720, -3)
        sticker('qr', S['qr'], s3, W / 2, 940, 0)
        sticker('190', S['190'], cta, W / 2, 740, -5)
        sticker('kwijt', S['kwijt'], cta, W / 2 + 40, 880, 3)
        # CTA
        if cta <= t < endc:
            k = (t - cta) / 0.3
            paste_c(L, CTA1, W / 2, 470, 0.7 + 0.3 * back(k), ease(k * 2))
            paste_c(L, CTA1b, W / 2, 585, 0.7 + 0.3 * back(k - 0.2), ease(k * 2 - 0.3))
            for i in range(3):
                kb = (t - cta - 0.35 - i * 0.12) / 0.3
                bob = 14 * math.sin((t - cta) * 5.5 - i * 1.1) if t - cta > 0.9 else 0
                paste_c(L, BTN[i], W / 2 + (i - 1) * 210, 780 + bob, back(kb))
            kt = (t - cta - 0.8) / 0.3
            bob = 8 * math.sin((t - cta) * 6)
            paste_c(L, TYP, W / 2, 985 + bob, back(kt))
        if t >= endc:
            k = (t - endc) / 0.4
            paste_c(L, END, W / 2, 760, 0.85 + 0.15 * back(k), ease(k * 1.5))
        # ondertitels
        if t < endc:
            for st, en, ch in CHUNKS:
                if st - 0.02 <= t < en:
                    k = (t - st) / 0.12
                    paste_c(L, sub_img(ch, t), W / 2, 1300, 0.9 + 0.1 * ease(k))
                    break
    return L

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        for ts in sys.argv[2:]:
            frame(round(float(ts) * FPS)).save(f'{OUT}/test_{ts}.png')
    else:
        part, parts = int(sys.argv[1]), int(sys.argv[2])
        total = int(math.ceil(DUR * FPS))
        for n in range(part, total, parts):
            frame(n).save(f'{OUT}/{n:05d}.png', compress_level=1)
