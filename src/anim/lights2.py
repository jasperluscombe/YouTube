"""The 9:14 Lights - Part 2: "Who's On The Stairs?"  (stories/21_lights_part2.json)

    python src/anim/lights2.py [scene numbers]
"""
import json, math, pathlib, random, sys
from multiprocessing import Pool

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import *  # noqa
import lights as L

ROOT = pathlib.Path(__file__).resolve().parents[2]
SID = "21_lights_part2"
OUT = ROOT / "out" / SID
N = 14
SEG = {i: (json.loads((OUT / f"scene_{i:02d}.json").read_text()) if (OUT / f"scene_{i:02d}.json").exists() else [["", 0, 5]])
       for i in range(1, N + 1)}


def at(i, k):
    s = SEG[i]
    return s[k][1] if -len(s) <= k < len(s) else s[-1][1]


# ------------------------------------------------------------------ props
def terminal(ctx, t, lines, typed_from, color=(0.45, 1.0, 0.6), glitch=0.0, size=92, top=560):
    """CRT screen filling the frame; lines appear typed starting at typed_from[k]."""
    rgb(ctx, hexc("#141613")); ctx.paint()
    rgb(ctx, hexc("#2c2f2a")); rrect(ctx, 50, 330, 980, 1060, 60); ctx.fill()
    rgb(ctx, hexc("#04140a")); rrect(ctx, 100, 380, 880, 900, 40); ctx.fill()
    glow(ctx, 540, 830, 700, color, 0.12)
    y = top
    for k, ln in enumerate(lines):
        t0 = typed_from[k] if k < len(typed_from) else 1e9
        n = int(clamp((t - t0) * 16, 0, len(ln)))
        if n > 0:
            s = ln[:n]
            jx = (random.Random(int(t * 30) + k).uniform(-18, 18)) * glitch
            if glitch > 0:
                text(ctx, s, 150 + jx + 6, y, size, (1, 0.1, 0.1), 0.6, anchor="left")
                text(ctx, s, 150 + jx - 6, y, size, (0.1, 0.6, 1), 0.6, anchor="left")
            text(ctx, s, 150 + jx, y, size, color, 1.0, anchor="left")
            if n < len(ln) or (k == len(lines) - 1 and int(t * 2) % 2 == 0):
                ext_w = len(s) * size * 0.45
                rgb(ctx, color); ctx.rectangle(160 + ext_w, y - size * 0.35, size * 0.4, size * 0.75); ctx.fill()
        y += size * 1.35
    for k in range(0, 900, 6):              # scanlines
        rgb(ctx, (0, 0, 0), 0.25); ctx.rectangle(100, 380 + k, 880, 2); ctx.fill()
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD); glow(ctx, 540, 830, 520, color, 0.06 + 0.03 * math.sin(t * 50)); ctx.restore()


def city_map(ctx, t, dots, labels=True, vanish=None, route=None, title=None):
    rgb(ctx, hexc("#04140a")); ctx.paint()
    rgb(ctx, (0.3, 0.9, 0.5), 0.18); ctx.set_line_width(3)
    for k in range(0, W, 90):
        ctx.move_to(k, 300); ctx.line_to(k, 1500); ctx.stroke()
    for k in range(300, 1500, 90):
        ctx.move_to(0, k); ctx.line_to(W, k); ctx.stroke()
    rgb(ctx, (0.2, 0.5, 0.9), 0.5); ctx.set_line_width(70)          # river
    ctx.move_to(-50, 1050); ctx.curve_to(300, 900, 700, 1150, 1130, 950); ctx.stroke()
    for k, (x, y, lab, col) in enumerate(dots):
        a = 1.0
        if vanish and k in vanish:
            a = 1 - prog(t, vanish[k], vanish[k] + 0.3)
        if a <= 0:
            continue
        pulse = 0.5 + 0.5 * math.sin(t * 6 + k)
        glow(ctx, x, y, 70, col, 0.6 * a * pulse)
        rgb(ctx, col, a); ctx.arc(x, y, 16, 0, 6.283); ctx.fill()
        if labels and lab:
            text(ctx, lab, x, y - 55, 52, col, a)
    if route:
        pts, p = route
        ctx.set_line_width(10); rgb(ctx, (1, 0.8, 0.3)); ctx.set_dash([28, 18])
        tot = len(pts) - 1
        upto = p * tot
        ctx.move_to(*pts[0])
        for k in range(1, len(pts)):
            f = clamp(upto - (k - 1))
            if f <= 0:
                break
            x0, y0 = pts[k - 1]; x1, y1 = pts[k]
            ctx.line_to(lerp(x0, x1, f), lerp(y0, y1, f))
        ctx.stroke(); ctx.set_dash([])
    if title:
        text(ctx, title, W / 2, 1620, 76, (0.5, 1, 0.65), outline=0)
    for k in range(300, 1500, 6):
        rgb(ctx, (0, 0, 0), 0.15); ctx.rectangle(0, k, W, 2); ctx.fill()


