"""Animated scenes for stories/20_lights_at_914.json - "Every Night At 9:14" Part 1.

    python src/voice.py stories/20_lights_at_914.json     # first (visuals sync to the speech)
    python src/anim/lights.py
    python src/assemble.py stories/20_lights_at_914.json
"""
import json, math, pathlib, random, sys
from multiprocessing import Pool

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import *  # noqa

ROOT = pathlib.Path(__file__).resolve().parents[2]
SID = "20_lights_at_914"
GY = 1250
S = 430
OUT = ROOT / "out" / SID


def segs(i):
    p = OUT / f"scene_{i:02d}.json"
    return json.loads(p.read_text()) if p.exists() else [["", 0, 5]]


SEG = {i: segs(i) for i in range(1, 17)}


def at(i, k):
    """Start time of the k-th spoken phrase in scene i (negative k counts from the end)."""
    s = SEG[i]
    return s[k][1] if -len(s) <= k < len(s) else s[-1][1]


# ------------------------------------------------------------------ sets & props
CITY_FAR = skyline(31, 0, GY, 300, 820, 60, 150)
CITY_NEAR = skyline(32, 0, GY, 160, 480, 100, 210)
RIVER_CITY = skyline(33, 0, 1050, 200, 700, 60, 140)
STARS = [(random.Random(k).uniform(0, W), random.Random(k + 999).uniform(0, 900), random.Random(k + 7).uniform(1, 2.6)) for k in range(160)]


def night_sky(ctx, t, bottom=GY, moon=True):
    vgrad(ctx, -400, bottom, [(0, hexc("#03050c")), (0.7, hexc("#0c1224")), (1, hexc("#1a2036"))])
    for k, (x, y, r) in enumerate(STARS):
        rgb(ctx, (1, 1, 1), 0.35 + 0.35 * math.sin(t * 1.3 + k))
        ctx.arc(x, y, r, 0, 6.283); ctx.fill()
    if moon:
        glow(ctx, 860, 600, 260, (0.8, 0.85, 1.0), 0.25)
        rgb(ctx, hexc("#e9ecf5")); ctx.arc(860, 600, 70, 0, 6.283); ctx.fill()
        rgb(ctx, hexc("#d5d9e6")); ctx.arc(840, 585, 14, 0, 6.283); ctx.fill(); ctx.arc(882, 625, 9, 0, 6.283); ctx.fill()


def city_lights(ctx, bld, base_y, col, level, t, seed=0, offset=0.0):
    """Skyline whose windows switch on with `level` 0..1 (each window has its own threshold)."""
    draw_skyline(ctx, bld, base_y, col, offset=offset)
    if level <= 0:
        return
    for i, (x, w, h, wins, cut) in enumerate(bld):
        for k, (u, v) in enumerate(wins):
            th = ((k * 0.618 + i * 0.37 + seed) % 1)
            if level > th:
                a = clamp((level - th) * 6) * (0.75 + 0.25 * math.sin(t * 9 + k))
                c = (1.0, 0.82, 0.45) if (k + i) % 5 else (0.75, 0.9, 1.0)
                rgb(ctx, c, a)
                ctx.rectangle(x + offset + 6 + u * (w - 18), base_y - h + 10 + v * (h - 30), 8, 11); ctx.fill()


def parapet(ctx, y=1180):
    rgb(ctx, hexc("#23262f")); ctx.rectangle(0, y, W, H - y); ctx.fill()
    rgb(ctx, hexc("#353946")); ctx.rectangle(0, y, W, 22); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.25)
    for x in range(0, W, 120):
        ctx.rectangle(x, y + 22, 3, 140); ctx.fill()


def sit_back(ctx, x, y, s, head_turn=0.0, breathe=0.0):
    """Character sitting on a ledge, seen from behind (y = ledge top)."""
    rgb(ctx, HOODIE)
    rrect(ctx, x - 0.13 * s, y - 0.36 * s - breathe * 3, 0.26 * s, 0.38 * s, 0.07 * s); ctx.fill()
    rgb(ctx, HOODIE_D)
    rrect(ctx, x - 0.2 * s, y - 0.33 * s, 0.08 * s, 0.3 * s, 0.04 * s); ctx.fill()
    rrect(ctx, x + 0.12 * s, y - 0.33 * s, 0.08 * s, 0.3 * s, 0.04 * s); ctx.fill()
    hx = x + head_turn * 0.03 * s
    rgb(ctx, HOODIE); ctx.arc(hx, y - 0.45 * s - breathe * 3, 0.105 * s, 0, 6.283); ctx.fill()
    rgb(ctx, HOODIE_D, 0.6); ctx.arc(hx, y - 0.44 * s - breathe * 3, 0.06 * s, 0, 6.283); ctx.fill()


def silhouette(ctx, x, y, s, wave=0.0, sign=0.0, col=(0.05, 0.04, 0.05)):
    """Dark figure standing in a window. wave = arm angle; sign 0..1 raises a sign in front."""
    rgb(ctx, col)
    ctx.arc(x, y - 0.88 * s, 0.1 * s, 0, 6.283); ctx.fill()
    rrect(ctx, x - 0.13 * s, y - 0.76 * s, 0.26 * s, 0.76 * s, 0.06 * s); ctx.fill()
    ctx.set_line_width(0.07 * s); ctx.set_line_cap(1)
    if sign <= 0:
        ctx.move_to(x + 0.12 * s, y - 0.7 * s)
        ctx.line_to(x + 0.12 * s + math.sin(1.9 + wave) * 0.3 * s, y - 0.7 * s - math.cos(1.9 + wave) * 0.3 * s * -1)
        ctx.stroke()


