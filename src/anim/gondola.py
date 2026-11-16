"""The Last Gondola - survival/horror starring Kai, Parts 1-3 (stories/32-34).

    python src/anim/gondola.py <part 1|2|3> [scene numbers]

Sets: stuck gondola cabin (outside on the cable / inside), the window with the man on the cable,
the roof hatch, surf shop, airport, base station, dawn rescue. Every human is a rig Character.
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
import lights as L

T1, T2, T3 = Timing("32_gondola_1"), Timing("33_gondola_2"), Timing("34_gondola_3")
SIDS = {1: "32_gondola_1", 2: "33_gondola_2", 3: "34_gondola_3"}

RUTH = Character("Ruth", age="elder", skin="#efc7aa", hair="#cfcfcf", hair_style="cap", top="#2f7f86",
                 pants="#3b3f4a", footwear="shoes", shoes="#4a3a2a", glasses=True, face_shape="oval", seed=3.0)
MAN = Character("Man", skin="#cdd5dc", hair="#1d1d22", hair_style="cap", top="#b3202a", pants="#25252c",
                footwear="shoes", shoes="#151518", glasses=True, face_shape="oval", seed=9.0)
DEE = Character("Dee", skin="#e9b892", hair="#5a3a22", hair_style="ponytail", top="#c2242c", pants="#2b2b33",
                footwear="shoes", shoes="#222226", face_shape="oval", seed=5.0)

CABIN = hexc("#e2a72a")
STORM = Particles(280, 6, (-200, -200, W + 200, H + 200), vel=(-380, 300), size=(1.5, 4.5), col=(0.95, 0.97, 1.0), alpha=0.8)
SNOWF = Particles(140, 5, (0, 0, W, H), vel=(-30, 110), size=(1.5, 4), col=(0.95, 0.97, 1.0), alpha=0.75)
COLD = (0.65, 0.78, 1.0)


def talk_fn(part, i, k0=0, k1=99):
    """Lip-sync from the narration for a character's spoken line (phrases k0..k1 of scene i)."""
    tm = {1: T1, 2: T2, 3: T3}[part]
    f = lipsync(ROOT / "out" / SIDS[part] / f"scene_{i:02d}.wav")
    a, b = tm.at(i, k0), (tm.at(i, k1 + 1) if k1 + 1 < len(tm.seg.get(i, [])) else 999)
    return lambda t: f(t) if a <= t < b else 0.0


def close(ch, ctx, cx, hy, r, t, **kw):
    """Draw a character so the head is centred at (cx, hy) with radius r."""
    s = r / 0.13
    mode = kw.pop("mode", "idle")
    y = hy + (0.718 if mode == "sit" else 0.888) * s
    return ch.draw(ctx, cx, y, s, t, mode=mode, **kw)


# ------------------------------------------------------------------ sets
def sky(ctx, t, dawn=0.0, y1=H + 300):
    a = [(0, (0.03, 0.04, 0.08)), (0.6, (0.10, 0.13, 0.20)), (1, (0.22, 0.26, 0.34))]
    b = [(0, (0.45, 0.50, 0.62)), (0.6, (0.80, 0.70, 0.72)), (1, (0.98, 0.82, 0.66))]
    vgrad(ctx, -300, y1, [(p, tuple(lerp(c1[i], c2[i], dawn) for i in range(3))) for (p, c1), (_, c2) in zip(a, b)])


def mountains(ctx, dawn=0.0, y=1500):
    for k, (col, base, amp, seed) in enumerate((("#2a3242", y - 300, 380, 1), ("#1a202c", y - 80, 300, 2))):
        c = hexc(col); c = tuple(lerp(c[i], (0.55, 0.55, 0.62)[i], dawn * (0.6 - 0.2 * k)) for i in range(3))
        r = random.Random(seed); rgb(ctx, c); ctx.move_to(-100, H + 300); x = -100
        while x < W + 200:
            ctx.line_to(x, base - r.uniform(0.3, 1) * amp); x += r.uniform(140, 260)
        ctx.line_to(W + 200, H + 300); ctx.close_path(); ctx.fill()
    rgb(ctx, (0.85, 0.9, 1.0), 0.75 + 0.2 * dawn)
    ctx.move_to(-100, y + 60); ctx.curve_to(300, y - 30, 700, y + 80, W + 100, y); ctx.line_to(W + 100, H + 300); ctx.line_to(-100, H + 300); ctx.fill()
    for k in range(9):                                                     # pines
        r = random.Random(k + 30); px, py, ph = r.uniform(0, W), y + r.uniform(20, 200), r.uniform(90, 170)
        rgb(ctx, hexc("#0e1a18")); ctx.move_to(px, py - ph); ctx.line_to(px - ph * 0.35, py); ctx.line_to(px + ph * 0.35, py); ctx.fill()


def tower(ctx, x, top, base, w=70, col="#3a3f48"):
    rgb(ctx, hexc(col)); ctx.set_line_width(10)
    ctx.move_to(x - w, base); ctx.line_to(x - 18, top); ctx.move_to(x + w, base); ctx.line_to(x + 18, top); ctx.stroke()
    ctx.set_line_width(5)
    n = 8
    for k in range(n):
        y0, y1 = base - (base - top) * k / n, base - (base - top) * (k + 1) / n
        xa, xb = lerp(w, 18, k / n), lerp(w, 18, (k + 1) / n)
        ctx.move_to(x - xa, y0); ctx.line_to(x + xb, y1); ctx.move_to(x + xa, y0); ctx.line_to(x - xb, y1); ctx.stroke()
    rgb(ctx, hexc(col)); ctx.rectangle(x - 120, top - 14, 240, 22); ctx.fill()
    for sx in (-100, 100):
        ctx.arc(x + sx, top - 18, 16, 0, 6.283); ctx.fill()


def cable(ctx, x0, y0, x1, y1, sag=0.0):
    rgb(ctx, (0.05, 0.05, 0.07)); ctx.set_line_width(7)
    ctx.move_to(x0, y0); ctx.curve_to(lerp(x0, x1, 0.33), lerp(y0, y1, 0.33) + sag, lerp(x0, x1, 0.66), lerp(y0, y1, 0.66) + sag, x1, y1); ctx.stroke()


def cabin_ext(ctx, t, x, cy, s=1.0, swing=0.0, lit=0.0, roof_snow=0.6, shape_on_roof=0.0, people=True, dawn=0.0):
    """Gondola cabin hanging at grip point (x, cy); s = scale (1 = 420 px wide)."""
    ctx.save(); ctx.translate(x, cy); ctx.rotate(swing); ctx.scale(s, s)
    rgb(ctx, hexc("#2a2d33")); ctx.rectangle(-12, 0, 24, 170); ctx.fill()               # hanger arm
    rgb(ctx, hexc("#2a2d33")); rrect(ctx, -60, -26, 120, 40, 12); ctx.fill()             # grip
    body_c = tuple(lerp(CABIN[i], (0.3, 0.3, 0.35)[i], 0.35 * (1 - dawn)) for i in range(3))
    rgb(ctx, body_c); rrect(ctx, -210, 160, 420, 420, 70); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.18); rrect(ctx, 30, 160, 180, 420, 70); ctx.fill()
    for k, wx in enumerate((-180, 10)):                                                 # windows
        rgb(ctx, (1.0, 0.85, 0.55) if lit > 0.5 else (0.08, 0.10, 0.15)); rrect(ctx, wx, 210, 170, 190, 26); ctx.fill()
        if lit > 0:
            glow(ctx, wx + 85, 305, 200, (1, 0.8, 0.5), 0.3 * lit)
        rgb(ctx, (0.85, 0.9, 1.0), 0.35); rrect(ctx, wx, 375, 170, 25, 10); ctx.fill()  # frost on the sill
    if people and lit < 0.5:
        for hx_ in (-95, 95):
            rgb(ctx, (0.02, 0.02, 0.03), 0.8); ctx.arc(hx_, 330, 30, 0, 6.283); ctx.fill()
    rgb(ctx, (0.92, 0.95, 1.0), 0.9); ctx.save(); ctx.translate(0, 170); ctx.scale(1, 0.25)       # roof snow
    ctx.arc(0, 0, 200 * roof_snow + 20, math.pi, 2 * math.pi); ctx.restore(); ctx.fill()
    if shape_on_roof > 0:                                                               # something crouched on the roof
        rgb(ctx, (0.01, 0.01, 0.02), shape_on_roof)
        ctx.save(); ctx.translate(40, 130); ctx.scale(1.3, 1); ctx.arc(0, 0, 55, math.pi, 2 * math.pi); ctx.restore(); ctx.fill()
        ctx.arc(95, 95, 26, 0, 6.283); ctx.fill()
    ctx.restore()


