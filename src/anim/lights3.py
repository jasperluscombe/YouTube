"""The 9:14 Lights - Part 3: "Lights Out"  (stories/22_lights_part3.json)

    python src/anim/lights3.py [scene numbers]
"""
import json, math, pathlib, random, sys
from multiprocessing import Pool

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import *  # noqa
import lights as L
import lights2 as L2

ROOT = pathlib.Path(__file__).resolve().parents[2]
SID = "22_lights_part3"
OUT = ROOT / "out" / SID
N = 15
SEG = {i: (json.loads((OUT / f"scene_{i:02d}.json").read_text()) if (OUT / f"scene_{i:02d}.json").exists() else [["", 0, 5]])
       for i in range(1, N + 1)}
SP = 430
STARS = [(random.Random(k).uniform(0, W), random.Random(k + 5).uniform(0, 1250), random.Random(k + 9).uniform(0.8, 2.8)) for k in range(900)]


def at(i, k):
    s = SEG[i]
    return s[k][1] if -len(s) <= k < len(s) else s[-1][1]


def clock(ctx, t, label, red=False, y=300, size=200):
    pulse = 1 + (0.06 * math.sin(t * 7) if red else 0)
    ctx.save(); ctx.translate(W / 2, y); ctx.scale(pulse, pulse)
    rgb(ctx, (0, 0, 0), 0.55); rrect(ctx, -270, -125, 540, 250, 30); ctx.fill()
    text(ctx, label, 0, 0, size, (1, 0.3, 0.25) if red else (0.6, 1, 0.7))
    ctx.restore()


def sit_back_pal(ctx, x, y, s, pal):
    hc, hd = pal[0], pal[1]
    rgb(ctx, hc); rrect(ctx, x - 0.13 * s, y - 0.36 * s, 0.26 * s, 0.38 * s, 0.07 * s); ctx.fill()
    rgb(ctx, hd); rrect(ctx, x - 0.2 * s, y - 0.33 * s, 0.08 * s, 0.3 * s, 0.04 * s); ctx.fill()
    rrect(ctx, x + 0.12 * s, y - 0.33 * s, 0.08 * s, 0.3 * s, 0.04 * s); ctx.fill()
    rgb(ctx, hc); ctx.arc(x, y - 0.45 * s, 0.105 * s, 0, 6.283); ctx.fill()
    rgb(ctx, hd, 0.6); ctx.arc(x, y - 0.44 * s, 0.06 * s, 0, 6.283); ctx.fill()


def street(ctx, t, off, lamps_on_from=None):
    """Dark street, parallax. lamps_on_from: x (screen) left of which lamps are lit (they chase you)."""
    L.night_sky(ctx, t, 1250, moon=False)
    draw_skyline(ctx, L.CITY_FAR, 1150, hexc("#0d1020"), offset=(off * 0.3) % 400 - 200)
    draw_skyline(ctx, L.CITY_NEAR, 1250, hexc("#07080f"), offset=(off * 0.6) % 600 - 300)
    vgrad(ctx, 1250, H, [(0, hexc("#15161b")), (1, hexc("#060608"))])
    rgb(ctx, (0.8, 0.75, 0.4), 0.4)
    for k in range(8):
        ctx.rectangle((k * 220 + off) % (W + 220) - 110, 1400, 120, 10); ctx.fill()
    for k in range(6):
        x = (k * 300 + off * 1.0) % (W + 300) - 150
        lit = lamps_on_from is not None and x < lamps_on_from
        rgb(ctx, hexc("#1c1d22")); ctx.rectangle(x - 6, 820, 12, 440); ctx.fill()
        ctx.rectangle(x - 6, 820, 70, 10); ctx.fill()
        if lit:
            ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
            cone(ctx, x + 60, 835, math.pi / 2, 0.6, 600, (1, 0.85, 0.55), 0.35)
            glow(ctx, x + 60, 835, 110, (1, 0.85, 0.55), 0.9)
            ctx.restore()