def sign_card(ctx, cx, cy, w, h, lines, flip=1.0, size=70):
    """White cardboard sign, flip = horizontal scale (for turning it over)."""
    ctx.save(); ctx.translate(cx, cy); ctx.scale(max(0.02, abs(flip)), 1)
    rgb(ctx, hexc("#efe9dc")); rrect(ctx, -w / 2, -h / 2, w, h, 10); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.15); ctx.set_line_width(4); rrect(ctx, -w / 2, -h / 2, w, h, 10); ctx.stroke()
    n = len(lines)
    for k, ln in enumerate(lines):
        text(ctx, ln, 0, (k - (n - 1) / 2) * size * 1.15, size, hexc("#1a1414"))
    ctx.restore()


def binoculars(ctx, t, shake=1.0):
    """Black mask with two overlapping lenses."""
    jx, jy = wobble(t, 1, 12) * 9 * shake, wobble(t, 2, 12) * 9 * shake
    ctx.push_group()
    ctx.set_source_rgb(0, 0, 0); ctx.paint()
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.arc(W / 2 - 230 + jx, 900 + jy, 340, 0, 6.283); ctx.fill()
    ctx.arc(W / 2 + 230 + jx, 900 + jy, 340, 0, 6.283); ctx.fill()
    ctx.pop_group_to_source(); ctx.paint()
    ctx.save(); ctx.set_operator(cairo.OPERATOR_OVER)
    g = cairo.RadialGradient(W / 2 + jx, 900 + jy, 300, W / 2 + jx, 900 + jy, 620)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.9)
    ctx.set_source(g); ctx.paint(); ctx.restore()
    return jx, jy


def window_scene(ctx, t, lit=1.0, fig=True, wave=0.0, sign_up=0.0, sign_lines=None, flip=1.0, zoom=1.0):
    """Close view of the lit window across the river (used through the binoculars too)."""
    ctx.save(); ctx.translate(W / 2, 900); ctx.scale(zoom, zoom); ctx.translate(-W / 2, -900)
    rgb(ctx, hexc("#0b0d14")); ctx.paint()
    for r in range(-6, 8):                # building facade with dark windows
        for c in range(-3, 5):
            rgb(ctx, hexc("#151925")); ctx.rectangle(c * 300 + 40, 900 + r * 330 - 120, 200, 240); ctx.fill()
    wx, wy, ww, wh = W / 2 - 230, 600, 460, 600
    glow(ctx, W / 2, 900, 700, (1, 0.8, 0.45), 0.35 * lit)
    rgb(ctx, (1.0, 0.86, 0.55), lit); ctx.rectangle(wx, wy, ww, wh); ctx.fill()
    rgb(ctx, hexc("#2a2420")); ctx.set_line_width(14); ctx.rectangle(wx, wy, ww, wh); ctx.stroke()
    ctx.move_to(W / 2, wy); ctx.line_to(W / 2, wy + wh); ctx.stroke()
    if fig and lit > 0.05:
        silhouette(ctx, W / 2 - 20, wy + wh, 480, wave=wave, sign=sign_up)
        if sign_up > 0:
            sy = lerp(wy + wh + 200, wy + 360, ease_out(sign_up))
            sign_card(ctx, W / 2 - 20, sy, 400, 260, sign_lines or [""], flip=flip, size=62)
    ctx.restore()


# ------------------------------------------------------------------ scenes
def s1(ctx, t, d):       # Every night at 9:14 ... every light turns on ... darkness.
    on, off = at(1, 1), at(1, -1)
    level = ease(prog(t, on, on + 0.7)) * (1 - prog(t, off, off + 0.15))
    z = 1 + 0.06 * t / d
    ctx.save(); ctx.translate(W / 2, GY); ctx.scale(z, z); ctx.translate(-W / 2, -GY)
    night_sky(ctx, t)
    city_lights(ctx, CITY_FAR, GY - 90, hexc("#0d1020"), level, t, 0.1)
    city_lights(ctx, CITY_NEAR, GY, hexc("#07080f"), level, t, 0.6)
    vgrad(ctx, GY, H, [(0, hexc("#07080d")), (1, hexc("#020203"))])
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    glow(ctx, W / 2, GY - 200, 900, (1, 0.7, 0.35), 0.25 * level)
    ctx.restore()
    ctx.restore()
    a = prog(t, 0.2, 0.8)
    text(ctx, "9:14 PM", W / 2, 300, 150, (1, 0.85, 0.5) if level > 0.3 else (0.85, 0.87, 0.95), a, outline=12)
    vignette(ctx, 0.75); grain(ctx, t); fade(ctx, t, d, 0.6, 0.15)


