"""Last Wave - zombie survival starring Kai, Parts 1-3 (stories/35-37).

    python src/anim/boardwalk.py <part 1|2|3> [scene numbers]

Sets: the surf shop under siege, the boardwalk, the beach at night, the open ocean (rip current),
the cliff cove, dawn rescue. Every human is a rig Character; the infected have white eyes.
"""
import math, pathlib, random, sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import *  # noqa
from cinema import camera, fog, god_rays, soft_shadow, backlight, depth_haze, dust, shot_card
from lighthouse import end_card, finish, wind
from nightshift import rule_card
from story import Timing, run, ROOT
from rig import Character, lipsync
from cast import KAI
from gondola import radio, surf_shop

T1, T2, T3 = Timing("35_boardwalk_1"), Timing("36_boardwalk_2"), Timing("37_boardwalk_3")
SIDS = {1: "35_boardwalk_1", 2: "36_boardwalk_2", 3: "37_boardwalk_3"}
TM = {1: T1, 2: T2, 3: T3}

TESS = Character("Tess", skin="#e8b896", hair="#2a1d14", hair_style="ponytail", top="#e8b72e", pants="#33415c",
                 footwear="shoes", shoes="#f2f2f2", face_shape="oval", seed=4.0)
ZCOLS = [("#8fa58a", "#5a5f66", "#3a3f4a"), ("#9aab8e", "#7a3b3b", "#2f3540"), ("#86a090", "#3d5a7a", "#4a3f35"),
         ("#94a88c", "#6b6b5a", "#2b2b30"), ("#8aa396", "#a0763a", "#3a3a44")]
ZOMBIES = [Character(f"Z{k}", skin=s, hair=["#2a221c", "#5a4030", "#1c1c1c", "#7a6a50", "#3a2a20"][k], hair_style=["short", "long", "buzz", "short", "bald"][k],
                     top=tp, pants=pn, footwear="shoes", shoes="#222222", eye_col="#f2f2ea", seed=20.0 + k)
           for k, (s, tp, pn) in enumerate(ZCOLS)]
LIFEGUARD = Character("LG", skin="#8fa58a", hair="#5a4030", hair_style="short", top="#d6302c", pants="#2b2b33",
                      eye_col="#f2f2ea", seed=31.0)
SEA_N = ((0.02, 0.05, 0.09), (0.05, 0.12, 0.18))
RAIN = Particles(160, 7, (0, 0, W, H), vel=(-60, 600), size=(1, 2.5), col=(0.8, 0.85, 0.95), alpha=0.35)


def talk_fn(part, i, k0=0, k1=99):
    tm = TM[part]
    f = lipsync(ROOT / "out" / SIDS[part] / f"scene_{i:02d}.wav")
    a, b = tm.at(i, k0), (tm.at(i, k1 + 1) if k1 + 1 < len(tm.seg.get(i, [])) else 999)
    return lambda t: f(t) if a <= t < b else 0.0


def close(ch, ctx, cx, hy, r, t, **kw):
    s = r / 0.13
    mode = kw.pop("mode", "idle")
    return ch.draw(ctx, cx, hy + (0.718 if mode == "sit" else 0.888) * s, s, t, mode=mode, **kw)


def zombie(ctx, k, x, y, s, t, walk=True, face=1, expr="angry", **kw):
    z = ZOMBIES[k % len(ZOMBIES)]
    return z.draw(ctx, x, y, s, t + k * 0.37, mode="walk" if walk else "idle", phase=t * 2.2 + k * 1.3, face=face,
                  expr=expr, arm_f=(1.45 + 0.08 * math.sin(t * 2 + k), 0.1), arm_b=(1.3, 0.15), look=(face * 0.5, 0), **kw)


# ------------------------------------------------------------------ sets
def sky(ctx, mood, y1=1200):
    """mood: 'dawn' | 'day' | 'dusk' | 'night' | 'grey'"""
    stops = {"dawn": [(0, "#3b4a7a"), (0.6, "#e59a7a"), (1, "#f6d29a")],
             "day": [(0, "#5f9fd0"), (1, "#bfe0f0")],
             "grey": [(0, "#5a6472"), (1, "#9aa3ae")],
             "dusk": [(0, "#2a2a4a"), (0.6, "#b85a4a"), (1, "#f0a060")],
             "night": [(0, "#04060c"), (0.7, "#0e1626"), (1, "#1c2638")]}[mood]
    vgrad(ctx, -300, y1, [(p, hexc(c)) for p, c in stops])
    if mood == "night":
        for k in range(50):
            r = random.Random(k); rgb(ctx, (1, 1, 1), r.uniform(0.2, 0.7)); ctx.arc(r.uniform(0, W), r.uniform(-200, y1 * 0.7), r.uniform(1, 2.5), 0, 6.283); ctx.fill()
        glow(ctx, 820, 260, 220, (0.85, 0.9, 1.0), 0.35); rgb(ctx, (0.92, 0.94, 1.0)); ctx.arc(820, 260, 55, 0, 6.283); ctx.fill()


def ocean(ctx, t, y0, night=True, rip=0.0, y1=H + 300, speed=1.0):
    c0, c1 = SEA_N if night else ((0.12, 0.42, 0.55), (0.06, 0.25, 0.38))
    vgrad(ctx, y0, y1, [(0, c0), (1, c1)])
    for k in range(26):                                                   # wave lines
        r = random.Random(k)
        yy = y0 + (k / 26) ** 1.6 * (y1 - y0)
        x = (r.uniform(0, W) + t * 40 * speed * (1 + k * 0.05)) % (W + 400) - 200
        rgb(ctx, (0.75, 0.85, 0.95) if night else (1, 1, 1), 0.25 + 0.3 * k / 26)
        ctx.set_line_width(2 + k * 0.25); ctx.move_to(x, yy); ctx.curve_to(x + 60, yy - 6, x + 140, yy - 6, x + 200 + k * 8, yy); ctx.stroke()
    if night:
        rgb(ctx, (0.85, 0.9, 1.0), 0.18)                                  # moon path
        for k in range(12):
            yy = y0 + 20 + k * 40; ww = 30 + k * 18 + 10 * math.sin(t * 2 + k)
            ctx.rectangle(820 - ww / 2 + 8 * math.sin(t * 3 + k), yy, ww, 6); ctx.fill()
    if rip > 0:                                                          # rip current: a dark channel pulling outward
        g = cairo.LinearGradient(380, 0, 700, 0)
        g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(0.5, 0.02, 0.03, 0.05, 0.45 * rip); g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g); ctx.rectangle(380, y0, 320, y1 - y0); ctx.fill()
        for k in range(8):
            yy = y1 - ((t * 260 + k * 160) % (y1 - y0))
            rgb(ctx, (0.85, 0.95, 1.0), 0.5 * rip); ctx.set_line_width(5)
            ctx.move_to(540 - 40, yy + 40); ctx.line_to(540, yy); ctx.line_to(540 + 40, yy + 40); ctx.stroke()


