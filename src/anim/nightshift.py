"""The Night Shift - zombie survival, Parts 1-3 (stories/26-28).

    python src/anim/nightshift.py <part 1|2|3> [scene numbers]
"""
import math, pathlib, random, sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import *  # noqa
import lights as L
from lighthouse import end_card, big_word, finish, surf, wind, crackle
from story import Timing, run
from bunker import radio

T1, T2, T3 = Timing("26_nightshift_1"), Timing("27_nightshift_2"), Timing("28_nightshift_3")
SP = 430
MIA = ((0.93, 0.45, 0.62), (0.75, 0.32, 0.47), (0.30, 0.32, 0.45), (0.22, 0.24, 0.34))
ZOMB = ((0.42, 0.48, 0.40), (0.32, 0.37, 0.30), (0.25, 0.25, 0.22), (0.18, 0.18, 0.16))
SOLDIER = ((0.35, 0.40, 0.28), (0.27, 0.31, 0.21), (0.30, 0.33, 0.24), (0.22, 0.25, 0.18))
FLOOR = 1300
BOX_COLS = [hexc("#c94b4b"), hexc("#4b7bc9"), hexc("#e0b83a"), hexc("#5aa86a"), hexc("#e8e2d6"), hexc("#9b5ac9")]


# ------------------------------------------------------------------ set pieces
def lights_flicker(t, seed=0):
    return 0.55 if math.sin(t * 23 + seed) * math.sin(t * 7.1 + seed) > 0.75 else 1.0


def store(ctx, t, light=1.0, empty=0.0, seed=1):
    """Pharmacy interior: tiled floor, aisles of shelves, fluorescent tubes."""
    lv = light * lights_flicker(t, seed)
    vgrad(ctx, -200, FLOOR, [(0, hexc("#1c2528")), (1, hexc("#2c393c"))])
    vgrad(ctx, FLOOR, H, [(0, hexc("#2e3436")), (1, hexc("#151819"))])
    rgb(ctx, (0, 0, 0), 0.18); ctx.set_line_width(3)
    for k in range(12):
        ctx.move_to(k * 120 - 300, FLOOR); ctx.line_to(k * 200 - 900, H); ctx.stroke()
    for k in range(4):
        rgb(ctx, (0.85, 0.97, 1.0), 0.85 * lv); ctx.rectangle(80 + k * 260, 150, 190, 16); ctx.fill()
        cone(ctx, 175 + k * 260, 165, math.pi / 2, 0.6, 1000, (0.8, 0.95, 1.0), 0.08 * lv)
    r = random.Random(seed)
    for row, sy in enumerate((560, 800, 1040)):
        rgb(ctx, hexc("#5c6466")); ctx.rectangle(0, sy, W, 16); ctx.fill()
        for k in range(18):
            if r.random() < empty:
                continue
            x = k * 62 + r.uniform(-6, 6)
            h = r.uniform(60, 110)
            rgb(ctx, r.choice(BOX_COLS)); ctx.rectangle(x, sy - h, 48, h); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.45 * (1 - lv)); ctx.paint()


def counter(ctx, t, x=640):
    rgb(ctx, hexc("#d9d3c4")); ctx.rectangle(x - 260, 1080, 520, 220); ctx.fill()
    rgb(ctx, hexc("#2e8a5a")); ctx.rectangle(x - 260, 1080, 520, 26); ctx.fill()
    rgb(ctx, hexc("#2a2c30")); rrect(ctx, x + 90, 990, 120, 90, 10); ctx.fill()
    rgb(ctx, (0.4, 1, 0.6), 0.8); ctx.rectangle(x + 105, 1003, 90, 40); ctx.fill()


def pharmacy_sign(ctx, t, x=540, y=330, a=1.0):
    glow(ctx, x, y, 260, (0.3, 1, 0.5), 0.35 * a)
    rgb(ctx, (0.35, 1, 0.55), a)
    ctx.rectangle(x - 22, y - 70, 44, 140); ctx.fill(); ctx.rectangle(x - 70, y - 22, 140, 44); ctx.fill()
    text(ctx, "PHARMACY", x, y + 130, 64, (0.75, 1, 0.8), a)