def s2(ctx, t, d):       # 212 nights, same rooftop, same dog.
    night_sky(ctx, t, 1180)
    draw_skyline(ctx, CITY_FAR, 1100, hexc("#0d1020"))
    draw_skyline(ctx, CITY_NEAR, 1180, hexc("#080a12"))
    parapet(ctx)
    turn = math.sin(prog(t, at(2, -1), d) * math.pi) * 1.2
    sit_back(ctx, 470, 1180, 520, head_turn=turn, breathe=math.sin(t * 1.5))
    dog(ctx, 680, 1180, 150, "back", wag=math.sin(t * 2.2))
    Particles(60, 4, (0, 0, W, 1200), vel=(30, 6), size=(1, 2.2), col=(0.8, 0.85, 1), alpha=0.3).draw(ctx, t)
    day_stamp(ctx, t, "NIGHT 212", 0.3)
    vignette(ctx, 0.75); grain(ctx, t); fade(ctx, t, d, 0.15, 0.15)


BUS_Y = 1250


def s3(ctx, t, d):       # Flashback: day three, shaking under a bus.
    vgrad(ctx, -200, GY, [(0, hexc("#1d232b")), (1, hexc("#39424d"))])
    draw_skyline(ctx, CITY_FAR, GY - 60, hexc("#2b323b"))
    vgrad(ctx, GY, H, [(0, hexc("#22272d")), (1, hexc("#111316"))])
    for k in range(6):                    # puddle reflections
        rgb(ctx, (0.6, 0.7, 0.8), 0.08); ctx.save(); ctx.translate(120 + k * 170, GY + 90 + (k % 3) * 70)
        ctx.scale(3, 0.4); ctx.arc(0, 0, 30, 0, 6.283); ctx.restore(); ctx.fill()
    # bus
    bx = 40
    rgb(ctx, hexc("#7d6a3c")); rrect(ctx, bx, 760, 760, 380, 40); ctx.fill()
    rgb(ctx, hexc("#3a4250"))
    for k in range(5):
        rrect(ctx, bx + 40 + k * 140, 800, 110, 130, 12); ctx.fill()
    rgb(ctx, hexc("#141414")); ctx.rectangle(bx + 30, 1120, 700, 50); ctx.fill()
    for wx in (bx + 150, bx + 610):
        rgb(ctx, hexc("#0b0b0b")); ctx.arc(wx, 1180, 72, 0, 6.283); ctx.fill()
        rgb(ctx, hexc("#3a3a3a")); ctx.arc(wx, 1180, 28, 0, 6.283); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.55); ctx.rectangle(bx + 30, 1140, 700, 110); ctx.fill()
    # dog shivering under the bus
    reach = prog(t, at(3, 1), at(3, 1) + 1.5)
    trust = prog(t, at(3, -1), d)
    dog(ctx, 420 + 60 * trust, GY - 2, 110, "stand", phase=t, face=1, shiver=1 - trust, head_up=0.6 * reach,
        wag=math.sin(t * 9) * trust)
    # you walk in, crouch, reach out
    walk = prog(t, 0.0, at(3, 1))
    px = lerp(1150, 760, ease(walk))
    if walk < 1:
        person(ctx, px, GY, S, "walk", phase=t * 7, face=-1)
    else:
        person(ctx, px, GY, S, "idle", face=-1, crouch=0.55 * ease(reach), lean=0.25 * reach,
               arm_f=(0.3 + 1.1 * ease(reach), 0.1))
    # rain
    ctx.set_line_width(2)
    r = random.Random(3)
    for k in range(140):
        x0, y0, sp = r.uniform(0, W + 200), r.uniform(0, H), r.uniform(1400, 1900)
        y = (y0 + t * sp) % H; x = (x0 - t * sp * 0.15) % (W + 200) - 100
        rgb(ctx, (0.75, 0.82, 0.9), 0.35)
        ctx.move_to(x, y); ctx.line_to(x - 6, y + 40); ctx.stroke()
    # faded flashback grade
    rgb(ctx, (0.55, 0.6, 0.65), 0.18); ctx.paint()
    day_stamp(ctx, t, "DAY 3", 0.2)
    vignette(ctx, 0.9); grain(ctx, t, 700, 0.09); fade(ctx, t, d, 0.35, 0.2)


def s4(ctx, t, d):       # The reason you still talk out loud.
    vgrad(ctx, -200, GY, [(0, hexc("#1b1512")), (1, hexc("#33261d"))])
    rgb(ctx, hexc("#0c0f1c")); ctx.rectangle(640, 380, 300, 380); ctx.fill()     # window
    rgb(ctx, (1, 1, 1), 0.5); ctx.arc(820, 480, 22, 0, 6.283); ctx.fill()
    rgb(ctx, hexc("#3a2b20")); ctx.set_line_width(16); ctx.rectangle(640, 380, 300, 380); ctx.stroke()
    vgrad(ctx, GY, H, [(0, hexc("#241a14")), (1, hexc("#0e0a08"))])
    # candle
    fl = 1 + 0.12 * wobble(t, 3, 6)
    rgb(ctx, hexc("#e8dcc2")); ctx.rectangle(520, 1170, 34, 80); ctx.fill()
    glow(ctx, 537, 1140, 700 * fl, (1, 0.7, 0.35), 0.4)
    rgb(ctx, (1, 0.85, 0.4)); ctx.save(); ctx.translate(537, 1150); ctx.scale(0.5, 1); ctx.arc(0, 0, 16 * fl, 0, 6.283); ctx.restore(); ctx.fill()
    rgb(ctx, hexc("#3b2c22")); ctx.rectangle(180, 1150, 160, 100); ctx.fill()     # crate seat
    talk = math.sin(t * 5) * (0.5 + 0.5 * math.sin(t * 1.3))
    person(ctx, 260, GY, S, "sit", face=1, lean=0.08, head_turn=0.4 * talk,
           arm_f=(0.9 + 0.25 * talk, -0.6), breathe=math.sin(t * 2))
    dog(ctx, 760, GY, 175, "sit", face=-1, wag=math.sin(t * 8), head_up=0.5 + 0.5 * math.sin(t * 1.7))
    vignette(ctx, 0.8); grain(ctx, t); fade(ctx, t, d, 0.2, 0.2)