def sand(ctx, y0, night=True):
    vgrad(ctx, y0, H + 300, [(0, hexc("#3a3a40" if night else "#e8cf98")), (1, hexc("#1e1e24" if night else "#c9a76a"))])


def foam(ctx, t, y, a=0.7):
    rgb(ctx, (0.9, 0.95, 1.0), a)
    ctx.move_to(-100, y)
    for k in range(13):
        ctx.line_to(k * 100, y + 14 * math.sin(t * 1.5 + k * 0.8))
    ctx.line_to(W + 100, y + 30); ctx.line_to(-100, y + 30); ctx.fill()


def boardwalk(ctx, t, mood="dawn"):
    sky(ctx, mood, 1100)
    ocean(ctx, t, 1000, night=mood == "night")
    rgb(ctx, hexc("#7a5a3c")); ctx.rectangle(-100, 1300, W + 200, H); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.22); ctx.set_line_width(4)
    for k in range(14):
        ctx.move_to(-100, 1330 + k * k * 4.2); ctx.line_to(W + 100, 1330 + k * k * 4.2); ctx.stroke()
    rgb(ctx, hexc("#5a4030")); ctx.rectangle(-100, 1180, W + 200, 16); ctx.fill()        # railing
    for k in range(7):
        ctx.rectangle(k * 180, 1180, 14, 130); ctx.fill()
    for k, x in enumerate((140, 900)):                                                   # lamps
        rgb(ctx, hexc("#2a2a30")); ctx.rectangle(x - 6, 700, 12, 620); ctx.fill()
        if mood in ("dusk", "night"):
            glow(ctx, x, 700, 200, (1, 0.8, 0.5), 0.45)
        rgb(ctx, (1, 0.9, 0.6) if mood in ("dusk", "night") else (0.85, 0.85, 0.8)); ctx.arc(x, 700, 22, 0, 6.283); ctx.fill()


def shopfront(ctx, t, x=540, mood="dawn", lit=True):
    """The surf shop seen from the boardwalk."""
    rgb(ctx, hexc("#2c8c9a")); ctx.rectangle(x - 420, 520, 840, 800); ctx.fill()
    rgb(ctx, hexc("#f6eee0")); ctx.rectangle(x - 440, 470, 880, 120); ctx.fill()
    text(ctx, "SURF SHACK", x, 532, 80, hexc("#c8302c"))
    rgb(ctx, (1, 0.85, 0.55) if lit else (0.06, 0.08, 0.1)); ctx.rectangle(x - 360, 650, 460, 520); ctx.fill()
    rgb(ctx, hexc("#1d4a54")); ctx.rectangle(x + 160, 650, 200, 670); ctx.fill()


def window_crowd(ctx, t, n=6, crack=0.0, press=1.0, mood="dusk", inside_dark=True):
    """Inside the shop looking out: big window full of infected hands and faces."""
    rgb(ctx, hexc("#1f5f6a")); ctx.paint()
    ctx.save(); ctx.rectangle(60, 260, 960, 1200); ctx.clip()
    sky(ctx, mood, 900); rgb(ctx, hexc("#7a5a3c")); ctx.rectangle(0, 1100, W, 800); ctx.fill()
    for k in range(n):
        r = random.Random(k)
        x = 120 + (k % 4) * 260 + r.uniform(-40, 40); far = k >= 4
        zombie(ctx, k, x, 1700 - (250 if far else 0), 900 if not far else 600, t, walk=False, face=1 if x < 540 else -1)
    for k in range(int(5 * press)):                                                      # hands on the glass
        r = random.Random(k + 40)
        hx, hy = r.uniform(150, 930), r.uniform(700, 1250) + 10 * math.sin(t * 3 + k)
        rgb(ctx, hexc("#8fa58a")); ctx.save(); ctx.translate(hx, hy); ctx.rotate(r.uniform(-0.4, 0.4))
        rrect(ctx, -50, -40, 100, 110, 30); ctx.fill()
        for f in range(4):
            rrect(ctx, -48 + f * 25, -100, 22, 70, 11); ctx.fill()
        ctx.restore()
    rgb(ctx, (0.7, 0.85, 0.95), 0.08); ctx.paint()
    if crack > 0:
        r = random.Random(4); rgb(ctx, (1, 1, 1), 0.9); ctx.set_line_width(4)
        for k in range(6):
            ctx.move_to(540, 900); x, y = 540, 900; a = k * 1.05 + 0.2
            for j in range(int(8 * crack)):
                x += math.cos(a) * 70; y += math.sin(a) * 70; a += r.uniform(-0.5, 0.5); ctx.line_to(x, y)
            ctx.stroke()
    ctx.restore()
    rgb(ctx, hexc("#0f2c32")); ctx.set_line_width(40); ctx.rectangle(60, 260, 960, 1200); ctx.stroke()
    if inside_dark:
        rgb(ctx, (0.02, 0.03, 0.06), 0.25); ctx.paint()


def board(ctx, x, y, w=420, col="#f4d35e", ang=0.0, a=1.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
    rgb(ctx, hexc(col), a); ctx.save(); ctx.scale(1, 0.16); ctx.arc(0, 0, w / 2, 0, 6.283); ctx.restore(); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.25 * a); ctx.rectangle(-w / 2 + 20, -2, w - 40, 4); ctx.fill()
    ctx.restore()


def rider(ctx, ch, x, y, s, t, paddle=True, face=1, **kw):
    """A person sitting on a surfboard in the water, paddling."""
    bob = math.sin(t * 1.8 + x * 0.01) * 10
    board(ctx, x, y + bob + 0.02 * s, 0.75 * s, "#f4d35e" if ch is KAI else "#98c1d9")
    ph = t * 4
    arm = (1.0 + 0.8 * math.sin(ph), 0.4) if paddle else None
    arm = kw.pop("arm_f", arm)
    r = ch.draw(ctx, x, y + bob, s, t, mode="sit", face=face, arm_f=arm, arm_b=(1.0 + 0.8 * math.sin(ph + math.pi), 0.4) if paddle else None, **kw)
    g = cairo.LinearGradient(0, y + bob + 0.02 * s, 0, y + bob + 0.3 * s)                       # legs fade into the water
    g.add_color_stop_rgba(0, 0.03, 0.08, 0.13, 0.55); g.add_color_stop_rgba(1, 0.03, 0.08, 0.13, 0.95)
    ctx.set_source(g); ctx.save(); ctx.translate(x, y + bob + 0.16 * s); ctx.scale(1, 0.35); ctx.arc(0, 0, 0.42 * s, 0, 6.283); ctx.restore(); ctx.fill()
    rgb(ctx, (0.8, 0.9, 1.0), 0.5); ctx.set_line_width(4)
    ctx.move_to(x - 0.4 * s, y + bob + 0.03 * s); ctx.curve_to(x - 0.1 * s, y + bob + 0.01 * s, x + 0.1 * s, y + bob + 0.05 * s, x + 0.4 * s, y + bob + 0.03 * s); ctx.stroke()
    return r


