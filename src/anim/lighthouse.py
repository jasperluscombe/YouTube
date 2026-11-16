"""The Last Lighthouse - Parts 1-3 (stories/23-25).

    python src/anim/lighthouse.py <part 1|2|3> [scene numbers]
"""
import math, pathlib, random, sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import *  # noqa
import lights as L
from story import Timing, run

T1, T2, T3 = Timing("23_lighthouse_1"), Timing("24_lighthouse_2"), Timing("25_lighthouse_3")
SP = 430
JUNO = ((0.98, 0.80, 0.15), (0.80, 0.62, 0.08), (0.25, 0.30, 0.45), (0.18, 0.22, 0.34))
DAD = ((0.45, 0.33, 0.25), (0.33, 0.24, 0.18), (0.22, 0.22, 0.26), (0.15, 0.15, 0.18))
CAT = (0.24, 0.24, 0.27)
CAT_L = (0.42, 0.42, 0.46)
STARS = [(random.Random(k).uniform(0, W), random.Random(k + 3).uniform(0, 1000), random.Random(k + 6).uniform(1, 2.4)) for k in range(150)]


# ------------------------------------------------------------------ world
def sky(ctx, t, storm=0.0, dawn=0.0, horizon=1100):
    night = [(0, hexc("#04060d")), (0.75, hexc("#0e1426")), (1, hexc("#1b2238"))]
    stormy = [(0, hexc("#07080b")), (0.7, hexc("#161a20")), (1, hexc("#262b33"))]
    morning = [(0, hexc("#2b3a6b")), (0.55, hexc("#d98a6a")), (1, hexc("#f6c77e"))]
    base = morning if dawn > 0.5 else (stormy if storm > 0.5 else night)
    vgrad(ctx, -600, horizon, base)
    rgb(ctx, base[-1][1]); ctx.rectangle(0, horizon - 1, W, 700); ctx.fill()   # no gap above the sea
    if storm <= 0.5 and dawn <= 0.5:
        for k, (x, y, r) in enumerate(STARS):
            rgb(ctx, (1, 1, 1), 0.4 + 0.3 * math.sin(t * 1.4 + k)); ctx.arc(x, y, r, 0, 6.283); ctx.fill()
    if storm > 0:
        for k in range(7):
            cx = (k * 230 + t * (30 + 6 * k)) % (W + 600) - 300
            rgb(ctx, (0.12, 0.13, 0.16), 0.75 * storm)
            ctx.save(); ctx.translate(cx, 120 + (k % 3) * 120); ctx.scale(3.2, 1); ctx.arc(0, 0, 90 + 10 * k, 0, 6.283); ctx.restore(); ctx.fill()
    if dawn > 0:
        glow(ctx, 760, horizon - 40, 700, (1, 0.8, 0.5), 0.5 * dawn)
        rgb(ctx, (1, 0.9, 0.6), dawn); ctx.arc(760, horizon - 10, 70, math.pi, 2 * math.pi); ctx.fill()


def waves(ctx, t, y0, amp, col, speed=1.0, ph=0.0, k=0.012, foam=True):
    ctx.move_to(-20, H + 20)
    pts = []
    for x in range(-20, W + 41, 20):
        y = y0 + amp * math.sin(k * x + t * speed + ph) + 0.45 * amp * math.sin(2.3 * k * x - t * speed * 1.3 + ph * 2)
        pts.append((x, y)); ctx.line_to(x, y)
    ctx.line_to(W + 40, H + 20); ctx.close_path(); rgb(ctx, col); ctx.fill()
    if foam:
        rgb(ctx, (0.85, 0.9, 0.95), 0.18); ctx.set_line_width(4)
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.stroke()


def sea(ctx, t, storm=0.0, horizon=1100, dawn=0.0):
    a = 10 + 70 * storm
    if dawn > 0.5:
        cols = [hexc("#5d6f8e"), hexc("#3f4f6d"), hexc("#2c3a55")]
    else:
        cols = [hexc("#0d1730"), hexc("#0a1226"), hexc("#070d1c")]
    waves(ctx, t, horizon, a * 0.3, cols[0], 0.8 + storm, 0.3)
    waves(ctx, t, horizon + 220, a * 0.7, cols[1], 1.1 + storm * 1.5, 1.7)
    waves(ctx, t, horizon + 520, a, cols[2], 1.4 + storm * 2, 3.1)


def rock(ctx, x, y, w=520, h=220, col=hexc("#1b1d22")):
    rgb(ctx, col)
    ctx.move_to(x - w / 2, y + h); ctx.line_to(x - w * 0.42, y + h * 0.3); ctx.line_to(x - w * 0.2, y)
    ctx.line_to(x + w * 0.18, y + h * 0.05); ctx.line_to(x + w * 0.45, y + h * 0.35); ctx.line_to(x + w / 2, y + h)
    ctx.close_path(); ctx.fill()


def tower(ctx, t, x, base, h, lit=1.0, beam=True, beam_len=1100, beam_a=0.35):
    """Lighthouse: tapered white tower, red bands, gallery, lamp room, cap. Returns lamp position."""
    wb, wt = h * 0.2, h * 0.12
    ctx.move_to(x - wb / 2, base); ctx.line_to(x - wt / 2, base - h); ctx.line_to(x + wt / 2, base - h); ctx.line_to(x + wb / 2, base)
    ctx.close_path(); rgb(ctx, hexc("#d8d4cc")); ctx.fill_preserve(); ctx.save(); ctx.clip()
    for k in range(3):
        y = base - h * (0.18 + k * 0.3)
        rgb(ctx, hexc("#a8322b")); ctx.rectangle(x - wb, y - h * 0.07, wb * 2, h * 0.14); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.25); ctx.rectangle(x, base - h, wb, h); ctx.fill()
    ctx.restore()
    rgb(ctx, hexc("#2a2c31")); ctx.rectangle(x - wt * 0.9, base - h - 10, wt * 1.8, 14); ctx.fill()
    lx, ly = x, base - h - 45
    rgb(ctx, hexc("#1a1c20")); ctx.rectangle(x - wt * 0.5, ly - 35, wt, 70); ctx.fill()
    if lit > 0:
        glow(ctx, lx, ly, 120 + 80 * lit, (1, 0.85, 0.55), 0.8 * lit)
        rgb(ctx, (1, 0.93, 0.7), lit); ctx.rectangle(x - wt * 0.4, ly - 28, wt * 0.8, 56); ctx.fill()
        if beam:
            ang = t * 1.3
            ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
            for side, f in ((-1, max(0, math.cos(ang))), (1, max(0, -math.cos(ang)))):
                if f > 0.02:
                    cone(ctx, lx, ly, math.pi if side < 0 else 0, 0.05 + 0.05 * f, beam_len * f, (1, 0.9, 0.65), beam_a * lit * f)
            ctx.restore()
    rgb(ctx, hexc("#2a2c31")); ctx.move_to(x - wt * 0.7, ly - 35); ctx.line_to(x, ly - 75); ctx.line_to(x + wt * 0.7, ly - 35); ctx.close_path(); ctx.fill()
    return lx, ly


def rain(ctx, t, n=120, a=0.35, slant=0.25):
    r = random.Random(7); ctx.set_line_width(2)
    for k in range(n):
        x0, y0, sp = r.uniform(0, W + 300), r.uniform(0, H), r.uniform(1500, 2100)
        y = (y0 + t * sp) % H; x = (x0 - t * sp * slant) % (W + 300) - 150
        rgb(ctx, (0.75, 0.82, 0.9), a); ctx.move_to(x, y); ctx.line_to(x - 40 * slant, y + 42); ctx.stroke()