def interior(ctx, t, storm=1.0, dawn=0.0, frost=0.3, dark=1.0, swing=0.0):
    """Inside the cabin looking across: two big windows over two benches."""
    ctx.save(); ctx.translate(540, 300); ctx.rotate(swing * 0.5); ctx.translate(-540, -300)
    rgb(ctx, hexc("#3b3a3e")); ctx.rectangle(-200, -200, W + 400, H + 400); ctx.fill()
    for wx in (60, 560):
        ctx.save(); rrect(ctx, wx, 300, 460, 680, 50); ctx.clip()
        sky(ctx, t, dawn); mountains(ctx, dawn, 1100)
        if storm > 0:
            ctx.save(); ctx.translate(-wx * 0.2, 0); STORM.draw(ctx, t); ctx.restore()
            rgb(ctx, (0.8, 0.85, 0.95), 0.18 * storm); ctx.paint()
        g = cairo.RadialGradient(wx + 230, 640, 120, wx + 230, 640, 420)
        g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0.9, 0.95, 1, 0.8 * frost)
        ctx.set_source(g); ctx.paint()
        ctx.restore()
        rgb(ctx, hexc("#26262a")); ctx.set_line_width(26); rrect(ctx, wx, 300, 460, 680, 50); ctx.stroke()
    rgb(ctx, hexc("#2c2b30")); ctx.rectangle(-200, 1000, W + 400, 140); ctx.fill()           # wall below windows
    rgb(ctx, hexc("#56545c")); ctx.rectangle(-200, 1560, W + 400, H); ctx.fill()               # metal floor
    rgb(ctx, (0, 0, 0), 0.25); ctx.set_line_width(4)
    for k in range(12):
        ctx.move_to(k * 110 - 60, 1560); ctx.line_to(k * 160 - 400, H + 50); ctx.stroke()
    rgb(ctx, (0.85, 0.92, 1.0), 0.25 * frost); ctx.rectangle(-200, 1560, W + 400, 30); ctx.fill()
    for bx in (40, 600):                                                                       # benches
        rgb(ctx, hexc("#1f3a5a")); rrect(ctx, bx, 1290, 440, 90, 20); ctx.fill()
        rgb(ctx, hexc("#16293f")); ctx.rectangle(bx + 20, 1380, 400, 180); ctx.fill()
    ctx.restore()
    if dark > 0:
        rgb(ctx, (0.02, 0.03, 0.08), 0.35 * dark); ctx.paint()


def window_close(ctx, t, storm=1.0, frost=0.4, dawn=0.0, inner=None, crack=0.0, crack_at=(540, 820)):
    """Fills the frame with one cabin window; inner(ctx) draws what's outside (before glass effects)."""
    rgb(ctx, hexc("#2a292e")); ctx.paint()
    ctx.save(); rrect(ctx, 90, 260, 900, 1240, 90); ctx.clip()
    sky(ctx, t, dawn); mountains(ctx, dawn, 1500)
    cable(ctx, -100, 700, W + 100, 640, 30)
    if inner:
        inner(ctx)
    STORM.draw(ctx, t)
    rgb(ctx, (0.8, 0.85, 0.95), 0.12 * storm); ctx.paint()
    g = cairo.RadialGradient(540, 880, 300, 540, 880, 760)
    g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0.9, 0.95, 1, 0.9 * frost)
    ctx.set_source(g); ctx.paint()
    if crack > 0:
        r = random.Random(4); rgb(ctx, (1, 1, 1), 0.9); ctx.set_line_width(3)
        cx, cy = crack_at
        for k in range(5):
            ctx.move_to(cx, cy); x, y = cx, cy; a = k * 1.25 + 0.3
            for j in range(int(6 * crack)):
                x += math.cos(a) * 70; y += math.sin(a) * 70; a += r.uniform(-0.5, 0.5); ctx.line_to(x, y)
            ctx.stroke()
    ctx.restore()
    rgb(ctx, hexc("#1e1d22")); ctx.set_line_width(60); rrect(ctx, 90, 260, 900, 1240, 90); ctx.stroke()
    rgb(ctx, hexc("#3a3940")); ctx.set_line_width(12); rrect(ctx, 70, 240, 940, 1280, 100); ctx.stroke()


def breath(ctx, t, x, y, d=1, rate=0.6, a=0.5, seed=0):
    """Puff of breath fog from a mouth, every 1/rate seconds."""
    ph = (t * rate + seed) % 1
    if ph < 0.6:
        p = ph / 0.6
        g = cairo.RadialGradient(x + d * 70 * p, y - 10 * p, 0, x + d * 70 * p, y - 10 * p, 30 + 70 * p)
        g.add_color_stop_rgba(0, 0.95, 0.97, 1, a * (1 - p)); g.add_color_stop_rgba(1, 0.95, 0.97, 1, 0)
        ctx.set_source(g); ctx.arc(x + d * 70 * p, y - 10 * p, 30 + 70 * p, 0, 6.283); ctx.fill()


def knock_fx(ctx, t, x, y, times, size=1.0):
    for k in times:
        p = (t - k) / 0.35
        if 0 <= p < 1:
            rgb(ctx, (1, 1, 1), 0.7 * (1 - p)); ctx.set_line_width(5)
            ctx.arc(x, y, (30 + 120 * p) * size, 0, 6.283); ctx.stroke()


def glove(ctx, x, y, s=1.0, col=(0.7, 0.12, 0.15)):
    rgb(ctx, col); ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -60, -70, 120, 140, 45); ctx.fill()
    for k in range(4):
        rrect(ctx, -58 + k * 30, -110, 26, 70, 13); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.2); ctx.rectangle(-60, 40, 120, 30); ctx.fill()
    ctx.restore()


def man_outside(ctx, t, x=540, hy=760, r=150, expr="happy", knock=None, alpha=1.0):
    """The man on the cable, framed by the window. Frozen in time: he never blinks or breathes."""
    close(MAN, ctx, x, hy, r, 0.31, face=0, expr=expr, look=(0, 0), breathe=0.0, arm_f=None)


def flake_shadow(ctx):
    rgb(ctx, (0, 0, 0), 0.25); ctx.paint()


def surf_shop(ctx, t):
    vgrad(ctx, -300, 1500, [(0, hexc("#2c8c9a")), (1, hexc("#1f6f7c"))])
    for k, (bx, col) in enumerate(((140, "#f4d35e"), (330, "#ee6c4d"), (520, "#f7f7f2"), (710, "#3d5a80"), (900, "#98c1d9"))):
        rgb(ctx, hexc(col)); ctx.save(); ctx.translate(bx, 760); ctx.scale(0.28, 1); ctx.arc(0, 0, 330, 0, 6.283); ctx.restore(); ctx.fill()
        rgb(ctx, (0, 0, 0), 0.15); ctx.rectangle(bx - 3, 440, 6, 640); ctx.fill()
    glow(ctx, 540, 300, 600, (1, 0.9, 0.6), 0.25)
    vgrad(ctx, 1500, H + 300, [(0, hexc("#c9a26b")), (1, hexc("#8a6a42"))])
    rgb(ctx, hexc("#7a4e2c")); ctx.rectangle(-100, 1480, W + 200, 50); ctx.fill()


def airport(ctx, t):
    vgrad(ctx, -300, 1300, [(0, hexc("#c9ced6")), (1, hexc("#9aa2ad"))])
    for k in range(5):
        rgb(ctx, (1, 1, 1), 0.5); ctx.rectangle(k * 240 - 40, 200, 160, 700); ctx.fill()
    vgrad(ctx, 1300, H + 300, [(0, hexc("#6a707a")), (1, hexc("#3a3e45"))])
    rgb(ctx, hexc("#2b2e33")); rrect(ctx, -100, 1380, W + 200, 160, 30); ctx.fill()             # empty belt
    rgb(ctx, hexc("#45494f")); ctx.set_line_width(4)
    for k in range(14):
        x = (k * 90 - t * 60) % (W + 200) - 100
        ctx.move_to(x, 1390); ctx.line_to(x, 1530); ctx.stroke()
    text(ctx, "BAGGAGE CLAIM 4", 540, 140, 70, (0.15, 0.17, 0.2))


def base_station(ctx, t, dawn=0.0):
    sky(ctx, t, 0.35 + dawn); mountains(ctx, 0.35 + dawn, 1350)
    cable(ctx, 200, 1100, W + 300, -200, 20)
    tower(ctx, 900, 380, 1400)