def cliffs(ctx, t, dawn=0.0):
    c = tuple(lerp(a, b, dawn) for a, b in zip((0.08, 0.08, 0.1), (0.42, 0.36, 0.34)))
    rgb(ctx, c)
    ctx.move_to(-100, H); ctx.line_to(-100, 500); ctx.line_to(140, 560); ctx.line_to(260, 900); ctx.line_to(300, 1250); ctx.line_to(260, H); ctx.fill()
    ctx.move_to(W + 100, H); ctx.line_to(W + 100, 450); ctx.line_to(900, 520); ctx.line_to(820, 880); ctx.line_to(780, 1250); ctx.line_to(820, H); ctx.fill()


def helicopter(ctx, t, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rgb(ctx, hexc("#d6532c")); rrect(ctx, -120, -50, 240, 100, 50); ctx.fill(); ctx.rectangle(100, -20, 180, 24); ctx.fill()
    rgb(ctx, hexc("#e8eef4")); rrect(ctx, -100, -35, 90, 50, 20); ctx.fill()
    rgb(ctx, (0.1, 0.1, 0.1)); ctx.set_line_width(8); w = 260 * abs(math.cos(t * 30))
    ctx.move_to(-w, -70); ctx.line_to(w, -70); ctx.stroke(); ctx.move_to(-80, 60); ctx.line_to(80, 60); ctx.stroke()
    ctx.restore()


def flipflop(ctx, x, y, ang=0.0, a=1.0, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.scale(s, s)
    rgb(ctx, hexc(KAI.shoes), a); ctx.save(); ctx.scale(1, 0.42); ctx.arc(0, 0, 80, 0, 6.283); ctx.restore(); ctx.fill()
    rgb(ctx, (0.1, 0.1, 0.1), a); ctx.set_line_width(8); ctx.move_to(-20, -25); ctx.line_to(30, 0); ctx.stroke()
    ctx.restore()


def underwater(ctx, t):
    vgrad(ctx, -300, H + 300, [(0, hexc("#0b2a3a")), (1, hexc("#01070c"))])
    for k in range(5):
        god_rays(ctx, t, 540, -200, angle=math.pi / 2, length=1700, spread=0.35, n=5, col=(0.5, 0.8, 1.0), alpha=0.06, seed=k)
    Particles(60, 3, (0, 0, W, H), vel=(5, -40), size=(1.5, 4), col=(0.7, 0.9, 1.0), alpha=0.35).draw(ctx, t)


def kai_leg(ctx, x, y, s=1.0, kick=0.0, shoe=True):
    """Kai's shin + foot dangling down into the water (seen from below)."""
    ctx.save(); ctx.translate(x, y); ctx.rotate(kick * 0.4); ctx.scale(s, s)
    rgb(ctx, hexc(KAI.pants)); rrect(ctx, -70, -500, 140, 200, 40); ctx.fill()
    rgb(ctx, hexc(KAI.skin)); rrect(ctx, -45, -330, 90, 330, 40); ctx.fill(); ctx.save(); ctx.translate(20, 10); ctx.scale(1.4, 0.6); ctx.arc(0, 0, 50, 0, 6.283); ctx.restore(); ctx.fill()
    if shoe:
        flipflop(ctx, 25, 45, 0.0, 1.0, 0.9)
    ctx.restore()


def grey_hand(ctx, x, y, s=1.0, ang=0.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.scale(s, s)
    rgb(ctx, hexc("#8fa58a")); rrect(ctx, -60, 0, 120, 360, 50); ctx.fill(); rrect(ctx, -75, -60, 150, 130, 50); ctx.fill()
    for f in range(4):
        rrect(ctx, -72 + f * 38, -150, 30, 110, 15); ctx.fill()
    rgb(ctx, hexc("#d6302c")); ctx.rectangle(-62, 200, 124, 160); ctx.fill()                # lifeguard sleeve
    ctx.restore()


def shirt_insert(ctx, t, t0):
    sky(ctx, "dawn", H)
    KAI.draw(ctx, 540, 2600, 2100, t, face=0, expr="tired", expr_to="happy", expr_k=prog(t, t0, t0 + 0.5),
             torn=1.0, dirt=0.8, lost_shoe=True)
    if t > t0:
        for k in range(6):
            a = prog(t, t0 + k * 0.15, t0 + k * 0.15 + 0.4) * (1 - prog(t, t0 + k * 0.15 + 0.4, t0 + k * 0.15 + 0.9))
            r = random.Random(k); x, y = r.uniform(250, 830), r.uniform(1250, 1800)
            rgb(ctx, (1, 1, 0.85), a); ctx.set_line_width(6)
            for ang in range(4):
                ctx.move_to(x, y); ctx.line_to(x + math.cos(ang * math.pi / 2) * 40, y + math.sin(ang * math.pi / 2) * 40); ctx.stroke()
    text(ctx, "THE SHIRT SURVIVED", 540, 330, 100, (1, 0.85, 0.4), prog(t, t0, t0 + 0.3), outline=10)


# ------------------------------------------------------------------ PART 1
def p1s1(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.8, focus=(540, 900), shake=0.2 if t < 0.4 else 0.05):
        window_crowd(ctx, t, n=7, crack=0.3, press=1.0, mood="dusk")
    shot_card(ctx, t, text, "PADDLE OUT?", 0.0, y=330, size=150)
    finish(ctx, t, d, fi=0.0)


def p1s2(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(540, 1200)):
        boardwalk(ctx, t, "dawn")
        shopfront(ctx, t, 540, "dawn", lit=t > T1.at(2, 1))
        soft_shadow(ctx, 380, 1555, 300)
        KAI.draw(ctx, 380, 1550, 760, t, face=1, expr="happy", look=(1, 0), arm_f=(1.2, 0.5))
        god_rays(ctx, t, 1000, 900, angle=2.6, length=1500, col=(1, 0.8, 0.55), alpha=0.15)
    finish(ctx, t, d)


def p1s3(ctx, t, d):
    worse = prog(t, T1.at(3, 1), T1.at(3, 1) + 0.4)
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 800)):
        sky(ctx, "grey" if worse > 0.5 else "dawn", H)
        rgb(ctx, (0.3, 0.32, 0.38), 0.6 * worse); ctx.paint()
        close(KAI, ctx, 540, 820, 240, t, face=0, expr="happy", expr_to="confused", expr_k=worse, talk=talk_fn(1, 3, 0, 0)(t),
              look=(0.5, -0.8))
    finish(ctx, t, d)


def p1s4(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.8, focus=(540, 1200), shake=0.15):
        boardwalk(ctx, t, "grey")
        for k in range(5):
            x = (k * 260 + t * 420 * (1 + 0.2 * k)) % (W + 400) - 200
            ch = Character(f"R{k}", skin=["#e8b896", "#c99a72", "#f0c8a8", "#a8775a", "#e2b08a"][k],
                           hair="#3a2a20", top=["#3d5a80", "#ee6c4d", "#6a994e", "#9a7aa0", "#e0a526"][k], seed=50 + k)
            ch.draw(ctx, x, 1600 + k * 40, 560 + k * 30, t, mode="run", phase=t * 9 + k, face=1, expr="fear", look=(1, 0))
        zombie(ctx, 0, 120 + t * 160, 1520, 600, t, face=1)
    finish(ctx, t, d)


def p1s5(ctx, t, d):
    burst = ease_out(prog(t, 0.0, 0.5))
    with camera(ctx, t, d, push=0.10, handheld=0.6, focus=(540, 1100), shake=0.4 if t < 0.4 else 0.05):
        surf_shop(ctx, t)
        rgb(ctx, (1, 1, 1), 0.6); ctx.rectangle(820, 400, 260, 1100); ctx.fill()             # open door, grey light
        soft_shadow(ctx, lerp(950, 560, burst), 1655, 300)
        TESS.draw(ctx, lerp(950, 560, burst), 1650, 820, t, mode="run" if burst < 1 else "idle", phase=t * 9, face=-1,
                  expr="fear", look=(-1, 0))
    finish(ctx, t, d)


def p1s6(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.5, focus=(540, 800)):
        surf_shop(ctx, t)
        close(TESS, ctx, 540, 820, 250, t, face=0, expr="fear", talk=talk_fn(1, 6)(t), look=(0.8, 0),
              arm_f=(1.5, 0.0))
    finish(ctx, t, d)


def p1s7(ctx, t, d):
    with camera(ctx, t, d, push=0.14, handheld=0.4, focus=(540, 1200)):
        boardwalk(ctx, t, "grey")
        x = lerp(160, 440, prog(t, 0, d))
        soft_shadow(ctx, x, 1705, 360)
        zombie(ctx, 0, x, 1700, 1000, t, face=1, expr="shock")
        RAIN.draw(ctx, t)
    finish(ctx, t, d)


def p1s8(ctx, t, d):
    n = int(clamp(prog(t, 0.5, d - 0.5)) * 6)
    with camera(ctx, t, d, push=0.06, handheld=0.6, focus=(540, 1100)):
        surf_shop(ctx, t)
        rgb(ctx, hexc("#9fb8c4")); ctx.rectangle(140, 500, 800, 900); ctx.fill()                # the glass door
        for k in range(n):
            board(ctx, 540, 1350 - k * 130, 860, ["#f4d35e", "#ee6c4d", "#f7f7f2", "#3d5a80", "#98c1d9", "#e0a526"][k], ang=0.05 * (k % 2 - 0.5))
        soft_shadow(ctx, 860, 1705, 300)
        KAI.draw(ctx, 860, 1700, 860, t, face=-1, expr="determined", look=(-1, -0.2), arm_f=(1.6 + 0.4 * math.sin(t * 5), 0.3))
    finish(ctx, t, d)


def p1s9(ctx, t, d):
    k1 = T1.at(9, 1)
    mood = "day" if t < k1 else "dusk"
    with camera(ctx, t, d, push=-0.06, handheld=0.4, focus=(540, 1200)):
        boardwalk(ctx, t, mood)
        shopfront(ctx, t, 540, mood, lit=False)
        n = 4 if t < k1 else 12
        for k in range(n):
            r = random.Random(k)
            zombie(ctx, k, r.uniform(60, 1020), 1500 + r.uniform(0, 300), r.uniform(380, 520), t, walk=False, face=1 if r.random() < 0.5 else -1)
    if t > k1:
        text(ctx, "40", 540, 300, 220, (1, 0.4, 0.3), prog(t, k1, k1 + 0.2), outline=14)
    finish(ctx, t, d)


def p1s10(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 900)):
        rgb(ctx, hexc("#2a3140")); ctx.paint(); glow(ctx, 540, 900, 700, (0.5, 0.6, 0.8), 0.2)
        radio(ctx, t, 1.0)
    if t < T1.at(10, 1):
        rgb(ctx, (0, 0, 0), 0.7 * prog(t, 0.0, 0.3) * (1 - prog(t, 0.6, 1.0))); ctx.paint()
    text(ctx, "STAY INDOORS", 540, 1650, 110, (1, 0.85, 0.4), prog(t, T1.at(10, -1), T1.at(10, -1) + 0.2), outline=10)
    finish(ctx, t, d)