def lightning(ctx, t, times, x=700):
    f = max([math.exp(-(t - b) * 9) for b in times if t >= b] + [0])
    if f > 0.05:
        rgb(ctx, (0.85, 0.9, 1), 0.55 * f); ctx.paint()
        r = random.Random(int(sum(times) * 10))
        rgb(ctx, (1, 1, 1), f); ctx.set_line_width(6)
        px, py = x, 0
        ctx.move_to(px, py)
        while py < 900:
            px += r.uniform(-60, 60); py += r.uniform(60, 120); ctx.line_to(px, py)
        ctx.stroke()
    return f


def flashes(times):
    return lambda t: max([math.exp(-(t - b) * 9) for b in times if t >= b] + [0])


def cat(ctx, x, y, s, mode="sit", face=1, tail=0.0, look=0.0, crouch=0.0, phase=0.0):
    """One-eyed grey cat. (x, y) ground, s = sitting height."""
    ctx.save(); ctx.translate(x, y); ctx.scale(face, 1)
    if mode == "sit":
        rgb(ctx, CAT); ctx.set_line_width(0.09 * s); ctx.set_line_cap(1)
        ctx.move_to(-0.25 * s, -0.05 * s); ctx.curve_to(-0.6 * s, 0, -0.6 * s, -0.35 * s + tail * 0.1 * s, -0.45 * s, -0.45 * s + tail * 0.15 * s); ctx.stroke()
        ctx.save(); ctx.translate(0, -0.33 * s * (1 - 0.3 * crouch)); ctx.scale(0.36, 0.38 * (1 - 0.3 * crouch)); ctx.arc(0, 0, s, 0, 6.283); ctx.restore(); ctx.fill()
        rgb(ctx, CAT_L); ctx.save(); ctx.translate(0.08 * s, -0.3 * s); ctx.scale(0.14, 0.24); ctx.arc(0, 0, s, 0, 6.283); ctx.restore(); ctx.fill()
        hx, hy = 0.05 * s, -0.78 * s + 0.2 * crouch * s
    else:  # stand / walk
        rgb(ctx, CAT); ctx.set_line_width(0.08 * s); ctx.set_line_cap(1)
        for k, (lx, ph) in enumerate(((-0.3, 0), (0.3, math.pi), (-0.2, math.pi), (0.4, 0))):
            a = 0.4 * math.sin(phase + ph) if mode == "walk" else 0
            ctx.move_to(lx * s, -0.35 * s); ctx.line_to(lx * s + math.sin(a) * 0.3 * s, -0.04 * s); ctx.stroke()
        ctx.save(); ctx.translate(0, -0.42 * s); ctx.scale(0.5, 0.2); ctx.arc(0, 0, s, 0, 6.283); ctx.restore(); ctx.fill()
        ctx.move_to(-0.45 * s, -0.45 * s); ctx.curve_to(-0.7 * s, -0.5 * s, -0.7 * s, -0.9 * s + tail * 0.1 * s, -0.55 * s, -1.0 * s); ctx.stroke()
        hx, hy = 0.5 * s, -0.62 * s
    rgb(ctx, CAT); ctx.arc(hx, hy, 0.2 * s, 0, 6.283); ctx.fill()
    for side in (-1, 1):
        ctx.move_to(hx + side * 0.17 * s, hy - 0.08 * s); ctx.line_to(hx + side * 0.13 * s + 0.02 * s, hy - 0.34 * s); ctx.line_to(hx + side * 0.02 * s, hy - 0.16 * s)
        ctx.close_path(); ctx.fill()
    ex = hx + 0.07 * s + look * 0.03 * s
    rgb(ctx, (0.95, 0.8, 0.2)); ctx.arc(ex, hy - 0.02 * s, 0.05 * s, 0, 6.283); ctx.fill()
    rgb(ctx, (0, 0, 0)); ctx.save(); ctx.translate(ex, hy - 0.02 * s); ctx.scale(0.35, 1); ctx.arc(0, 0, 0.04 * s, 0, 6.283); ctx.restore(); ctx.fill()
    rgb(ctx, (0.12, 0.12, 0.14)); ctx.set_line_width(0.025 * s)   # scarred eye
    ex2 = hx - 0.08 * s
    ctx.move_to(ex2 - 0.05 * s, hy - 0.07 * s); ctx.line_to(ex2 + 0.05 * s, hy + 0.03 * s); ctx.stroke()
    ctx.move_to(ex2 + 0.05 * s, hy - 0.07 * s); ctx.line_to(ex2 - 0.05 * s, hy + 0.03 * s); ctx.stroke()
    rgb(ctx, (0.9, 0.6, 0.6)); ctx.arc(hx + 0.17 * s, hy + 0.05 * s, 0.025 * s, 0, 6.283); ctx.fill()
    ctx.restore()