# ------------------------------------------------------------------ scenes
def s1(ctx, t, d):
    L2.lobby(ctx, t, outside_fig=True)
    L2.desk(ctx, t, 230)
    person(ctx, 380, 1250, SP, "idle", face=1, breathe=math.sin(t * 4))
    dog(ctx, 160, 1250, 130, "sit", face=1, head_up=1, wag=math.sin(t * 6) * 0.5)
    clock(ctx, t, "9:10" if t < at(1, -1) else "9:10", y=330)
    text(ctx, "4 MINUTES", W / 2, 500, 70, (1, 0.8, 0.5), prog(t, at(1, -2), at(1, -2) + 0.3), outline=8)
    vignette(ctx, 0.85); grain(ctx, t); fade(ctx, t, d, 0.0, 0.1)


def s2(ctx, t, d):
    op = ease(prog(t, 0.3, 1.2))
    L2.lobby(ctx, t, glass_open=op)
    run = prog(t, at(2, 1), at(2, 1) + 1.2)
    jump = abs(math.sin(t * 7)) * 50 * prog(t, at(2, 1) + 1.2, d)
    dog(ctx, lerp(250, 640, ease(run)), 1250 - jump, 150, "trot" if run < 1 else "stand", phase=t * 12, face=1,
        wag=math.sin(t * 16), head_up=1)
    person(ctx, 820, 1250, SP, "idle", face=-1, pal=MARA, arm_f=(0.6 + 0.4 * prog(t, at(2, -1), d), 0.6),
           breathe=math.sin(t * 3))
    person(ctx, 150, 1250, SP, "idle", face=1)
    vignette(ctx, 0.8); grain(ctx, t); fade(ctx, t, d, 0.1, 0.1)


def s3(ctx, t, d):
    L2.lobby(ctx, t, rain=True)
    talk = math.sin(t * 7) * (0.5 + 0.5 * math.sin(t * 2.3))
    person(ctx, 640, 1250, SP, "idle", face=-1, pal=MARA, head_turn=0.4 * talk,
           arm_f=(1.0 + 0.5 * talk, -0.8 + 0.4 * math.sin(t * 5)), arm_b=(0.6 - 0.3 * talk, 0.9))
    person(ctx, 330, 1250, SP, "idle", face=1, breathe=math.sin(t * 2))
    dog(ctx, 480, 1250, 120, "sit", face=-1, head_up=0.7, wag=math.sin(t * 5))
    text(ctx, "MARA", 640, 700, 70, (0.5, 0.9, 0.9), prog(t, at(3, 0), at(3, 0) + 0.4), outline=8)
    vignette(ctx, 0.8); grain(ctx, t); fade(ctx, t, d, 0.1, 0.1)


GREY = ((0.45, 0.45, 0.48), (0.35, 0.35, 0.38), (0.25, 0.25, 0.28), (0.2, 0.2, 0.22))


def s4(ctx, t, d):
    L.night_sky(ctx, t, 1250, moon=False)
    L.city_lights(ctx, L.CITY_NEAR, 1250, hexc("#0a0b12"), 0.0, t)
    rgb(ctx, hexc("#0b0e1a")); ctx.rectangle(640, 560, 200, 690); ctx.fill()
    pulse = 0.8 + 0.2 * math.sin(t * 4)
    glow(ctx, 740, 760, 260, (1, 0.8, 0.45), 0.7 * pulse)
    rgb(ctx, (1, 0.86, 0.55)); ctx.rectangle(700, 700, 80, 110); ctx.fill()
    vgrad(ctx, 1250, H, [(0, hexc("#17181d")), (1, hexc("#08080a"))])
    w = prog(t, 0.3, at(4, -1))
    a = 1 - prog(t, at(4, 2), at(4, 2) + 1.0)
    if a > 0:
        ctx.push_group()
        person(ctx, lerp(150, 620, w), 1250, SP * (1 - 0.3 * w), "walk", phase=t * 5, face=1, pal=GREY)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
    if t > at(4, -1):
        person(ctx, 300, 1450, 360, "idle", face=1, pal=MARA, lean=0.1, head_turn=-0.5, breathe=math.sin(t * 2))
    rgb(ctx, (0.5, 0.55, 0.6), 0.2); ctx.paint()
    text(ctx, "HER BROTHER", W / 2, 300, 80, (0.85, 0.85, 0.9), prog(t, at(4, -1), at(4, -1) + 0.4) * 0.9, outline=8)
    vignette(ctx, 0.9); grain(ctx, t, 600, 0.08); fade(ctx, t, d, 0.2, 0.2)