def p1s11(ctx, t, d):
    with camera(ctx, t, d, push=0.07, handheld=0.3, focus=(540, 1300)):
        sky(ctx, "dusk", 1100)
        ocean(ctx, t, 1000, night=False)
        sand(ctx, 1450, night=False)
        foam(ctx, t, 1440)
        for k in range(7):
            soft_shadow(ctx, 90 + k * 150, 1605, 140)
            zombie(ctx, k, 90 + k * 150, 1600, 420, t, walk=False, face=-1 if k % 2 else 1)
    finish(ctx, t, d)


def p1s12(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 800)):
        surf_shop(ctx, t); rgb(ctx, (0.05, 0.05, 0.1), 0.5); ctx.paint()
        close(TESS, ctx, 540, 820, 260, t, face=0, expr="suspicious", talk=talk_fn(1, 12)(t) * 0.5, look=(0.6, 0.3))
    finish(ctx, t, d)


def p1s13(ctx, t, d):
    cr = 0.4
    with camera(ctx, t, d, push=0.10, handheld=0.5, focus=(540, 900), shake=0.6 if 0 < t - cr < 0.3 else 0.05):
        window_crowd(ctx, t, n=7, crack=prog(t, cr, cr + 0.3), press=1.0, mood="night")
    finish(ctx, t, d)


def p1s14(ctx, t, d):
    look = (1, 0) if t < T1.at(14, 1) else (0.2, 0.6) if t < T1.at(14, 2) else (-0.8, 0.4)
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 1000)):
        surf_shop(ctx, t); rgb(ctx, (0.05, 0.05, 0.12), 0.55); ctx.paint()
        board(ctx, 200, 1450, 700, "#f4d35e", ang=-1.4); board(ctx, 320, 1450, 700, "#98c1d9", ang=-1.4)
        close(KAI, ctx, 640, 900, 230, t, face=-1, expr="neutral", expr_to="determined", expr_k=prog(t, T1.at(14, 2), d), look=look)
    finish(ctx, t, d)


def p1s15(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 900)):
        sky(ctx, "night", 1000); ocean(ctx, t, 950, night=True, rip=0.3)
        close(TESS, ctx, 540, 1150, 240, t, face=0, expr="fear", look=(0, 0), head_turn=0.3 * math.sin(t * 3))
    finish(ctx, t, d)