SHELF = [(k, random.Random(k).random()) for k in range(60)]


def s5(ctx, t, d):       # Search the stores ... give him the bigger half.
    split = at(5, -2)
    vgrad(ctx, -200, GY, [(0, hexc("#1c2125")), (1, hexc("#2c3338"))])
    for k in range(4):                    # dead fluorescent tubes, one flickering
        a = 0.9 if k != 2 else (0.9 if math.sin(t * 17) * math.sin(t * 3) > 0 else 0.15)
        rgb(ctx, (0.85, 0.95, 1.0), a * 0.8); ctx.rectangle(80 + k * 260, 140, 180, 14); ctx.fill()
        cone(ctx, 170 + k * 260, 150, math.pi / 2, 0.55, 900, (0.8, 0.95, 1), 0.10 * a)
    off = -t * 160 if t < split else 0
    for row, sy in enumerate((520, 760, 1000)):   # shelves scroll by
        rgb(ctx, hexc("#4b5157")); ctx.rectangle(0, sy, W, 16); ctx.fill()
        for k, r in SHELF:
            if r < 0.78:
                continue
            x = (k * 97 + row * 41 + off) % (W + 200) - 100
            rgb(ctx, [hexc("#a33a2a"), hexc("#3f6f8a"), hexc("#c49a2a")][k % 3])
            ctx.rectangle(x, sy - 90, 60, 90); ctx.fill()
    vgrad(ctx, GY, H, [(0, hexc("#30363a")), (1, hexc("#151819"))])
    for k in range(12):
        rgb(ctx, (0, 0, 0), 0.25); x = (k * 140 + off * 1.3) % (W + 140) - 70
        ctx.move_to(x, GY); ctx.line_to(x - 200, H); ctx.set_line_width(3); ctx.stroke()
    if t < split:
        person(ctx, 600, GY, S, "walk", phase=t * 6.5, face=1)
        rgb(ctx, hexc("#4a5a3a")); rrect(ctx, 470, 880, 90, 150, 20); ctx.fill()   # backpack
        dog(ctx, 300, GY, 140, "trot", phase=t * 9, face=1, wag=math.sin(t * 8))
    else:
        k = prog(t, split, split + 1.5)
        person(ctx, 400, GY, S, "sit", face=1, lean=0.15, arm_f=(1.1 + 0.25 * ease(k), -0.4))
        rgb(ctx, hexc("#3b2c22")); ctx.rectangle(320, 1150, 150, 100); ctx.fill()
        eat = max(0, math.sin((t - split) * 7)) * prog(t, split + 1.2, split + 1.5)
        dog(ctx, 760, GY, 170, "sit", face=-1, wag=math.sin(t * 10), head_up=0.3 - 0.6 * eat)
        rgb(ctx, hexc("#c9a46a")); ctx.save(); ctx.translate(lerp(560, 640, ease(k)), lerp(1010, 1050, ease(k)))
        ctx.scale(1.4, 1); ctx.arc(0, 0, 28 * (1 - 0.6 * eat), 0, 6.283); ctx.restore(); ctx.fill()
    vignette(ctx, 0.75); grain(ctx, t); fade(ctx, t, d, 0.15, 0.2)