def hatch(ctx, t, turn=0.0, dents=(), shake=0.0):
    """Looking up at the cabin ceiling: roof hatch with a turning handle."""
    vgrad(ctx, -300, H + 300, [(0, hexc("#2a292e")), (1, hexc("#45444b"))])
    rgb(ctx, (0, 0, 0), 0.3); ctx.set_line_width(5)
    for k in range(8):
        ctx.move_to(-100, 200 + k * 230); ctx.line_to(W + 100, 200 + k * 230); ctx.stroke()
    for (dx, dy, a) in dents:
        g = cairo.RadialGradient(dx, dy, 0, dx, dy, 120)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.5 * a); g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g); ctx.arc(dx, dy, 120, 0, 6.283); ctx.fill()
    ctx.save(); ctx.translate(540 + wobble(t, 3, 30) * 10 * shake, 760)
    rgb(ctx, hexc("#5d5c64")); rrect(ctx, -300, -300, 600, 600, 30); ctx.fill()
    rgb(ctx, hexc("#2a292f")); ctx.set_line_width(12); rrect(ctx, -300, -300, 600, 600, 30); ctx.stroke()
    rgb(ctx, hexc("#2a292f")); ctx.arc(0, 0, 60, 0, 6.283); ctx.fill()
    ctx.rotate(turn); rgb(ctx, hexc("#9a9aa3")); rrect(ctx, -30, -30, 260, 60, 30); ctx.fill()
    rgb(ctx, hexc("#c4c4cc")); ctx.arc(0, 0, 40, 0, 6.283); ctx.fill()
    ctx.restore()


def radio(ctx, t, on=1.0):
    rgb(ctx, hexc("#1c1c20")); rrect(ctx, 300, 600, 480, 900, 60); ctx.fill()
    rgb(ctx, hexc("#1c1c20")); ctx.rectangle(640, 300, 50, 320); ctx.fill()
    rgb(ctx, hexc("#2e3036")); rrect(ctx, 350, 680, 380, 300, 30); ctx.fill()
    for k in range(7):
        rgb(ctx, (0, 0, 0), 0.6); rrect(ctx, 380, 1030 + k * 55, 320, 22, 11); ctx.fill()
    led = (1, 0.25, 0.2) if on > 0.5 and int(t * 6) % 2 else (0.2, 0.05, 0.05)
    glow(ctx, 380, 640, 60, led, 0.6 * on); rgb(ctx, led); ctx.arc(380, 640, 14, 0, 6.283); ctx.fill()
    r = random.Random(int(t * 15))
    rgb(ctx, (0.4, 0.9, 0.6), 0.8 * on); ctx.set_line_width(4); ctx.move_to(370, 830)
    for k in range(30):
        ctx.line_to(370 + k * 11.5, 830 + r.uniform(-90, 90) * on)
    ctx.stroke()


def thermometer(ctx, t, temp):
    rgb(ctx, hexc("#e8e8ec")); rrect(ctx, 380, 300, 320, 1200, 160); ctx.fill()
    rgb(ctx, hexc("#d9dde3")); rrect(ctx, 500, 380, 80, 960, 40); ctx.fill()
    lvl = 1340 - 900 * clamp(temp)
    rgb(ctx, (0.85, 0.15, 0.15)); rrect(ctx, 515, lvl, 50, 1340 - lvl, 25); ctx.fill(); ctx.arc(540, 1380, 80, 0, 6.283); ctx.fill()
    for k in range(9):
        rgb(ctx, (0.2, 0.2, 0.25)); ctx.rectangle(600, 400 + k * 110, 50, 6); ctx.fill()


def clock(ctx, t, h0, h1, p):
    rgb(ctx, hexc("#e9e6dd")); ctx.arc(540, 900, 380, 0, 6.283); ctx.fill()
    rgb(ctx, hexc("#2a2a30")); ctx.set_line_width(26); ctx.arc(540, 900, 380, 0, 6.283); ctx.stroke()
    for k in range(12):
        a = k * math.pi / 6; rgb(ctx, hexc("#2a2a30")); ctx.set_line_width(12)
        ctx.move_to(540 + math.cos(a) * 320, 900 + math.sin(a) * 320); ctx.line_to(540 + math.cos(a) * 350, 900 + math.sin(a) * 350); ctx.stroke()
    hrs = lerp(h0, h1, p)
    for ang, ln, wdt in ((hrs / 12 * 2 * math.pi, 200, 22), (hrs * 2 * math.pi, 290, 12)):
        ctx.move_to(540, 900); ctx.line_to(540 + math.sin(ang) * ln, 900 - math.cos(ang) * ln); ctx.set_line_width(wdt); ctx.stroke()


def polaroid(ctx, t, a=1.0):
    ctx.save(); ctx.translate(540, 880); ctx.rotate(-0.06)
    rgb(ctx, (0.95, 0.93, 0.86), a); ctx.rectangle(-330, -400, 660, 800); ctx.fill()
    ctx.save(); ctx.rectangle(-290, -360, 580, 580); ctx.clip()
    vgrad(ctx, -360, 220, [(0, (0.55, 0.65, 0.75)), (1, (0.85, 0.88, 0.92))], x=-290, w=580)
    close(MAN, ctx, 0, -80, 150, 0.31, face=0, expr="happy", breathe=0.0)
    rgb(ctx, (0.9, 0.75, 0.5), 0.25); ctx.paint()
    ctx.restore()
    text(ctx, "MIKE - SKI PATROL - 2006", 0, 300, 44, (0.2, 0.2, 0.25))
    ctx.restore()


def beach_bubble(ctx, t, p):
    if p <= 0:
        return
    ctx.save(); ctx.translate(560, 560); ctx.scale(ease_out(p), ease_out(p))
    rgb(ctx, (1, 1, 1), 0.95); ctx.arc(0, 0, 330, 0, 6.283); ctx.fill()
    ctx.arc(-190, 330, 40, 0, 6.283); ctx.fill(); ctx.arc(-240, 420, 22, 0, 6.283); ctx.fill()
    ctx.save(); ctx.arc(0, 0, 305, 0, 6.283); ctx.clip()
    vgrad(ctx, -310, 310, [(0, hexc("#7fd1e8")), (0.55, hexc("#bfeaf5")), (0.56, hexc("#2b8fb3")), (0.75, hexc("#2b8fb3")), (0.76, hexc("#f2d49b")), (1, hexc("#e8c47f"))], x=-310, w=620)
    rgb(ctx, (1, 0.9, 0.4)); ctx.arc(170, -170, 60, 0, 6.283); ctx.fill()
    gx, gy = -60 + 140 * ((t * 0.4) % 1), -40 - 40 * math.sin(t * 2)                       # seagull with a sandwich
    rgb(ctx, (1, 1, 1)); ctx.save(); ctx.translate(gx, gy); ctx.scale(1, 0.6); ctx.arc(0, 0, 40, 0, 6.283); ctx.restore(); ctx.fill()
    rgb(ctx, (0.3, 0.3, 0.35)); ctx.set_line_width(8); w_ = math.sin(t * 12) * 30
    ctx.move_to(gx - 70, gy - w_); ctx.line_to(gx, gy - 10); ctx.line_to(gx + 70, gy - w_); ctx.stroke()
    rgb(ctx, hexc("#e0b26a")); ctx.rectangle(gx + 30, gy + 10, 50, 26); ctx.fill()
    ctx.restore(); ctx.restore()