def p1s16(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.6, focus=(540, 900), shake=0.5 if t < 0.4 else 0.1):
        window_crowd(ctx, t, n=8, crack=0.6 + 0.4 * prog(t, 0, 0.5), press=1.0, mood="night")
    finish(ctx, t, d)


def p1s17(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.5, focus=(540, 1000)):
        surf_shop(ctx, t); rgb(ctx, (0.05, 0.05, 0.12), 0.5); ctx.paint()
        board(ctx, 300, 1100, 900, "#f4d35e", ang=-1.35); board(ctx, 420, 1120, 900, "#98c1d9", ang=-1.35)
        close(KAI, ctx, 660, 860, 240, t, face=-1, expr="determined", talk=talk_fn(1, 17, 1)(t), look=(-1, 0), arm_f=(1.2, 0.6))
    finish(ctx, t, d)


def p1s18(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 1300)):
        sky(ctx, "night", 1100); ocean(ctx, t, 1000, night=True)
        sand(ctx, 1450); foam(ctx, t, 1440, 0.5)
        for k in range(6):
            zombie(ctx, k, 100 + k * 180, 1650, 380, t, walk=False, face=-1)
        rgb(ctx, (0, 0, 0), 0.35); ctx.paint()
    end_card(ctx, t, T1, 18, "PADDLE", "OUT?", "COMMENT: YES OR NO", "PART 2 NEXT")
    finish(ctx, t, d, fo=0.3)


# ------------------------------------------------------------------ PART 2
def p2s1(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.8, focus=(540, 900), shake=0.5 if t < 0.5 else 0.1):
        window_crowd(ctx, t, n=8, crack=1.0, press=1.0, mood="night")
        if t > 0.3:
            rgb(ctx, (1, 1, 1), 0.6 * (1 - prog(t, 0.3, 0.7))); ctx.paint()
    shot_card(ctx, t, text, "PADDLE OUT?", 0.0, y=330, size=150)
    finish(ctx, t, d, fi=0.0)


def p2s2(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.8, focus=(540, 1300), pan=(120, 0), shake=0.1):
        sky(ctx, "night", 1100); ocean(ctx, t, 1000, night=True); sand(ctx, 1400); foam(ctx, t, 1390, 0.5)
        for k in range(5):
            zombie(ctx, k, -160 + k * 120 + t * 90, 1700 + (k % 2) * 60, 520, t * 1.6, face=1, expr="shock")
        KAI.draw(ctx, 600 + t * 70, 1680, 700, t, mode="run", phase=t * 10, face=1, expr="fear", look=(-1, 0), arm_b=(0.6, 0.4))
        TESS.draw(ctx, 450 + t * 70, 1720, 640, t, mode="run", phase=t * 10 + 1.5, face=1, expr="fear", look=(1, 0))
        board(ctx, 660 + t * 70, 1350, 600, "#f4d35e", ang=-0.2)
    finish(ctx, t, d)


def p2s3(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.6, focus=(540, 1100)):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True, speed=2)
        foam(ctx, t, 1350, 0.8)
        rider(ctx, TESS, 400, 1350, 560, t, face=1, expr="fear", look=(1, -0.3))
        rider(ctx, KAI, 720, 1300, 600, t, face=-1, expr="determined", talk=talk_fn(2, 3, 1)(t), look=(-1, 0))
    finish(ctx, t, d)


def p2s4(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 1200)):
        sky(ctx, "night", 1000); ocean(ctx, t, 950, night=True)
        sand(ctx, 1500); foam(ctx, t, 1490, 0.7)
        for k in range(8):
            soft_shadow(ctx, 70 + k * 135, 1705, 120)
            zombie(ctx, k, 70 + k * 135, 1700, 520 + (k % 3) * 40, t, walk=False, face=-1 if k % 2 else 1, expr="angry")
    finish(ctx, t, d)


def p2s5(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 900)):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True)
        close(TESS, ctx, 540, 900, 240, t, mode="sit", face=0, expr="happy", expr_to="sad", expr_k=prog(t, T2.at(5, 1), T2.at(5, 1) + 0.5),
              look=(0, -0.2))
    finish(ctx, t, d)


def p2s6(ctx, t, d):
    with camera(ctx, t, d, push=-0.10, handheld=0.5, focus=(540, 1300), pan=(0, -200)):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True, rip=prog(t, 0.3, 1.5), speed=3)
        sand(ctx, 1700 + 250 * prog(t, 0, d)); foam(ctx, t, 1690 + 250 * prog(t, 0, d), 0.6)
        y = 1300 - 200 * prog(t, 0, d)
        rider(ctx, TESS, 460, y, 380, t, face=1, expr="fear", look=(0, 1))
        rider(ctx, KAI, 640, y - 30, 400, t, face=-1, expr="shock", look=(0, 1))
    finish(ctx, t, d)


def p2s7(ctx, t, d):
    with camera(ctx, t, d, push=0.05, handheld=0.2, focus=(540, 900)):
        sky(ctx, "day", 500); ocean(ctx, t, 450, night=False, rip=1.0, y1=1500)
        sand(ctx, 1500, night=False); foam(ctx, t, 1490, 0.9)
    text(ctx, "RIP CURRENT", 540, 320, 120, (1, 1, 1), prog(t, 0.2, 0.5), outline=12)
    finish(ctx, t, d)


def p2s8(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.6, focus=(540, 1100), shake=0.1):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True, rip=0.8, speed=3)
        rider(ctx, TESS, 540, 1300, 640, t, face=-1, expr="fear", look=(-1, 0))
    if t > T2.at(8, 1):
        text(ctx, "WRONG WAY", 540, 1700, 110, (1, 0.4, 0.3), prog(t, T2.at(8, 1), T2.at(8, 1) + 0.2), outline=10)
    finish(ctx, t, d)


def p2s9(ctx, t, d):
    with camera(ctx, t, d, push=0.16, handheld=0.3, focus=(540, 1000)):
        sky(ctx, "night", 1100); ocean(ctx, t, 1000, night=True); sand(ctx, 1350); foam(ctx, t, 1340, 0.5)
        for k in range(5):
            zombie(ctx, k, 140 + k * 200, 1900, 900, t, walk=False, face=-1 if k % 2 else 1)
    finish(ctx, t, d)


def p2s10(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.5, focus=(540, 900)):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True, rip=0.6, speed=2)
        close(KAI, ctx, 540, 900, 260, t, mode="sit", face=0, expr="angry", talk=talk_fn(2, 10, 1)(t), look=(-0.6, 0), arm_f=(1.6, 0.2))
    finish(ctx, t, d)


def p2s11(ctx, t, d):
    with camera(ctx, t, d, push=0.03, handheld=0.2):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True, rip=0.6)
        rgb(ctx, (0, 0, 0), 0.4); ctx.paint()
    rule_card(ctx, t, 0.2, [("DON'T FIGHT IT", T2.at(11, 1)), ("GO SIDEWAYS", T2.at(11, 2)), ("THEN COME IN", T2.at(11, -1))],
              title="RIP CURRENT")
    finish(ctx, t, d)