def s5(ctx, t, d):
    rr = random.Random(4)
    dots = [(rr.uniform(120, 960), rr.uniform(380, 1450), "", (1, 0.8, 0.4)) for _ in range(40)]
    van = {k: 0.4 + k * (max(0.5, d - 1.5) / 40) for k in range(40)}
    L2.city_map(ctx, t, dots, labels=False, vanish=van,
                title="THEY'RE COLLECTING THEM" if t > at(5, -1) else None)
    grain(ctx, t); fade(ctx, t, d, 0.05, 0.05)


def s6(ctx, t, d):
    pts = [(300, 1300), (300, 1120), (570, 1120), (570, 850), (840, 850), (840, 600)]
    p = ease(prog(t, at(6, 1), at(6, 3)))
    L2.city_map(ctx, t, [(300, 1300, "YOU", (0.45, 1, 0.6))], route=(pts, p), title="6 BLOCKS" if p > 0.2 else None)
    a = prog(t, at(6, 2), at(6, 2) + 0.4)
    if a > 0:
        rgb(ctx, (1, 0.85, 0.2), a)
        ctx.move_to(850, 520); ctx.line_to(800, 610); ctx.line_to(845, 610); ctx.line_to(820, 690); ctx.line_to(890, 580)
        ctx.line_to(845, 580); ctx.line_to(870, 520); ctx.close_path(); ctx.fill()
        text(ctx, "SUBSTATION", 840, 470, 52, (1, 0.85, 0.3), a)
    if t > at(6, -1):
        rgb(ctx, (0, 0, 0), 0.6 * prog(t, at(6, -1), at(6, -1) + 0.5)); ctx.paint()
        text(ctx, "FOREVER.", W / 2, 900, 160, (1, 1, 1), prog(t, at(6, -1), at(6, -1) + 0.4), outline=12)
    grain(ctx, t); fade(ctx, t, d, 0.05, 0.05)


def s7(ctx, t, d):
    off = t * 900
    street(ctx, t, off)
    for k, (x, pal) in enumerate([(520, None), (700, MARA)]):
        person(ctx, x + math.sin(t * 3 + k) * 10, 1300, SP, "run", phase=t * 14 + k, face=-1, pal=pal)
    dog(ctx, 330, 1300, 130, "trot", phase=t * 18, face=-1)
    vignette(ctx, 0.85); grain(ctx, t); fade(ctx, t, d, 0.0, 0.0)


def s8(ctx, t, d):
    off = t * 900
    chase = lerp(-100, 420, prog(t, at(8, 2), d))
    street(ctx, t, off, lamps_on_from=W + 200 - chase if t > at(8, 2) else None)
    for k, (x, pal) in enumerate([(400, None), (580, MARA)]):
        person(ctx, x + math.sin(t * 3 + k) * 10, 1300, SP, "run", phase=t * 15 + k, face=-1, pal=pal)
    dog(ctx, 220, 1300, 130, "trot", phase=t * 19, face=-1)
    clock(ctx, t, "9:12" if t < at(8, 1) else "9:13", red=t > at(8, 1), y=300, size=170)
    vignette(ctx, 0.85); grain(ctx, t); fade(ctx, t, d, 0.0, 0.1)


def substation(ctx, t, lever, strain=0.0):
    L.night_sky(ctx, t, 1250, moon=False)
    vgrad(ctx, 1250, H, [(0, hexc("#17181c")), (1, hexc("#060607"))])
    for k in range(3):
        x = 140 + k * 150
        rgb(ctx, hexc("#2b2f36")); ctx.rectangle(x, 860, 110, 390); ctx.fill()
        for j in range(5):
            rgb(ctx, hexc("#3a3f48")); ctx.rectangle(x - 10, 900 + j * 60, 130, 18); ctx.fill()
    rgb(ctx, (0.6, 0.6, 0.65), 0.25); ctx.set_line_width(3)
    for x in range(0, W, 40):
        ctx.move_to(x, 1000); ctx.line_to(x + 40, 1250); ctx.stroke(); ctx.move_to(x + 40, 1000); ctx.line_to(x, 1250); ctx.stroke()
    rgb(ctx, hexc("#4a3a2a")); ctx.rectangle(640, 760, 260, 490); ctx.fill()
    rgb(ctx, hexc("#2a2018")); ctx.rectangle(660, 780, 220, 140); ctx.fill()
    text(ctx, "MAIN", 770, 850, 64, (1, 0.8, 0.2))
    ang = lerp(-0.9, 0.9, lever) + math.sin(t * 50) * 0.03 * strain
    ctx.save(); ctx.translate(770, 1010); ctx.rotate(ang)
    rgb(ctx, hexc("#8a2a20")); ctx.set_line_width(36); ctx.set_line_cap(1); ctx.move_to(0, 0); ctx.line_to(0, -300); ctx.stroke()
    rgb(ctx, hexc("#202020")); ctx.arc(0, -300, 40, 0, 6.283); ctx.fill()
    hx, hy = 0, -300
    ctx.restore()
    rgb(ctx, hexc("#555555")); ctx.arc(770, 1010, 40, 0, 6.283); ctx.fill()
    return 770 + math.sin(ang) * 300, 1010 - math.cos(ang) * 300