def shutter(ctx, t, down=1.0, dent=0.0, x0=0, x1=W, top=420, bottom=FLOOR, glow_out=0.0):
    h = (bottom - top) * down
    if glow_out > 0:
        vgrad(ctx, top, bottom, [(0, (1, 0.8, 0.55)), (1, (1, 0.65, 0.4))], x=x0, w=x1 - x0)
    rgb(ctx, hexc("#8a8f94")); ctx.rectangle(x0, top, x1 - x0, h); ctx.fill()
    for k in range(int(h // 34) + 1):
        y = top + k * 34
        dx = dent * 30 * math.exp(-((y - 900) / 220) ** 2) * math.sin(t * 9) if dent else 0
        rgb(ctx, hexc("#6d7277")); ctx.rectangle(x0 + dx, y, x1 - x0, 6); ctx.fill()
    if dent > 0:
        for k in range(3):
            rgb(ctx, (0, 0, 0), 0.25 * dent); ctx.save(); ctx.translate(380 + k * 160, 880 + (k % 2) * 70)
            ctx.scale(1.4, 1); ctx.arc(0, 0, 45 * dent, 0, 6.283); ctx.restore(); ctx.fill()
    rgb(ctx, hexc("#4a4f54")); ctx.rectangle(x0, top - 40, x1 - x0, 40); ctx.fill()


def zombie(ctx, x, y, s, t, k=0, face=1, speed=1.0):
    jerk = 0.08 * math.sin(t * 13 + k * 3) * (math.sin(t * 2 + k) > 0.6)
    person(ctx, x, y, s, "walk", phase=t * 3.2 * speed + k, face=face, lean=0.25 + jerk, pal=ZOMB,
           arm_f=(1.45 + 0.1 * math.sin(t * 2 + k), 0.1), arm_b=(1.3, 0.2), head_turn=0.4 * math.sin(t + k))


def back_door(ctx, t, knocks=(), shadow=0.0, x=540, y=FLOOR):
    off = sum(math.exp(-(t - b) * 14) * 6 * math.sin((t - b) * 70) for b in knocks if t >= b)
    vgrad(ctx, -200, y, [(0, hexc("#1a1f22")), (1, hexc("#262d30"))])
    vgrad(ctx, y, H, [(0, hexc("#23282a")), (1, hexc("#0f1112"))])
    rgb(ctx, hexc("#3c4246")); ctx.rectangle(x - 220 + off, 380, 440, y - 380); ctx.fill()
    rgb(ctx, hexc("#2b3033")); ctx.set_line_width(12); ctx.rectangle(x - 200 + off, 400, 400, y - 420); ctx.stroke()
    rgb(ctx, hexc("#c94b4b")); ctx.rectangle(x - 140 + off, 520, 280, 70); ctx.fill()
    text(ctx, "EMPLOYEES ONLY", x + off, 555, 40, (1, 1, 1))
    rgb(ctx, hexc("#b8bcc0")); ctx.rectangle(x - 160 + off, 860, 320, 30); ctx.fill()
    if shadow > 0:
        rgb(ctx, (1, 0.85, 0.6), 0.5); ctx.rectangle(x - 220, y - 8, 440, 8); ctx.fill()
        rgb(ctx, (0, 0, 0), shadow); ctx.rectangle(x - 80, y - 8, 50, 8); ctx.fill(); ctx.rectangle(x + 30, y - 8, 50, 8); ctx.fill()


def bottle(ctx, x, y, s=1.0, full=1.0):
    rgb(ctx, (0.75, 0.9, 1.0), 0.35); rrect(ctx, x - 22 * s, y - 120 * s, 44 * s, 120 * s, 10 * s); ctx.fill()
    if full > 0:
        rgb(ctx, (0.35, 0.65, 1.0), 0.8); rrect(ctx, x - 22 * s, y - 120 * s * full, 44 * s, 120 * s * full, 10 * s); ctx.fill()
    rgb(ctx, (0.2, 0.4, 0.9)); ctx.rectangle(x - 10 * s, y - 135 * s, 20 * s, 16 * s); ctx.fill()


def water_heater(ctx, t, x=540, flow=0.0, label=True):
    vgrad(ctx, -200, FLOOR, [(0, hexc("#1d1b18")), (1, hexc("#2c2924"))])
    vgrad(ctx, FLOOR, H, [(0, hexc("#25221e")), (1, hexc("#100f0d"))])
    rgb(ctx, hexc("#b7b2a6")); ctx.set_line_width(18)
    ctx.move_to(x - 70, 300); ctx.line_to(x - 70, 520); ctx.stroke(); ctx.move_to(x + 70, 300); ctx.line_to(x + 70, 520); ctx.stroke()
    rgb(ctx, hexc("#e6e2d8")); rrect(ctx, x - 200, 500, 400, 760, 60); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.12); ctx.rectangle(x + 60, 520, 120, 720); ctx.fill()
    if label:
        rgb(ctx, hexc("#2b5fa8")); rrect(ctx, x - 140, 700, 280, 150, 14); ctx.fill()
        text(ctx, "40 GAL", x, 760, 80, (1, 1, 1)); text(ctx, "WATER HEATER", x, 820, 34, (0.85, 0.9, 1))
    rgb(ctx, hexc("#9a6a2a")); ctx.rectangle(x - 30, 1180, 60, 40); ctx.fill()     # drain valve
    rgb(ctx, hexc("#c43a2a")); ctx.arc(x, 1200, 26, 0, 6.283); ctx.fill()
    if flow > 0:
        rgb(ctx, (0.55, 0.8, 1.0), 0.8 * flow); ctx.set_line_width(14 * flow)
        ctx.move_to(x, 1225)
        ctx.curve_to(x + 20, 1260, x + 40, 1300, x + 60, 1340 + 20 * math.sin(t * 20)); ctx.stroke()
        Particles(20, 2, (x + 30, 1300, x + 110, 1380), vel=(0, 120), size=(2, 4), col=(0.7, 0.9, 1), alpha=0.6 * flow).draw(ctx, t)


def rule_card(ctx, t, t0, lines, title="THE RULE OF THREES"):
    p = prog(t, t0, t0 + 0.4)
    if p <= 0:
        return
    ctx.save(); ctx.translate(W / 2, 900); s = 0.9 + 0.1 * ease_out(p); ctx.scale(s, s)
    rgb(ctx, (0.05, 0.06, 0.07), 0.9 * p); rrect(ctx, -470, -420, 940, 840, 40); ctx.fill()
    rgb(ctx, (1, 0.8, 0.25), p); rrect(ctx, -470, -420, 940, 130, 40); ctx.fill(); ctx.rectangle(-470, -330, 940, 40); ctx.fill()
    text(ctx, "RULE", 0, -355, 90, (0.1, 0.08, 0.05), p)
    text(ctx, title, 0, -200, 70, (1, 0.85, 0.4), p)
    for k, (ln, tk) in enumerate(lines):
        a = prog(t, tk, tk + 0.3) * p
        if a > 0:
            text(ctx, ln, 0, -60 + k * 120, 64, (1, 1, 1) if k != 2 else (0.5, 0.8, 1), a)
    ctx.restore()


def phones(ctx, t, on):
    rgb(ctx, hexc("#14181a")); ctx.paint()
    for k in range(6):
        x, y = 180 + (k % 3) * 360, 600 + (k // 3) * 620
        a = on * (0.6 + 0.4 * math.sin(t * 8 + k))
        rgb(ctx, hexc("#0b0c0e")); rrect(ctx, x - 130, y - 230, 260, 460, 34); ctx.fill()
        rgb(ctx, (0.75, 0.12, 0.1), a); rrect(ctx, x - 112, y - 205, 224, 410, 20); ctx.fill()
        if on > 0:
            text(ctx, "EMERGENCY", x, y - 40, 40, (1, 1, 1), on); text(ctx, "ALERT", x, y + 10, 40, (1, 0.9, 0.5), on)
            ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD); glow(ctx, x, y, 300, (1, 0.2, 0.15), 0.18 * a); ctx.restore()


def parking_lot(ctx, t):
    L.night_sky(ctx, t, 1100, moon=False)
    draw_skyline(ctx, L.CITY_NEAR, 1100, hexc("#070911"))
    vgrad(ctx, 1100, H, [(0, hexc("#1a1c22")), (1, hexc("#08090b"))])
    rgb(ctx, (0.85, 0.85, 0.7), 0.45); ctx.set_line_width(6)
    for k in range(6):
        ctx.move_to(100 + k * 180, 1200); ctx.line_to(20 + k * 220, 1500); ctx.stroke()
    rgb(ctx, hexc("#16171b")); ctx.rectangle(860, 600, 14, 520); ctx.fill()
    cone(ctx, 868, 600, math.pi / 2, 0.55, 900, (1, 0.85, 0.55), 0.25)
    glow(ctx, 868, 600, 90, (1, 0.85, 0.55), 0.9)
    rgb(ctx, hexc("#2c3e5c")); rrect(ctx, 120, 1220, 360, 130, 30); ctx.fill(); rrect(ctx, 190, 1150, 220, 90, 30); ctx.fill()


# ------------------------------------------------------------------ PART 1
def p1s1(ctx, t, d):
    knocks = [0.3, 0.55, 0.8, 2.6, 2.85, 3.1, 5.0, 5.25, 5.5]
    back_door(ctx, t, knocks, shadow=0.9)
    big_word(ctx, t, "DAY 3", 0.0, y=260, size=150)
    big_word(ctx, t, "OPEN IT?", T1.at(1, -1), y=1500, size=170, col=(1, 0.85, 0.4))
    finish(ctx, t, d, fi=0.0)


def p1s2(ctx, t, d):
    store(ctx, t, seed=2); counter(ctx, t)
    pharmacy_sign(ctx, t)
    person(ctx, 700, 1080, SP, "idle", face=-1, breathe=math.sin(t * 2), head_turn=0.3 * math.sin(t * 0.7))
    rgb(ctx, hexc("#d9d3c4")); ctx.rectangle(380, 1080, 520, 220); ctx.fill()
    rgb(ctx, hexc("#2e8a5a")); ctx.rectangle(380, 1080, 520, 26); ctx.fill()
    text(ctx, "OPEN 24 HOURS", W / 2, 1600, 70, (0.75, 1, 0.8), prog(t, 0.3, 0.8), outline=8)
    finish(ctx, t, d)


def p1s3(ctx, t, d):
    store(ctx, t, seed=3); counter(ctx, t, 540)
    write = math.sin(t * 6) * 0.2
    person(ctx, 420, 1300, 290, "sit", face=1, pal=MIA, arm_f=(1.3 + write, -0.9), head_turn=0.5 * (t > T1.at(3, 1)))
    rgb(ctx, hexc("#f2efe6")); ctx.rectangle(470, 1060, 120, 18); ctx.fill()
    text(ctx, "MIA, 7", W / 2, 360, 100, (1, 0.7, 0.8), prog(t, T1.at(3, 1), T1.at(3, 1) + 0.4), outline=10)
    finish(ctx, t, d)


def p1s4(ctx, t, d):
    phones(ctx, t, ease(prog(t, T1.at(4, 0) + 1.0, T1.at(4, 0) + 1.3)))
    finish(ctx, t, d, fi=0.05)


def p1s5(ctx, t, d):
    store(ctx, t, light=0.7, seed=5); counter(ctx, t, 540)
    radio(ctx, t, 540, 1080, 0.6 + 0.4 * math.sin(t * 10))
    for k, (line, ph) in enumerate([("STAY INSIDE", 0), ("LOCK YOUR DOORS", 1), ("DO NOT LET ANYONE IN", 2)]):
        a = prog(t, T1.at(5, min(ph + 1, 2)), T1.at(5, min(ph + 1, 2)) + 0.3)
        if a > 0:
            rgb(ctx, (0.7, 0.1, 0.1), 0.85 * a); rrect(ctx, 90, 330 + k * 140, 900, 110, 16); ctx.fill()
            text(ctx, line, W / 2, 385 + k * 140, 66, (1, 1, 1), a)
    finish(ctx, t, d)


def p1s6(ctx, t, d):
    parking_lot(ctx, t)
    fast = prog(t, T1.at(6, -1), d)
    for k in range(5):
        x = 150 + k * 190 + (t * (20 + 160 * fast)) * (1 if k % 2 else 0.6)
        zombie(ctx, x % (W + 200) - 100, 1250 + (k % 3) * 70, 300 + 30 * (k % 2), t, k, speed=1 + 3 * fast)
    rgb(ctx, (0, 0, 0), 0.25); ctx.paint()
    finish(ctx, t, d)


def p1s7(ctx, t, d):
    down = ease(prog(t, 0.3, T1.at(7, -1) + 0.3)) * 0.97
    slam = T1.at(7, -1) + 0.3
    sh = math.exp(-(t - slam) * 10) * 12 if t > slam else 0
    ctx.save(); ctx.translate(wobble(t, 1, 40) * sh, 0)
    parking_lot(ctx, t)
    for k in range(3):
        zombie(ctx, 260 + k * 250, 1250, 330, t, k, speed=1.6)
    shutter(ctx, t, down=down, top=0, bottom=FLOOR + 80)
    if t > slam:
        rgb(ctx, ZOMB[0]); ctx.set_line_width(40); ctx.set_line_cap(1)
        ctx.move_to(520, FLOOR + 80); ctx.line_to(560, FLOOR + 30); ctx.stroke()
    ctx.restore()
    finish(ctx, t, d)


def p1s8(ctx, t, d):
    store(ctx, t, light=0.6, seed=8)
    person(ctx, 400, 1400, SP, "sit", face=1, breathe=math.sin(t * 2))
    person(ctx, 640, 1400, 290, "sit", face=-1, pal=MIA, breathe=math.sin(t * 2.5))
    finish(ctx, t, d)


def p1s9(ctx, t, d):
    rgb(ctx, hexc("#1c2124")); ctx.paint()
    r = random.Random(9)
    for k in range(int(40 * ease(prog(t, 0, d * 0.7)))):
        x, y = r.uniform(140, 940), 1400 - (k // 9) * 70 - r.uniform(0, 30)
        rgb(ctx, r.choice(BOX_COLS)); rrect(ctx, x - 60, y - 40, 120, 70, 14); ctx.fill()
    text(ctx, "FOOD: WEEKS", W / 2, 420, 110, (0.6, 1, 0.7), prog(t, T1.at(9, -1), T1.at(9, -1) + 0.4), outline=10)
    finish(ctx, t, d)


def p1s10(ctx, t, d):
    rgb(ctx, hexc("#1b2023")); ctx.paint()
    rgb(ctx, hexc("#b9bdc1")); rrect(ctx, 240, 1000, 600, 260, 30); ctx.fill()
    rgb(ctx, hexc("#9aa0a4")); ctx.set_line_width(40); ctx.set_line_cap(1)
    ctx.move_to(540, 1000); ctx.line_to(540, 700); ctx.line_to(700, 700); ctx.line_to(700, 760); ctx.stroke()
    stop = T1.at(10, -1) + 0.6
    if t < stop:
        Particles(14, 4, (690, 780, 712, 1000), vel=(0, 600), size=(5, 9), col=(0.6, 0.85, 1), alpha=0.8).draw(ctx, t)
    elif (t - stop) < 2.0 and (t * 1.2) % 1 < 0.15:
        rgb(ctx, (0.6, 0.85, 1)); ctx.arc(700, 790 + ((t * 1.2) % 1) * 1300, 8, 0, 6.283); ctx.fill()
    big_word(ctx, t, "DAY 2", 0.2, y=330, size=140)
    finish(ctx, t, d)


def fridge(ctx, t, n):
    rgb(ctx, hexc("#1a1e20")); ctx.paint()
    rgb(ctx, hexc("#d8dde0")); rrect(ctx, 190, 300, 700, 1300, 30); ctx.fill()
    rgb(ctx, (0.8, 0.92, 1.0), 0.25); rrect(ctx, 230, 340, 620, 1220, 20); ctx.fill()
    glow(ctx, 540, 900, 500, (0.8, 0.92, 1), 0.25)
    for row in range(3):
        rgb(ctx, hexc("#aab3b8")); ctx.rectangle(230, 680 + row * 330, 620, 10); ctx.fill()
    for k in range(int(n)):
        bottle(ctx, 300 + (k % 6) * 95, 670 + (k // 6) * 330, 0.9)


def p1s11(ctx, t, d):
    n = 11 if t < T1.at(11, 1) else 2
    fridge(ctx, t, n)
    big_word(ctx, t, "11", 0.2, y=1500, size=150, col=(0.5, 0.8, 1)) if t < T1.at(11, 1) else big_word(ctx, t, "2", T1.at(11, 1), y=1500, size=170, col=(1, 0.4, 0.3))
    finish(ctx, t, d)


def p1s12(ctx, t, d):
    knocks = [T1.at(12, -1) + k * 0.25 for k in range(3)] + [T1.at(12, -1) + 2 + k * 0.25 for k in range(3)]
    back_door(ctx, t, knocks, shadow=0.9)
    finish(ctx, t, d)


def p1s13(ctx, t, d):
    z = 1 + 0.25 * ease(t / d)
    ctx.save(); ctx.translate(540, FLOOR); ctx.scale(z, z); ctx.translate(-540, -FLOOR)
    back_door(ctx, t, [], shadow=1.0)
    ctx.restore()
    for k, (w, ph) in enumerate([("PLEASE.", 1), ("I'M NOT SICK.", 2), ("I HAVE WATER.", 3)]):
        a = prog(t, T1.at(13, ph), T1.at(13, ph) + 0.3)
        if a > 0:
            text(ctx, w, W / 2, 1540 + k * 120, 84, (0.9, 0.9, 0.85), a, font="DejaVu Serif", outline=6)
    finish(ctx, t, d)


def p1s14(ctx, t, d):
    store(ctx, t, light=0.6, seed=14)
    person(ctx, 380, 1400, 520, "idle", face=1, breathe=math.sin(t * 4), head_turn=-0.6 * prog(t, T1.at(14, 1), d))
    person(ctx, 660, 1400, 330, "idle", face=-1, pal=MIA, head_turn=0.4)
    finish(ctx, t, d)


def p1s15(ctx, t, d):
    back_door(ctx, t, [0.6, 0.85, 1.1], shadow=0.9)
    rgb(ctx, (0, 0, 0), 0.35); ctx.paint()
    end_card(ctx, t, T1, 15, "OPEN", "IT?", "COMMENT: YES OR NO", "PART 2 IS UP NEXT")
    finish(ctx, t, d, fo=0.25)


# ------------------------------------------------------------------ PART 2
def p2s1(ctx, t, d):
    back_door(ctx, t, [0.4, 0.65, 0.9], shadow=0.9)
    text(ctx, "PREVIOUSLY", W / 2, 260, 80, (1, 1, 1), 0.8, outline=8)
    finish(ctx, t, d, fi=0.0)


def under_door(ctx, t, twist=0.0):
    rgb(ctx, hexc("#0c0d0e")); ctx.paint()
    rgb(ctx, (1, 0.85, 0.6), 0.55); ctx.rectangle(0, 820, W, 280); ctx.fill()
    for k, x in enumerate((360, 660)):
        a = twist * 1.6 if k == 1 else 0
        ctx.save(); ctx.translate(x, 1080); ctx.rotate(a)
        rgb(ctx, hexc("#151515")); rrect(ctx, -90, -70, 200, 80, 30); ctx.fill()
        rgb(ctx, ZOMB[3]); ctx.rectangle(-30, -300, 70, 240); ctx.fill()
        ctx.restore()
    rgb(ctx, hexc("#0c0d0e")); ctx.rectangle(0, 0, W, 820); ctx.fill(); ctx.rectangle(0, 1100, W, H); ctx.fill()


def p2s2(ctx, t, d):
    under_door(ctx, t)
    finish(ctx, t, d)


def p2s3(ctx, t, d):
    under_door(ctx, t, twist=ease(prog(t, T2.at(3, -1) + 0.2, T2.at(3, -1) + 1.4)))
    finish(ctx, t, d)


def p2s4(ctx, t, d):
    back_door(ctx, t, [], shadow=0.9)
    person(ctx, lerp(560, 300, ease(prog(t, 0.2, d))), 1500, 560, "idle", face=1, back_view=True, breathe=math.sin(t * 5))
    finish(ctx, t, d)


def p2s5(ctx, t, d):
    knock_end = T2.at(5, 1)
    knocks = [k * 1.1 + j * 0.25 for k in range(int(knock_end / 1.1)) for j in range(3)]
    back_door(ctx, t, knocks, shadow=0.9)
    ang = t * 0.9
    rgb(ctx, hexc("#e9e4d8")); ctx.arc(540, 250, 110, 0, 6.283); ctx.fill()
    rgb(ctx, hexc("#222222")); ctx.set_line_width(10); ctx.move_to(540, 250); ctx.line_to(540 + math.sin(ang) * 80, 250 - math.cos(ang) * 80); ctx.stroke()
    finish(ctx, t, d)


def p2s6(ctx, t, d):
    store(ctx, t, light=0.5, seed=6)
    rgb(ctx, (0, 0, 0), 0.5); ctx.paint()
    rule_card(ctx, t, T2.at(6, 1), [])
    finish(ctx, t, d)


def p2s7(ctx, t, d):
    store(ctx, t, light=0.5, seed=7)
    rgb(ctx, (0, 0, 0), 0.5); ctx.paint()
    lines = ["3 MIN WITHOUT AIR", "3 HRS WITHOUT SHELTER", "3 DAYS WITHOUT WATER", "3 WEEKS WITHOUT FOOD"]
    rule_card(ctx, t, -1, [(ln, T2.at(7, k) if k < len(T2.seg.get(7, [])) else 0.5 + k) for k, ln in enumerate(lines)])
    finish(ctx, t, d, fi=0.0)


def p2s8(ctx, t, d):
    rgb(ctx, hexc("#1c2124")); ctx.paint()
    rgb(ctx, hexc("#d9d3c4")); ctx.rectangle(0, 1180, W, 400); ctx.fill()
    bottle(ctx, 420, 1180, 2.2, 0.9); bottle(ctx, 660, 1180, 2.2, 0.9)
    big_word(ctx, t, "DAY 3", T2.at(8, -1), y=400, size=170, col=(1, 0.4, 0.3))
    finish(ctx, t, d)


def p2s9(ctx, t, d):
    store(ctx, t, light=0.6, seed=9)
    drink = math.sin(prog(t, 0.3, d * 0.6) * math.pi)
    info = person(ctx, 600, 1400, 330, "sit", face=-1, pal=MIA, arm_f=(1.6 + 0.8 * drink, -1.2), head_turn=0.5 * prog(t, T2.at(9, 1), d))
    bottle(ctx, info["hand"][0], info["hand"][1] + 40, 0.7, 0.5)
    person(ctx, 340, 1400, SP, "sit", face=1, breathe=math.sin(t * 2))
    finish(ctx, t, d)


def p2s10(ctx, t, d):
    store(ctx, t, light=0.4, seed=10)
    rgb(ctx, hexc("#3a3a44")); rrect(ctx, 220, 1330, 640, 80, 20); ctx.fill()
    ctx.save(); ctx.translate(540, 1330); ctx.rotate(-math.pi / 2); ctx.translate(-540, -1330)
    person(ctx, 540, 1080, 330, "idle", face=1, pal=MIA, breathe=math.sin(t * 1.5) * 2)
    ctx.restore()
    person(ctx, 820, 1420, SP, "idle", face=-1, crouch=0.5, arm_f=(1.6, 0.4))
    finish(ctx, t, d, v=0.95)


def p2s11(ctx, t, d):
    dent = ease(prog(t, T2.at(11, 1), d))
    shake = math.sin(t * 30) * 4 * (0.3 + dent)
    ctx.save(); ctx.translate(shake, 0)
    store(ctx, t, light=0.5, seed=11)
    shutter(ctx, t, 1.0, dent=0.3 + 0.7 * dent, x0=80, x1=1000, top=420)
    ctx.restore()
    finish(ctx, t, d)


def p2s12(ctx, t, d):
    store(ctx, t, light=0.6, empty=0.97, seed=12)
    person(ctx, lerp(200, 880, (t / d)), 1400, SP, "walk", phase=t * 7, face=1, head_turn=math.sin(t * 3))
    for k, w in enumerate(["SPORTS DRINKS", "SODA", "ICE"]):
        a = prog(t, T2.at(12, k + 1) if k + 1 < len(T2.seg.get(12, [])) else 1 + k, (T2.at(12, k + 1) if k + 1 < len(T2.seg.get(12, [])) else 1 + k) + 0.3)
        if a > 0:
            text(ctx, w + ": GONE", W / 2, 330 + k * 110, 72, (1, 0.45, 0.35), a, outline=8)
    finish(ctx, t, d)


def p2s13(ctx, t, d):
    rgb(ctx, hexc("#141819")); ctx.paint()
    glow(ctx, 540, 900, 700, (0.9, 0.6, 0.6), 0.12)
    person(ctx, 540, 1650, 1100, "idle", face=1, pal=MIA, head_turn=0.2, breathe=math.sin(t * 1.4) * 2)
    finish(ctx, t, d, v=0.95)


def p2s14(ctx, t, d):
    water_heater(ctx, t, label=False)
    rgb(ctx, (0, 0, 0), 0.75); ctx.paint()
    end_card(ctx, t, T2, 14, "WHERE'S", "WATER?", "COMMENT YOUR GUESS", "PART 3 IS UP NEXT")
    finish(ctx, t, d, fo=0.25)


# ------------------------------------------------------------------ PART 3
def p3s1(ctx, t, d):
    store(ctx, t, light=0.5, seed=21)
    shutter(ctx, t, 1.0, dent=0.8, x0=80, x1=1000, top=420)
    turn = prog(t, T3.at(1, -1), d)
    person(ctx, 540, 1500, 560, "idle", face=1 if turn < 0.5 else -1, back_view=turn < 0.5, breathe=math.sin(t * 4))
    finish(ctx, t, d, fi=0.0)


def p3s2(ctx, t, d):
    water_heater(ctx, t, label=t > T3.at(2, -1))
    glow(ctx, 540, 880, 600, (0.5, 0.8, 1), 0.2 * prog(t, T3.at(2, 1), d))
    finish(ctx, t, d)


def p3s3(ctx, t, d):
    rgb(ctx, hexc("#1d1b18")); ctx.paint()
    rgb(ctx, hexc("#3a3d40")); rrect(ctx, 240, 360, 600, 1100, 20); ctx.fill()
    flip = ease(prog(t, T3.at(3, 0) + 1.0, T3.at(3, 0) + 1.4))
    for k in range(8):
        y = 460 + k * 120
        rgb(ctx, hexc("#202224")); rrect(ctx, 300, y, 200, 80, 10); ctx.fill(); rrect(ctx, 580, y, 200, 80, 10); ctx.fill()
        on = not (k == 5 and flip > 0.5)
        rgb(ctx, (0.85, 0.85, 0.8)); rrect(ctx, 300 + (120 if on else 20), y + 10, 60, 60, 8); ctx.fill()
    rgb(ctx, (1, 0.85, 0.3)); text(ctx, "WATER HEATER", 400, 1105, 26, (1, 0.85, 0.3))
    text(ctx, "POWER OFF", W / 2, 260, 100, (1, 1, 1), flip, outline=10)
    finish(ctx, t, d)


def p3s4(ctx, t, d):
    rgb(ctx, hexc("#1b2023")); ctx.paint()
    rgb(ctx, hexc("#b9bdc1")); rrect(ctx, 240, 1000, 600, 260, 30); ctx.fill()
    rgb(ctx, hexc("#9aa0a4")); ctx.set_line_width(40); ctx.set_line_cap(1)
    ctx.move_to(540, 1000); ctx.line_to(540, 700); ctx.line_to(700, 700); ctx.line_to(700, 760); ctx.stroke()
    turn = ease(prog(t, 0.4, 1.4))
    ctx.save(); ctx.translate(450, 860); ctx.rotate(turn * 1.5)
    rgb(ctx, (0.85, 0.2, 0.15)); ctx.rectangle(-70, -14, 140, 28); ctx.fill(); ctx.restore()
    text(ctx, "HOT TAP OPEN", W / 2, 320, 96, (1, 0.6, 0.4), turn, outline=10)
    text(ctx, "lets air in", W / 2, 430, 60, (0.9, 0.9, 0.9), turn, outline=6)
    finish(ctx, t, d)


def p3s5(ctx, t, d):
    flow = ease(prog(t, T3.at(5, 1), T3.at(5, 1) + 0.6))
    water_heater(ctx, t, flow=flow)
    bottle(ctx, 640, 1420, 1.4, min(1, max(0, t - T3.at(5, 1)) / 3))
    finish(ctx, t, d)


def p3s6(ctx, t, d):
    store(ctx, t, light=0.8, seed=26)
    drink = prog(t, 0.2, T3.at(6, 1))
    laugh = abs(math.sin(t * 8)) * 25 * (t > T3.at(6, -1))
    info = person(ctx, 560, 1400 - laugh, 360, "idle", face=-1, pal=MIA, arm_f=(2.3 * (1 - prog(t, T3.at(6, 1), T3.at(6, 1) + 0.4)) + 0.3, -1.0))
    if drink < 1:
        bottle(ctx, info["hand"][0], info["hand"][1] + 40, 0.8, 1 - drink)
    person(ctx, 320, 1400, SP, "idle", face=1, breathe=math.sin(t * 2), head_turn=0.4)
    finish(ctx, t, d, v=0.7)


def p3s7(ctx, t, d):
    rgb(ctx, hexc("#1c2124")); ctx.paint()
    n = int(30 * ease(prog(t, 0.2, d * 0.8)))
    for k in range(n):
        bottle(ctx, 150 + (k % 10) * 85, 1450 - (k // 10) * 210, 1.0)
    big_word(ctx, t, "40 GALLONS", 0.3, y=380, size=150, col=(0.5, 0.8, 1))
    finish(ctx, t, d)


def p3s8(ctx, t, d):
    store(ctx, t, light=0.6, seed=28, empty=0.5)
    shutter(ctx, t, 1.0, dent=0.6, x0=80, x1=1000, top=420)
    n = ease(prog(t, 0.3, d * 0.8))
    for k in range(int(5 * n) + 1):
        rgb(ctx, hexc("#5c6466")); ctx.rectangle(120 + k * 170, 1050, 150, 250); ctx.fill()
    person(ctx, lerp(900, 200, (t * 0.4) % 1), 1420, SP, "walk", phase=t * 6, face=-1, lean=0.2, arm_f=(1.5, -0.6))
    finish(ctx, t, d)


def p3s9(ctx, t, d):
    store(ctx, t, light=0.7, seed=29)
    rgb(ctx, hexc("#3d2f28")); ctx.rectangle(0, 1380, W, 400); ctx.fill()
    person(ctx, 330, 1400, SP, "sit", face=1, arm_f=(1.0, -0.5))
    person(ctx, 720, 1400, 300, "sit", face=-1, pal=MIA, arm_f=(1.2 + 0.4 * math.sin(t * 3), -0.6))
    r = random.Random(int(t * 2))
    for k in range(6):
        rgb(ctx, (0.95, 0.95, 0.92)); ctx.save(); ctx.translate(430 + k * 45, 1480 + r.uniform(-8, 8)); ctx.rotate(r.uniform(-0.3, 0.3))
        rrect(ctx, -26, -36, 52, 72, 6); ctx.fill(); rgb(ctx, (0.8, 0.15, 0.15)); ctx.arc(0, 0, 8, 0, 6.283); ctx.fill(); ctx.restore()
    big_word(ctx, t, "DAY 5" if t < T3.at(9, 1) else "DAY 6", 0.2 if t < T3.at(9, 1) else T3.at(9, 1), y=330, size=140)
    finish(ctx, t, d)


def p3s10(ctx, t, d):
    store(ctx, t, light=0.7, seed=30)
    shutter(ctx, t, 1.0, dent=0.6, x0=80, x1=1000, top=420)
    pulse = (math.sin(t * 6) > 0) * prog(t, T3.at(10, 1), d)
    for k, col in enumerate(((1, 0.2, 0.2), (0.2, 0.4, 1))):
        rgb(ctx, col, 0.35 * pulse * (k == int(t * 3) % 2)); ctx.rectangle(80, 420, 920, 880); ctx.fill()
    big_word(ctx, t, "DAY 7", 0.2, y=280, size=140)
    finish(ctx, t, d)


def p3s11(ctx, t, d):
    knocks = [T3.at(11, -1) + k * 0.3 for k in range(3)]
    shk = sum(math.exp(-(t - b) * 12) * 8 * math.sin((t - b) * 60) for b in knocks if t >= b)
    ctx.save(); ctx.translate(shk, 0)
    store(ctx, t, light=0.7, seed=31)
    shutter(ctx, t, 1.0, dent=0.5, x0=80, x1=1000, top=420)
    ctx.restore()
    text(ctx, "ANYONE INSIDE?", W / 2, 300, 100, (1, 1, 1), prog(t, 0.2, 0.6), outline=10)
    finish(ctx, t, d)


def p3s12(ctx, t, d):
    up = ease(prog(t, T3.at(12, -1) + 0.3, d))
    store(ctx, t, light=0.7, seed=32)
    shutter(ctx, t, 1 - up * 0.95, dent=0.5, x0=80, x1=1000, top=420, glow_out=1.0)
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD); glow(ctx, 540, 900, 900, (1, 0.8, 0.5), 0.35 * up); ctx.restore()
    person(ctx, 540, 1500, 560, "idle", face=1, back_view=True, arm_f=(2.4 * (1 - up), 0.3))
    finish(ctx, t, d, v=0.6)


def p3s13(ctx, t, d):
    vgrad(ctx, -200, 1100, [(0, hexc("#2b3a6b")), (0.6, hexc("#d98a6a")), (1, hexc("#f6c77e"))])
    glow(ctx, 540, 1080, 700, (1, 0.8, 0.5), 0.5)
    rgb(ctx, (1, 0.9, 0.6)); ctx.arc(540, 1100, 80, math.pi, 2 * math.pi); ctx.fill()
    vgrad(ctx, 1100, H, [(0, hexc("#4a4a50")), (1, hexc("#2a2a2e"))])
    for k, x in enumerate((180, 600)):
        rgb(ctx, hexc("#4a5238")); rrect(ctx, x, 980, 360, 200, 20); ctx.fill(); rrect(ctx, x + 230, 900, 130, 120, 14); ctx.fill()
        rgb(ctx, hexc("#151515")); ctx.arc(x + 80, 1190, 46, 0, 6.283); ctx.fill(); ctx.arc(x + 290, 1190, 46, 0, 6.283); ctx.fill()
        if k == 1:
            rgb(ctx, (1, 1, 1)); text(ctx, "WATER", x + 120, 1080, 46, (1, 1, 1))
        if (t * 2 + k) % 1 < 0.5:
            glow(ctx, x + 300, 890, 50, (1, 0.6, 0.2), 0.9)
    for k in range(4):
        person(ctx, 150 + k * 260, 1450, 380, "idle", face=1 if k % 2 else -1, pal=SOLDIER, breathe=math.sin(t * 2 + k))
    finish(ctx, t, d, v=0.5)


def p3s14(ctx, t, d):
    vgrad(ctx, -200, 1100, [(0, hexc("#5a6a9b")), (0.6, hexc("#e9a37a")), (1, hexc("#fad58e"))])
    vgrad(ctx, 1100, H, [(0, hexc("#5a5a60")), (1, hexc("#33333a"))])
    rgb(ctx, hexc("#4a5238")); rrect(ctx, 760, 960, 360, 220, 20); ctx.fill()
    w = prog(t, 0, d)
    x = lerp(200, 700, w)
    person(ctx, x, 1400, SP, "walk", phase=t * 5, face=1, arm_b=(-0.4, 0.2))
    person(ctx, x - 150, 1400, 290, "walk", phase=t * 6 + 1, face=1, pal=MIA, arm_f=(1.0, 0.2))
    finish(ctx, t, d, v=0.5)


def p3s15(ctx, t, d):
    water_heater(ctx, t, flow=0.6)
    rgb(ctx, (0, 0, 0), 0.75); ctx.paint()
    end_card(ctx, t, T3, 15, "KNEW", "THAT?", "COMMENT: YES OR NO", "NEW STORY TOMORROW")
    finish(ctx, t, d, fo=0.3)


P1 = [p1s1, p1s2, p1s3, p1s4, p1s5, p1s6, p1s7, p1s8, p1s9, p1s10, p1s11, p1s12, p1s13, p1s14, p1s15]
P2 = [p2s1, p2s2, p2s3, p2s4, p2s5, p2s6, p2s7, p2s8, p2s9, p2s10, p2s11, p2s12, p2s13, p2s14]
P3 = [p3s1, p3s2, p3s3, p3s4, p3s5, p3s6, p3s7, p3s8, p3s9, p3s10, p3s11, p3s12, p3s13, p3s14, p3s15]


# ------------------------------------------------------------------ sound
def hum(d, amt=1.0):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * 120 * t) * 0.04 + band_noise(d, 100, 400, 3) * 0.04) * amt


def knock_sfx(d, times):
    return env_at(d, times, 0.12) * (tone(d, 90) * 0.8 + band_noise(d, 80, 1500, 9) * 0.5)


def groans(d, seed, amt=1.0):
    x = silence(d); rng = np.random.default_rng(seed)
    for t0 in rng.uniform(0, max(0.1, d - 1.2), max(1, int(d / 2.5))):
        i, n = int(t0 * SR), int(1.1 * SR)
        if i + n > len(x):
            continue
        tt = np.arange(n) / SR
        f = 95 + 25 * np.sin(2 * np.pi * 1.3 * tt) + rng.uniform(-15, 15)
        v = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.sin(np.pi * tt / 1.1) ** 1.5
        x[i:i + n] += v * 0.05 * amt
    return x + band_noise(d, 80, 500, seed) * 0.03 * amt


def alarm(d, start):
    t = np.arange(int(d * SR)) / SR
    on = (t > start) & ((t * 2.5) % 1 < 0.6)
    return (np.sin(2 * np.pi * 950 * t) + 0.5 * np.sin(2 * np.pi * 1900 * t)) * 0.08 * on


def sfx_for(tm, part):
    def sfx(i, d):
        t = np.arange(int(d * SR)) / SR
        x = hum(d)
        if part == 1:
            if i in (1, 12, 13, 15):
                ks = {1: [0.3, 0.55, 0.8, 2.6, 2.85, 3.1, 5.0, 5.25, 5.5], 12: [tm.at(12, -1) + k * 0.25 for k in range(3)] + [tm.at(12, -1) + 2 + k * 0.25 for k in range(3)],
                      13: [], 15: [0.6, 0.85, 1.1]}[i]
                x += knock_sfx(d, ks) + L.heart(d, 80) * 0.6
            if i == 4:
                x += alarm(d, tm.at(4, 0) + 1.0)
            if i == 5:
                x += band_noise(d, 900, 5000, 5) * 0.06
            if i in (6, 7):
                x = groans(d, i, 1.4) + wind(d, 0.5, i)
            if i == 7:
                x += env_at(d, [0.3], d) * band_noise(d, 200, 2000, 7) * 0.15 + env_at(d, [tm.at(7, -1) + 0.3], 0.6) * (tone(d, 60) + band_noise(d, 50, 800, 8)) * 0.9
            if i == 10:
                stop = tm.at(10, -1) + 0.6
                x += band_noise(d, 800, 5000, 10) * 0.15 * (t < stop)
        elif part == 2:
            if i in (1, 5):
                ks = [0.4, 0.65, 0.9] if i == 1 else [k * 1.1 + j * 0.25 for k in range(int(tm.at(5, 1) / 1.1)) for j in range(3)]
                x += knock_sfx(d, ks)
            if i == 3:
                x += env_at(d, [tm.at(3, -1) + 0.3], 0.6) * band_noise(d, 100, 1500, 3) * 0.4
            if i in (2, 3, 4, 13):
                x += L.heart(d, 90) * 0.7
            if i == 5:
                x += env_at(d, [k * 1.0 for k in range(int(d))], 0.03) * band_noise(d, 3000, 8000, 5) * 0.25 * (t > tm.at(5, 1))
            if i == 11:
                x += groans(d, 11, 2.0) + env_at(d, list(np.arange(tm.at(11, 1), d, 0.45)), 0.25) * (tone(d, 70) + band_noise(d, 80, 1200, 11) * 0.6) * 0.7
        else:
            if i in (1, 8):
                x += groans(d, 30 + i, 1.2)
            if i == 3:
                x += env_at(d, [tm.at(3, 0) + 1.2], 0.08) * band_noise(d, 1000, 6000, 3) * 0.6
            if i == 5:
                x += band_noise(d, 400, 6000, 35) * 0.18 * (t > tm.at(5, 1))
            if i == 6:
                x += env_at(d, list(np.arange(tm.at(6, -1), d, 0.25)), 0.08) * tone(d, 520) * 0.05
            if i == 10:
                x += alarm(d, 99) + tone(d, 45) * 0.15 * np.clip((t - tm.at(10, 1)) / 2, 0, 1) + band_noise(d, 60, 300, 40) * 0.2
            if i == 11:
                x += knock_sfx(d, [tm.at(11, -1) + k * 0.3 for k in range(3)]) * 1.5
            if i == 12:
                up = tm.at(12, -1) + 0.3
                x += band_noise(d, 200, 3000, 12) * 0.25 * ((t > up) & (t < d - 0.5))
            if i in (13, 14):
                x = hum(d, 0.2) + wind(d, 0.3, i) + tone(d, 60) * 0.05
        return fades(x * 0.6, 0.03, 0.1)
    return sfx


def music1(durs):
    return piano_score(sum(durs), 0.0)


def music2(durs):
    return piano_score(sum(durs), 0.0)


def music3(durs):
    turn = sum(durs[:5])
    total = sum(durs)
    tense = piano_score(turn, 0.0)
    warm = piano_score(total - turn, total + 100, bpm=72, seed=5)
    return np.concatenate([tense, warm])[: int(total * SR)]


PARTS = {1: ("26_nightshift_1", P1, sfx_for(T1, 1), music1), 2: ("27_nightshift_2", P2, sfx_for(T2, 2), music2),
         3: ("28_nightshift_3", P3, sfx_for(T3, 3), music3)}

if __name__ == "__main__":
    run(PARTS, {1: T1, 2: T2, 3: T3})