def p2s12(ctx, t, d):
    off = t * 120
    with camera(ctx, t, d, push=0.05, handheld=0.4, focus=(540, 1100)):
        sky(ctx, "night", 900)
        ctx.save(); ctx.translate(-off % 300, 0); ocean(ctx, t, 850, night=True); ctx.restore()
        rider(ctx, TESS, 420, 1250, 480, t, face=1, expr="determined", look=(1, 0))
        rider(ctx, KAI, 720, 1220, 500, t, face=1, expr="tired", look=(1, 0))
        rgb(ctx, (1, 1, 1), 0.6); ctx.set_line_width(8)
        for k in range(3):                                            # sideways arrows
            x = (k * 380 + t * 200) % 1300 - 100
            ctx.move_to(x, 1600); ctx.line_to(x + 120, 1600); ctx.line_to(x + 90, 1570); ctx.move_to(x + 120, 1600); ctx.line_to(x + 90, 1630); ctx.stroke()
    finish(ctx, t, d)


def p2s13(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 1200), pan=(-100, 0)):
        sky(ctx, "night", 1000); ocean(ctx, t, 950, night=True)
        sand(ctx, 1400); foam(ctx, t, 1390, 0.6)
        for k in range(9):
            zombie(ctx, k, (k * 150 + t * 120) % (W + 300) - 150, 1650 + (k % 3) * 40, 420, t, face=1)
    finish(ctx, t, d)


def p2s14(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.2, focus=(540, 1100)):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True, speed=0.3)
        rider(ctx, TESS, 400, 1250, 500, t, paddle=False, face=1, expr="tired", look=(1, 0))
        rider(ctx, KAI, 700, 1230, 520, t, paddle=False, face=-1, expr="tired", look=(-1, 0))
    finish(ctx, t, d)


def p2s15(ctx, t, d):
    bump = 0.6
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 1200), shake=0.5 if 0 < t - bump < 0.3 else 0):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True, speed=0.3)
        rgb(ctx, (0.02, 0.03, 0.05)); ctx.save(); ctx.translate(380, 1420); ctx.scale(1.6, 0.4); ctx.arc(0, 0, 120, 0, 6.283); ctx.restore(); ctx.fill()
        rider(ctx, KAI, 620, 1300, 640, t, paddle=False, face=-1, expr="neutral", expr_to="fear", expr_k=prog(t, bump, bump + 0.3), look=(-1, 0.8))
    finish(ctx, t, d)


def p2s16(ctx, t, d):
    with camera(ctx, t, d, push=0.14, handheld=0.3, focus=(540, 1000)):
        ocean(ctx, t, -300, night=True, speed=0.3)
        ctx.save(); ctx.translate(540, 1000); ctx.rotate(-0.3)
        rgb(ctx, hexc("#8fa58a"))                                                                     # arms spread out
        for sy in (-1, 1):
            ctx.save(); ctx.translate(-150, sy * 120); ctx.rotate(sy * 0.5); rrect(ctx, -320, -45, 330, 90, 45); ctx.fill(); ctx.restore()
        rgb(ctx, hexc("#2b2b33")); rrect(ctx, 200, -110, 380, 220, 70); ctx.fill()                   # legs
        rgb(ctx, hexc("#d6302c")); rrect(ctx, -260, -150, 520, 300, 90); ctx.fill()                # back of the lifeguard shirt
        text(ctx, "LIFEGUARD", 0, 0, 74, (1, 1, 1))
        rgb(ctx, hexc("#5a4030")); ctx.arc(-370, 0, 125, 0, 6.283); ctx.fill()                       # back of the head
        ctx.restore()
        rgb(ctx, SEA_N[0], 0.45); ctx.rectangle(0, 1080, W, 400); ctx.fill()
    finish(ctx, t, d)


def p2s17(ctx, t, d):
    grab = 0.5
    g = ease_out(prog(t, grab, grab + 0.25))
    with camera(ctx, t, d, push=0.10, handheld=0.6, focus=(540, 900), shake=0.6 if 0 < t - grab < 0.4 else 0.1):
        underwater(ctx, t)
        kai_leg(ctx, 600, 700, 1.4, kick=0.1 * math.sin(t * 8))
        grey_hand(ctx, lerp(640, 600, g), lerp(1700, 900, g), 1.2, ang=-0.15)
    finish(ctx, t, d)


def p2s18(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.4, focus=(540, 1200)):
        underwater(ctx, t)
        kai_leg(ctx, 600, 500, 1.0)
        grey_hand(ctx, 600, 650, 0.9)
        rgb(ctx, (0, 0, 0), 0.35); ctx.paint()
    end_card(ctx, t, T2, 18, "KICK", "FREE?", "COMMENT: YES OR NO", "PART 3 NEXT")
    finish(ctx, t, d, fo=0.3)


# ------------------------------------------------------------------ PART 3
def p3s1(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.8, focus=(540, 900), shake=0.25):
        underwater(ctx, t)
        kai_leg(ctx, 600, 700, 1.4, kick=0.3 * math.sin(t * 9))
        grey_hand(ctx, 600, 900, 1.2, ang=-0.15)
    shot_card(ctx, t, text, "KICK FREE?", 0.0, y=330, size=150)
    finish(ctx, t, d, fi=0.0)


def p3s2(ctx, t, d):
    tip = 0.25 * math.sin(t * 6) * prog(t, 0.2, 0.6)
    with camera(ctx, t, d, push=0.10, handheld=0.8, focus=(540, 1100), shake=0.3, roll=0.06):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True, speed=2)
        rider(ctx, TESS, 300, 1200, 400, t, paddle=False, face=1, expr="shock", talk=0.8, look=(1, 0))
        ctx.save(); ctx.translate(680, 1350); ctx.rotate(tip); ctx.translate(-680, -1350)
        rider(ctx, KAI, 680, 1300, 620, t, paddle=False, face=-1, expr="fear", look=(0, 1), arm_f=(1.8, 0.2))
        ctx.restore()
    finish(ctx, t, d)


def p3s3(ctx, t, d):
    k1, k2 = T3.at(3, 1), T3.at(3, 2)
    with camera(ctx, t, d, push=0.08, handheld=0.7, focus=(540, 900), shake=0.4 if any(0 < t - k < 0.25 for k in (k1, k2)) else 0.1):
        underwater(ctx, t)
        kick = math.sin(t * 10) if t > k1 else 0.2 * math.sin(t * 6)
        off = t > k2 + 0.4
        kai_leg(ctx, 600, 650 - (200 * prog(t, k2 + 0.4, k2 + 0.8)), 1.4, kick=kick * 0.5, shoe=not off)
        hy = 880 + 600 * prog(t, k2 + 0.4, d)
        grey_hand(ctx, 600, hy, 1.2, ang=-0.15)
        if off:
            flipflop(ctx, 630, hy - 60, 0.3, 1.0, 1.2)
    finish(ctx, t, d)