def snowcat(ctx, t, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    glow(ctx, 120, -40, 260, (1, 0.9, 0.6), 0.35)
    rgb(ctx, hexc("#c43a2a")); rrect(ctx, -150, -150, 300, 120, 20); ctx.fill()
    rgb(ctx, hexc("#1a1a1e")); rrect(ctx, -180, -40, 360, 60, 30); ctx.fill()
    rgb(ctx, (1, 0.95, 0.75)); ctx.arc(140, -90, 16, 0, 6.283); ctx.fill()
    ctx.restore()


# ------------------------------------------------------------------ PART 1
def p1s1(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.8, focus=(540, 800), shake=0.15 if t < 0.5 else 0.0):
        window_close(ctx, t, frost=0.5, inner=lambda c: man_outside(c, t, 540, 820, 150, knock=True))
        glove(ctx, 780 + 15 * math.sin(t * 9), 1300, 1.1)
        knock_fx(ctx, t, 780, 1260, [0.1, 0.5, 1.6, 2.0, T1.at(1, -1), T1.at(1, -1) + 0.4])
    shot_card(ctx, t, text, "TRUST HIM?", 0.0, y=330, size=150)
    finish(ctx, t, d, fi=0.0)


def p1s2(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(540, 1100)):
        surf_shop(ctx, t)
        soft_shadow(ctx, 540, 1625, 380)
        h = KAI.draw(ctx, 540, 1620, 1000, t, face=0, expr="neutral", expr_to="happy", expr_k=prog(t, T1.at(2, -1), T1.at(2, -1) + 0.4),
                     arm_f=(0.3 + 2.2 * ease(prog(t, T1.at(2, -1), T1.at(2, -1) + 0.5)), 0.3))
        hx, hy = h["hand"]
        rgb(ctx, (1, 0.85, 0.3)); ctx.save(); ctx.translate(hx, hy - 40); ctx.rotate(-0.2); rrect(ctx, -90, -50, 180, 100, 10); ctx.fill()
        text(ctx, "WINNER", 0, 0, 34, (0.5, 0.15, 0.1)); ctx.restore()
        dust(ctx, t, (0, 200, W, 1500), light=(540, 300))
    finish(ctx, t, d)


def p1s3(ctx, t, d):
    look_down = ease(prog(t, T1.at(3, 2), T1.at(3, 2) + 0.6))
    with camera(ctx, t, d, push=0.05, handheld=0.3, focus=(540, 1200)):
        airport(ctx, t)
        soft_shadow(ctx, 540, 1745, 380)
        KAI.draw(ctx, 540, 1740, 980, t, face=0, expr="confused", expr_to="sad", expr_k=prog(t, T1.at(3, 1), T1.at(3, 1) + 0.5),
                 look=(0, 0.9 * look_down), arm_f=(0.35, 0.4), arm_b=(-0.35, 0.4))
    finish(ctx, t, d)


def p1s4(ctx, t, d):
    worse = prog(t, T1.at(4, 1), T1.at(4, 1) + 0.4)
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 700)):
        base_station(ctx, t)
        close(KAI, ctx, 540, 760, 230, t, face=0, expr="happy", expr_to="shock", expr_k=worse, talk=talk_fn(1, 4, 0, 0)(t),
              look=(0, -0.6 * worse))
        SNOWF.draw(ctx, t)
    if worse > 0:
        rgb(ctx, (0.6, 0.7, 1.0), 0.25 * worse); ctx.paint()
    finish(ctx, t, d)


def p1s5(ctx, t, d):
    p = t / d
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 900), pan=(0, -120)):
        base_station(ctx, t, -0.15)
        cx, cy = lerp(380, 760, p), lerp(1010, 420, p)
        cabin_ext(ctx, t, cx, cy, 0.55, swing=0.05 * math.sin(t * 1.5), lit=1.0)
        SNOWF.draw(ctx, t)
        fog(ctx, t, 100, 700, (0.75, 0.78, 0.85), 0.3)
    day_stamp(ctx, t, "4:30 PM", 0.3)
    finish(ctx, t, d)


def p1s6(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.4, focus=(540, 1100)):
        interior(ctx, t, storm=0.4, frost=0.1, dark=0.0)
        RUTH.draw(ctx, 280, 1565, 780, t, mode="sit", face=1, expr="neutral", look=(1, 0.2))
        KAI.draw(ctx, 800, 1565, 800, t, mode="sit", face=-1, expr="happy", look=(-1, 0))
    finish(ctx, t, d)


def p1s7(ctx, t, d):
    k1, k2 = T1.at(7, 1), T1.at(7, 2)
    look = (0.3, 1.0) if t < k1 else (0.2, -1.0) if t < k2 else (0.9, 0)
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(540, 800)):
        interior(ctx, t, storm=0.8, frost=0.2, dark=0.2)
        close(RUTH, ctx, 520, 820, 260, t, face=1, expr="suspicious", talk=talk_fn(1, 7, 2)(t), look=look, head_turn=0.2)
    finish(ctx, t, d)


def p1s8(ctx, t, d):
    stop = T1.at(8, 2)
    jolt = prog(t, T1.at(8, 0) + 0.3, T1.at(8, 0) + 0.6)
    sw = 0.25 * math.exp(-(t - stop) * 1.2) * math.sin((t - stop) * 4) if t > stop else 0.04 * math.sin(t * 9) * jolt
    with camera(ctx, t, d, push=0.05, handheld=0.6, focus=(540, 700), shake=0.6 if abs(t - stop) < 0.4 else 0.1 * jolt):
        sky(ctx, t); mountains(ctx, 0, 1700)
        cable(ctx, -100, 260, W + 100, 180, 25)
        lit = 1.0 if t < T1.at(8, 1) + 0.2 else 0.0
        cabin_ext(ctx, t, 540, 230, 1.1, swing=sw, lit=lit)
        STORM.draw(ctx, t)
    finish(ctx, t, d)


def p1s9(ctx, t, d):
    sw = 0.12 * math.sin(t * 1.3) + 0.05 * math.sin(t * 3.1)
    with camera(ctx, t, d, push=-0.08, handheld=0.5, focus=(540, 500)):
        sky(ctx, t); mountains(ctx, 0, 1750)
        rgb(ctx, (0, 0, 0), 0.35); ctx.rectangle(0, 1300, W, H); ctx.fill()
        cable(ctx, -100, 240, W + 100, 300, 30)
        tower(ctx, 980, 260, 2000)
        cabin_ext(ctx, t, 470, 260, 0.75, swing=sw)
        depth_haze(ctx, 900, 1920, (0.05, 0.06, 0.1), 0.7)
        STORM.draw(ctx, t)
    text(ctx, "200 FT", 540, 1500, 120, (1, 1, 1), prog(t, 0.6, 1.0), outline=10)
    finish(ctx, t, d)


def p1s10(ctx, t, d):
    die = T1.at(10, -1) + 1.2
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 900)):
        rgb(ctx, hexc("#2a3140")); ctx.paint(); glow(ctx, 540, 900, 700, (0.5, 0.6, 0.8), 0.25)
        radio(ctx, t, 1.0 if t < die else 0.0)
    finish(ctx, t, d)


def p1s11(ctx, t, d):
    reach = ease(prog(t, 0.6, 2.2))
    with camera(ctx, t, d, push=0.12, handheld=0.5, focus=(600, 1000)):
        window_close(ctx, t, frost=0.35, inner=lambda c: (tower(c, 760, 600, 2000), cable(c, -100, 640, W + 100, 600, 10)))
        rgb(ctx, hexc("#77757e")); rrect(ctx, 820, 900, 70, 260, 30); ctx.fill()                      # door latch
        hx = lerp(1300, 860, reach)
        rgb(ctx, KAI.top and hexc(KAI.top)); ctx.set_line_width(110); ctx.move_to(1400, 1500); ctx.line_to(hx + 60, 1080); ctx.stroke()
        rgb(ctx, hexc(KAI.skin)); ctx.arc(hx, 1040, 70, 0, 6.283); ctx.fill()
    finish(ctx, t, d)


def p1s12(ctx, t, d):
    grab = T1.at(12, 0) + 0.2
    g = ease(prog(t, grab, grab + 0.25))
    with camera(ctx, t, d, push=0.14, handheld=0.6, focus=(540, 800), shake=0.4 if 0 < t - grab < 0.3 else 0):
        interior(ctx, t, storm=1, frost=0.4, dark=0.6)
        close(RUTH, ctx, 520, 760, 280, t, face=1, expr="angry", talk=talk_fn(1, 12, 1)(t), look=(1, 0.1),
              arm_f=(lerp(0.2, 1.5, g), 0.3))
    finish(ctx, t, d)


def p1s13(ctx, t, d):
    with camera(ctx, t, d, push=0.03, handheld=0.2):
        interior(ctx, t, storm=1, frost=0.5, dark=0.8)
        flake_shadow(ctx)
    rule_card(ctx, t, 0.2, [("STAY INSIDE", T1.at(13, 1)), ("NEVER CLIMB OUT", T1.at(13, 2)), ("RESCUE COMES TO YOU", T1.at(13, 3))],
              title="IF A LIFT STOPS")
    finish(ctx, t, d)


def p1s14(ctx, t, d):
    lift = ease(prog(t, T1.at(14, 1), T1.at(14, 1) + 0.6))
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 1300)):
        interior(ctx, t, storm=1, frost=0.6, dark=0.7)
        RUTH.draw(ctx, 280, 1565, 780, t, mode="sit", face=1, expr="angry", talk=talk_fn(1, 14, 0, 0)(t), look=(1, 0.3))
        KAI.draw(ctx, 800, 1565 - 40 * lift, 800, t, mode="sit", face=-1, expr="shock", expr_to="sad", expr_k=lift, look=(-0.2, 1 - 2 * lift))
        breath(ctx, t, 760, 1000, -1, 0.7, 0.4)
        rgb(ctx, (0.75, 0.88, 1.0), 0.18 + 0.1 * math.sin(t * 3)); ctx.rectangle(0, 1560, W, 360); ctx.fill()
    finish(ctx, t, d)