def rowboat(ctx, x, y, w=420, tilt=0.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(tilt)
    rgb(ctx, hexc("#6b4a2e")); ctx.move_to(-w / 2, -40); ctx.line_to(w / 2, -40); ctx.line_to(w * 0.38, 30); ctx.line_to(-w * 0.4, 30); ctx.close_path(); ctx.fill()
    rgb(ctx, hexc("#8a6440")); ctx.rectangle(-w / 2, -48, w, 12); ctx.fill()
    ctx.restore()


def sailboat(ctx, x, y, s=1.0, tip=0.0, sink=0.0):
    ctx.save(); ctx.translate(x, y + sink * 120); ctx.rotate(tip); ctx.scale(s, s)
    rgb(ctx, hexc("#d9d6cf")); ctx.move_to(-240, -30); ctx.line_to(240, -30); ctx.line_to(180, 50); ctx.line_to(-200, 50); ctx.close_path(); ctx.fill()
    rgb(ctx, hexc("#3a3a3a")); ctx.set_line_width(14); ctx.move_to(0, -30); ctx.line_to(0, -460); ctx.stroke()
    rgb(ctx, hexc("#bfb8a8"), 0.9); ctx.move_to(10, -440); ctx.line_to(200, -60); ctx.line_to(10, -60); ctx.close_path(); ctx.fill()
    ctx.restore()


def end_card(ctx, t, tm, i, q1, q2, cta, button, red=True):
    q = prog(t, 0.2, 0.6)
    ctx.save(); ctx.translate(W / 2, 330); s = 1 + (1 - ease_out(q)) * 0.5; ctx.scale(s, s)
    text(ctx, q1, 0, -80, 125, (1, 1, 1), ease(q), outline=12)
    if q2:
        text(ctx, q2, 0, 70, 125, (1, 0.8, 0.4), ease(q), outline=12)
    ctx.restore()
    c = prog(t, tm.at(i, 1), tm.at(i, 1) + 0.4)
    if c > 0:
        bob = math.sin(t * 5) * 8
        rgb(ctx, (0, 0, 0), 0.6 * c); rrect(ctx, 110, 590 + bob, 860, 150, 30); ctx.fill()
        text(ctx, cta, W / 2, 665 + bob, 70, (1, 1, 1), c)
    f = prog(t, tm.at(i, -1), tm.at(i, -1) + 0.4)
    if f > 0:
        bw = 120 + 34 * len(button)
        rgb(ctx, hexc("#c4302b"), f); rrect(ctx, W / 2 - bw / 2, 800, bw, 120, 60); ctx.fill()
        text(ctx, button, W / 2, 860, 62, (1, 1, 1), f)


def finish(ctx, t, d, v=0.8, g=True, fi=0.1, fo=0.1):
    vignette(ctx, v)
    if g:
        grain(ctx, t)
    fade(ctx, t, d, fi, fo)


def big_word(ctx, t, word, t0, y=900, size=260, col=(1, 1, 1)):
    p = prog(t, t0, t0 + 0.3)
    if p > 0:
        ctx.save(); ctx.translate(W / 2, y); s = 1 + (1 - ease_out(p)) * 0.6; ctx.scale(s, s)
        text(ctx, word, 0, 0, size, col, ease(p), outline=14); ctx.restore()


# ------------------------------------------------------------------ PART 1
def p1s1(ctx, t, d):
    z = 1 + 0.08 * t / d
    ctx.save(); ctx.translate(W / 2, 1100); ctx.scale(z, z); ctx.translate(-W / 2, -1100)
    sky(ctx, t); rock(ctx, 540, 1060); tower(ctx, t, 540, 1080, 620); sea(ctx, t)
    ctx.restore(); finish(ctx, t, d, fi=0.0)


HOUSES = [(k * 140 - 40, 1000 - (k * 53 % 120), 110) for k in range(9)]


def p1s2(ctx, t, d):
    cut = T1.at(2, -1)
    if t < cut:
        sky(ctx, t)
        for (x, y, w) in HOUSES:
            rgb(ctx, hexc("#141821")); ctx.rectangle(x, y, w, 1100 - y); ctx.fill()
            ctx.move_to(x - 10, y); ctx.line_to(x + w / 2, y - 70); ctx.line_to(x + w + 10, y); ctx.fill()
            rgb(ctx, (1, 0.8, 0.4), 0.5 * (1 - prog(t, 0, cut))); ctx.rectangle(x + 30, y + 40, 22, 30); ctx.fill()
        lvl = lerp(1250, 820, ease(prog(t, 0, cut)))
        sea(ctx, t, 0.2, horizon=lvl)
    else:
        sky(ctx, t); rock(ctx, 540, 1060); tower(ctx, t, 540, 1080, 620); sea(ctx, t)
        cat(ctx, 640, 1062, 70, "sit", face=-1, tail=math.sin(t * 3))
    finish(ctx, t, d)


def window_frame(ctx, t, storm=0.0):
    rgb(ctx, hexc("#2a2420")); ctx.paint()
    ctx.save(); rrect(ctx, 140, 380, 800, 900, 400); ctx.clip()
    sky(ctx, t, storm, horizon=1050); sea(ctx, t, storm, horizon=1050)
    ctx.restore()
    rgb(ctx, hexc("#3a3029")); ctx.set_line_width(40); rrect(ctx, 140, 380, 800, 900, 400); ctx.stroke()
    ctx.set_line_width(16); ctx.move_to(540, 380); ctx.line_to(540, 1280); ctx.stroke(); ctx.move_to(140, 830); ctx.line_to(940, 830); ctx.stroke()
    rgb(ctx, hexc("#4a3d33")); ctx.rectangle(80, 1280, 920, 70); ctx.fill()


def p1s3(ctx, t, d):
    window_frame(ctx, t)
    tail = math.sin(t * 4) * (0.5 + 0.5 * math.sin(t))
    cat(ctx, 560, 1282, 380, "sit", face=1, tail=tail, look=math.sin(t * 0.8))
    text(ctx, "PEPPER", W / 2, 260, 110, (0.85, 0.85, 0.9), prog(t, 0.2, 0.6), outline=10)
    finish(ctx, t, d)


def spiral(ctx, t, scroll, lit=0.7):
    rgb(ctx, hexc("#26221f")); ctx.paint()
    ctx.save(); ctx.translate(0, scroll % 520)
    for k in range(-2, 6):
        y = k * 520
        d = 1 if k % 2 else -1
        rgb(ctx, hexc("#3b342e")); ctx.set_line_width(20)
        x0, x1 = (160, 920) if d > 0 else (920, 160)
        ctx.move_to(x0, y + 520); ctx.line_to(x1, y); ctx.stroke()
        for j in range(12):
            f = j / 12
            rgb(ctx, hexc("#4a4139")); ctx.rectangle(lerp(x0, x1, f) - 20, lerp(y + 520, y, f) - 6, 40, 8); ctx.fill()
        glow(ctx, 540, y + 260, 260, (1, 0.8, 0.5), 0.25 * lit)
    ctx.restore()


def lamp_room(ctx, t, lit, fire=0.0, storm=0.0):
    sky(ctx, t, storm, horizon=1150); sea(ctx, t, storm, horizon=1150)
    rgb(ctx, hexc("#1a1c20"), 0.92)
    for x in (60, 360, 700, 1000):
        ctx.rectangle(x - 18, 250, 36, 1100); ctx.fill()
    rgb(ctx, hexc("#2a2c31")); ctx.rectangle(0, 1250, W, 700); ctx.fill()
    ctx.rectangle(0, 180, W, 80); ctx.fill()
    # Fresnel lens
    cx, cy = 540, 820
    glow(ctx, cx, cy, 500, (1, 0.85, 0.55), 0.6 * lit)
    for k in range(7):
        rgb(ctx, (0.9, 0.95, 1.0), 0.18 + 0.4 * lit * (k % 2)); ctx.set_line_width(10)
        ctx.save(); ctx.translate(cx, cy); ctx.scale(1, 1.4); ctx.arc(0, 0, 60 + k * 30, 0, 6.283); ctx.restore(); ctx.stroke()
    rgb(ctx, (1, 0.95, 0.75), lit); ctx.arc(cx, cy, 50, 0, 6.283); ctx.fill()
    if fire > 0:
        r = random.Random(int(t * 20))
        for k in range(14):
            rgb(ctx, (1, r.uniform(0.4, 0.8), 0.1), 0.6 * fire)
            ctx.save(); ctx.translate(cx + r.uniform(-50, 50), cy + 40 - r.uniform(0, 120)); ctx.scale(0.5, 1)
            ctx.arc(0, 0, r.uniform(15, 40), 0, 6.283); ctx.restore(); ctx.fill()


def logbook(ctx, t, lines, starts, y0=520):
    rgb(ctx, hexc("#1a1512")); ctx.paint()
    glow(ctx, 540, 900, 900, (1, 0.8, 0.5), 0.25)
    rgb(ctx, hexc("#e9dfc8")); rrect(ctx, 90, 300, 900, 1250, 20); ctx.fill()
    rgb(ctx, (0.5, 0.6, 0.8), 0.35); ctx.set_line_width(3)
    for k in range(14):
        ctx.move_to(130, 420 + k * 80); ctx.line_to(950, 420 + k * 80); ctx.stroke()
    for k, (ln, t0) in enumerate(zip(lines, starts)):
        n = int(clamp((t - t0) * 14, 0, len(ln)))
        if n:
            text(ctx, ln[:n], 150, y0 + k * 80, 64, hexc("#2b2a3a"), anchor="left")
    return 150 + 30 * 1


def p1s4(ctx, t, d):
    a, b = T1.at(4, 1), T1.at(4, 2)
    if t < a:
        spiral(ctx, t, t * 420)
        person(ctx, 540, 1250, SP, "walk", phase=t * 6, face=1 if int(t * 420 / 520) % 2 else -1, lean=0.15)
        text(ctx, "112 STEPS", W / 2, 300, 100, (1, 0.9, 0.7), 0.9, outline=10)
    elif t < b:
        lamp_room(ctx, t, ease(prog(t, a, a + 0.6)))
        person(ctx, 300, 1250, SP, "idle", face=1, arm_f=(1.6, -0.2))
    else:
        logbook(ctx, t, ["DAY 1094 -"], [b + 0.3])
    finish(ctx, t, d)


def p1s5(ctx, t, d):
    logbook(ctx, t, ["DAY 1091 - NO SHIPS.", "DAY 1092 - NO SHIPS.", "DAY 1093 - NO SHIPS.", "DAY 1094 - NO SHIPS.", "NOBODY."],
            [-9, -9, -9, T1.at(5, 1), T1.at(5, 2) if len(T1.seg.get(5, [])) > 2 else T1.at(5, 1) + 1.5])
    finish(ctx, t, d, g=True)


def p1s6(ctx, t, d):
    lamp_room(ctx, t, 1.0)
    person(ctx, 540, 1420, 560, "idle", back_view=True, breathe=math.sin(t * 2))
    cat(ctx, 800, 1420, 110, "sit", face=-1, tail=math.sin(t * 2))
    finish(ctx, t, d)


def p1s7(ctx, t, d):
    cut = T1.at(7, 2)
    if t < cut:
        st = ease(prog(t, 0, cut))
        sky(ctx, t, storm=st); rock(ctx, 540, 1060); tower(ctx, t, 540, 1080, 620); sea(ctx, t, storm=0.4 * st)
        rain(ctx, t, int(60 * st), 0.3)
    else:
        rgb(ctx, hexc("#120f0d")); ctx.paint()
        rgb(ctx, hexc("#2a2420")); ctx.set_line_width(40)
        for y in (520, 760):
            ctx.move_to(0, y); ctx.line_to(W, y + 60); ctx.stroke()
        cat(ctx, 560, 500, 260, "sit", face=-1, crouch=0.6, tail=0.2, look=-1)
        glow(ctx, 560, 300, 60, (0.95, 0.8, 0.2), 0.4)
    finish(ctx, t, d)


def far_light(ctx, x, y, a, r=10):
    if a > 0.02:
        glow(ctx, x, y, 90, (1, 0.9, 0.6), 0.8 * a)
        rgb(ctx, (1, 0.95, 0.8), a); ctx.arc(x, y, r, 0, 6.283); ctx.fill()


def p1s8(ctx, t, d):
    z = 1 + 0.15 * ease(t / d)
    ctx.save(); ctx.translate(820, 1080); ctx.scale(z, z); ctx.translate(-820, -1080)
    sky(ctx, t, storm=1.0); sea(ctx, t, 0.5)
    blink = T1.at(8, 2)
    far_light(ctx, 820, 1085, (0.5 + 0.5 * math.sin((t - blink) * 6)) * (t > blink))
    ctx.restore()
    rain(ctx, t, 60, 0.25); finish(ctx, t, d)


MORSE = [0, 0, 0, 1, 1, 1, 0, 0, 0]


def p1s9(ctx, t, d):
    sky(ctx, t, storm=1.0); sea(ctx, t, 0.5)
    on = 0.0
    for k in range(9):
        t0 = T1.at(9, k); dur = 0.25 if MORSE[k] == 0 else 0.7
        if t0 <= t < t0 + dur:
            on = 1.0
    far_light(ctx, 820, 1085, on, 14)
    y = 1500
    for k in range(9):
        if t >= T1.at(9, k):
            x = 140 + k * 100
            rgb(ctx, (1, 0.9, 0.6))
            if MORSE[k] == 0:
                ctx.arc(x, y, 18, 0, 6.283); ctx.fill()
            else:
                rrect(ctx, x - 38, y - 12, 76, 24, 12); ctx.fill()
    rain(ctx, t, 50, 0.25); finish(ctx, t, d, fi=0.05)


def p1s10(ctx, t, d):
    sky(ctx, t, storm=1.0); sea(ctx, t, 0.5)
    rgb(ctx, (0, 0, 0), 0.4); ctx.paint()
    for k, ch in enumerate("SOS"):
        p = prog(t, T1.at(10, k), T1.at(10, k) + 0.3)
        if p > 0:
            ctx.save(); ctx.translate(250 + k * 290, 880); s = 1 + (1 - ease_out(p)) * 0.6; ctx.scale(s, s)
            text(ctx, ch, 0, 0, 330, (1, 0.9, 0.6), ease(p), outline=16); ctx.restore()
    finish(ctx, t, d, fi=0.05)


def p1s11(ctx, t, d):
    sky(ctx, t, storm=1.0)
    rgb(ctx, hexc("#2a2c31")); ctx.rectangle(0, 1180, W, 30); ctx.fill()
    rgb(ctx, hexc("#2a2c31")); ctx.set_line_width(8)
    for x in range(0, W, 70):
        ctx.move_to(x, 1180); ctx.line_to(x, 1000); ctx.stroke()
    ctx.move_to(0, 1000); ctx.line_to(W, 1000); ctx.stroke()
    sea(ctx, t, 0.5, horizon=1300)
    flash = (math.sin(t * 9) > 0.3) * prog(t, T1.at(11, 1), T1.at(11, 1) + 0.2)
    info = person(ctx, 380, 1180, 520, "idle", face=1, arm_f=(1.6 + 0.03 * math.sin(t * 40), -0.1), breathe=math.sin(t * 4))
    hx, hy = info["hand"]
    rgb(ctx, hexc("#3a3a3a")); rrect(ctx, hx - 10, hy - 45, 110, 90, 12); ctx.fill()
    if flash:
        ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
        cone(ctx, hx + 100, hy, -0.05, 0.12, 900, (1, 0.95, 0.75), 0.5); ctx.restore()
    q = "WHO ARE YOU?"
    n = int(clamp((t - T1.at(11, -1)) * 8, 0, len(q)))
    if n:
        text(ctx, q[:n], W / 2, 420, 110, (1, 0.9, 0.6), outline=10)
    rain(ctx, t, 60, 0.3); finish(ctx, t, d)


def p1s12(ctx, t, d):
    sky(ctx, t, storm=1.0); sea(ctx, t, 0.6)
    blink = (math.sin(t * 2.2) > 0.6) * prog(t, T1.at(12, -1), d)
    far_light(ctx, 820, 1085, blink)
    rain(ctx, t, 70, 0.3); finish(ctx, t, d)


def p1s13(ctx, t, d):
    sky(ctx, t, storm=1.0); sea(ctx, t, 0.6)
    rgb(ctx, (0, 0, 0), 0.45); ctx.paint()
    for k, w in enumerate(["CHILD", "ON", "BOARD."]):
        big_word(ctx, t, w, T1.at(13, k), y=650 + k * 260, size=230, col=(1, 0.9, 0.6) if k < 2 else (1, 0.4, 0.3))
    finish(ctx, t, d, fi=0.05)


def p1s14(ctx, t, d):
    bolts = [0.2, T1.at(14, 1), T1.at(14, 1) + 1.8]
    sky(ctx, t, storm=1.0); sea(ctx, t, 1.0)
    out = T1.at(14, -1) + 0.8
    if t < out:
        far_light(ctx, 820, 1100 + 30 * math.sin(t * 3), 0.6 + 0.4 * math.sin(t * 7))
    rain(ctx, t, 160, 0.4)
    lightning(ctx, t, bolts)
    finish(ctx, t, d)


def p1s15(ctx, t, d):
    sky(ctx, t, storm=1.0); rock(ctx, 540, 1260); tower(ctx, t, 540, 1280, 560); sea(ctx, t, 0.7, horizon=1300)
    rain(ctx, t, 100, 0.3)
    end_card(ctx, t, T1, 15, "WOULD", "YOU GO?", "COMMENT: YES OR NO", "PART 2 IS UP NEXT")
    finish(ctx, t, d, fo=0.25)


# ------------------------------------------------------------------ PART 2
def p2s1(ctx, t, d):
    sky(ctx, t, storm=1.0); sea(ctx, t, 0.6)
    dark = T2.at(1, -1) + 0.6
    if t < dark:
        far_light(ctx, 820, 1085, float(math.sin(t * 7) > 0))
    text(ctx, "PREVIOUSLY", W / 2, 260, 80, (1, 1, 1), 0.8, outline=8)
    big_word(ctx, t, "S O S", T2.at(1, 1), y=600, size=200, col=(1, 0.9, 0.6))
    rain(ctx, t, 60); finish(ctx, t, d, fi=0.0)


def dock(ctx, t, storm=1.0):
    sky(ctx, t, storm=storm, horizon=1000)
    rgb(ctx, hexc("#d8d4cc")); ctx.rectangle(820, 0, 180, 1100); ctx.fill()
    rgb(ctx, hexc("#a8322b")); ctx.rectangle(820, 300, 180, 160); ctx.fill()
    sea(ctx, t, storm * 0.7, horizon=1150)
    rock(ctx, 820, 1050, 700, 300)


def p2s2(ctx, t, d):
    dock(ctx, t)
    bob = math.sin(t * 2.4) * 30
    rowboat(ctx, 380, 1300 + bob, tilt=math.sin(t * 2) * 0.08)
    rgb(ctx, hexc("#b9a77e")); ctx.set_line_width(5); ctx.move_to(560, 1270 + bob); ctx.line_to(700, 1120); ctx.stroke()
    person(ctx, 720, 1140, SP, "idle", face=-1, crouch=0.4 * prog(t, T2.at(2, -1), d), arm_f=(1.0, 0.4))
    rain(ctx, t, 120, 0.35); finish(ctx, t, d)


def p2s3(ctx, t, d):
    dock(ctx, t)
    bob = math.sin(t * 2.4) * 30
    rowboat(ctx, 380, 1300 + bob, tilt=math.sin(t * 2) * 0.08)
    person(ctx, 360, 1260 + bob, SP, "idle", face=1, crouch=0.3)
    jp = prog(t, 0.2, 1.0)
    if jp < 1:
        cx, cy = lerp(760, 470, jp), lerp(1120, 1255 + bob, jp) - math.sin(jp * math.pi) * 260
        cat(ctx, cx, cy, 110, "stand", face=-1, tail=1)
    else:
        cat(ctx, 470, 1258 + bob, 110, "sit", face=-1, crouch=0.6, tail=math.sin(t * 6))
    rain(ctx, t, 120, 0.35); finish(ctx, t, d)


def row_scene(ctx, t, storm=1.0, juno=False, beam=None, cat_on=True):
    sky(ctx, t, storm=storm)
    if beam is not None:
        tower(ctx, t, 860, 1050, 260, lit=beam, beam_len=900)
    waves(ctx, t, 1100, 40 * storm, hexc("#0d1730"), 1.5, 0.3)
    swell = math.sin(t * 1.6) * 110 * storm
    by = 1350 + swell
    tilt = math.cos(t * 1.6) * 0.18 * storm
    ctx.save(); ctx.translate(540, by); ctx.rotate(tilt); ctx.translate(-540, -by)
    rowboat(ctx, 540, by)
    stroke = math.sin(t * 3.2)
    info = person(ctx, 500, by - 30, 380, "sit", face=-1, lean=0.25 * stroke, arm_f=(1.4 + 0.6 * stroke, -0.3), arm_b=(1.2 + 0.6 * stroke, -0.3))
    rgb(ctx, hexc("#8a6440")); ctx.set_line_width(10)
    hx, hy = info["hand"]; ctx.move_to(hx, hy); ctx.line_to(hx - 160, hy + 160 + 40 * stroke); ctx.stroke()
    if cat_on:
        cat(ctx, 680, by - 38, 80, "sit", face=-1, crouch=0.7, tail=0.1)
    if juno:
        person(ctx, 330, by - 30, 300, "sit", face=1, pal=JUNO, breathe=math.sin(t * 8) * 2)
    ctx.restore()
    waves(ctx, t, 1500 + swell * 0.3, 70 * storm, hexc("#070d1c"), 1.9, 2.6)


def p2s4(ctx, t, d):
    row_scene(ctx, t, 1.0)
    rain(ctx, t, 170, 0.4, 0.4); finish(ctx, t, d)


def p2s5(ctx, t, d):
    bolt = T2.at(5, 1) - 0.1
    sky(ctx, t, storm=1.0); sea(ctx, t, 1.0)
    f = lightning(ctx, t, [0.0, bolt])
    if t > bolt:
        a = max(f, 0.35)
        ctx.push_group(); sailboat(ctx, 760, 1150, 0.7, tip=1.0); ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
    rain(ctx, t, 150, 0.4); finish(ctx, t, d)


def p2s6(ctx, t, d):
    sky(ctx, t, storm=1.0)
    waves(ctx, t, 1150, 50, hexc("#0d1730"), 1.5, 0.3)
    sailboat(ctx, 560, 1400, 1.4, tip=1.05 + 0.05 * math.sin(t * 2))
    sx, sy = 560 - math.sin(1.05) * 300 * 1.4, 1400 - math.cos(1.05) * 300 * 1.4
    person(ctx, sx + 20, sy + 160, 330, "idle", face=1, pal=JUNO, arm_f=(2.4, 0.2), arm_b=(2.2, 0.3), breathe=math.sin(t * 9) * 3)
    waves(ctx, t, 1550, 80, hexc("#070d1c"), 1.9, 2.6)
    text(ctx, "MAYBE 10 YEARS OLD", W / 2, 300, 70, (1, 0.85, 0.3), prog(t, T2.at(6, -1), T2.at(6, -1) + 0.4), outline=8)
    rain(ctx, t, 150, 0.4); finish(ctx, t, d)


def p2s7(ctx, t, d):
    row_scene(ctx, t, 0.8, juno=t > T2.at(7, 1))
    if t > T2.at(7, 1):
        text(ctx, "JUNO", W / 2, 300, 110, (1, 0.85, 0.3), prog(t, T2.at(7, 1), T2.at(7, 1) + 0.4), outline=10)
    rain(ctx, t, 150, 0.4); finish(ctx, t, d)


def p2s8(ctx, t, d):
    sky(ctx, t, storm=1.0)
    waves(ctx, t, 1150, 40, hexc("#0d1730"), 1.2, 0.3)
    sailboat(ctx, 560, 1300, 1.0, tip=1.1, sink=ease(t / d) * 1.5)
    waves(ctx, t, 1450, 60, hexc("#070d1c"), 1.4, 2.6)
    rain(ctx, t, 90, 0.3); finish(ctx, t, d)


def p2s9(ctx, t, d):
    row_scene(ctx, t, 0.8, juno=True, beam=1.0)
    rain(ctx, t, 140, 0.4); finish(ctx, t, d)


def p2s10(ctx, t, d):
    b = 0.0 if (math.sin(t * 31) * math.sin(t * 7) < -0.2 and t > T2.at(10, 1)) else 1.0
    sky(ctx, t, storm=1.0); rock(ctx, 540, 1060); tower(ctx, t, 540, 1080, 620, lit=b); sea(ctx, t, 0.8)
    rain(ctx, t, 120, 0.35); finish(ctx, t, d)


def p2s11(ctx, t, d):
    off = T2.at(11, 0) + 0.2
    b = 1 - prog(t, off, off + 0.15)
    sky(ctx, t, storm=1.0); rock(ctx, 540, 1060); tower(ctx, t, 540, 1080, 620, lit=b); sea(ctx, t, 0.8)
    if b < 1:
        rgb(ctx, (0, 0, 0), 0.6 * (1 - b)); ctx.paint()
    rain(ctx, t, 120, 0.3); finish(ctx, t, d)


def p2s12(ctx, t, d):
    sky(ctx, t, storm=1.0); rock(ctx, 540, 1060); tower(ctx, t, 540, 1080, 620, lit=0); sea(ctx, t, 0.9)
    rgb(ctx, (0, 0, 0), 0.5); ctx.paint()
    lightning(ctx, t, [0.6, T2.at(12, -1)])
    rain(ctx, t, 140, 0.35); finish(ctx, t, d)


def huddle(ctx, t, point=0.0):
    sky(ctx, t, storm=0.8)
    tower(ctx, t, 880, 1150, 420, lit=0, beam=False)
    sea(ctx, t, 0.5, horizon=1150)
    rock(ctx, 540, 1150, 1300, 600, hexc("#15171b"))
    person(ctx, 360, 1300, SP, "sit", face=1, breathe=math.sin(t * 3))
    rgb(ctx, hexc("#15171b")); ctx.rectangle(270, 1300 - 110, 160, 110); ctx.fill()
    person(ctx, 600, 1300, 330, "idle" if point else "sit", face=1, pal=JUNO,
           arm_f=(2.6 * point, -0.1 * point) if point else None, breathe=math.sin(t * 9) * 2)
    if not point:
        rgb(ctx, hexc("#15171b")); ctx.rectangle(540, 1300 - 85, 130, 85); ctx.fill()
        cat(ctx, 640, 1215, 80, "sit", face=-1, crouch=0.6, tail=0.3)
    else:
        cat(ctx, 700, 1300, 90, "sit", face=1, look=1)


def p2s13(ctx, t, d):
    huddle(ctx, t); rain(ctx, t, 90, 0.3); finish(ctx, t, d)


def p2s14(ctx, t, d):
    huddle(ctx, t, point=ease(prog(t, 0.2, T2.at(14, -1)))); rain(ctx, t, 70, 0.3); finish(ctx, t, d)


BOATS = [(random.Random(k).uniform(80, 1000), random.Random(k + 50).uniform(0, 1)) for k in range(34)]


def horizon_lights(ctx, t, n, approach=0.0, turn=0.0, y=1090):
    for k, (x, ph) in enumerate(BOATS[:int(n)]):
        yy = y + 20 * ph + approach * (60 + 200 * ph)
        xx = x + turn * (300 if x < 540 else -300) * ph * 0 + turn * math.copysign(1, 540 - x) * 120 * ph
        far_light(ctx, xx, yy, 0.7 + 0.3 * math.sin(t * 3 + k), 6 + 6 * approach * ph)


def p2s15(ctx, t, d):
    sky(ctx, t, storm=0.7); sea(ctx, t, 0.5)
    horizon_lights(ctx, t, 34 * ease(prog(t, T2.at(15, 0), T2.at(15, 2))), approach=0.4 * prog(t, T2.at(15, -1), d))
    big_word(ctx, t, "DOZENS.", T2.at(15, 1), y=420, size=170, col=(1, 0.9, 0.6))
    rain(ctx, t, 50, 0.25); finish(ctx, t, d)


def p2s16(ctx, t, d):
    sky(ctx, t, storm=0.7); rock(ctx, 540, 1260); tower(ctx, t, 540, 1280, 560, lit=0)
    sea(ctx, t, 0.5, horizon=1300); horizon_lights(ctx, t, 34, approach=0.5, y=1290)
    end_card(ctx, t, T2, 16, "HOW WOULD YOU", "SAVE THEM?", "COMMENT YOUR PLAN", "PART 3 IS UP NEXT")
    finish(ctx, t, d, fo=0.25)


# ------------------------------------------------------------------ PART 3
def p3s1(ctx, t, d):
    sky(ctx, t, storm=0.7); rock(ctx, 540, 1060); tower(ctx, t, 540, 1080, 620, lit=0); sea(ctx, t, 0.6)
    horizon_lights(ctx, t, 34, approach=0.5 + 0.3 * t / d)
    rain(ctx, t, 60, 0.25); finish(ctx, t, d, fi=0.0)


def p3s2(ctx, t, d):
    rgb(ctx, hexc("#161412")); ctx.paint()
    glow(ctx, 540, 900, 700, (1, 0.6, 0.3), 0.15)
    rgb(ctx, hexc("#3b3f36")); rrect(ctx, 220, 760, 640, 480, 30); ctx.fill()
    rgb(ctx, hexc("#2a2d27")); ctx.arc(400, 1000, 110, 0, 6.283); ctx.fill()
    rgb(ctx, hexc("#e8e2d0")); ctx.arc(700, 900, 70, 0, 6.283); ctx.fill()
    rgb(ctx, (0.8, 0.1, 0.1)); ctx.set_line_width(8); ctx.move_to(700, 900); ctx.line_to(650, 945); ctx.stroke()
    text(ctx, "FUEL", 700, 1010, 40, (0.9, 0.9, 0.85))
    Particles(30, 3, (300, 300, 800, 760), vel=(10, -60), size=(14, 34), col=(0.5, 0.5, 0.5), alpha=0.25).draw(ctx, t)
    r = random.Random(int(t * 6))
    if r.random() < 0.3:
        for k in range(6):
            rgb(ctx, (1, 0.8, 0.3)); ctx.arc(400 + r.uniform(-90, 90), 1000 + r.uniform(-90, 90), 4, 0, 6.283); ctx.fill()
    person(ctx, 900, 1450, 520, "idle", face=-1, lean=0.1)
    finish(ctx, t, d)


def p3s3(ctx, t, d):
    lamp_room(ctx, t, 0.0, fire=ease(prog(t, T3.at(3, 1), T3.at(3, 1) + 1.0)), storm=0.6)
    text(ctx, "300 YEARS OF FIRE", W / 2, 300, 90, (1, 0.8, 0.4), prog(t, T3.at(3, -1), T3.at(3, -1) + 0.4), outline=10)
    finish(ctx, t, d)


def chair(ctx, x, y, s=1.0):
    rgb(ctx, hexc("#6b4a2e")); ctx.set_line_width(12 * s)
    ctx.move_to(x, y); ctx.line_to(x, y - 120 * s); ctx.stroke()
    ctx.move_to(x, y - 50 * s); ctx.line_to(x + 90 * s, y - 50 * s); ctx.line_to(x + 90 * s, y + 20 * s); ctx.stroke()
    ctx.move_to(x, y - 50 * s); ctx.line_to(x, y + 20 * s); ctx.stroke()


def books(ctx, x, y, n=5, s=1.0):
    for k in range(n):
        rgb(ctx, [hexc("#7a3b2e"), hexc("#2e4a6b"), hexc("#5a5a3a")][k % 3])
        ctx.rectangle(x - 55 * s, y - (k + 1) * 26 * s, 110 * s, 22 * s); ctx.fill()


def p3s4(ctx, t, d):
    spiral(ctx, t, t * 300, lit=0.3)
    face = 1 if int(t * 300 / 520) % 2 else -1
    info = person(ctx, 540, 1250, SP, "walk", phase=t * 5, face=face, lean=0.2, arm_f=(1.5, -0.6), arm_b=(1.4, -0.6))
    hx, hy = info["hand"]
    k = sum(t > T3.at(4, j) for j in (1, 2, 3))
    if k <= 1:
        chair(ctx, hx - 40 * face, hy + 30)
    elif k == 2:
        rgb(ctx, hexc("#6b4a2e")); ctx.rectangle(hx - 110, hy - 20, 220, 26); ctx.fill()
    else:
        books(ctx, hx, hy + 20, 6)
    finish(ctx, t, d)


def p3s5(ctx, t, d):
    spiral(ctx, t, t * 260, lit=0.3)
    face = 1 if int(t * 260 / 520) % 2 else -1
    info = person(ctx, 540, 1250, 320, "walk", phase=t * 6, face=face, pal=JUNO, arm_f=(1.5, -0.7))
    books(ctx, info["hand"][0], info["hand"][1] + 20, 7, 0.8)
    finish(ctx, t, d)


def p3s6(ctx, t, d):
    lit = T3.at(6, -1) + 0.4
    rgb(ctx, hexc("#120e0b")); ctx.paint()
    fire = ease(prog(t, lit, lit + 1.0))
    glow(ctx, 540, 1000, 600 + 300 * fire, (1, 0.6, 0.25), 0.15 + 0.5 * fire)
    rgb(ctx, hexc("#5a3b2a")); rrect(ctx, 300, 900, 480, 330, 16); ctx.fill()
    rgb(ctx, hexc("#e9dfc8")); ctx.rectangle(320, 915, 440, 300); ctx.fill()
    text(ctx, "LOGBOOK", 540, 1000, 70, hexc("#3a2a20"))
    text(ctx, "DAY 1 - 1094", 540, 1090, 46, hexc("#3a2a20"))
    for side in (-1, 1):
        rgb(ctx, HOODIE); ctx.set_line_width(100); ctx.set_line_cap(1)
        ctx.move_to(540 + side * 420, H + 60); ctx.line_to(540 + side * 270, 1150); ctx.stroke()
    if fire > 0:
        r = random.Random(int(t * 24))
        for k in range(26):
            rgb(ctx, (1, r.uniform(0.35, 0.85), 0.1), 0.7 * fire)
            ctx.save(); ctx.translate(540 + r.uniform(-200, 200), 900 - r.uniform(0, 280) * fire); ctx.scale(0.5, 1)
            ctx.arc(0, 0, r.uniform(20, 55), 0, 6.283); ctx.restore(); ctx.fill()
    elif t > T3.at(6, -1) - 0.3:
        rgb(ctx, (1, 0.85, 0.3)); ctx.arc(700, 880, 12, 0, 6.283); ctx.fill(); glow(ctx, 700, 880, 80, (1, 0.7, 0.3), 0.8)
    finish(ctx, t, d)


def p3s7(ctx, t, d):
    z = 1 + 0.1 * t / d
    ctx.save(); ctx.translate(540, 500); ctx.scale(z, z); ctx.translate(-540, -500)
    sky(ctx, t, storm=0.6); rock(ctx, 540, 1060)
    blaze = ease(prog(t, 0.0, T3.at(7, 1)))
    tower(ctx, t * 1.4, 540, 1080, 620, lit=0.3 + 0.7 * blaze, beam_len=1500, beam_a=0.55)
    sea(ctx, t, 0.5)
    ctx.restore()
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD); glow(ctx, 540, 400, 900, (1, 0.7, 0.3), 0.25 * blaze); ctx.restore()
    rain(ctx, t, 50, 0.2); finish(ctx, t, d)