def s6(ctx, t, d):       # Everyone gone. Cars running. Coffee still warm.
    pan = -t * 25
    vgrad(ctx, -200, GY, [(0, hexc("#596474")), (1, hexc("#a4a9ae"))])
    draw_skyline(ctx, CITY_FAR, GY - 120, hexc("#6d7680"), offset=pan * 0.4)
    draw_skyline(ctx, CITY_NEAR, GY - 40, hexc("#3c434b"), offset=pan * 0.8)
    vgrad(ctx, GY - 40, H, [(0, hexc("#3a3f44")), (1, hexc("#1a1c1f"))])
    rgb(ctx, (0.9, 0.9, 0.85), 0.5)
    for k in range(6):
        ctx.rectangle((k * 230 + pan) % (W + 230) - 115, GY + 160, 120, 10); ctx.fill()
    # traffic light blinking yellow
    tlx = 900 + pan
    rgb(ctx, hexc("#1a1a1a")); ctx.rectangle(tlx, 640, 14, 560); ctx.fill(); rrect(ctx, tlx - 30, 560, 74, 190, 12); ctx.fill()
    if (t % 1.0) < 0.5:
        glow(ctx, tlx + 7, 655, 90, (1, 0.75, 0.1), 0.9)
    # car with open door
    cx = 330 + pan
    rgb(ctx, hexc("#7b2d2d")); rrect(ctx, cx, 1050, 470, 140, 40); ctx.fill()
    rrect(ctx, cx + 90, 960, 270, 120, 40); ctx.fill()
    rgb(ctx, hexc("#9fb3c4"), 0.7); rrect(ctx, cx + 115, 980, 100, 75, 14); ctx.fill(); rrect(ctx, cx + 235, 980, 100, 75, 14); ctx.fill()
    rgb(ctx, hexc("#5e2222")); ctx.move_to(cx + 330, 1060); ctx.line_to(cx + 420, 1010); ctx.line_to(cx + 430, 1150); ctx.line_to(cx + 340, 1180); ctx.close_path(); ctx.fill()
    for wx in (cx + 90, cx + 380):
        rgb(ctx, hexc("#0e0e0e")); ctx.arc(wx, 1195, 52, 0, 6.283); ctx.fill()
    glow(ctx, cx + 470, 1090, 60, (1, 0.9, 0.6), 0.8)
    Particles(25, 5, (cx - 220, 1050, cx + 10, 1200), vel=(-60, -40), size=(8, 20), col=(0.85, 0.85, 0.85), alpha=0.18).draw(ctx, t)
    # coffee cup on the roof, steaming
    rgb(ctx, hexc("#f2ece0")); ctx.move_to(cx + 200, 960); ctx.line_to(cx + 250, 960); ctx.line_to(cx + 244, 900); ctx.line_to(cx + 206, 900); ctx.close_path(); ctx.fill()
    rgb(ctx, hexc("#6b4a2e")); ctx.rectangle(cx + 204, 915, 42, 18); ctx.fill()
    ctx.set_line_width(5)
    for k in range(3):
        p = (t * 0.5 + k / 3) % 1
        rgb(ctx, (1, 1, 1), 0.45 * (1 - p))
        y0 = 890 - p * 160
        ctx.move_to(cx + 225 + math.sin(p * 9 + k) * 12, y0); ctx.curve_to(cx + 205, y0 - 30, cx + 245, y0 - 60, cx + 225 + math.sin(p * 9 + k + 1) * 15, y0 - 90); ctx.stroke()
    # you and Biscuit walk past slowly
    person(ctx, 820, GY + 60, S, "walk", phase=t * 5.5, face=-1)
    dog(ctx, 960, GY + 60, 130, "trot", phase=t * 8, face=-1)
    Particles(12, 9, (0, 700, W, GY), vel=(-180, 15), size=(4, 8), col=(0.9, 0.9, 0.85), alpha=0.5).draw(ctx, t)
    rgb(ctx, (0.6, 0.65, 0.7), 0.12); ctx.paint()
    vignette(ctx, 0.7); grain(ctx, t); fade(ctx, t, d, 0.15, 0.2)


def s7(ctx, t, d):       # A thousand screens ... the same two words.
    words = at(7, -1)
    z = 1 + 0.05 * t / d
    ctx.save(); ctx.translate(W / 2, 800); ctx.scale(z, z); ctx.translate(-W / 2, -800)
    rgb(ctx, hexc("#0b0c10")); ctx.paint()
    rgb(ctx, hexc("#16181f")); ctx.rectangle(60, 300, 960, 1000); ctx.fill()
    r = random.Random(int(t * 14))
    for row in range(4):
        for col in range(3):
            x, y = 110 + col * 300, 350 + row * 230
            rgb(ctx, hexc("#050505")); rrect(ctx, x - 10, y - 10, 280, 200, 10); ctx.fill()
            if t < words:
                for k in range(26):
                    g = r.uniform(0.2, 0.9); rgb(ctx, (g, g, g), 0.8)
                    ctx.rectangle(x, y + r.uniform(0, 175), 260, r.uniform(2, 10)); ctx.fill()
            else:
                rgb(ctx, hexc("#1b2a6b")); ctx.rectangle(x, y, 260, 180); ctx.fill()
                text(ctx, "NO SIGNAL", x + 130, y + 90, 50, (1, 1, 1))
            glow(ctx, x + 130, y + 90, 200, (0.6, 0.7, 1.0), 0.12)
    rgb(ctx, hexc("#2a2c33")); ctx.set_line_width(24); ctx.rectangle(60, 300, 960, 1000); ctx.stroke()
    ctx.restore()
    vgrad(ctx, 1300, H, [(0, hexc("#14151a")), (1, hexc("#060607"))])
    person(ctx, 470, 1560, 470, "idle", back_view=True, breathe=math.sin(t * 2))
    dog(ctx, 680, 1560, 150, "back", wag=0)
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    glow(ctx, 540, 1200, 500, (0.4, 0.5, 0.9), 0.12)
    ctx.restore()
    vignette(ctx, 0.75); grain(ctx, t, 400); fade(ctx, t, d, 0.15, 0.2)


def s8(ctx, t, d):       # But tonight, at 9:14 ... something is different.
    flip = at(8, 1)
    night_sky(ctx, t, 1180)
    draw_skyline(ctx, CITY_FAR, 1100, hexc("#0d1020"))
    draw_skyline(ctx, CITY_NEAR, 1180, hexc("#080a12"))
    parapet(ctx)
    stand = ease(prog(t, flip + 0.3, flip + 1.4))
    if stand < 0.5:
        sit_back(ctx, 470, 1180, 520, breathe=math.sin(t * 1.5))
    else:
        person(ctx, 470, 1200, 520, "idle", back_view=True, breathe=math.sin(t * 3))
    dog(ctx, 680, 1180, 150, "back")
    clock = "9:13" if t < flip else "9:14"
    pulse = 1 + 0.06 * math.sin(t * 6) * (t > flip)
    ctx.save(); ctx.translate(W / 2, 380); ctx.scale(pulse, pulse)
    rgb(ctx, (0, 0, 0), 0.5); rrect(ctx, -260, -120, 520, 240, 30); ctx.fill()
    text(ctx, clock, 0, 0, 200, (1, 0.35, 0.3) if t > flip else (0.6, 1, 0.7), outline=0)
    ctx.restore()
    vignette(ctx, 0.85); grain(ctx, t); fade(ctx, t, d, 0.15, 0.15)


