"""Animated scenes for stories/02_day_40_bunker.json.

    python src/anim/bunker.py          # renders assets/clips/02_day_40_bunker/scene_XX.mp4 (+ .sfx.wav)
"""
import math, pathlib, sys
from multiprocessing import Pool

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import *  # noqa

ROOT = pathlib.Path(__file__).resolve().parents[2]
SID = "02_day_40_bunker"
GY = 1250  # ground line
S = 430    # character height


# ---------------------------------------------------------------- shared sets
FAR = skyline(1, 0, GY, 250, 650, 70, 160)
NEAR = skyline(2, 0, GY, 120, 380, 110, 220)
RUIN_FAR = skyline(5, 0, 1000, 120, 420, 60, 150, broken=True)
RUIN_NEAR = skyline(6, 0, 1000, 60, 260, 90, 200, broken=True)


def bunker_room(ctx, t, light=1.0, swing=True):
    """Concrete room, shelves, table, hanging lamp. Returns lamp position."""
    vgrad(ctx, 0, GY, [(0, hexc("#1d2230")), (1, hexc("#2c3140"))])
    ctx.set_line_width(2)
    for row in range(0, GY, 90):          # concrete blocks
        off = 90 if (row // 90) % 2 else 0
        rgb(ctx, (0, 0, 0), 0.12)
        ctx.move_to(0, row); ctx.line_to(W, row); ctx.stroke()
        for x in range(-off, W, 180):
            ctx.move_to(x, row); ctx.line_to(x, row + 90); ctx.stroke()
    vgrad(ctx, GY, H, [(0, hexc("#191b22")), (1, hexc("#0c0d11"))])
    # shelves
    for k, sy in enumerate((700, 860, 1020)):
        rgb(ctx, hexc("#4a3a2c"))
        ctx.rectangle(50, sy, 300, 14); ctx.fill()
    rgb(ctx, hexc("#3a2d22"))
    ctx.rectangle(50, 560, 12, 690); ctx.fill()
    ctx.rectangle(338, 560, 12, 690); ctx.fill()
    # lamp
    ang = 0.13 * math.sin(t * 1.7) if swing else 0
    lx, ly = 690 + math.sin(ang) * 520, math.cos(ang) * 520
    rgb(ctx, (0.1, 0.1, 0.1)); ctx.set_line_width(4)
    ctx.move_to(690, 0); ctx.line_to(lx, ly); ctx.stroke()
    flick = 1 - 0.25 * max(0, math.sin(t * 23) * math.sin(t * 7.3)) if light < 1 else 1
    a = light * flick
    cone(ctx, lx, ly, math.pi / 2 + ang, 0.62, 900, (1.0, 0.82, 0.55), 0.35 * a)
    glow(ctx, lx, ly + 10, 160, (1.0, 0.8, 0.5), 0.55 * a)
    rgb(ctx, hexc("#2a2a2a"))
    ctx.move_to(lx - 45, ly + 20); ctx.line_to(lx + 45, ly + 20); ctx.line_to(lx + 20, ly - 10)
    ctx.line_to(lx - 20, ly - 10); ctx.close_path(); ctx.fill()
    rgb(ctx, (1, 0.9, 0.7), a); ctx.arc(lx, ly + 22, 12, 0, 6.283); ctx.fill()
    return lx, ly


def cans(ctx, n):
    cols = [hexc("#b8432f"), hexc("#3d7a4a"), hexc("#c99a2e")]
    k = 0
    for sy in (700, 860, 1020):
        for i in range(5):
            if k >= n:
                return
            x = 70 + i * 55
            rgb(ctx, hexc("#9aa0a8")); ctx.rectangle(x, sy - 70, 44, 70); ctx.fill()
            rgb(ctx, cols[k % 3]); ctx.rectangle(x, sy - 52, 44, 32); ctx.fill()
            rgb(ctx, hexc("#c9ced6")); ctx.save(); ctx.translate(x + 22, sy - 70)
            ctx.scale(1, 0.3); ctx.arc(0, 0, 22, 0, 6.283); ctx.restore(); ctx.fill()
            k += 1


def table(ctx):
    rgb(ctx, hexc("#5a4634")); ctx.rectangle(430, 1050, 560, 26); ctx.fill()
    rgb(ctx, hexc("#3e3024"))
    ctx.rectangle(460, 1076, 20, GY - 1076); ctx.fill()
    ctx.rectangle(940, 1076, 20, GY - 1076); ctx.fill()
    rgb(ctx, hexc("#2d2a28")); ctx.rectangle(300, 1150, 150, 18); ctx.fill()   # stool
    ctx.rectangle(315, 1168, 14, GY - 1168); ctx.fill(); ctx.rectangle(420, 1168, 14, GY - 1168); ctx.fill()


def radio(ctx, t, x, y, level):
    rgb(ctx, hexc("#3b3f36")); rrect(ctx, x - 120, y - 130, 240, 130, 16); ctx.fill()
    rgb(ctx, hexc("#24261f")); rrect(ctx, x - 100, y - 112, 120, 92, 10); ctx.fill()
    for k in range(6):                    # speaker grille
        rgb(ctx, (0, 0, 0), 0.5); ctx.rectangle(x - 92, y - 104 + k * 14, 104, 5); ctx.fill()
    dial = (0.4, 1.0, 0.55)
    glow(ctx, x + 62, y - 70, 70 + 50 * level, dial, 0.3 + 0.5 * level)
    rgb(ctx, dial, 0.6 + 0.4 * level); ctx.arc(x + 62, y - 70, 22, 0, 6.283); ctx.fill()
    rgb(ctx, (0.1, 0.1, 0.1)); ctx.set_line_width(5)
    ctx.move_to(x + 90, y - 130); ctx.line_to(x + 150, y - 300); ctx.stroke()


def static_lines(ctx, t, x, y, amt):
    import random
    r = random.Random(int(t * 15))
    ctx.set_line_width(3)
    for k in range(int(5 * amt)):
        rgb(ctx, (0.7, 0.9, 0.8), r.uniform(0.2, 0.6) * amt)
        sx, sy = x + r.uniform(-60, 60), y - r.uniform(160, 260)
        ctx.move_to(sx, sy)
        for j in range(5):
            ctx.line_to(sx + (j + 1) * 18 * r.choice((-1, 1)), sy - (j + 1) * 14 + r.uniform(-10, 10))
        ctx.stroke()


def tally(ctx, n, x0=640, y0=420):
    rgb(ctx, (0.85, 0.85, 0.8), 0.55)
    ctx.set_line_width(7)
    ctx.set_line_cap(1)
    for i in range(int(n)):
        g, k = divmod(i, 5)
        gx, gy = x0 + (g % 2) * 190, y0 + (g // 2) * 140
        if k < 4:
            ctx.move_to(gx + k * 30, gy); ctx.line_to(gx + k * 30 + 4, gy + 100)
        else:
            ctx.move_to(gx - 14, gy + 80); ctx.line_to(gx + 112, gy + 18)
        ctx.stroke()


# ---------------------------------------------------------------- scenes
def s1(ctx, t, d):   # Day one. Sirens. Run for the bunker.
    pulse = 0.5 + 0.5 * math.sin(t * 7)
    vgrad(ctx, 0, GY, [(0, hexc("#070a16")), (0.7, hexc("#2a1328")), (1, hexc("#5a1a22"))])
    rgb(ctx, (1, 0.1, 0.1), 0.10 * pulse); ctx.paint()
    draw_skyline(ctx, FAR, GY - 120, hexc("#1a1424"), (1, 0.75, 0.4), 0.5, t, offset=-t * 25)
    # billboard alert
    bx = 120 - t * 25
    rgb(ctx, hexc("#7a1414") if pulse > 0.5 else hexc("#4a0c0c")); ctx.rectangle(bx, 640, 330, 150); ctx.fill()
    text(ctx, "EMERGENCY ALERT", bx + 165, 690, 46, (1, 0.85, 0.75))
    text(ctx, "TAKE SHELTER NOW", bx + 165, 748, 40, (1, 0.7, 0.2))
    glow(ctx, bx + 165, 715, 300, (1, 0.15, 0.1), 0.25 * pulse)
    draw_skyline(ctx, NEAR, GY, hexc("#0e0b14"), (1, 0.6, 0.3), 0.35, t, offset=-t * 70)
    # siren tower + rotating beam
    tx = 900 - t * 70
    rgb(ctx, hexc("#111111")); ctx.rectangle(tx - 8, 760, 16, GY - 760); ctx.fill()
    cone(ctx, tx, 760, t * 4.5, 0.22, 1100, (1, 0.15, 0.1), 0.35)
    glow(ctx, tx, 760, 90, (1, 0.2, 0.15), 0.9)
    # ground + moving road marks
    vgrad(ctx, GY, H, [(0, hexc("#1c1820")), (1, hexc("#08070b"))])
    rgb(ctx, (0.9, 0.8, 0.3), 0.5)
    for k in range(8):
        x = (k * 200 - t * 420) % (W + 200) - 100
        ctx.rectangle(x, GY + 120, 110, 12); ctx.fill()
    # bunker entrance slides in from the right
    ex = lerp(1300, 760, ease(prog(t, 0.0, d * 0.75)))
    rgb(ctx, hexc("#4b4f57")); ctx.rectangle(ex, 1000, 360, GY - 1000); ctx.fill()
    for k in range(9):
        rgb(ctx, (0.95, 0.75, 0.1) if k % 2 else (0.1, 0.1, 0.1))
        ctx.rectangle(ex + k * 40, 1000, 40, 22); ctx.fill()
    rgb(ctx, hexc("#06060a")); ctx.rectangle(ex + 90, 1050, 180, GY - 1050); ctx.fill()
    glow(ctx, ex + 180, 1140, 160, (1, 0.6, 0.3), 0.25)
    # runner
    end = d * 0.86
    px = lerp(200, ex + 180, ease(prog(t, d * 0.55, end))) if t > d * 0.55 else 200 + math.sin(t * 2) * 10
    if t < end:
        s = S * (1 - 0.25 * prog(t, end - 0.4, end))
        person(ctx, px, GY + 20 * prog(t, end - 0.4, end), s, mode="run", phase=t * 13, face=1)
    # dust kicked up
    Particles(40, 3, (0, GY - 200, W, GY + 40), vel=(-160, -20), col=(0.6, 0.5, 0.5), alpha=0.25).draw(ctx, t)
    day_stamp(ctx, t, "DAY 1")
    secs = max(0, 90 - int(t / d * 84))
    text(ctx, f"{secs} SECONDS", W / 2, 470, 78, (1, 0.35, 0.3), 0.9, outline=8)
    vignette(ctx, 0.7); grain(ctx, t); fade(ctx, t, d, 0.2, 0.2)


def s2(ctx, t, d):   # Day ten. Rationing.
    bunker_room(ctx, t)
    cans(ctx, 15 - int(prog(t, 0.5, d - 0.5) * 6))
    table(ctx)
    # can + spoon on table, half bottle
    rgb(ctx, hexc("#9aa0a8")); ctx.rectangle(690, 980, 60, 70); ctx.fill()
    rgb(ctx, hexc("#b8432f")); ctx.rectangle(690, 998, 60, 30); ctx.fill()
    rgb(ctx, (0.6, 0.8, 1.0), 0.35); rrect(ctx, 820, 900, 56, 150, 12); ctx.fill()
    rgb(ctx, (0.35, 0.6, 0.95), 0.75); rrect(ctx, 820, 975, 56, 75, 10); ctx.fill()
    eat = math.sin(t * 3.2)
    person(ctx, 375, GY, S, mode="sit", face=1, lean=0.12 + 0.05 * max(0, eat),
           arm_f=(1.25 + 0.35 * eat, -1.1 - 0.5 * eat), breathe=math.sin(t * 2))
    Particles(50, 7, (300, 300, 1050, 1200), vel=(6, -4), size=(1.5, 3), col=(1, 0.9, 0.7), alpha=0.35).draw(ctx, t)
    day_stamp(ctx, t, "DAY 10")
    vignette(ctx, 0.8); grain(ctx, t); fade(ctx, t, d, 0.15, 0.15)


def s3(ctx, t, d):   # Day twenty. Radio silent. Static.
    z = 1 + 0.05 * t / d
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2)
    bunker_room(ctx, t, light=0.55, swing=False)
    cans(ctx, 6)
    tally(ctx, lerp(10, 20, ease(prog(t, 0.2, d * 0.8))))
    table(ctx)
    radio(ctx, t, 760, 1050, 0.3 + 0.2 * math.sin(t * 11))
    static_lines(ctx, t, 720, 1050, 1.0)
    person(ctx, 375, GY, S, mode="sit", face=1, lean=0.38, arm_f=(1.6, -0.2), breathe=math.sin(t * 1.4))
    ctx.restore()
    rgb(ctx, (0, 0, 0), 0.25); ctx.paint()
    day_stamp(ctx, t, "DAY 20")
    vignette(ctx, 0.9); grain(ctx, t, 500, 0.08); fade(ctx, t, d, 0.15, 0.15)


BANGS = [0.5, 1.4, 1.9, 2.9, 3.4]


def s4(ctx, t, d):   # Day thirty. Scratching at the door.
    shake = sum(math.exp(-(t - b) * 9) for b in BANGS if t >= b)
    ctx.save(); ctx.translate(wobble(t, 1, 40) * 14 * shake, wobble(t, 2, 40) * 14 * shake)
    vgrad(ctx, 0, GY, [(0, hexc("#0b0d13")), (1, hexc("#151821"))])
    vgrad(ctx, GY, H, [(0, hexc("#0d0e12")), (1, hexc("#050507"))])
    # door
    dx = 640 + sum(math.exp(-(t - b) * 12) * 10 * math.sin((t - b) * 60) for b in BANGS if t >= b)
    rgb(ctx, hexc("#3a3f48")); ctx.rectangle(dx, 560, 360, GY - 560); ctx.fill()
    rgb(ctx, hexc("#2a2e35")); ctx.set_line_width(14); ctx.rectangle(dx + 20, 580, 320, GY - 600); ctx.stroke()
    for k in range(12):
        rgb(ctx, hexc("#5a606b")); ctx.arc(dx + 40 + (k % 2) * 280, 610 + (k // 2) * 110, 8, 0, 6.283); ctx.fill()
    rgb(ctx, hexc("#62676f")); ctx.set_line_width(12); ctx.arc(dx + 180, 900, 60, 0, 6.283); ctx.stroke()
    for a in range(4):
        ctx.move_to(dx + 180, 900); ctx.line_to(dx + 180 + math.cos(a * 1.57 + t * 0.2) * 60, 900 + math.sin(a * 1.57 + t * 0.2) * 60); ctx.stroke()
    # scratches appear
    n = int(prog(t, 0.3, d - 0.4) * 14)
    ctx.set_line_width(5)
    for k in range(n):
        rgb(ctx, (0.75, 0.75, 0.72), 0.7)
        sx = dx + 60 + (k * 53) % 240
        sy = 700 + (k * 97) % 380
        for j in range(3):
            ctx.move_to(sx + j * 14, sy); ctx.line_to(sx + j * 14 + 30, sy + 90); ctx.stroke()
    # character backing away with flashlight
    px = lerp(380, 250, ease(prog(t, 0.4, d)))
    j = wobble(t, 4, 9) * 0.05 + 0.03 * shake
    info = person(ctx, px, GY, S, mode="idle", face=1, lean=-0.06, arm_f=(1.5 + j, -0.05),
                  breathe=math.sin(t * 6))
    hx, hy = info["hand"]
    rgb(ctx, hexc("#222222")); rrect(ctx, hx - 6, hy - 14, 50, 26, 6); ctx.fill()
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    cone(ctx, hx + 44, hy, -0.12 + j, 0.2, 900, (1, 0.95, 0.75), 0.45)
    glow(ctx, dx + 180, 880, 260, (1, 0.95, 0.75), 0.18)
    ctx.restore()
    ctx.restore()
    day_stamp(ctx, t, "DAY 30")
    vignette(ctx, 1.0); grain(ctx, t, 500, 0.07); fade(ctx, t, d, 0.15, 0.15)


def s5(ctx, t, d):   # Day forty. The radio crackles. Survivors!
    wake = prog(t, 0.6, 1.0)
    bunker_room(ctx, t, light=0.6 + 0.4 * wake, swing=True)
    cans(ctx, 3)
    tally(ctx, 20)
    table(ctx)
    radio(ctx, t, 760, 1050, 0.4 + 0.6 * wake)
    for k in range(4):                    # sound rings
        r = ((t * 260 + k * 120) % 480)
        rgb(ctx, (0.5, 1, 0.65), 0.5 * (1 - r / 480) * wake)
        ctx.set_line_width(6); ctx.arc(700, 990, 40 + r, -2.6, -0.5); ctx.stroke()
    if t < 0.75:
        person(ctx, 375, GY, S, mode="sit", face=1, lean=0.38, arm_f=(1.6, -0.2))
    else:
        jump = math.sin(prog(t, 0.75, 1.15) * math.pi) * 40
        person(ctx, 470, GY - jump, S, mode="idle", face=1, lean=0.2,
               arm_f=(1.3, 0.2), arm_b=(0.9, 0.5), breathe=math.sin(t * 5))
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    glow(ctx, 740, 980, 600, (1, 0.75, 0.4), 0.18 * wake)
    ctx.restore()
    day_stamp(ctx, t, "DAY 40")
    vignette(ctx, 0.75); grain(ctx, t); fade(ctx, t, d, 0.15, 0.15)


ASH = Particles(140, 11, (0, 0, W, H), vel=(18, 55), size=(2, 4.5), col=(0.85, 0.95, 0.75), alpha=0.45)


def green_sky(ctx, t, horizon=1000):
    vgrad(ctx, 0, horizon, [(0, hexc("#0f2414")), (0.55, hexc("#3f7a2e")), (1, hexc("#b7e36a"))])
    for k in range(6):                    # drifting clouds
        cx = (k * 260 + t * (20 + k * 4)) % (W + 500) - 250
        cy = 180 + k * 110
        rgb(ctx, (0.75, 0.95, 0.55), 0.10)
        ctx.save(); ctx.translate(cx, cy); ctx.scale(3.2, 1); ctx.arc(0, 0, 70 + k * 6, 0, 6.283); ctx.restore(); ctx.fill()
    glow(ctx, W * 0.7, horizon - 260, 420, (0.85, 1, 0.5), 0.35)


def s6(ctx, t, d):   # Open the hatch. The sky is green.
    tilt = lerp(-520, 0, ease(prog(t, 1.2, d * 0.75)))
    ctx.save(); ctx.translate(0, -tilt)
    vgrad(ctx, -700, 1, [(0, hexc("#0a1a0e")), (1, hexc("#0f2414"))])
    green_sky(ctx, t, GY)
    draw_skyline(ctx, RUIN_FAR, GY - 60, hexc("#1d2a1a"))
    draw_skyline(ctx, RUIN_NEAR, GY, hexc("#0e150d"))
    # character rising through the hatch
    rise = ease_out(prog(t, 0.9, 2.6))
    look = prog(t, 2.8, 3.6)
    person(ctx, 520, GY + (1 - rise) * 470, S, mode="idle", face=1, lean=-0.12 * look,
           head_turn=-1.0 * look, arm_f=(0.4 + 1.2 * (1 - rise), 0.6), breathe=math.sin(t * 3))
    vgrad(ctx, GY, H + 600, [(0, hexc("#2b3324")), (1, hexc("#0b0e09"))])
    for k in range(10):                   # rubble
        rgb(ctx, hexc("#1a2016")); ctx.save(); ctx.translate(80 + k * 107, GY + 30 + (k * 37) % 90)
        ctx.scale(1.8, 0.7); ctx.arc(0, 0, 18 + (k * 13) % 20, 0, 6.283); ctx.restore(); ctx.fill()
    # hatch opening + lid swinging up
    rgb(ctx, hexc("#050505")); ctx.save(); ctx.translate(540, GY + 8); ctx.scale(1, 0.22)
    ctx.arc(0, 0, 150, 0, 6.283); ctx.restore(); ctx.fill()
    open_a = ease_out(prog(t, 0.2, 0.9)) * 1.9
    ctx.save(); ctx.translate(390, GY + 8); ctx.rotate(-open_a)
    rgb(ctx, hexc("#4a5048")); rrect(ctx, 0, -18, 300, 36, 10); ctx.fill()
    rgb(ctx, hexc("#62685f")); ctx.set_line_width(6); ctx.arc(150, 0, 40, 0, 6.283); ctx.stroke()
    ctx.restore()
    ctx.restore()
    ASH.draw(ctx, t)
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    rgb(ctx, (0.3, 0.5, 0.1), 0.25 * (1 - prog(t, 0.2, 1.0))); ctx.paint()   # flash of light
    ctx.restore()
    vignette(ctx, 0.6); grain(ctx, t); fade(ctx, t, d, 0.15, 0.15)


def s7(ctx, t, d):   # North or stay?
    z = 1 + 0.07 * t / d
    ctx.save(); ctx.translate(W / 2, H * 0.55); ctx.scale(z, z); ctx.translate(-W / 2, -H * 0.55)
    HZ = 980
    green_sky(ctx, t, HZ)
    draw_skyline(ctx, RUIN_FAR, HZ, hexc("#1d2a1a"))
    # signal tower on the horizon, blinking
    rgb(ctx, hexc("#0e150d")); ctx.set_line_width(5)
    ctx.move_to(700, HZ); ctx.line_to(725, 760); ctx.line_to(750, HZ); ctx.stroke()
    blink = (t % 1.2) < 0.25
    if blink:
        glow(ctx, 725, 755, 60, (1, 0.2, 0.15), 1.0)
    vgrad(ctx, HZ, H, [(0, hexc("#33402a")), (1, hexc("#0d110b"))])
    # road to the horizon
    rgb(ctx, hexc("#1b1d1a"))
    ctx.move_to(530, HZ); ctx.line_to(550, HZ); ctx.line_to(1000, H); ctx.line_to(80, H); ctx.close_path(); ctx.fill()
    rgb(ctx, (0.85, 0.8, 0.4), 0.6)
    for k in range(12):                   # dashes flowing toward horizon
        p = ((k / 12) + t * 0.05) % 1
        y = lerp(H, HZ, p ** 0.5)
        w = lerp(20, 2, p ** 0.5); h = lerp(70, 4, p ** 0.5)
        ctx.rectangle(540 - w / 2 + lerp(0, 0, p), y - h, w, h); ctx.fill()
    rgb(ctx, (0, 0, 0), 0.5); ctx.set_line_width(3)
    ctx.move_to(420, 1500); ctx.line_to(470, 1430); ctx.line_to(450, 1380); ctx.line_to(500, 1300); ctx.stroke()
    # signpost
    rgb(ctx, hexc("#3b2c20")); ctx.rectangle(860, 1060, 16, 320); ctx.fill()
    rgb(ctx, hexc("#d9c9a3")); ctx.move_to(800, 1080); ctx.line_to(990, 1080); ctx.line_to(1020, 1115)
    ctx.line_to(990, 1150); ctx.line_to(800, 1150); ctx.close_path(); ctx.fill()
    text(ctx, "NORTH 30", 900, 1115, 48, hexc("#2a2018"))
    # the choice: character from behind, looking left/right
    look = math.sin(t * 1.6) if t > 0.8 else 0
    person(ctx, 520, 1400, 470, mode="idle", face=1, back_view=True, head_turn=look * 1.2,
           breathe=math.sin(t * 2.2))
    ctx.restore()
    Particles(90, 21, (0, 0, W, H), vel=(220, 10), size=(1.5, 3.5), col=(0.85, 0.95, 0.7), alpha=0.35).draw(ctx, t)
    vignette(ctx, 0.65); grain(ctx, t); fade(ctx, t, d, 0.15, 0.4)


SCENES = [s1, s2, s3, s4, s5, s6, s7]


# ---------------------------------------------------------------- sound design
def sfx(i, d):
    t = np.arange(int(d * SR)) / SR
    bed = drone(d, 49 if i < 5 else 55, seed=i) * 0.35
    if i == 0:
        f = 700 + 420 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 2.4))
        siren = (tone(d, f) * 0.6 + tone(d, f * 2) * 0.15) * 0.45
        steps = env_at(d, [k * math.pi / 13 for k in range(int(d * 13 / math.pi))], 0.09) * tone(d, 70) * 0.7
        x = bed + siren + steps
    elif i == 1:
        clicks = env_at(d, [k * 2 * math.pi / 3.2 + 0.3 for k in range(int(d * 3.2 / 6.28) + 1)], 0.05)
        x = bed + band_noise(d, 2500, 7000, 3) * clicks * 0.4 + tone(d, 120) * 0.04
    elif i == 2:
        crackle = 0.6 + 0.4 * np.sin(2 * np.pi * 7 * t) * np.sin(2 * np.pi * 0.7 * t)
        x = bed + band_noise(d, 900, 6500, 4) * crackle * 0.22
    elif i == 3:
        bangs = env_at(d, BANGS, 0.35) * tone(d, 55) * 1.0 + env_at(d, BANGS, 0.08) * band_noise(d, 80, 900, 5) * 0.7
        scr_env = (np.sin(2 * np.pi * 3.1 * t) > 0.2).astype(np.float32) * (np.sin(2 * np.pi * 0.4 * t) > -0.3)
        scratch = band_noise(d, 2500, 9000, 6) * scr_env * 0.22
        heart = env_at(d, [k / 1.6 for k in range(int(d * 1.6) + 1)], 0.12) * tone(d, 45) * 0.5
        x = bed + bangs + scratch + heart
    elif i == 4:
        stat = band_noise(d, 900, 6500, 7) * 0.2 * (1 - np.clip((t - 0.6) / 0.4, 0, 1)) + 0.03 * band_noise(d, 900, 6500, 8)
        beep = env_at(d, [0.6], 0.5) * tone(d, 880) * 0.3
        swell = (tone(d, 220) + tone(d, 277.2) * 0.7 + tone(d, 329.6) * 0.6) * np.clip((t - 0.7) / 2, 0, 1) * 0.12
        x = bed + stat + beep + swell
    elif i == 5:
        wind = band_noise(d, 120, 900, 9) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.3 * t)) * 0.35
        creak = tone(d, 160 - 60 * np.clip(t / 0.9, 0, 1), "saw") * ((t > 0.2) & (t < 0.9)) * 0.12
        thud = env_at(d, [0.9], 0.4) * tone(d, 50) * 0.9
        pad = (tone(d, 196) + tone(d, 233) * 0.6) * np.clip((t - 1) / 2, 0, 1) * 0.08
        x = bed + wind + creak + thud + pad
    else:
        wind = band_noise(d, 150, 1200, 10) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t)) * 0.35
        beeps = env_at(d, [k * 1.2 for k in range(int(d / 1.2) + 1)], 0.2) * tone(d, 1320) * 0.08
        pad = (tone(d, 174.6) + tone(d, 220) * 0.6 + tone(d, 261.6) * 0.5) * 0.06
        x = bed + wind + beeps + pad
    return fades(x * 0.6, 0.05, 0.15)


def job(i):
    wav = ROOT / "out" / SID / f"scene_{i + 1:02d}.wav"
    d = sf.info(str(wav)).duration + 0.3
    outdir = ROOT / "assets" / "clips" / SID
    outdir.mkdir(parents=True, exist_ok=True)
    save_wav(outdir / f"scene_{i + 1:02d}.sfx.wav", sfx(i, d))
    render(SCENES[i], d, outdir / f"scene_{i + 1:02d}.mp4")
    return f"scene {i + 1} ({d:.1f}s)"


if __name__ == "__main__":
    only = [int(a) - 1 for a in sys.argv[1:]] or range(len(SCENES))
    with Pool(4) as p:
        for r in p.imap_unordered(job, only):
            print("  rendered", r, flush=True)