def p3s8(ctx, t, d):
    sky(ctx, t, storm=0.5); sea(ctx, t, 0.4)
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    cone(ctx, 1080, 700, math.pi - 0.05 * math.sin(t), 0.06, 1400, (1, 0.9, 0.65), 0.35); ctx.restore()
    horizon_lights(ctx, t, 34, approach=0.5, turn=ease(prog(t, T3.at(8, 1), d)))
    finish(ctx, t, d)


def p3s9(ctx, t, d):
    lamp_room(ctx, t, 0.0, fire=1.0, storm=0.3)
    toss = math.sin(t * 2.5)
    info = person(ctx, 380, 1300, SP, "idle", face=1, lean=0.15 * toss, arm_f=(1.3 + 0.6 * max(0, toss), -0.3))
    if toss < 0.2:
        books(ctx, info["hand"][0] + 30, info["hand"][1] + 20, 2)
    person(ctx, 160, 1300, 300, "idle", face=1, pal=JUNO, arm_f=(1.3, -0.4))
    books(ctx, 210, 1110, 5, 0.7)
    cat(ctx, 880, 1300, 110, "sit", face=-1, tail=math.sin(t * 2))
    finish(ctx, t, d)


DAWN_BOATS = [(80 + k * 75 + (k * 37) % 40, 1210 + (k * 53) % 140, 0.5 + ((k * 13) % 7) / 10) for k in range(13)]