def p1s15(ctx, t, d):
    with camera(ctx, t, d, push=0.07, handheld=0.3, focus=(540, 1200)):
        interior(ctx, t, storm=1, frost=0.6, dark=0.8)
        rgb(ctx, hexc("#4a5a3a")); rrect(ctx, 250, 1320, 580, 160, 40); ctx.fill()                # backpack seat
        RUTH.draw(ctx, 380, 1385, 760, t, mode="sit", face=1, expr="tired", look=(0.6, 0))
        KAI.draw(ctx, 700, 1385, 780, t, mode="sit", face=-1, expr="neutral", look=(-0.3, -0.2))
        breath(ctx, t, 410, 840, 1, 0.5, 0.35, 0.3); breath(ctx, t, 670, 820, -1, 0.55, 0.35, 0.7)
    finish(ctx, t, d)


def p1s16(ctx, t, d):
    temp = lerp(0.55, 0.12, ease(prog(t, 0.4, d - 0.4)))
    with camera(ctx, t, d, push=0.06, handheld=0.2, focus=(540, 900)):
        rgb(ctx, hexc("#1c2230")); ctx.paint()
        thermometer(ctx, t, temp)
        g = cairo.RadialGradient(540, 900, 300, 540, 900, 1100)
        g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0.85, 0.92, 1, 0.8 * prog(t, 0, d))
        ctx.set_source(g); ctx.paint()
    text(ctx, "10°F" if t < T1.at(16, 2) else "0°F", 540, 1650, 140, (0.8, 0.9, 1), 1, outline=10)
    finish(ctx, t, d)


def p1s17(ctx, t, d):
    k0 = T1.at(17, -1)
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 900), shake=0.3 if any(0 < t - k < 0.2 for k in (k0 + 0.3, k0 + 0.7)) else 0):
        window_close(ctx, t, frost=0.6)
        rgb(ctx, (0, 0, 0), 0.45); ctx.paint()
        knock_fx(ctx, t, 540, 900, [k0 + 0.3, k0 + 0.7], 1.6)
    day_stamp(ctx, t, "12:00 AM", 0.2)
    finish(ctx, t, d)


def p1s18(ctx, t, d):
    reveal = ease(prog(t, 0.2, 1.4))
    with camera(ctx, t, d, push=0.12, handheld=0.5, focus=(540, 800)):
        window_close(ctx, t, frost=0.5, inner=lambda c: man_outside(c, t, 540, 800, 150 * (0.7 + 0.3 * reveal),
                                                                     knock=t > T1.at(18, -2)))
        if reveal < 1:
            rgb(ctx, (0.02, 0.03, 0.05), 0.8 * (1 - reveal)); ctx.paint()
    finish(ctx, t, d)


def p1s19(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 1300)):
        window_close(ctx, t, frost=0.6, inner=lambda c: man_outside(c, t, 540, 1150, 120, knock=True))
        rgb(ctx, (0, 0, 0), 0.45); ctx.paint()
    end_card(ctx, t, T1, 19, "TRUST", "HIM?", "COMMENT: YES OR NO", "PART 2 NEXT")
    finish(ctx, t, d, fo=0.3)


# ------------------------------------------------------------------ PART 2
def p2s1(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.6, focus=(540, 800)):
        window_close(ctx, t, frost=0.5, inner=lambda c: man_outside(c, t, 540, 820, 150, knock=True))
        knock_fx(ctx, t, 540, 1100, [0.3, 0.7, 2.3, 2.7], 1.2)
    shot_card(ctx, t, text, "TRUST HIM?", 0.0, y=330, size=150)
    finish(ctx, t, d, fi=0.0)


def p2s2(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(600, 1000)):
        window_close(ctx, t, frost=0.4, inner=lambda c: man_outside(c, t, 420, 760, 120))
        rgb(ctx, hexc("#77757e")); rrect(ctx, 820, 900, 70, 260, 30); ctx.fill()
        rgb(ctx, hexc(KAI.top)); ctx.set_line_width(110); ctx.move_to(1400, 1500); ctx.line_to(920, 1080); ctx.stroke()
        rgb(ctx, hexc(KAI.skin)); ctx.arc(860, 1040, 70, 0, 6.283); ctx.fill()
    finish(ctx, t, d)


def p2s3(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 800)):
        interior(ctx, t, storm=1, frost=0.4, dark=0.7)
        close(RUTH, ctx, 520, 800, 270, t, face=1, expr="neutral", expr_to="suspicious", expr_k=prog(t, 0.8, 1.6), look=(1, 0.8))
    finish(ctx, t, d)


def p2s4(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.5, focus=(540, 1000), pan=(-60, 0)):
        sky(ctx, t, 0.25); mountains(ctx, 0.25, 1900)
        glow(ctx, 540, 1150, 700, (0.75, 0.85, 1.0), 0.45)                       # cold light from the station
        cable(ctx, -100, 1250, W + 100, 1210, 5)
        for bx in (420, 640):                                                     # boots on the bare cable
            rgb(ctx, hexc("#25252c")); ctx.rectangle(bx - 55, -100, 110, 1270); ctx.fill()
            rgb(ctx, hexc("#151518")); rrect(ctx, bx - 90, 1150, 180, 110, 40); ctx.fill()
            rgb(ctx, (0.8, 0.9, 1.0), 0.5); ctx.rectangle(bx + 40, -100, 10, 1250); ctx.fill()   # rim light
        STORM.draw(ctx, t)
    for k, w in enumerate(("NO HARNESS", "NO ROPE")):
        text(ctx, w, 540, 450 + k * 160, 110, (1, 1, 1), prog(t, T2.at(4, k), T2.at(4, k) + 0.2), outline=10)
    finish(ctx, t, d)


def p2s5(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 800)):
        window_close(ctx, t, frost=0.4, inner=lambda c: close(MAN, c, 540, 820, 190, 0.31, face=0, expr="happy",
                                                                 talk=talk_fn(2, 5, 1)(t), breathe=0.0))
    finish(ctx, t, d)


def p2s6(ctx, t, d):
    with camera(ctx, t, d, push=0.16, handheld=0.3, focus=(540, 900)):
        window_close(ctx, t, frost=0.3, dawn=0.2, inner=lambda c: (glow(c, 540, 760, 650, (0.75, 0.85, 1.0), 0.5),
                                                                    close(MAN, c, 540, 760, 300, 0.31, face=0, expr="happy", breathe=0.0)))
    if t > T2.at(6, -1):
        text(ctx, "NO BREATH", 540, 1680, 120, (0.75, 0.9, 1), prog(t, T2.at(6, -1), T2.at(6, -1) + 0.2), outline=10)
    finish(ctx, t, d)


def p2s7(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.4, focus=(540, 1100)):
        interior(ctx, t, storm=1, frost=0.5, dark=0.7)
        rgb(ctx, hexc("#4a5a3a")); rrect(ctx, 250, 1320, 580, 160, 40); ctx.fill()
        man_outside(ctx, t, 300, 600, 60)
        RUTH.draw(ctx, 380, 1385, 760, t, mode="sit", face=1, expr="fear", look=(-0.3, -0.6))
        KAI.draw(ctx, 700, 1385, 780, t, mode="sit", face=-1, expr="fear", look=(0.3, -0.6))
        breath(ctx, t, 410, 840, 1, 0.8, 0.6, 0.1); breath(ctx, t, 670, 820, -1, 0.9, 0.6, 0.5)
    finish(ctx, t, d)


def p2s8(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 800)):
        interior(ctx, t, storm=1, frost=0.5, dark=0.8)
        close(RUTH, ctx, 480, 820, 290, t, face=1, expr="fear", talk=talk_fn(2, 8, 0, 0)(t) * 0.5, look=(1, 0))
    finish(ctx, t, d)


def p2s9(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 800)):
        interior(ctx, t, storm=1, frost=0.5, dark=0.6)
        close(KAI, ctx, 560, 820, 280, t, face=-1, expr="fear", expr_to="determined", expr_k=prog(t, 0.6, 1.4),
              talk=talk_fn(2, 9, 1)(t), look=(-1, 0), arm_f=(lerp(1.2, 0.2, prog(t, 0.2, 1.0)), 0.4))
    finish(ctx, t, d)