def s9(ctx, t, d):       # The city stays dark. One window. Across the river.
    one = at(9, 1)
    z = 1 + 1.3 * ease(prog(t, one + 0.8, d))
    tx, ty = 812, 610               # the window
    ctx.save(); ctx.translate(tx, ty); ctx.scale(z, z); ctx.translate(-tx, -ty)
    night_sky(ctx, t, 1050)
    draw_skyline(ctx, RIVER_CITY, 1050, hexc("#090b15"))
    rgb(ctx, hexc("#0b0e1a")); ctx.rectangle(760, 520, 110, 530); ctx.fill()   # tall tower
    lit = ease(prog(t, one, one + 0.25))
    if lit > 0:
        glow(ctx, tx, ty, 160, (1, 0.8, 0.45), 0.7 * lit)
        rgb(ctx, (1, 0.86, 0.55), lit); ctx.rectangle(tx - 10, ty - 13, 20, 26); ctx.fill()
    vgrad(ctx, 1050, 1350, [(0, hexc("#0a0f1c")), (1, hexc("#05070d"))])          # river
    for k in range(18):
        y = 1070 + k * 15
        rgb(ctx, (0.6, 0.65, 0.85), 0.05 + 0.03 * math.sin(t * 2 + k))
        ctx.rectangle(0, y, W, 2); ctx.fill()
    if lit > 0:
        for k in range(10):
            rgb(ctx, (1, 0.8, 0.45), 0.35 * lit * (1 - k / 10))
            ctx.rectangle(tx - 14 + math.sin(t * 3 + k) * 8, 1070 + k * 26, 28, 10); ctx.fill()
    ctx.restore()
    parapet(ctx, 1350)
    vignette(ctx, 0.85); grain(ctx, t); fade(ctx, t, d, 0.15, 0.15)


def s10(ctx, t, d):      # A person. Waving at you.
    appear = prog(t, at(10, 1) - 0.4, at(10, 1) + 0.6)
    window_scene(ctx, t, lit=1.0, fig=appear > 0, wave=math.sin(t * 3) * 0.6 * prog(t, at(10, -1), d) + 0.2,
                 zoom=1 + 0.08 * t / d)
    if appear < 1:
        rgb(ctx, hexc("#ffdb8c"), 1 - appear); ctx.rectangle(W / 2 - 230, 600, 460, 600); ctx.fill()
    vignette(ctx, 0.9); grain(ctx, t, 500); fade(ctx, t, d, 0.15, 0.15)


BARKS = [0.15, 0.6, 1.05, 1.9, 2.35, 3.1]


def s11(ctx, t, d):      # Biscuit barks for the first time in months.
    night_sky(ctx, t, 1180, moon=False)
    draw_skyline(ctx, CITY_NEAR, 1180, hexc("#080a12"))
    glow(ctx, 1040, 700, 260, (1, 0.8, 0.45), 0.4)
    parapet(ctx)
    bark = max([math.exp(-(t - b) * 14) for b in BARKS if t >= b] + [0])
    dog(ctx, 470, 1190 - bark * 18, 360, "sit", face=1, head_up=1.0, bark=bark, wag=0)
    vignette(ctx, 0.8); grain(ctx, t); fade(ctx, t, d, 0.1, 0.15)


def s12(ctx, t, d):      # Binoculars. Hands shaking. A sign.
    view = at(12, 1)
    if t < view:
        night_sky(ctx, t, 1180, moon=False)
        draw_skyline(ctx, CITY_NEAR, 1180, hexc("#080a12"))
        parapet(ctx)
        k = ease(prog(t, 0.2, view))
        info = person(ctx, 420, 1200, 520, "idle", face=1, head_turn=0.2,
                      arm_f=(0.3 + 2.0 * k + wobble(t, 1, 20) * 0.05, -0.3 - 1.4 * k), arm_b=(0.2 + 1.8 * k, -1.0 * k))
        hx, hy = info["hand"]
        rgb(ctx, hexc("#1a1a1a")); rrect(ctx, hx - 10, hy - 30, 70, 60, 12); ctx.fill()
        dog(ctx, 760, 1180, 150, "sit", face=-1, head_up=1)
    else:
        sign = prog(t, at(12, -1), at(12, -1) + 1.2)
        window_scene(ctx, t, lit=1, wave=0, sign_up=sign, sign_lines=[""], zoom=1.15)
        binoculars(ctx, t, 1.3)
    vignette(ctx, 0.6); grain(ctx, t); fade(ctx, t, d, 0.1, 0.1)


def s13(ctx, t, d):      # "DON'T COME HERE"
    window_scene(ctx, t, lit=1, sign_up=1, sign_lines=["DON'T", "COME HERE"], zoom=1.15 + 0.25 * ease(t / d))
    binoculars(ctx, t, 1.5)
    grain(ctx, t); fade(ctx, t, d, 0.05, 0.1)