def p3s10(ctx, t, d):
    dawn = ease(prog(t, 0, T3.at(10, 1)))
    sky(ctx, t, storm=1 - dawn, dawn=dawn); sea(ctx, t, 0.1, dawn=dawn)
    rock(ctx, 900, 1060, 400, 200); tower(ctx, t, 900, 1080, 560, lit=0.4, beam=False)
    for k, (x, y, s) in enumerate(DAWN_BOATS):
        if t > T3.at(10, -1) - 0.5 + k * 0.08:
            sailboat(ctx, x, y + 6 * math.sin(t + k), 0.25 * s, tip=0.05 * math.sin(t + k))
    finish(ctx, t, d)


CROWD = [(60 + k * 62, 1300 + (k % 3) * 25, 220 + (k * 37) % 120,
          ((0.3 + (k * 0.13) % 0.6, 0.3 + (k * 0.29) % 0.5, 0.35 + (k * 0.17) % 0.5),) * 2 + ((0.2, 0.2, 0.25), (0.15, 0.15, 0.2)))
         for k in range(16)]


def p3s11(ctx, t, d):
    sky(ctx, t, dawn=1.0); sea(ctx, t, 0.1, dawn=1.0)
    rock(ctx, 540, 1250, 1400, 500, hexc("#3a3532"))
    for k, (x, y, s, pal) in enumerate(CROWD):
        if t > T3.at(11, min(k // 4, 3)):
            wave = math.sin(t * 4 + k) if k % 3 == 0 else 0
            person(ctx, x, y, s, "idle", face=1 if k % 2 else -1, pal=pal, arm_f=(2.4 + 0.3 * wave, 0.2) if k % 3 == 0 else None)
    big_word(ctx, t, "140 STRANGERS", T3.at(11, -1), y=380, size=130, col=(1, 1, 1))
    finish(ctx, t, d)


def p3s12(ctx, t, d):
    sky(ctx, t, dawn=1.0); sea(ctx, t, 0.1, dawn=1.0)
    rock(ctx, 540, 1250, 1400, 500, hexc("#3a3532"))
    run_p = prog(t, T3.at(12, 1), d)
    person(ctx, lerp(300, 1000, run_p), 1380, 300, "run" if run_p > 0 else "idle", phase=t * 14, face=1, pal=JUNO,
           head_turn=1.0 if run_p == 0 else 0)
    if t < T3.at(12, 1):
        big_word(ctx, t, "!", T3.at(12, 0) + 0.3, y=900, size=260, col=(1, 0.85, 0.3))
    finish(ctx, t, d)


def p3s13(ctx, t, d):
    sky(ctx, t, dawn=1.0); sea(ctx, t, 0.1, dawn=1.0)
    sailboat(ctx, 860, 1250, 0.6)
    rock(ctx, 540, 1300, 1400, 500, hexc("#3a3532"))
    m = ease(prog(t, 0.0, T3.at(13, 1)))
    hug = prog(t, T3.at(13, -1), T3.at(13, -1) + 0.6)
    dx = lerp(860, 600, m)
    person(ctx, dx, 1420, 480, "walk" if 0 < m < 1 else "idle", phase=t * 5, face=-1, pal=DAD,
           arm_f=(1.4 * hug, 0.6 * hug) if hug else None, crouch=0.25 * hug)
    jx = lerp(150, dx - 120, ease(prog(t, 0.0, T3.at(13, -1))))
    person(ctx, jx, 1420, 320, "run" if hug == 0 else "idle", phase=t * 13, face=1, pal=JUNO,
           arm_f=(2.0, 0.2) if hug else None)
    finish(ctx, t, d)


def p3s14(ctx, t, d):
    sky(ctx, t, dawn=1.0, horizon=1350); sea(ctx, t, 0.05, horizon=1350, dawn=1.0)
    rgb(ctx, hexc("#2a2c31")); ctx.rectangle(0, 1180, W, 40); ctx.fill()
    ctx.set_line_width(8)
    for x in range(0, W, 70):
        ctx.move_to(x, 1180); ctx.line_to(x, 1010); ctx.stroke()
    ctx.move_to(0, 1010); ctx.line_to(W, 1010); ctx.stroke()
    person(ctx, 460, 1180, 560, "idle", back_view=True, breathe=math.sin(t * 1.5))
    cat(ctx, 720, 1180, 150, "sit", face=1, tail=math.sin(t * 2), look=0.5)
    finish(ctx, t, d, v=0.5)


def p3s15(ctx, t, d):
    p3s14(ctx, t + 9, d + 9)
    rgb(ctx, (0, 0, 0), 0.3); ctx.paint()
    end_card(ctx, t, T3, 15, "THE END", "", "WHAT WOULD YOU BURN?", "NEW STORY TOMORROW")
    fade(ctx, t, d, 0.1, 0.3)


P1 = [p1s1, p1s2, p1s3, p1s4, p1s5, p1s6, p1s7, p1s8, p1s9, p1s10, p1s11, p1s12, p1s13, p1s14, p1s15]
P2 = [p2s1, p2s2, p2s3, p2s4, p2s5, p2s6, p2s7, p2s8, p2s9, p2s10, p2s11, p2s12, p2s13, p2s14, p2s15, p2s16]
P3 = [p3s1, p3s2, p3s3, p3s4, p3s5, p3s6, p3s7, p3s8, p3s9, p3s10, p3s11, p3s12, p3s13, p3s14, p3s15]


# ------------------------------------------------------------------ sound
def surf(d, storm, seed):
    t = np.arange(int(d * SR)) / SR
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * (0.12 + 0.1 * storm) * t + seed)
    return band_noise(d, 60, 900 + 1500 * storm, seed) * swell * (0.15 + 0.25 * storm)


def wind(d, amt, seed):
    t = np.arange(int(d * SR)) / SR
    return band_noise(d, 200, 1500, seed + 50) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.21 * t + seed)) * 0.18 * amt