def p3s4(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 900)):
        underwater(ctx, t)
        y = 900 + 300 * prog(t, 0, d)
        grey_hand(ctx, 540, y, 1.3)
        flipflop(ctx, 560, y - 100, 0.2, 1.0, 1.4)
    finish(ctx, t, d)


def p3s5(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.2, focus=(540, 900)):
        underwater(ctx, t)
        a = 1 - prog(t, 0.3, d)
        ctx.save(); ctx.translate(540, 1100 + 500 * prog(t, 0, d)); ctx.scale(0.7, 0.7)
        rgb(ctx, (0.02, 0.05, 0.06), 0.9 * a); rrect(ctx, -160, -300, 320, 600, 120); ctx.fill(); ctx.arc(0, -400, 110, 0, 6.283); ctx.fill()
        flipflop(ctx, 120, -420, 0.4, a, 1.0)
        ctx.restore()
    finish(ctx, t, d)


def p3s6(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 1000)):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True, speed=0.5)
        close(KAI, ctx, 540, 1000, 250, t, mode="sit", face=0, expr="tired", expr_to="happy", expr_k=0.6 * prog(t, T3.at(6, 1), T3.at(6, 1) + 0.6),
              talk=talk_fn(3, 6, 1)(t), look=(0, 0.3), lost_shoe=True)
    finish(ctx, t, d)


def p3s7(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 1000)):
        sky(ctx, "night", 900); ocean(ctx, t, 850, night=True, speed=0.5)
        close(TESS, ctx, 540, 1000, 250, t, mode="sit", face=1, expr="fear", look=(1, -0.2), arm_f=(1.6, 0.0))
    finish(ctx, t, d)


def p3s8(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(540, 1300), pan=(-80, 0)):
        sky(ctx, "night", 1000); ocean(ctx, t, 950, night=True)
        sand(ctx, 1450); foam(ctx, t, 1440, 0.5)
        for k in range(10):
            zombie(ctx, k, (k * 120 + t * 90) % (W + 200) - 100, 1700 + (k % 3) * 30, 380, t, face=1)
    finish(ctx, t, d)


def p3s9(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 900), pan=(160, 0)):
        sky(ctx, "night", 1000); ocean(ctx, t, 950, night=True)
        close(KAI, ctx, 400, 1050, 220, t, mode="sit", face=1, expr="determined", look=(1, -0.2), head_turn=0.3 * math.sin(t * 1.5), lost_shoe=True)
    finish(ctx, t, d)


def p3s10(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 1100)):
        sky(ctx, "night", 1200); ocean(ctx, t, 1100, night=True)
        cliffs(ctx, t)
        sand(ctx, 1500); foam(ctx, t, 1490, 0.6)
        rgb(ctx, (0.25, 0.25, 0.3)); ctx.rectangle(300, 1500, 480, 500); ctx.fill()
        vgrad(ctx, 1500, 1800, [(0, hexc("#5a5a62")), (1, hexc("#2e2e36"))], x=300, w=480)
    text(ctx, "NO WAY DOWN", 540, 330, 110, (1, 1, 1), prog(t, T3.at(10, -1), T3.at(10, -1) + 0.2), outline=10)
    finish(ctx, t, d)


def p3s11(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.4, focus=(540, 1100)):
        sky(ctx, "night", 1000)
        rgb(ctx, hexc("#16161c"))                                       # rocks
        for k in range(7):
            r = random.Random(k); ctx.arc(r.uniform(0, W), 1500 + r.uniform(-100, 200), r.uniform(150, 280), 0, 6.283); ctx.fill()
        for k in range(5):
            zombie(ctx, k, 160 + k * 190, 1350 + 20 * math.sin(t * 3 + k), 460, t, walk=True, face=1 if k % 2 else -1, expr="angry")
        rgb(ctx, hexc("#16161c")); ctx.rectangle(-100, 1400, W + 200, 700); ctx.fill()
    finish(ctx, t, d)


def p3s12(ctx, t, d):
    p = prog(t, 0, d)
    with camera(ctx, t, d, push=0.06, handheld=0.6, focus=(540, 1100), shake=0.15):
        sky(ctx, "night", 900)
        ocean(ctx, t, 850, night=True, speed=3)
        rgb(ctx, (0.08, 0.18, 0.26)); ctx.move_to(-100, 1500)                # the wave face
        ctx.curve_to(200, 1100, 700, 900, 1180, 1050); ctx.line_to(1180, H); ctx.line_to(-100, H); ctx.fill()
        foam(ctx, t, 1020 + 60 * math.sin(t), 0.8)
        for x, ch in ((360 + 80 * p, TESS), (700 + 80 * p, KAI)):
            board(ctx, x, 1250, 420, "#f4d35e" if ch is KAI else "#98c1d9", ang=0.35)
            ch.draw(ctx, x, 1230, 420, t, mode="sit", face=1, expr="shock" if ch is TESS else "happy", look=(1, 0.3), lean=0.3,
                    talk=0.8 if ch is TESS else 0, lost_shoe=ch is KAI)
    finish(ctx, t, d)


def p3s13(ctx, t, d):
    dawn = prog(t, 0.5, d)
    with camera(ctx, t, d, push=0.06, handheld=0.2, focus=(540, 1300)):
        sky(ctx, "night" if dawn < 0.5 else "dawn", 1200)
        rgb(ctx, (0.9, 0.6, 0.5), 0.0)
        ocean(ctx, t, 1100, night=dawn < 0.5)
        cliffs(ctx, t, dawn)
        sand(ctx, 1500, night=dawn < 0.5)
        for x, ch in ((420, TESS), (680, KAI)):
            ch.draw(ctx, x, 1700, 520, t, mode="sit", face=1 if ch is TESS else -1, expr="tired", look=(0, -0.5), lost_shoe=ch is KAI, torn=0.8 if ch is KAI else 0)
    finish(ctx, t, d)


def p3s14(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(540, 900)):
        sky(ctx, "dawn", 1100); ocean(ctx, t, 1000, night=False)
        helicopter(ctx, t, lerp(1200, 700, prog(t, T3.at(14, 1), d)), 400, 1.2)
        rgb(ctx, hexc("#e8eef4")); ctx.save(); ctx.translate(lerp(-200, 300, prog(t, 0, d)), 1120)
        rrect(ctx, -160, -60, 320, 90, 30); ctx.fill(); rgb(ctx, hexc("#d6532c")); ctx.rectangle(-160, -10, 320, 20); ctx.fill(); ctx.restore()
        cliffs(ctx, t, 1.0)
    finish(ctx, t, d)