def p2s10(ctx, t, d):
    kn = [k for k in np.arange(0.4, d, 1.1)]
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 800), shake=0.15 if any(0 < t - k < 0.15 for k in kn) else 0):
        window_close(ctx, t, frost=0.5, inner=lambda c: man_outside(c, t, 540, 800, 170, knock=True))
        knock_fx(ctx, t, 540, 1150, kn, 1.2)
    finish(ctx, t, d)


def p2s11(ctx, t, d):
    with camera(ctx, t, d, push=0.05, handheld=0.2, focus=(540, 900)):
        rgb(ctx, hexc("#151a24")); ctx.paint()
        clock(ctx, t, 0, 2, ease(prog(t, 0.2, d - 0.3)))
    finish(ctx, t, d)


def p2s12(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.5, focus=(540, 1300)):
        interior(ctx, t, storm=1, frost=0.7, dark=0.7)
        KAI.draw(ctx, 560, 1565, 900, t + 0.03 * math.sin(t * 40), mode="sit", face=-1, expr="tired", torn=0.8, look=(0, 1))
        rgb(ctx, (0.8, 0.9, 1.0), 0.25); ctx.rectangle(0, 1560, W, 360); ctx.fill()
    finish(ctx, t, d)


def p2s13(ctx, t, d):
    cr = T2.at(13, -1)
    with camera(ctx, t, d, push=0.1, handheld=0.5, focus=(540, 800), shake=0.5 if 0 < t - cr < 0.3 else 0.05):
        interior(ctx, t, storm=1, frost=0.7, dark=0.7)
        close(KAI, ctx, 560 + 4 * math.sin(t * 45), 820, 280, t, face=-1, expr="happy", expr_to="shock", expr_k=prog(t, cr, cr + 0.2),
              talk=talk_fn(2, 13, 0, 0)(t), look=(-0.6, -0.3), torn=0.8)
        if t > cr:
            r = random.Random(1); rgb(ctx, (1, 1, 1), 0.9); ctx.set_line_width(4); ctx.move_to(60, 500)
            for k in range(int(12 * prog(t, cr, cr + 0.3))):
                ctx.line_to(60 + k * 40, 500 + r.uniform(-30, 30));
            ctx.stroke()
    finish(ctx, t, d)


def p2s14(ctx, t, d):
    with camera(ctx, t, d, push=0.14, handheld=0.3, focus=(540, 900)):
        window_close(ctx, t, frost=0.5, inner=lambda c: man_outside(c, t, 540, 760, 220, knock=True), crack=0.6 + 0.4 * prog(t, 0, d), crack_at=(560, 1100))
        glove(ctx, 560, 1120, 1.2)
    finish(ctx, t, d)


def p2s15(ctx, t, d):
    stop = T2.at(15, 1)
    shiver = 1.0 if t < stop else 0.0
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 800)):
        interior(ctx, t, storm=1, frost=0.8, dark=0.8)
        close(RUTH, ctx, 520 + shiver * 5 * math.sin(t * 50), 820, 290, t, face=1, expr="fear", expr_to="tired",
              expr_k=prog(t, stop, stop + 1.0), look=(0.3, 0.6))
    rule_card(ctx, t, T2.at(15, -2), [("SHIVERING STOPS", T2.at(15, -2) + 0.3), ("= THE COLD IS WINNING", T2.at(15, -1))],
              title="HYPOTHERMIA") if t > T2.at(15, -2) else None
    finish(ctx, t, d)


def p2s16(ctx, t, d):
    hug = ease(prog(t, 0.4, 1.4))
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1100)):
        interior(ctx, t, storm=1, frost=0.8, dark=0.75)
        backlight(ctx, 540, 1000, 500, (1, 0.7, 0.45), 0.25 * hug)
        rgb(ctx, hexc("#4a5a3a")); rrect(ctx, 250, 1320, 580, 160, 40); ctx.fill()
        RUTH.draw(ctx, 400, 1385, 760, t, mode="sit", face=1, expr="tired", look=(0, 0.4), lean=0.15)
        KAI.draw(ctx, lerp(720, 640, hug), 1385, 780, t, mode="sit", face=-1, expr="determined", look=(-0.4, 0.4),
                 arm_f=(lerp(0.2, 1.4, hug), lerp(0.3, 1.2, hug)), torn=0.8)
    finish(ctx, t, d)


def p2s17(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 800)):
        window_close(ctx, t, frost=0.6, crack=1.0, crack_at=(560, 1100),
                     inner=lambda c: man_outside(c, t, 540, 800, 170) if t < T2.at(17, 1) else None)
    finish(ctx, t, d)


def p2s18(ctx, t, d):
    dip = T2.at(18, 0) + 0.3
    sw = -0.15 * math.exp(-(t - dip) * 1.5) * math.cos((t - dip) * 5) if t > dip else 0.02 * math.sin(t * 2)
    dy = 40 * math.exp(-(t - dip) * 2) if t > dip else 0
    with camera(ctx, t, d, push=0.05, handheld=0.5, focus=(540, 700), shake=0.6 if 0 < t - dip < 0.4 else 0.05):
        sky(ctx, t); mountains(ctx, 0, 1700)
        cable(ctx, -100, 300, W + 100, 220, 25 + dy)
        cabin_ext(ctx, t, 540, 270 + dy, 1.1, swing=sw, shape_on_roof=prog(t, dip - 0.2, dip))
        STORM.draw(ctx, t)
    finish(ctx, t, d)


def p2s19(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.4, focus=(540, 1300)):
        sky(ctx, t); mountains(ctx, 0, 1700)
        cable(ctx, -100, 1150, W + 100, 1080, 25)
        cabin_ext(ctx, t, 540, 1110, 1.0, swing=0.05 * math.sin(t * 2), shape_on_roof=1.0)
        STORM.draw(ctx, t)
        rgb(ctx, (0, 0, 0), 0.35); ctx.paint()
    end_card(ctx, t, T2, 19, "HOLD", "ON?", "COMMENT: YES OR NO", "PART 3 NEXT")
    finish(ctx, t, d, fo=0.3)


# ------------------------------------------------------------------ PART 3
def p3s1(ctx, t, d):
    dents = [(lerp(200, 880, ((t * 0.3 + k * 0.33) % 1)), 380, 0.8) for k in range(2)]
    with camera(ctx, t, d, push=0.10, handheld=0.5, focus=(540, 800)):
        hatch(ctx, t, 0.0, dents)
    shot_card(ctx, t, text, "ON THE ROOF", 0.0, y=1500, size=130)
    finish(ctx, t, d, fi=0.0)


def p3s2(ctx, t, d):
    steps = [0.5 + k * 0.9 for k in range(int(d / 0.9))]
    x = lerp(150, 950, prog(t, 0.3, d))
    with camera(ctx, t, d, push=0.06, handheld=0.4, focus=(540, 900), shake=0.25 if any(0 < t - s < 0.12 for s in steps) else 0):
        interior(ctx, t, storm=1, frost=0.8, dark=0.85)
        g = cairo.RadialGradient(x, 120, 0, x, 120, 200)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.7); g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g); ctx.arc(x, 120, 200, 0, 6.283); ctx.fill()
        rgb(ctx, hexc("#4a5a3a")); rrect(ctx, 250, 1320, 580, 160, 40); ctx.fill()
        RUTH.draw(ctx, 400, 1385, 760, t, mode="sit", face=1, expr="tired", look=(0, -1), lean=0.15)
        KAI.draw(ctx, 700, 1385, 780, t, mode="sit", face=-1, expr="fear", look=((x - 600) / 400, -1), torn=0.8)
    finish(ctx, t, d)


def p3s3(ctx, t, d):
    turn = 0.9 * ease(prog(t, T3.at(3, 0) + 0.8, d))
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 760)):
        hatch(ctx, t, turn, [(540, 300, 0.6)])
    finish(ctx, t, d)


def p3s4(ctx, t, d):
    ff = T3.at(4, -1)
    with camera(ctx, t, d, push=0.06, handheld=0.7, focus=(540, 700), shake=0.3):
        interior(ctx, t, storm=1, frost=0.8, dark=0.85)
        rgb(ctx, hexc("#5d5c64")); rrect(ctx, 340, -60, 400, 200, 20); ctx.fill()
        rgb(ctx, hexc("#9a9aa3")); rrect(ctx, 400, 120, 280, 50, 25); ctx.fill()
        KAI.draw(ctx, 420, 1700, 1250, t, face=1, expr="angry", look=(0.5, -1), arm_f=(2.5, 0.2), arm_b=(2.3, 0.3),
                 torn=0.8, lost_shoe=t > ff)
        if t > ff:                                              # flip-flop tumbling away
            p = (t - ff) / 1.2
            ctx.save(); ctx.translate(lerp(700, 1150, p), 1700 + 400 * p * p); ctx.rotate(p * 8)
            rgb(ctx, hexc(KAI.shoes)); ctx.scale(1, 0.4); ctx.arc(0, 0, 70, 0, 6.283); ctx.restore(); ctx.fill()
    finish(ctx, t, d)