def rain_s(d, amt, seed):
    return band_noise(d, 1500, 9000, seed + 90) * 0.12 * amt


def thunder(d, times, seed):
    return env_at(d, times, 2.5) * (band_noise(d, 20, 220, seed + 7) * 0.9 + tone(d, 38) * 0.3)


def meow(d, t0):
    x = silence(d); i = int(t0 * SR); n = int(0.6 * SR)
    if i + n > len(x):
        return x
    tt = np.arange(n) / SR
    f = 700 + 250 * np.sin(np.pi * tt / 0.6) + 15 * np.sin(2 * np.pi * 7 * tt)
    v = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.6) ** 0.7
    x[i:i + n] = (v + 0.3 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR) * np.sin(np.pi * tt / 0.6)) * 0.12
    return x


def beeps(d, spans, f=880):
    x = silence(d)
    for a, b in spans:
        i, j = int(a * SR), int(b * SR)
        if i < len(x):
            seg = np.sin(2 * np.pi * f * np.arange(j - i) / SR) * 0.18
            x[i:min(j, len(x))] += seg[: min(j, len(x)) - i]
    return x


def crackle(d, amt, seed):
    rng = np.random.default_rng(seed)
    return (env_at(d, list(rng.uniform(0, d, int(d * 25 * amt))), 0.015) * band_noise(d, 1500, 8000, seed) * 0.4
            + band_noise(d, 60, 400, seed + 1) * 0.12 * amt)