def s14(ctx, t, d):      # Flip: IT'S NOT ME TURNING THEM ON
    f0 = at(14, 0) + 0.6
    p = prog(t, f0, f0 + 0.6)
    flip = math.cos(p * math.pi)
    lines = ["DON'T", "COME HERE"] if p < 0.5 else ["IT'S NOT ME", "TURNING", "THEM ON"]
    window_scene(ctx, t, lit=1, sign_up=1, sign_lines=lines, flip=flip, zoom=1.4 + 0.3 * ease(prog(t, at(14, -1), d)))
    binoculars(ctx, t, 1.8)
    grain(ctx, t); fade(ctx, t, d, 0.05, 0.1)


def door_hut(ctx, x, y, bulb, ajar=0.0):
    rgb(ctx, hexc("#1f222b")); ctx.rectangle(x - 200, y - 480, 400, 480); ctx.fill()
    rgb(ctx, hexc("#2b2f3a")); ctx.rectangle(x - 220, y - 500, 440, 30); ctx.fill()
    rgb(ctx, hexc("#121419")); ctx.rectangle(x - 90, y - 330, 180, 330); ctx.fill()
    if ajar > 0:
        g = cairo.LinearGradient(x + 90 - 40 * ajar, 0, x + 90 + 200, 0)
        g.add_color_stop_rgba(0, 1, 0.9, 0.7, 0.9); g.add_color_stop_rgba(1, 1, 0.9, 0.7, 0)
        ctx.set_source(g)
        ctx.move_to(x + 90 - 40 * ajar, y - 330); ctx.line_to(x + 90, y - 330); ctx.line_to(x + 420, y + 260)
        ctx.line_to(x + 60, y + 260); ctx.close_path(); ctx.fill()
        rgb(ctx, (1, 0.92, 0.75)); ctx.rectangle(x + 90 - 40 * ajar, y - 330, 40 * ajar, 330); ctx.fill()
    rgb(ctx, hexc("#2b2f3a")); ctx.rectangle(x - 90, y - 330, 180 - 40 * ajar, 330); ctx.fill()
    rgb(ctx, hexc("#6a6f7a")); ctx.arc(x + 50 - 40 * ajar, y - 160, 9, 0, 6.283); ctx.fill()
    if bulb > 0:
        ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
        cone(ctx, x, y - 380, math.pi / 2, 0.75, 700, (1, 0.85, 0.6), 0.35 * bulb)
        glow(ctx, x, y - 385, 180, (1, 0.85, 0.6), 0.8 * bulb)
        ctx.restore()
    rgb(ctx, (1, 0.95, 0.8) if bulb > 0.3 else (0.3, 0.3, 0.3)); ctx.arc(x, y - 385, 14, 0, 6.283); ctx.fill()


def flicker(t, t0):
    if t < t0:
        return 0.0
    k = t - t0
    if k > 1.2:
        return 1.0
    return 1.0 if math.sin(k * 47) * math.sin(k * 13) > 0.1 else 0.0


def s15(ctx, t, d):      # The window goes dark ... the stairwell light flickers on.
    cut = at(15, 1)
    if t < cut:
        lit = 1 - ease(prog(t, 0.4, 0.9))
        window_scene(ctx, t, lit=lit, sign_up=1, sign_lines=["IT'S NOT ME", "TURNING", "THEM ON"], zoom=1.7)
        binoculars(ctx, t, 1.2)
    else:
        b = flicker(t, at(15, -1) + 0.4)
        night_sky(ctx, t, 1000, moon=False)
        vgrad(ctx, 1000, H, [(0, hexc("#191b22")), (1, hexc("#0a0b0e"))])
        door_hut(ctx, 540, 1150, b)
        turn = prog(t, at(15, -1) + 1.4, at(15, -1) + 1.8)
        person(ctx, 820, 1500, 540, "idle", face=1 if turn < 0.5 else -1, breathe=math.sin(t * 4),
                   arm_f=(0.6, -0.8))
        dog(ctx, 280, 1500, 170, "sit", face=1, head_up=1)
    vignette(ctx, 0.85); grain(ctx, t); fade(ctx, t, d, 0.05, 0.15)


def s16(ctx, t, d):      # Biscuit stares at the door. Part two...
    z = 1 + 0.25 * ease(t / d)
    ctx.save(); ctx.translate(540, 900); ctx.scale(z, z); ctx.translate(-540, -900)
    night_sky(ctx, t, 1000, moon=False)
    vgrad(ctx, 1000, H, [(0, hexc("#191b22")), (1, hexc("#0a0b0e"))])
    ajar = ease(prog(t, 0.8, d - 1.5))
    door_hut(ctx, 540, 1150, 1.0, ajar=ajar)
    shadow = prog(t, d - 1.8, d - 0.9)
    if shadow > 0:                       # something on the stairs
        rgb(ctx, (0, 0, 0), 0.85 * shadow)
        ctx.save(); ctx.translate(560, 1150); ctx.scale(1, -1)
        ctx.move_to(0, 0); ctx.line_to(120, 0); ctx.line_to(260, -420); ctx.line_to(160, -440); ctx.close_path(); ctx.restore(); ctx.fill()
    ctx.restore()
    dog(ctx, 820, 1560, 330, "sit", face=-1, head_up=1, shiver=0.25)
    p2 = prog(t, at(16, -2), at(16, -2) + 0.4)
    if p2 > 0:
        ctx.save(); ctx.translate(W / 2, 330); s = 1 + (1 - ease_out(p2)) * 0.6; ctx.scale(s, s)
        text(ctx, "PART 2", 0, 0, 170, (1, 0.3, 0.25), ease(p2), outline=14)
        ctx.restore()
    vignette(ctx, 0.95); grain(ctx, t, 500); fade(ctx, t, d, 0.05, 0.35)