def p3s5(ctx, t, d):
    tug = math.sin(t * 3.0)
    with camera(ctx, t, d, push=0.10, handheld=0.6, focus=(540, 800), shake=0.2 + 0.2 * max(0, tug)):
        interior(ctx, t, storm=1, frost=0.8, dark=0.85)
        close(KAI, ctx, 420, 900 + 20 * tug, 260, t, face=1, expr="angry", talk=talk_fn(3, 5, 2)(t), look=(0.6, -1),
              arm_f=(2.5, 0.2), arm_b=(2.3, 0.3))
    finish(ctx, t, d)


def p3s6(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 900)):
        interior(ctx, t, storm=1, frost=0.8, dark=0.9)
        close(RUTH, ctx, 500, 900, 280, t, face=1, expr="tired", talk=talk_fn(3, 6, 1)(t) * 0.5, look=(1, 0.3), lean=0.2)
    finish(ctx, t, d)


def p3s7(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(540, 1000)):
        interior(ctx, t, storm=0.8, frost=0.8, dark=0.8)
        close(KAI, ctx, 640, 1250, 220, t, face=-1, expr="happy", talk=0.25 + 0.4 * abs(math.sin(t * 7)), look=(-1, 0), torn=0.8)
        beach_bubble(ctx, t, prog(t, T3.at(7, 1), T3.at(7, 1) + 0.4))
    finish(ctx, t, d)


def p3s8(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 900)):
        interior(ctx, t, storm=0.7, frost=0.8, dark=0.75)
        backlight(ctx, 540, 900, 500, (1, 0.75, 0.5), 0.2)
        close(RUTH, ctx, 520, 900, 280, t, face=1, expr="tired", expr_to="happy", expr_k=0.6 * prog(t, 0.3, 1.2), look=(1, 0.2), lean=0.2)
    finish(ctx, t, d)


def p3s9(ctx, t, d):
    dawn = ease(prog(t, 0.5, d))
    with camera(ctx, t, d, push=-0.06, handheld=0.2, focus=(540, 700)):
        sky(ctx, t, dawn * 0.6); mountains(ctx, dawn * 0.6, 1700)
        cable(ctx, -100, 600, W + 100, 520, 25)
        cabin_ext(ctx, t, 540, 560, 0.9, swing=0.01 * math.sin(t), dawn=dawn)
        ctx.save(); ctx.set_operator(cairo.OPERATOR_OVER); rgb(ctx, (1, 1, 1), 0.0); ctx.restore()
        Particles(int(200 * (1 - dawn)) + 20, 8, (0, 0, W, H), vel=(-120, 140), size=(1.5, 3.5), alpha=0.6).draw(ctx, t)
    finish(ctx, t, d)


def p3s10(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1300)):
        sky(ctx, t, 0.65); mountains(ctx, 0.65, 1100)
        snowcat(ctx, t, 300 + t * 30, 1500, 1.2)
        for k, (x, ch) in enumerate(((650, DEE), (860, Character("P", skin="#d9a07a", hair="#2a1d14", top="#c2242c", pants="#2b2b33", footwear="shoes", shoes="#222222", seed=8.0)))):
            soft_shadow(ctx, x, 1605, 200)
            r = ch.draw(ctx, x, 1600, 520, t, face=-1, expr="determined", look=(-0.3, -1))
            breath(ctx, t, r["head"][0] - 30, r["head"][1] + 20, -1, 0.7, 0.6, k * 0.4)
    finish(ctx, t, d)


def p3s11(ctx, t, d):
    climb = prog(t, 0, d)
    with camera(ctx, t, d, push=0.05, handheld=0.3, focus=(540, 900), pan=(0, -150)):
        sky(ctx, t, 0.7); mountains(ctx, 0.7, 1700)
        tower(ctx, 540, 200, 2200, 120)
        rgb(ctx, (0.95, 0.8, 0.2)); ctx.set_line_width(6); ctx.move_to(540, 200); ctx.line_to(600, 1900); ctx.stroke()    # rope
        y = lerp(1700, 900, climb)
        DEE.draw(ctx, 600, y + 300, 420, t, mode="walk", phase=t * 3, face=1, expr="determined", look=(-0.5, -1), arm_f=(2.6, 0.3), arm_b=(2.4, 0.3))
        rgb(ctx, (0.1, 0.1, 0.1)); ctx.set_line_width(5); ctx.move_to(600, y + 120); ctx.line_to(600, y - 60); ctx.stroke()  # clipped on
    text(ctx, "CLIPPED ON", 540, 1600, 100, (1, 1, 1), prog(t, T3.at(11, 1), T3.at(11, 1) + 0.2), outline=10)
    finish(ctx, t, d)


def p3s12(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(540, 900), pan=(0, 200)):
        sky(ctx, t, 0.75); mountains(ctx, 0.75, 1800)
        y = lerp(500, 1300, ease(prog(t, 0, d)))
        rgb(ctx, (0.95, 0.8, 0.2)); ctx.set_line_width(6); ctx.move_to(540, -300); ctx.line_to(540, y - 900); ctx.stroke()
        KAI.draw(ctx, 470, y, 760, t, face=1, expr="tired", look=(0.3, 1), arm_f=(2.7, 0.2), arm_b=(2.5, 0.2),
                 torn=1.0, dirt=0.6, lost_shoe=True)
        rgb(ctx, (1, 1, 1), 0.8)                                                # frosty eyebrows
    finish(ctx, t, d)


def p3s13(ctx, t, d):
    with camera(ctx, t, d, push=0.07, handheld=0.3, focus=(540, 1100)):
        sky(ctx, t, 0.85); mountains(ctx, 0.85, 1500)
        soft_shadow(ctx, 380, 1705, 300); soft_shadow(ctx, 720, 1705, 300)
        DEE.draw(ctx, 380, 1700, 820, t, face=1, expr="happy", talk=talk_fn(3, 13, 1)(t), look=(1, 0))
        KAI.draw(ctx, 720, 1700, 840, t, face=-1, expr="tired", expr_to="happy", expr_k=prog(t, T3.at(13, -1), T3.at(13, -1) + 0.6),
                 look=(-1, 0), torn=1.0, dirt=0.6, lost_shoe=True)
        rgb(ctx, hexc("#7a8fa8")); ctx.save(); ctx.translate(720, 1350)                     # blanket around his legs
        rrect(ctx, -130, 80, 260, 250, 60); ctx.restore(); ctx.fill()
    finish(ctx, t, d)


def p3s14(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 1000)):
        sky(ctx, t, 0.85); mountains(ctx, 0.85, 1500)
        DEE.draw(ctx, 330, 1700, 820, t, face=1, expr="neutral", expr_to="confused", expr_k=prog(t, 1.0, 2.0), look=(1, 0))
        KAI.draw(ctx, 740, 1700, 840, t, face=-1, expr="fear", talk=0.2 + 0.4 * abs(math.sin(t * 7)), look=(-1, -0.3),
                 arm_f=(1.6 + 0.3 * math.sin(t * 3), 0.6), torn=1.0, dirt=0.6, lost_shoe=True)
    finish(ctx, t, d)


def p3s15(ctx, t, d):
    ph = T3.at(15, 1)
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 800)):
        sky(ctx, t, 0.85); mountains(ctx, 0.85, 1500)
        if t < ph:
            close(DEE, ctx, 540, 820, 280, t, face=0, expr="neutral", expr_to="sad", expr_k=prog(t, 0.2, 1.2), talk=talk_fn(3, 15, 1)(t))
        else:
            rgb(ctx, (0, 0, 0), 0.5); ctx.paint()
            polaroid(ctx, t)
    finish(ctx, t, d)


def p3s16(ctx, t, d):
    with camera(ctx, t, d, push=0.18, handheld=0.3, focus=(540, 700)):
        sky(ctx, t, 0.9); mountains(ctx, 0.9, 1800)
        cable(ctx, -100, 520, W + 100, 440, 25)
        cabin_ext(ctx, t, 540, 480, 1.3, roof_snow=1.0, dawn=1.0, people=False)
    for k, w in enumerate(("NO", "FOOTPRINTS")):
        text(ctx, w, 540, 1450 + k * 150, 120, (1, 1, 1), prog(t, T3.at(16, -1), T3.at(16, -1) + 0.2), outline=10)
    finish(ctx, t, d)