def gulls(d, seed):
    x = silence(d); rng = np.random.default_rng(seed)
    for t0 in rng.uniform(0.3, max(0.4, d - 1), 4):
        i = int(t0 * SR); n = int(0.35 * SR)
        if i + n > len(x):
            continue
        tt = np.arange(n) / SR
        f = 1700 - 900 * tt / 0.35
        x[i:i + n] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.35) * 0.05
    return x


def sfx1(i, d):
    storm = {1: 0, 2: 0.2, 3: 0.1, 4: 0, 5: 0, 6: 0.1, 7: 0.5}.get(i, 0.8)
    x = surf(d, storm, i) + wind(d, storm, i) + rain_s(d, max(0, storm - 0.3), i)
    if i == 3:
        x += meow(d, 0.6)
    if i == 4:
        x += env_at(d, [k * math.pi / 6 for k in range(int(T1.at(4, 1) * 6 / math.pi))], 0.05) * band_noise(d, 200, 2000, 4) * 0.5
        x += env_at(d, [T1.at(4, 1)], 1.0) * tone(d, 220) * 0.1
    if i in (4, 5):
        s0 = T1.at(4, 2) if i == 4 else T1.at(5, 1)
        x += band_noise(d, 3000, 8000, 5) * 0.05 * (np.arange(len(x)) / SR > s0)
    if i == 9:
        x += beeps(d, [(T1.at(9, k), T1.at(9, k) + (0.25 if MORSE[k] == 0 else 0.7)) for k in range(9)])
    if i == 10:
        x += env_at(d, [T1.at(10, k) for k in range(3)], 0.6) * tone(d, 55) * 0.6
    if i == 11:
        x += env_at(d, list(np.arange(T1.at(11, 1), d, 0.22)), 0.05) * band_noise(d, 1000, 4000, 11) * 0.3
    if i == 13:
        x += env_at(d, [T1.at(13, k) for k in range(3)], 0.8) * (tone(d, 49) + band_noise(d, 30, 200, 13) * 0.4) * 0.7
    if i == 14:
        x += thunder(d, [0.2, T1.at(14, 1), T1.at(14, 1) + 1.8], 14)
    return fades(x * 0.6, 0.03, 0.1)