SCENES = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16]


# ------------------------------------------------------------------ sound design
def bark_sfx(d, times):
    x = silence(d)
    for b in times:
        i = int(b * SR); n = int(0.16 * SR)
        if i + n > len(x):
            continue
        tt = np.arange(n) / SR
        env = np.exp(-tt * 22) * np.minimum(1, tt * 400)
        voice = np.sin(2 * np.pi * np.cumsum(np.linspace(520, 300, n)) / SR) + 0.5 * np.sign(np.sin(2 * np.pi * np.cumsum(np.linspace(260, 150, n)) / SR))
        x[i:i + n] += (voice * 0.5 + band_noise(0.16, 300, 3000, int(b * 100))[:n] * 0.5) * env
    return x * 0.5


def heart(d, bpm=72, amp=0.45):
    times = []
    t = 0.2
    while t < d:
        times += [t, t + 0.22]; t += 60 / bpm
    return env_at(d, times, 0.12) * tone(d, 48) * amp


def sfx(i, d):
    t = np.arange(int(d * SR)) / SR
    bed = band_noise(d, 60, 300, i) * 0.06
    if i == 1:
        on, off = at(1, 1), at(1, -1)
        x = bed + env_at(d, [on], 0.6) * (tone(d, 55) + band_noise(d, 80, 600, 2) * 0.5) * 0.7 \
            + tone(d, 120, "saw") * 0.03 * ((t > on) & (t < off)) + env_at(d, [off], 0.4) * tone(d, 50) * 0.6
    elif i in (2, 8, 15):
        x = bed + band_noise(d, 150, 900, 10 + i) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t)) * 0.18
        if i == 8:
            x += env_at(d, [k * 1.0 for k in range(int(d) + 1)], 0.03) * band_noise(d, 3000, 8000, 3) * 0.3
            x += heart(d, 80) * (t > at(8, 1))
        if i == 15:
            b0 = at(15, -1) + 0.4
            buzz = np.array([flicker(tt, b0) for tt in t[::441]]).repeat(441)[: len(t)]
            x += tone(d, 120, "saw") * 0.06 * buzz + heart(d, 96)
    elif i == 3:
        x = bed + band_noise(d, 800, 7000, 31) * 0.22 + env_at(d, [1.5], 2.0) * band_noise(d, 30, 200, 32) * 0.5
    elif i == 4:
        x = bed + env_at(d, list(np.random.default_rng(4).uniform(0, d, 25)), 0.01) * band_noise(d, 2000, 8000, 4) * 0.25
    elif i == 5:
        split = at(5, -2)
        steps = [k * math.pi / 6.5 for k in range(int(split * 6.5 / math.pi) + 1)]
        x = bed + env_at(d, steps, 0.05) * band_noise(d, 1500, 6000, 5) * 0.35 + tone(d, 120) * 0.02
    elif i == 6:
        x = bed + (tone(d, 32) * 0.3 + tone(d, 64) * 0.1) * (0.8 + 0.2 * np.sin(2 * np.pi * 9 * t)) * 0.35 \
            + band_noise(d, 150, 900, 6) * 0.12
    elif i == 7:
        words = at(7, -1)
        x = bed + band_noise(d, 500, 8000, 7) * 0.18 * (t < words) + tone(d, 1000) * 0.05 * (t >= words)
    elif i == 9:
        x = bed + band_noise(d, 100, 700, 9) * 0.15 + env_at(d, [at(9, 1)], 0.3) * tone(d, 70) * 0.6
    elif i == 10:
        x = bed + tone(d, 1567) * 0.02 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)) + heart(d, 84)
    elif i == 11:
        x = bed + bark_sfx(d, BARKS)
    elif i in (12, 13, 14):
        x = bed + heart(d, 100 + (i - 12) * 10)
        if i == 14:
            f0 = at(14, 0) + 0.6
            x += env_at(d, [f0, f0 + 0.3], 0.12) * band_noise(d, 800, 5000, 14) * 0.4
    else:  # 16
        growl = band_noise(d, 50, 220, 16) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t)) * 0.4 * np.clip(t / 2, 0, 1)
        creak = tone(d, 220 - 80 * np.clip((t - 0.8) / (d - 2.3), 0, 1), "saw") * 0.05 * ((t > 0.8) & (t < d - 1.5))
        sting = env_at(d, [d - 1.8], 1.6) * (tone(d, 41) + band_noise(d, 30, 300, 17) * 0.5)
        x = bed + growl + creak + sting
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
    only = [int(a) for a in sys.argv[1:]] or range(1, len(SCENES) + 1)
    durs = [dur_of(i) for i in range(1, len(SCENES) + 1)]
    outdir = ROOT / "assets" / "clips" / SID
    outdir.mkdir(parents=True, exist_ok=True)
    save_wav(outdir / "music.wav", piano_score(sum(durs), sum(durs[:7])))
    with Pool(4) as p:
        for r in p.imap_unordered(job, only):
            print("  rendered", r, flush=True)