def p3s17(ctx, t, d):
    sh = T3.at(17, 1)
    with camera(ctx, t, d, push=0.12, handheld=0.2, focus=(540, 1100)):
        sky(ctx, t, 1.0)
        KAI.draw(ctx, 540, 2600, 2100, t, face=0, expr="tired", expr_to="happy", expr_k=prog(t, sh, sh + 0.5),
                 torn=1.0, dirt=1.0, soot=0.6, lost_shoe=True)
        if t > sh:
            for k in range(6):
                a = prog(t, sh + k * 0.15, sh + k * 0.15 + 0.4) * (1 - prog(t, sh + k * 0.15 + 0.4, sh + k * 0.15 + 0.9))
                r = random.Random(k)
                x, y = r.uniform(250, 830), r.uniform(1250, 1800)
                rgb(ctx, (1, 1, 0.85), a); ctx.set_line_width(6)
                for ang in range(4):
                    ctx.move_to(x, y); ctx.line_to(x + math.cos(ang * math.pi / 2) * 40, y + math.sin(ang * math.pi / 2) * 40); ctx.stroke()
    text(ctx, "THE SHIRT SURVIVED", 540, 330, 100, (1, 0.85, 0.4), prog(t, sh, sh + 0.3), outline=10)
    finish(ctx, t, d)


def p3s18(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.2, focus=(540, 1200)):
        sky(ctx, t, 1.0); mountains(ctx, 1.0, 1400)
        god_rays(ctx, t, 900, 500, angle=2.4, length=1800, col=(1, 0.85, 0.6), alpha=0.18)
        for x, ch, f in ((380, RUTH, 1), (700, KAI, -1)):
            soft_shadow(ctx, x, 1705, 300)
            kw = dict(torn=1.0, dirt=0.6, lost_shoe=True) if ch is KAI else {}
            ch.draw(ctx, x, 1700, 800, t, face=f, expr="happy", talk=talk_fn(3, 18, 0, 0)(t) if ch is KAI else 0, look=(-f * 0.2, 0), **kw)
            rgb(ctx, hexc("#7a8fa8")); rrect(ctx, x - 130, 1430, 260, 250, 60); ctx.fill()
    finish(ctx, t, d)


def p3s19(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 1300)):
        sky(ctx, t); mountains(ctx, 0, 1700)
        cable(ctx, -100, 1150, W + 100, 1080, 25)
        cabin_ext(ctx, t, 540, 1110, 1.0, swing=0.05 * math.sin(t * 2))
        man_outside(ctx, t, 820, 1350, 60)
        STORM.draw(ctx, t)
        rgb(ctx, (0, 0, 0), 0.35); ctx.paint()
    end_card(ctx, t, T3, 19, "TRUST", "HIM?", "COMMENT: YES OR NO", "NEW STORY TOMORROW")
    finish(ctx, t, d, fo=0.4)


P1 = [globals()[f"p1s{i}"] for i in range(1, 20)]
P2 = [globals()[f"p2s{i}"] for i in range(1, 20)]
P3 = [globals()[f"p3s{i}"] for i in range(1, 20)]


# ------------------------------------------------------------------ sound
def knock_s(d, times, seed=0):
    x = silence(d)
    for k, c in enumerate(times):
        i, n = int(c * SR), int(0.12 * SR)
        if 0 <= i and i + n <= len(x):
            tt = np.arange(n) / SR
            x[i:i + n] += (np.sin(2 * np.pi * 180 * tt) * 0.6 + band_noise(0.12, 300, 2000, seed + k)[:n] * 0.4) * np.exp(-tt * 40) * 0.8
    return x


def creak_s(d, times, seed=0):
    x = silence(d)
    for k, c in enumerate(times):
        i, n = int(c * SR), int(0.6 * SR)
        if i + n > len(x):
            continue
        tt = np.arange(n) / SR
        f = 120 + 60 * np.sin(np.pi * tt / 0.6) + np.random.default_rng(seed + k).uniform(-20, 20)
        saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
        x[i:i + n] += saw * np.sin(np.pi * tt / 0.6) ** 2 * 0.07
    return x


def sfx_for(tm, part):
    def sfx(i, d):
        x = wind(d, 1.2, i + part * 30) * 1.1 + band_noise(d, 2500, 8000, i) * 0.02
        indoor_quiet = (part == 1 and i in (2, 3)) or (part == 3 and i >= 13)
        if indoor_quiet:
            x = band_noise(d, 100, 600, i) * 0.03 if i in (2, 3) and part == 1 else wind(d, 0.3, i)
        if part == 1:
            if i == 1:
                x += knock_s(d, [0.1, 0.5, 1.6, 2.0, tm.at(1, -1), tm.at(1, -1) + 0.4])
            if i == 8:
                x += creak_s(d, [tm.at(8, 2), tm.at(8, 2) + 0.7], 8) * 3 + env_at(d, [tm.at(8, 2)], 0.6) * band_noise(d, 40, 200, 88) * 0.8
            if i == 9:
                x += creak_s(d, list(np.arange(0.5, d, 1.6)), 9) * 2
            if i == 10:
                die = tm.at(10, -1) + 1.2
                t = np.arange(len(x)) / SR
                x += band_noise(d, 800, 5000, 10) * 0.12 * (t < die)
            if i == 17:
                x += knock_s(d, [tm.at(17, -1) + 0.3, tm.at(17, -1) + 0.7])
            if i in (18, 19):
                x += knock_s(d, list(np.arange(tm.at(i, -2), d, 1.1)), i) * 0.7
        elif part == 2:
            if i in (1, 10, 14):
                x += knock_s(d, list(np.arange(0.4, d, 1.1)), i)
            if i == 13:
                c = tm.at(13, -1)
                x += env_at(d, [c], 0.3) * band_noise(d, 1500, 9000, 13) * 0.6
            if i == 18:
                dip = tm.at(18, 0) + 0.3
                x += env_at(d, [dip], 0.7) * band_noise(d, 30, 200, 18) * 1.2 + creak_s(d, [dip + 0.1, dip + 0.9], 18) * 3
        else:
            if i in (1, 2):
                x += knock_s(d, [0.5 + k * 0.9 for k in range(int(d / 0.9))], i) * 0.8
            if i in (3, 4, 5):
                x += creak_s(d, list(np.arange(0.6, d, 1.0)), i) * 2
            if i == 10:
                t = np.arange(len(x)) / SR
                x += band_noise(d, 40, 180, 10) * 0.25 + np.sin(2 * np.pi * 55 * t) * 0.03
        return fades(x * 0.6, 0.03, 0.1)
    return sfx


def drone_score(total, seed=0):
    t = np.arange(int(total * SR)) / SR
    x = (np.sin(2 * np.pi * 41.2 * t) * 0.25 + np.sin(2 * np.pi * 41.9 * t) * 0.25
         + np.sin(2 * np.pi * 61.7 * t) * 0.1 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t)))
    x += band_noise(total, 60, 300, seed) * 0.08
    glints = env_at(total, list(np.random.default_rng(seed).uniform(2, max(3, total - 2), int(total / 9))), 2.5)
    x += glints * np.sin(2 * np.pi * 1568 * t) * 0.02
    return fades(x.astype(np.float32) * 0.6, 2.0, 2.0)


def music1(durs):
    a = sum(durs[:4])
    warm = piano_score(a, a + 100, bpm=72, seed=3)
    return np.concatenate([warm, drone_score(sum(durs) - a, 1)])[: int(sum(durs) * SR)]


def music2(durs):
    return drone_score(sum(durs), 2)


def music3(durs):
    total = sum(durs)
    a = sum(durs[:8])
    b = sum(durs[:14])
    return np.concatenate([drone_score(a, 3), piano_score(b - a, b + 100, bpm=64, seed=7),
                           drone_score(sum(durs[:16]) - b, 4) * 0.8, piano_score(total - sum(durs[:16]), 999, bpm=70, seed=9)])[: int(total * SR)]


PARTS = {1: ("32_gondola_1", P1, sfx_for(T1, 1), music1), 2: ("33_gondola_2", P2, sfx_for(T2, 2), music2),
         3: ("34_gondola_3", P3, sfx_for(T3, 3), music3)}

if __name__ == "__main__":
    run(PARTS, {1: T1, 2: T2, 3: T3})