def p3s15(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1100)):
        sky(ctx, "dawn", 1100); ocean(ctx, t, 1000, night=False); sand(ctx, 1400, night=False)
        soft_shadow(ctx, 540, 1755, 360)
        KAI.draw(ctx, 540, 1750, 1000, t, face=0, expr="tired", look=(0, 0), torn=1.0, dirt=0.6, lost_shoe=True)
        rgb(ctx, (0.95, 0.4, 0.35), 0.35); ctx.arc(540, 1750 - 0.888 * 1000 + 30, 22, 0, 6.283); ctx.fill()   # sunburnt nose
    finish(ctx, t, d)


def p3s16(ctx, t, d):
    shirt_insert(ctx, t, T3.at(16, 1))
    finish(ctx, t, d)


def p3s17(ctx, t, d):
    hug = ease(prog(t, 0.3, 1.2))
    with camera(ctx, t, d, push=0.07, handheld=0.2, focus=(540, 1200)):
        sky(ctx, "dawn", 1100); ocean(ctx, t, 1000, night=False); sand(ctx, 1400, night=False)
        god_rays(ctx, t, 900, 800, angle=2.5, length=1600, col=(1, 0.85, 0.6), alpha=0.16)
        soft_shadow(ctx, 380, 1705, 280); soft_shadow(ctx, 700, 1705, 300)
        TESS.draw(ctx, lerp(360, 470, hug), 1700, 700, t, face=1, expr="happy", talk=talk_fn(3, 17, 1, 1)(t), look=(1, -0.2), arm_f=(lerp(0.2, 1.5, hug), 0.4))
        KAI.draw(ctx, 700, 1700, 760, t, face=-1, expr="happy", talk=talk_fn(3, 17, 3)(t), look=(-1, 0), torn=1.0, dirt=0.6, lost_shoe=True)
    finish(ctx, t, d)


def p3s18(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 1300)):
        sky(ctx, "night", 1100); ocean(ctx, t, 1000, night=True)
        sand(ctx, 1450); foam(ctx, t, 1440, 0.5)
        for k in range(6):
            zombie(ctx, k, 100 + k * 180, 1650, 380, t, walk=False, face=-1)
        rgb(ctx, (0, 0, 0), 0.35); ctx.paint()
    end_card(ctx, t, T3, 18, "PADDLE", "OUT?", "COMMENT: YES OR NO", "NEW STORY TOMORROW")
    finish(ctx, t, d, fo=0.4)


P1 = [globals()[f"p1s{i}"] for i in range(1, 19)]
P2 = [globals()[f"p2s{i}"] for i in range(1, 19)]
P3 = [globals()[f"p3s{i}"] for i in range(1, 19)]


# ------------------------------------------------------------------ sound
def surf(d, amt, seed):
    t = np.arange(int(d * SR)) / SR
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * t / 6.0 + seed) ** 2
    return band_noise(d, 150, 3000, seed + 70) * swell * 0.16 * amt


def moans(d, times, seed=0):
    x = silence(d)
    for k, c in enumerate(times):
        i, n = int(c * SR), int(1.4 * SR)
        if i + n > len(x):
            continue
        tt = np.arange(n) / SR
        f = 95 + 25 * np.sin(np.pi * tt / 1.4) + np.random.default_rng(seed + k).uniform(-15, 15)
        saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
        x[i:i + n] += saw * np.sin(np.pi * tt / 1.4) ** 2 * 0.05
    return x


def glass(d, at, seed=0):
    return env_at(d, [at], 0.5) * band_noise(d, 2000, 10000, seed) * 0.7


def sfx_for(tm, part):
    def sfx(i, d):
        x = surf(d, 1.0, i + part * 30) + wind(d, 0.4, i)
        groans = moans(d, list(np.arange(0.4, d, 1.7)), i * 7 + part)
        if part == 1:
            if i in (2, 3):
                x = surf(d, 0.6, i) + band_noise(d, 3000, 8000, i) * 0.01
            if i in (1, 9, 11, 13, 16, 18):
                x += groans * (1.5 if i != 11 else 0.8)
            if i == 4:
                x += band_noise(d, 400, 3000, 44) * 0.08 + moans(d, [1.0], 4)
            if i in (6, 7, 12):
                x += groans * 0.5
            if i == 8:
                x += env_at(d, list(np.arange(0.6, d, 0.7)), 0.15) * band_noise(d, 100, 1200, 8) * 0.5
            if i == 10:
                x += band_noise(d, 800, 5000, 10) * 0.08
            if i == 13:
                x += glass(d, 0.4, 13)
            if i == 16:
                x += glass(d, 0.1, 16)
        elif part == 2:
            if i == 1:
                x += glass(d, 0.3, 21) * 1.4 + groans * 2
            if i in (2, 4, 9, 13):
                x += groans * 1.5
            if i in (6, 7, 8, 10, 11):
                x += band_noise(d, 60, 400, i) * 0.15
            if i in (15, 17, 18):
                x *= 0.6
                x += env_at(d, [0.6 if i == 15 else 0.5], 0.5) * band_noise(d, 40, 250, i) * 0.8
        else:
            if i in (1, 2, 3, 4, 5):
                x = band_noise(d, 40, 500, i) * 0.12 + env_at(d, list(np.arange(0.3, d, 2.2)), 0.6) * band_noise(d, 200, 800, i + 9) * 0.1
            if i in (8, 11):
                x += groans * 1.4
            if i == 12:
                x += surf(d, 2.5, 12)
            if i == 14:
                t = np.arange(len(x)) / SR
                x += band_noise(d, 30, 200, 14) * (0.15 + 0.1 * np.sin(2 * np.pi * 18 * t))
        return fades(x * 0.6, 0.03, 0.1)
    return sfx


def drone_score(total, seed=0):
    t = np.arange(int(total * SR)) / SR
    x = (np.sin(2 * np.pi * 43.65 * t) * 0.25 + np.sin(2 * np.pi * 44.2 * t) * 0.25
         + np.sin(2 * np.pi * 65.4 * t) * 0.1 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.06 * t)))
    x += band_noise(total, 60, 300, seed) * 0.08
    pulse = env_at(total, list(np.arange(1.0, total, 1.2)), 0.25) * np.sin(2 * np.pi * 55 * t) * 0.12
    return fades((x + pulse).astype(np.float32) * 0.6, 2.0, 2.0)


def music1(durs):
    a = sum(durs[:3])
    return np.concatenate([piano_score(a, a + 100, bpm=84, seed=5), drone_score(sum(durs) - a, 1)])[: int(sum(durs) * SR)]


def music2(durs):
    return drone_score(sum(durs), 2)


def music3(durs):
    total = sum(durs)
    a = sum(durs[:11])
    return np.concatenate([drone_score(a, 3), piano_score(total - a, 999, bpm=70, seed=11)])[: int(total * SR)]


PARTS = {1: ("35_boardwalk_1", P1, sfx_for(T1, 1), music1), 2: ("36_boardwalk_2", P2, sfx_for(T2, 2), music2),
         3: ("37_boardwalk_3", P3, sfx_for(T3, 3), music3)}

if __name__ == "__main__":
    run(PARTS, {1: T1, 2: T2, 3: T3})