def s9(ctx, t, d):
    strain = prog(t, 0.6, d)
    hx, hy = substation(ctx, t, 0.0 + 0.04 * math.sin(t * 9) * strain, strain)
    person(ctx, 520, 1250, SP, "idle", face=1, lean=-0.35 * strain, arm_f=(2.1, 0.0), arm_b=(2.0, 0.1))
    person(ctx, 1000, 1250, SP, "idle", face=-1, pal=MARA, lean=-0.35 * strain, arm_f=(2.2, 0.0), arm_b=(2.0, 0.1))
    dog(ctx, 300, 1250, 120, "sit", face=1, head_up=1)
    r = random.Random(int(t * 12))
    for k in range(int(6 * strain)):
        rgb(ctx, (1, 0.8, 0.3), r.uniform(0.5, 1)); ctx.arc(770 + r.uniform(-60, 60), 1010 + r.uniform(-60, 30), r.uniform(2, 5), 0, 6.283); ctx.fill()
    vignette(ctx, 0.85); grain(ctx, t); fade(ctx, t, d, 0.05, 0.05)


def s10(ctx, t, d):
    rgb(ctx, hexc("#070708")); ctx.paint()
    clock(ctx, t, "9:14", red=True, y=900, size=330)
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    glow(ctx, W / 2, 900, 900, (1, 0.2, 0.15), 0.25 + 0.15 * math.sin(t * 9))
    ctx.restore()
    grain(ctx, t, 500); fade(ctx, t, d, 0.0, 0.0)


def s11(ctx, t, d):
    pull = at(11, 1)
    lev = ease_out(prog(t, pull + 0.3, pull + 0.9))
    hx, hy = substation(ctx, t, lev, 1 - lev)
    person(ctx, 520, 1250, SP, "idle", face=1, lean=-0.4 + 0.3 * lev, arm_f=(2.1 - 1.0 * lev, 0.0))
    person(ctx, 1000, 1250, SP, "idle", face=-1, pal=MARA, lean=-0.4 + 0.3 * lev, arm_f=(2.2 - 1.0 * lev, 0.0))
    flood = prog(t, 0.0, pull + 0.8) * (1 - prog(t, pull + 0.9, pull + 1.0))
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    rgb(ctx, (1, 0.92, 0.75), 0.85 * flood ** 1.5); ctx.paint()
    ctx.restore()
    if t > pull + 0.95:
        rgb(ctx, (0, 0, 0), 1); ctx.paint()
    vignette(ctx, 0.6); grain(ctx, t); fade(ctx, t, d, 0.0, 0.0)


def s12(ctx, t, d):
    rgb(ctx, (0, 0, 0)); ctx.paint()
    a = 0.15 * prog(t, at(12, -1), d)
    draw_skyline(ctx, L.CITY_NEAR, 1250, (a * 0.4, a * 0.45, a * 0.6))
    grain(ctx, t, 120, 0.03)


def stars(ctx, t, n):
    for k, (x, y, r) in enumerate(STARS[:int(n)]):
        rgb(ctx, (1, 1, 1), 0.35 + 0.45 * (0.5 + 0.5 * math.sin(t * 1.3 + k)))
        ctx.arc(x, y, r, 0, 6.283); ctx.fill()