def sfx2(i, d):
    storm = {13: 0.6, 14: 0.5, 15: 0.5, 16: 0.5}.get(i, 1.0)
    x = surf(d, storm, i + 20) + wind(d, storm, i + 20) + rain_s(d, storm, i + 20)
    t = np.arange(len(x)) / SR
    if i == 3:
        x += meow(d, 1.1) * 1.4
    if i in (4, 7, 9):
        x += env_at(d, list(np.arange(0.3, d, 2 * math.pi / 3.2)), 0.25) * band_noise(d, 300, 3000, i) * 0.35
    if i == 5:
        x += thunder(d, [0.0, T2.at(5, 1) - 0.1], 5)
    if i == 8:
        x *= 0.6
    if i == 10:
        x += tone(d, 120, "saw") * 0.06 * (t > T2.at(10, 1))
    if i == 11:
        x += env_at(d, [T2.at(11, 0) + 0.2], 1.0) * (tone(d, 60) * 0.5 + band_noise(d, 50, 400, 11) * 0.3)
    if i == 12:
        x += thunder(d, [0.6, T2.at(12, -1)], 12)
    return fades(x * 0.6, 0.03, 0.1)


def sfx3(i, d):
    storm = {1: 0.6, 2: 0.3, 3: 0.5, 4: 0.3, 5: 0.3, 6: 0.3, 7: 0.6, 8: 0.5, 9: 0.3}.get(i, 0.0)
    x = surf(d, storm, i + 40) + wind(d, storm, i + 40) + rain_s(d, max(0, storm - 0.3), i + 40)
    t = np.arange(len(x)) / SR
    if i == 2:
        x += env_at(d, list(np.arange(0.2, d, 0.9)), 0.4) * (tone(d, 45) * 0.4 + band_noise(d, 80, 600, 2) * 0.3) * np.clip(1 - t / d, 0, 1)
    if i in (3, 6, 7, 9):
        start = {3: T3.at(3, 1), 6: T3.at(6, -1) + 0.4, 7: 0, 9: 0}[i]
        x += crackle(d, 1.0, i) * (t > start)
    if i in (4, 5):
        x += env_at(d, list(np.arange(0.2, d, math.pi / 5)), 0.05) * band_noise(d, 200, 2000, i) * 0.45
    if i == 6:
        x += env_at(d, [T3.at(6, -1) + 0.3], 0.3) * band_noise(d, 2000, 7000, 66) * 0.5
    if i == 7:
        x += env_at(d, [0.1], 2.5) * (tone(d, 98) + tone(d, 147) * 0.6) * 0.15
    if i >= 10 and i != 13:
        x += surf(d, 0.05, i + 60) + gulls(d, i)
    if i == 11:
        x += band_noise(d, 200, 1200, 111) * 0.08 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t))
    if i == 13:
        x += surf(d, 0.05, 73) + gulls(d, 13)
    return fades(x * 0.6, 0.03, 0.1)


def music1(durs):
    return piano_score(sum(durs), sum(durs[:7]))


def music2(durs):
    return piano_score(sum(durs), 0.0)


def music3(durs):
    blaze = sum(durs[:6])
    total = sum(durs)
    tense = piano_score(blaze, 0.0)
    warm = piano_score(total - blaze, total + 100, bpm=72, seed=3)
    return np.concatenate([tense, warm])[: int(total * SR)]


PARTS = {1: ("23_lighthouse_1", P1, sfx1, music1), 2: ("24_lighthouse_2", P2, sfx2, music2), 3: ("25_lighthouse_3", P3, sfx3, music3)}

if __name__ == "__main__":
    run(PARTS, {1: T1, 2: T2, 3: T3})