def stairwell(ctx, t, depth, lit_upto, s=430):
    """Side cutaway of a stairwell. depth = px scrolled downward."""
    FL = 620
    rgb(ctx, hexc("#121318")); ctx.paint()
    ctx.save(); ctx.translate(0, -depth)
    top = int(depth // FL) - 2
    for lv in range(top, top + 6):
        y = lv * FL
        lit = lv <= lit_upto
        a = 1.0 if lit else 0.0
        if lit:
            cone(ctx, 540, y + 40, math.pi / 2, 0.9, 700, (1, 0.85, 0.6), 0.25)
            glow(ctx, 540, y + 40, 150, (1, 0.85, 0.6), 0.6)
        rgb(ctx, (1, 0.95, 0.8) if lit else (0.25, 0.25, 0.25)); ctx.arc(540, y + 40, 12, 0, 6.283); ctx.fill()
        rgb(ctx, hexc("#2a2c33") if lit else hexc("#1a1b20"))
        ctx.rectangle(80, y + FL - 40, 920, 26); ctx.fill()           # landing
        d = 1 if lv % 2 else -1                                      # flight direction
        ctx.set_line_width(22)
        x0, x1 = (180, 900) if d > 0 else (900, 180)
        ctx.move_to(x0, y + FL - 40); ctx.line_to(x1, y + 2 * FL - 40); ctx.stroke()
        rgb(ctx, hexc("#5a5d66") if lit else hexc("#2a2b30")); ctx.set_line_width(5)
        ctx.move_to(x0, y + FL - 140); ctx.line_to(x1, y + 2 * FL - 140); ctx.stroke()
        num = 23 - lv
        if 1 <= num <= 23:
            text(ctx, str(num), 150 if d < 0 else 930, y + FL - 120, 90, (0.9, 0.9, 0.85) if lit else (0.3, 0.3, 0.3))
    ctx.restore()


def lobby(ctx, t, rain=True, outside_fig=False, flash=0.0, glass_open=0.0):
    vgrad(ctx, -100, 1250, [(0, hexc("#0d0f14")), (1, hexc("#1a1d24"))])
    vgrad(ctx, 1250, H, [(0, hexc("#1b1d22")), (1, hexc("#08090b"))])
    for x in (120, 960):
        rgb(ctx, hexc("#16181e")); ctx.rectangle(x - 40, 300, 80, 950); ctx.fill()
    # glass doors (right)
    gx = 560
    rgb(ctx, hexc("#0e1a26")); ctx.rectangle(gx, 520, 420, 730); ctx.fill()
    if rain:
        r = random.Random(int(t * 20)); ctx.set_line_width(2)
        for k in range(70):
            x, y = r.uniform(gx, gx + 420), r.uniform(520, 1250)
            rgb(ctx, (0.6, 0.75, 0.9), 0.35); ctx.move_to(x, y); ctx.line_to(x - 4, y + 30); ctx.stroke()
    if flash > 0:
        rgb(ctx, (0.85, 0.9, 1), 0.6 * flash); ctx.rectangle(gx, 520, 420, 730); ctx.fill()
    if outside_fig:
        L.silhouette(ctx, gx + 260, 1250, 420, sign=1, col=(0.04, 0.05, 0.08))
        L.sign_card(ctx, gx + 260, 1010, 230, 150, ["DON'T", "COME HERE"], size=40)
    rgb(ctx, hexc("#2a2e36")); ctx.set_line_width(14); ctx.rectangle(gx, 520, 420, 730); ctx.stroke()
    off = glass_open * 200
    ctx.move_to(gx + 210 + off, 520); ctx.line_to(gx + 210 + off, 1250); ctx.stroke()
    rgb(ctx, (1, 1, 1), 0.05); ctx.move_to(gx + 30, 560); ctx.line_to(gx + 120, 560); ctx.line_to(gx + 30, 760); ctx.fill()


def desk(ctx, t, x=330):
    rgb(ctx, hexc("#2c2620")); ctx.rectangle(x - 200, 1080, 400, 170); ctx.fill()
    rgb(ctx, hexc("#3a3129")); ctx.rectangle(x - 215, 1065, 430, 22); ctx.fill()
    rgb(ctx, hexc("#202020"))
    rrect(ctx, x - 90, 930, 180, 130, 10); ctx.fill()
    rgb(ctx, (0.45, 1, 0.6), 0.8 + 0.2 * math.sin(t * 30)); ctx.rectangle(x - 75, 945, 150, 100); ctx.fill()
    glow(ctx, x, 995, 300, (0.45, 1, 0.6), 0.3)


# ------------------------------------------------------------------ scenes
def s1(ctx, t, d):
    if t < at(1, 4):
        flipt = at(1, 3)
        p = prog(t, flipt - 0.2, flipt + 0.4)
        lines = ["DON'T", "COME HERE"] if p < 0.5 else ["IT'S NOT ME", "TURNING", "THEM ON"]
        L.window_scene(ctx, t, lit=1, sign_up=1, sign_lines=lines, flip=math.cos(p * math.pi), zoom=1.3)
        L.binoculars(ctx, t, 1.0)
        text(ctx, "PREVIOUSLY", W / 2, 260, 80, (1, 1, 1), 0.8, outline=8)
    else:
        L.night_sky(ctx, t, 1000, moon=False)
        vgrad(ctx, 1000, H, [(0, hexc("#191b22")), (1, hexc("#0a0b0e"))])
        L.door_hut(ctx, 540, 1150, L.flicker(t, at(1, 5)))
    vignette(ctx, 0.8); grain(ctx, t); fade(ctx, t, d, 0.0, 0.1)


def s2(ctx, t, d):
    z = 1 + 0.08 * t / d
    ctx.save(); ctx.translate(540, 1100); ctx.scale(z, z); ctx.translate(-540, -1100)
    L.night_sky(ctx, t, 1000, moon=False)
    vgrad(ctx, 1000, H, [(0, hexc("#191b22")), (1, hexc("#0a0b0e"))])
    L.door_hut(ctx, 540, 1150, 1.0)
    ctx.restore()
    person(ctx, 470, 1720, 560, "idle", back_view=True, breathe=math.sin(t * 3))
    dog(ctx, 700, 1720, 170, "back")
    vignette(ctx, 0.9); grain(ctx, t); fade(ctx, t, d, 0.1, 0.1)


def s3(ctx, t, d):
    go = at(3, 1)
    L.night_sky(ctx, t, 1000, moon=False)
    vgrad(ctx, 1000, H, [(0, hexc("#191b22")), (1, hexc("#0a0b0e"))])
    L.door_hut(ctx, 540, 1150, 1.0, ajar=ease(prog(t, go - 0.8, go + 0.4)) * 1.6)
    w = prog(t, go, d)
    px = lerp(170, 560, ease(w))
    sc = 1 - 0.25 * w
    if w < 0.95:
        person(ctx, px, 1250 - 100 * w, S_P * sc, "walk" if 0 < w < 1 else "idle", phase=t * 6, face=1)
        dog(ctx, px - 140 * sc, 1250 - 100 * w, 130 * sc, "trot" if 0 < w < 1 else "stand", phase=t * 8, face=1)
    vignette(ctx, 0.9); grain(ctx, t); fade(ctx, t, d, 0.1, 0.15)


S_P = 430


def s4(ctx, t, d):
    depth = t * 260
    stairwell(ctx, t, depth, lit_upto=int((depth + 900) // 620))
    face = 1 if int((depth + 620) // 620) % 2 else -1
    person(ctx, 540, 1130, S_P, "walk", phase=t * 7, face=face, lean=0.1)
    dog(ctx, 540 - face * 170, 1130, 125, "trot", phase=t * 9, face=face)
    vignette(ctx, 0.9); grain(ctx, t); fade(ctx, t, d, 0.1, 0.1)


def s5(ctx, t, d):
    depth = 620 * 4 + t * 900
    stairwell(ctx, t, depth, lit_upto=int((depth + 900) // 620))
    face = 1 if int((depth + 620) // 620) % 2 else -1
    person(ctx, 540, 1130, S_P, "run", phase=t * 11, face=face)
    dog(ctx, 540 - face * 170, 1130, 125, "trot", phase=t * 13, face=face)
    lobby_at = at(5, -1)
    floor = max(1, 23 - int(prog(t, 0, lobby_at) * 22))
    lab = "L" if t > lobby_at + 0.6 else str(floor)
    rgb(ctx, (0, 0, 0), 0.5); rrect(ctx, 340, 180, 400, 240, 30); ctx.fill()
    text(ctx, lab, W / 2, 300, 190, (1, 0.85, 0.5))
    vignette(ctx, 0.9); grain(ctx, t); fade(ctx, t, d, 0.05, 0.2)


def s6(ctx, t, d):
    lobby(ctx, t)
    desk(ctx, t)
    w = prog(t, 0.0, at(6, 1))
    person(ctx, lerp(-100, 700, ease(w)), 1250, S_P, "walk" if w < 1 else "idle", phase=t * 5, face=-1 if w >= 1 else 1)
    dog(ctx, lerp(-250, 860, ease(w)), 1250, 130, "trot" if w < 1 else "sit", phase=t * 8, face=1 if w < 1 else -1, head_up=1)
    vignette(ctx, 0.85); grain(ctx, t); fade(ctx, t, d, 0.1, 0.1)


def s7(ctx, t, d):
    terminal(ctx, t, ["_"], [0.5])
    grain(ctx, t); fade(ctx, t, d, 0.1, 0.05)


def s8(ctx, t, d):
    terminal(ctx, t, ["HELLO.", "NIGHT 212.", "YOU ARE", "STILL HERE."], [at(8, 0), at(8, 1), at(8, 2), at(8, 2) + 0.45])
    grain(ctx, t); fade(ctx, t, d, 0.05, 0.05)


def s9(ctx, t, d):
    rgb(ctx, hexc("#0b0c0e")); ctx.paint()
    glow(ctx, 540, 300, 900, (0.45, 1, 0.6), 0.25)
    rgb(ctx, hexc("#1d1f22")); rrect(ctx, 60, 900, 960, 520, 30); ctx.fill()
    for r in range(4):
        for c in range(11):
            rgb(ctx, hexc("#2c2f33")); rrect(ctx, 95 + c * 82, 950 + r * 105, 70, 85, 10); ctx.fill()
    shake = math.sin(t * 40) * 6
    for side, x in ((-1, 380), (1, 700)):
        k = max(0, math.sin(t * 9 + side)) * 30
        rgb(ctx, HOODIE); ctx.set_line_width(110); ctx.set_line_cap(1)
        ctx.move_to(x + side * 260, H + 100); ctx.line_to(x + shake, 1150 - k); ctx.stroke()
        rgb(ctx, hexc("#c99a7a")); ctx.arc(x + shake, 1130 - k, 48, 0, 6.283); ctx.fill()
    q = at(9, -1)
    s = "> WHO ARE YOU?"
    n = int(clamp((t - q) * 12, 0, len(s)))
    rgb(ctx, hexc("#04140a")); rrect(ctx, 100, 260, 880, 260, 30); ctx.fill()
    text(ctx, s[:n] if n else ">", 140, 390, 84, (0.45, 1, 0.6), anchor="left")
    grain(ctx, t); vignette(ctx, 0.7); fade(ctx, t, d, 0.05, 0.05)


def s10(ctx, t, d):
    terminal(ctx, t, ["I AM THE CITY.", "I KEEP THE", "LIGHTS ON...", "SO I CAN FIND", "WHO IS LEFT."],
             [at(10, 0), at(10, 1), at(10, 1) + 0.6, at(10, 2), at(10, 2) + 0.7], size=84)
    grain(ctx, t); fade(ctx, t, d, 0.05, 0.05)


def s11(ctx, t, d):
    a = prog(t, at(11, 1), at(11, 1) + 0.3)
    b = prog(t, at(11, 2), at(11, 2) + 0.3)
    dots = [(300, 1300, "YOU", (0.45, 1, 0.6))] if a > 0 else []
    if b > 0:
        dots.append((780, 760, "HER", (1, 0.75, 0.3)))
    city_map(ctx, t, dots, title="2 SURVIVORS DETECTED")
    grain(ctx, t); fade(ctx, t, d, 0.05, 0.05)


def s12(ctx, t, d):
    red = at(12, 1)
    if t < red:
        terminal(ctx, t, ["2 SURVIVORS", "DETECTED."], [-10, -10], glitch=0.6 * (t > red - 1.0))
    else:
        terminal(ctx, t, ["SHE IS", "LYING", "TO YOU."], [red, red + 0.35, red + 0.7], color=(1, 0.25, 0.2),
                 glitch=0.25 + 0.5 * max(0, math.sin(t * 13)), size=150, top=640)
    grain(ctx, t, 500); fade(ctx, t, d, 0.05, 0.05)


BARK2 = []


def s13(ctx, t, d):
    fig = at(13, 1)
    fl = max(0, 1 - (t - (fig - 0.1)) * 4) if t > fig - 0.1 else 0
    lobby(ctx, t, outside_fig=t > fig, flash=fl)
    desk(ctx, t, 230)
    bark = max([math.exp(-(t - b) * 14) for b in (0.2, 0.6, 1.0, 1.6, 2.1) if t >= b] + [0])
    dog(ctx, 420, 1250, 180, "sit", face=1, head_up=1, bark=bark)
    person(ctx, 160, 1250, S_P, "idle", face=1, breathe=math.sin(t * 5), crouch=0.15)
    vignette(ctx, 0.85); grain(ctx, t); fade(ctx, t, d, 0.05, 0.1)


def s14(ctx, t, d):
    rgb(ctx, hexc("#06070a")); ctx.paint()
    ctx.save(); ctx.rectangle(0, 0, W / 2, H); ctx.clip()
    glow(ctx, 270, 1000, 520, (0.45, 1, 0.6), 0.35)
    rgb(ctx, hexc("#202020")); rrect(ctx, 120, 860, 300, 220, 14); ctx.fill()
    rgb(ctx, (0.45, 1, 0.6)); ctx.rectangle(140, 880, 260, 180); ctx.fill()
    text(ctx, "THE MACHINE", 270, 1240, 76, (0.6, 1, 0.7), outline=8)
    ctx.restore()
    ctx.save(); ctx.rectangle(W / 2, 0, W / 2, H); ctx.clip()
    rgb(ctx, hexc("#0c1420")); ctx.rectangle(W / 2, 0, W / 2, H); ctx.fill()
    r = random.Random(int(t * 20)); ctx.set_line_width(2)
    for k in range(60):
        x, y = r.uniform(W / 2, W), r.uniform(0, H)
        rgb(ctx, (0.6, 0.75, 0.9), 0.3); ctx.move_to(x, y); ctx.line_to(x - 4, y + 30); ctx.stroke()
    L.silhouette(ctx, 810, 1150, 380, sign=1, col=(0.02, 0.03, 0.05))
    L.sign_card(ctx, 810, 930, 210, 130, ["DON'T", "COME HERE"], size=36)
    text(ctx, "THE STRANGER", 810, 1240, 76, (1, 0.8, 0.45), outline=8)
    ctx.restore()
    rgb(ctx, (1, 1, 1), 0.6); ctx.rectangle(W / 2 - 3, 0, 6, H); ctx.fill()
    q = prog(t, 0.2, 0.6)
    text(ctx, "WHO DO", W / 2, 300, 150, (1, 1, 1), ease(q), outline=14)
    text(ctx, "YOU TRUST?", W / 2, 460, 150, (1, 0.8, 0.4), ease(q), outline=14)
    c = prog(t, at(14, -2), at(14, -2) + 0.4)
    if c > 0:
        bob = math.sin(t * 5) * 8
        rgb(ctx, (0, 0, 0), 0.6 * c); rrect(ctx, 140, 1330 + bob, 800, 120, 30); ctx.fill()
        text(ctx, "COMMENT: MACHINE OR STRANGER", W / 2, 1390 + bob, 60, (1, 1, 1), c)
    f = prog(t, at(14, -1), at(14, -1) + 0.4)
    if f > 0:
        rgb(ctx, hexc("#c4302b"), f); rrect(ctx, 260, 1500, 560, 120, 60); ctx.fill()
        text(ctx, "PART 3 IS UP NEXT", W / 2, 1560, 62, (1, 1, 1), f)
    vignette(ctx, 0.6); grain(ctx, t); fade(ctx, t, d, 0.1, 0.25)


SCENES = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14]


# ------------------------------------------------------------------ sound
def typing(d, t0, n, rate=16):
    return env_at(d, [t0 + k / rate + 0.01 * math.sin(k * 7) for k in range(n)], 0.02) * band_noise(d, 2000, 7000, 9) * 0.5


def sfx(i, d):
    t = np.arange(int(d * SR)) / SR
    bed = band_noise(d, 60, 300, i) * 0.06
    if i == 1:
        b0 = at(1, 5)
        buzz = np.array([L.flicker(tt, b0) for tt in t[::441]]).repeat(441)[: len(t)]
        x = bed + L.heart(d, 80) * 0.6 + tone(d, 120, "saw") * 0.06 * buzz
    elif i in (2,):
        x = bed + band_noise(d, 150, 900, 22) * 0.12 + tone(d, 120, "saw") * 0.04 + L.heart(d, 88)
    elif i == 3:
        go = at(3, 1)
        x = bed + env_at(d, [go - 0.6], 1.0) * tone(d, 210 - 60 * np.clip(t - go + 0.6, 0, 1), "saw") * 0.06 \
            + env_at(d, [go + k * 0.48 for k in range(10)], 0.05) * band_noise(d, 200, 2000, 3) * 0.5
    elif i in (4, 5):
        rate = 7 if i == 4 else 11
        x = bed + env_at(d, [k * math.pi / rate for k in range(int(d * rate / math.pi) + 1)], 0.06) * band_noise(d, 150, 1800, i) * 0.55 \
            + env_at(d, [k * (620 / (260 if i == 4 else 900)) for k in range(30)], 0.08) * band_noise(d, 2000, 6000, 7) * 0.3 \
            + L.heart(d, 96 if i == 4 else 120)
    elif i in (6, 13):
        x = bed + band_noise(d, 800, 7000, 61) * 0.14 + tone(d, 60) * 0.03
        if i == 13:
            fig = at(13, 1)
            x += env_at(d, [fig - 0.1], 1.5) * band_noise(d, 30, 300, 5) * 0.8 + L.bark_sfx(d, [0.2, 0.6, 1.0, 1.6, 2.1])
    elif i in (7, 8, 10):
        starts = {7: [], 8: [at(8, 0), at(8, 1), at(8, 2)], 10: [at(10, 0), at(10, 1), at(10, 2)]}[i]
        x = bed + tone(d, 15734 / 2) * 0.004 + tone(d, 60) * 0.02
        for s0 in starts:
            x += typing(d, s0, 14)
    elif i == 9:
        x = bed + typing(d, at(9, -1), 14, 12) + typing(d, 0.2, 20, 9) * 0.6
    elif i == 11:
        x = bed + env_at(d, [at(11, 1), at(11, 2)], 0.25) * tone(d, 1320) * 0.25
    elif i == 12:
        red = at(12, 1)
        x = bed + band_noise(d, 400, 6000, 12) * 0.25 * ((t > red - 1) & (t < red + 0.3)) \
            + env_at(d, [red], 1.6) * (tone(d, 41) + band_noise(d, 30, 200, 4) * 0.5) * 0.9
    else:
        x = bed + band_noise(d, 800, 7000, 64) * 0.08 + L.heart(d, 70) * 0.5
    return fades(x * 0.6, 0.03, 0.1)


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
    save_wav(outdir / "music.wav", piano_score(sum(durs), 0.0))
    with Pool(4) as p:
        for r in p.imap_unordered(job, only):
            print("  rendered", r, flush=True)