def s13(ctx, t, d):
    vgrad(ctx, 0, 1250, [(0, hexc("#020308")), (1, hexc("#0a0f22"))])
    n = 900 * ease(prog(t, at(13, 1) - 0.5, d - 0.5))
    g = cairo.LinearGradient(0, 200, W, 1100)       # milky way band
    g.add_color_stop_rgba(0, 0.6, 0.65, 0.9, 0); g.add_color_stop_rgba(0.5, 0.6, 0.65, 0.9, 0.12 * n / 900); g.add_color_stop_rgba(1, 0.6, 0.65, 0.9, 0)
    ctx.set_source(g); ctx.paint()
    stars(ctx, t, n)
    draw_skyline(ctx, L.CITY_NEAR, 1250, hexc("#030305"))
    vgrad(ctx, 1250, H, [(0, hexc("#050506")), (1, hexc("#000000"))])
    grain(ctx, t, 150, 0.04); fade(ctx, t, d, 0.4, 0.15)


def s14(ctx, t, d):
    vgrad(ctx, 0, 1180, [(0, hexc("#020308")), (1, hexc("#0c1226"))])
    g = cairo.LinearGradient(0, 100, W, 1000)
    g.add_color_stop_rgba(0, 0.6, 0.65, 0.9, 0); g.add_color_stop_rgba(0.5, 0.6, 0.65, 0.9, 0.12); g.add_color_stop_rgba(1, 0.6, 0.65, 0.9, 0)
    ctx.set_source(g); ctx.paint()
    stars(ctx, t, 900)
    sh = prog(t, 2.0, 2.8)
    if 0 < sh < 1:
        rgb(ctx, (1, 1, 1), 1 - sh); ctx.set_line_width(3)
        ctx.move_to(200 + sh * 500, 200 + sh * 200); ctx.line_to(140 + sh * 500, 176 + sh * 200); ctx.stroke()
    draw_skyline(ctx, L.CITY_FAR, 1100, hexc("#05060a"))
    L.parapet(ctx)
    L.sit_back(ctx, 360, 1180, 480, head_turn=0.6 * prog(t, at(14, -1), d), breathe=math.sin(t * 1.4))
    sit_back_pal(ctx, 620, 1180, 470, MARA)
    dog(ctx, 820, 1180, 140, "back", wag=math.sin(t * 3))
    vignette(ctx, 0.7); grain(ctx, t, 150, 0.04); fade(ctx, t, d, 0.2, 0.2)


def s15(ctx, t, d):
    s14(ctx, t + 10, d + 10)
    rgb(ctx, (0, 0, 0), 0.35); ctx.paint()
    q = prog(t, 0.2, 0.6)
    ctx.save(); ctx.translate(W / 2, 320); s = 1 + (1 - ease_out(q)) * 0.5; ctx.scale(s, s)
    text(ctx, "THE END", 0, 0, 180, (1, 0.85, 0.5), ease(q), outline=14)
    ctx.restore()
    c = prog(t, at(15, 0), at(15, 0) + 0.4)
    if c > 0:
        bob = math.sin(t * 5) * 8
        rgb(ctx, (0, 0, 0), 0.6 * c); rrect(ctx, 110, 560 + bob, 860, 170, 30); ctx.fill()
        text(ctx, "WOULD YOU PULL THE LEVER?", W / 2, 620 + bob, 70, (1, 1, 1), c)
        text(ctx, "tell me in the comments", W / 2, 690 + bob, 46, (0.85, 0.85, 0.9), c)
    f = prog(t, at(15, -2), at(15, -2) + 0.4)
    if f > 0:
        rgb(ctx, hexc("#c4302b"), f); rrect(ctx, 200, 790, 680, 120, 60); ctx.fill()
        text(ctx, "NEW STORY TOMORROW", W / 2, 850, 62, (1, 1, 1), f)
    fade(ctx, t, d, 0.1, 0.3)


SCENES = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15]


# ------------------------------------------------------------------ sound
def sfx(i, d):
    t = np.arange(int(d * SR)) / SR
    bed = band_noise(d, 60, 300, i) * 0.06
    if i in (1, 2, 3):
        x = bed + band_noise(d, 800, 7000, 31) * 0.12
        if i == 1:
            x += env_at(d, [k * 1.0 for k in range(int(d) + 1)], 0.03) * band_noise(d, 3000, 8000, 3) * 0.3
        if i == 2:
            x += env_at(d, [0.3], 0.9) * band_noise(d, 300, 2000, 4) * 0.3 + L.bark_sfx(d, [at(2, 1) + 1.3, at(2, 1) + 1.8]) * 0.5
    elif i == 4:
        x = bed + tone(d, 1046) * 0.02 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * t)) + band_noise(d, 100, 600, 41) * 0.1
    elif i in (5, 6):
        x = bed + tone(d, 60) * 0.03
        if i == 5:
            x += env_at(d, [0.4 + k * (max(0.5, d - 1.5) / 40) for k in range(40)], 0.06) * tone(d, 880) * 0.12
        else:
            x += env_at(d, [at(6, -1)], 1.5) * (tone(d, 41) + band_noise(d, 30, 200, 6) * 0.5) * 0.8
    elif i in (7, 8):
        x = bed + env_at(d, [k * math.pi / 15 for k in range(int(d * 15 / math.pi) + 1)], 0.05) * band_noise(d, 150, 2000, i) * 0.6 \
            + L.heart(d, 140) + band_noise(d, 200, 1200, 7) * 0.15
        if i == 8:
            x += env_at(d, [at(8, 2) + k * 0.35 for k in range(12)], 0.25) * (tone(d, 60) * 0.5 + band_noise(d, 80, 500, 8) * 0.3)
    elif i == 9:
        x = bed + band_noise(d, 50, 300, 9) * 0.3 * np.clip(t / d, 0, 1) + env_at(d, list(np.arange(0.6, d, 0.17)), 0.04) * band_noise(d, 3000, 9000, 10) * 0.3 \
            + tone(d, 120, "saw") * 0.06 + L.heart(d, 150)
    elif i == 10:
        x = bed + env_at(d, [0.0], 2.0) * (tone(d, 41) + band_noise(d, 30, 300, 11) * 0.6) * 0.9 + tone(d, 1760) * 0.03
    elif i == 11:
        pull = at(11, 1)
        rise = np.clip(t / (pull + 0.8), 0, 1) * (t < pull + 0.9)
        x = bed + (band_noise(d, 200, 8000, 12) * 0.5 + tone(d, 220 + 600 * rise) * 0.2) * rise ** 2 \
            + env_at(d, [pull + 0.9], 2.5) * (tone(d, 35) + band_noise(d, 20, 400, 13) * 0.8) * 1.2
    elif i == 12:
        x = silence(d) + band_noise(d, 2000, 6000, 14) * 0.01 * np.clip((t - 2) / 3, 0, 1)
    else:
        crick = (np.sin(2 * np.pi * 4500 * t) * (np.sin(2 * np.pi * 18 * t) > 0.6) * (np.sin(2 * np.pi * 0.7 * t) > 0)) * 0.02
        x = bed * 0.5 + crick + band_noise(d, 100, 600, 15) * 0.05
    return fades(x * 0.6, 0.03, 0.1)


def music(durs):
    """Tense pulse until the lever; silence in the dark; then the piano returns under the stars."""
    lever = sum(durs[:11])
    calm = sum(durs[:12])
    total = sum(durs)
    tense = piano_score(lever, 0.0)
    gap = np.zeros(int((calm - lever) * SR), dtype=np.float32)
    piano = piano_score(total - calm + 1, total + 100)
    out = np.concatenate([tense, gap, piano])[: int(total * SR)]
    return out


def dur_of(i):
    return sf.info(str(OUT / f"scene_{i:02d}.wav")).duration + 0.3


def job(i):
    d = dur_of(i)
    outdir = ROOT / "assets" / "clips" / SID
    outdir.mkdir(parents=True, exist_ok=True)
    save_wav(outdir / f"scene_{i:02d}.sfx.wav", sfx(i, d))
    render(SCENES[i - 1], d, outdir / f"scene_{i:02d}.mp4")
    return f"scene {i} ({d:.1f}s)"


if __name__ == "__main__":
    only = [int(a) for a in sys.argv[1:]] or range(1, N + 1)
    durs = [dur_of(i) for i in range(1, N + 1)]
    outdir = ROOT / "assets" / "clips" / SID
    outdir.mkdir(parents=True, exist_ok=True)
    save_wav(outdir / "music.wav", music(durs))
    with Pool(4) as p:
        for r in p.imap_unordered(job, only):
            print("  rendered", r, flush=True)
