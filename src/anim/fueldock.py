"""Zombie Outbreak Day 3: The Fuel Dock - Kai, Tess, Walt and Dana, Parts 1-3 (stories/41-43). Fast format.

    python src/anim/fueldock.py <part 1|2|3> [scene numbers]

Sets: the marina fuel dock at night (floating dock, pumps, pier, town across the water), the siphon,
the pier and ramp from the side, the generator shed, the marina office window.
"""
import json, math, pathlib, random, sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import *  # noqa
from cinema import camera, fog, god_rays, soft_shadow, backlight, shot_card
from lighthouse import end_card, finish, wind
from nightshift import rule_card
from story import Timing, run, ROOT
from rig import Character, lipsync
from cast import KAI
import boardwalk as B
from boardwalk import TESS, sky, ocean, zombie, close, shirt_insert, surf, moans, flipflop
from rescueboat import FISH, big, knocks

SIDS = {1: "41_dock_1", 2: "42_dock_2", 3: "43_dock_3"}
T1, T2, T3 = (Timing(SIDS[k]) for k in (1, 2, 3))
TM = {1: T1, 2: T2, 3: T3}
sys.path.insert(0, str(ROOT / "src"))
from voice import phrases, speaker  # noqa: E402

DANA = Character("Dana", skin="#b98562", hair="#1c1410", hair_style="bun", top="#2f9c95", pants="#2f9c95", footwear="shoes",
                 shoes="#f2f2f2", face_shape="oval", seed=45.0)
K = dict(lost_shoe=True)
DECK_Y = 1420
VO = {}


def talk(part, i, who, t):
    """Mouth openness for the phrases of scene i spoken by `who` (lip-sync from the scene audio)."""
    key = (part, i, who)
    if key not in VO:
        st = json.loads((ROOT / "stories" / f"{SIDS[part]}.json").read_text())
        ps = phrases(st["scenes"][i - 1]["narration"]); seg = TM[part].seg.get(i, [])
        wins = [(seg[k][1], seg[k][2]) for k, p in enumerate(ps) if speaker(p) == who and k < len(seg)]
        f = lipsync(ROOT / "out" / SIDS[part] / f"scene_{i:02d}.wav")
        VO[key] = lambda t, f=f, wins=wins: f(t) if any(a <= t < b for a, b in wins) else 0.0
    return VO[key](t)


# ------------------------------------------------------------------ sets
def town(ctx, t, y=900, heads=0.0):
    """The town across the water: dark roofs, a few windows, and (heads) the infected on the shore."""
    rgb(ctx, hexc("#0c1220"))
    for k in range(14):
        r = random.Random(k + 5); x = k * 85 - 40; h = r.uniform(60, 190)
        ctx.rectangle(x, y - h, 80, h); ctx.fill()
        if r.random() < 0.3:
            rgb(ctx, (1, 0.8, 0.45), 0.7); ctx.rectangle(x + 25, y - h + 25, 14, 18); ctx.fill(); rgb(ctx, hexc("#0c1220"))
    if heads > 0:
        for k in range(40):
            r = random.Random(k + 90); x = r.uniform(0, W)
            rgb(ctx, (0.56, 0.65, 0.54), heads); ctx.arc(x, y - 6 + r.uniform(0, 8), 6, 0, 6.283); ctx.fill()


def lamp(ctx, x, y, h=520, on=0.0):
    rgb(ctx, hexc("#2a2f38")); ctx.rectangle(x - 7, y - h, 14, h); ctx.fill()
    if on > 0:
        ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD); glow(ctx, x, y - h, 420, (1, 0.9, 0.65), 0.55 * on); ctx.restore()
    rgb(ctx, (1, 0.95, 0.75) if on > 0.5 else (0.3, 0.32, 0.36)); ctx.arc(x, y - h, 24, 0, 6.283); ctx.fill()


def pump(ctx, x, y, s=1.0, on=0.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rgb(ctx, hexc("#b3382c")); rrect(ctx, -90, -420, 180, 420, 24); ctx.fill()
    rgb(ctx, hexc("#12161c")); rrect(ctx, -65, -380, 130, 110, 10); ctx.fill()
    if on > 0:
        rgb(ctx, (0.5, 1, 0.6), on); ctx.rectangle(-50, -350, 100, 40); ctx.fill()
    rgb(ctx, hexc("#1c1c1c")); ctx.set_line_width(14); ctx.move_to(90, -300); ctx.curve_to(170, -300, 170, -120, 100, -140); ctx.stroke()
    ctx.restore()


def dock(ctx, t, lights=0.0, heads=0.0, pumps=True, horizon=880):
    """On the floating fuel dock at night, looking across the water to the town."""
    sky(ctx, "night", horizon + 20)
    town(ctx, t, horizon, heads)
    ocean(ctx, t, horizon, night=True, y1=DECK_Y + 30)
    vgrad(ctx, DECK_Y, H + 300, [(0, hexc("#4a4034")), (1, hexc("#2a241c"))], x=-200, w=W + 400)
    rgb(ctx, (0, 0, 0), 0.25); ctx.set_line_width(4)
    for k in range(10):
        ctx.move_to(-200, DECK_Y + 30 + k * k * 6); ctx.line_to(W + 200, DECK_Y + 30 + k * k * 6); ctx.stroke()
    for x in (90, 990):
        lamp(ctx, x, DECK_Y + 20, 560, lights)
    if pumps:
        pump(ctx, 250, DECK_Y + 40, 1.0, lights); pump(ctx, 830, DECK_Y + 40, 1.0, lights)
    if lights > 0:
        rgb(ctx, (1, 0.9, 0.6), 0.10 * lights); ctx.paint()
    else:
        rgb(ctx, (0.02, 0.04, 0.10), 0.18); ctx.paint()


def fuel_can(ctx, x, y, s=1.0, wrapped=False):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rgb(ctx, hexc("#e8b72e") if wrapped else hexc("#c43a2a")); rrect(ctx, -90, -220, 180, 220, 24); ctx.fill()
    if not wrapped:
        rgb(ctx, hexc("#8a2a1e")); rrect(ctx, -40, -260, 80, 50, 10); ctx.fill(); rgb(ctx, hexc("#1c1c1c")); ctx.rectangle(30, -285, 40, 40); ctx.fill()
    ctx.restore()


def fishing_boat(ctx, t, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y + 6 * math.sin(t * 1.4)); ctx.scale(s, s)
    rgb(ctx, hexc("#d8d2c0")); rrect(ctx, -40, -260, 220, 160, 16); ctx.fill()
    rgb(ctx, hexc("#12161c")); rrect(ctx, -15, -235, 170, 60, 10); ctx.fill()
    rgb(ctx, hexc("#2f5a3c")); ctx.move_to(-380, -110); ctx.line_to(340, -110); ctx.line_to(280, 30); ctx.line_to(-300, 30); ctx.close_path(); ctx.fill()
    rgb(ctx, hexc("#e8e2d0")); ctx.rectangle(-372, -110, 706, 18); ctx.fill()
    ctx.restore()


def siphon(ctx, t, flow=0.0, thumb=False, down=1.0):
    """Cut-away: fuel tank (high, left) -> hose -> can (low, right)."""
    rgb(ctx, hexc("#141a26")); ctx.paint()
    rgb(ctx, hexc("#3a4250")); rrect(ctx, 80, 420, 420, 520, 30); ctx.fill()                          # tank
    rgb(ctx, hexc("#c98a2a")); rrect(ctx, 100, 560, 380, 360, 20); ctx.fill()
    cy = lerp(700, 1500, down)                                                                       # can goes lower than the tank
    fuel_can(ctx, 800, cy, 1.3)
    rgb(ctx, hexc("#d9d2b0")); ctx.set_line_width(26); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(300, 860); ctx.curve_to(300, 250, 800, 250, 800, cy - 300); ctx.stroke()
    if flow > 0:
        rgb(ctx, hexc("#c98a2a"), 0.95); ctx.set_line_width(14); ctx.set_dash([40, 30], -t * 260)
        ctx.move_to(300, 860); ctx.curve_to(300, 250, 800, 250, 800, cy - 300); ctx.stroke(); ctx.set_dash([])
    if thumb:
        rgb(ctx, hexc(KAI.skin)); ctx.arc(800, cy - 300, 36, 0, 6.283); ctx.fill()
    rgb(ctx, (1, 1, 1), 0.7); ctx.set_line_width(6)
    for k in range(3):
        y = 1000 + ((t * 160 + k * 120) % 360)
        ctx.move_to(990, y); ctx.line_to(1010, y + 30); ctx.line_to(1030, y); ctx.stroke()


def pier_side(ctx, t, n=8, advance=0.0, pins=2, ramp_down=0.0, lights=1.0, falling=0, office=True, office_lit=1.0):
    """Side view: the long pier (left) -> ramp -> the floating fuel dock (right)."""
    ctx.save(); ctx.translate(0, 230)
    _pier_side(ctx, t, n, advance, pins, ramp_down, lights, falling, office, office_lit)
    ctx.restore()


def _pier_side(ctx, t, n, advance, pins, ramp_down, lights, falling, office, office_lit):
    sky(ctx, "night", 1000)
    town(ctx, t, 980)
    if office:
        rgb(ctx, hexc("#1c2230")); ctx.rectangle(-20, 640, 260, 300); ctx.fill()
        rgb(ctx, (1, 0.85, 0.5), office_lit); ctx.rectangle(60, 720, 90, 90); ctx.fill()
        if office_lit > 0.3:
            rgb(ctx, (0.05, 0.05, 0.08)); ctx.arc(105, 765, 20, 0, 6.283); ctx.fill(); ctx.set_line_width(9)
            ctx.move_to(118, 775); ctx.line_to(140, 735 + 12 * math.sin(t * 8)); ctx.stroke()
    ocean(ctx, t, 1000, night=True)
    py = 1180
    rgb(ctx, hexc("#3a2f24"))
    for k in range(6):
        ctx.rectangle(40 + k * 120, py, 22, 420); ctx.fill()
    rgb(ctx, hexc("#5a4a38")); ctx.rectangle(-100, py - 26, 760, 30); ctx.fill()                       # pier deck
    for x in (150, 500):
        lamp(ctx, x, py - 20, 330, lights)
    ctx.save(); ctx.translate(660, py - 12); ctx.rotate(0.12 + 1.2 * ramp_down)                        # the ramp
    rgb(ctx, hexc("#7c838c")); ctx.rectangle(0, -10, 200, 20); ctx.fill(); ctx.restore()
    rgb(ctx, hexc("#4a4034")); rrect(ctx, 840, py + 10, 320, 60, 14); ctx.fill()                       # floating dock
    rgb(ctx, hexc("#2a5a8a")); rrect(ctx, 860, py + 60, 280, 40, 14); ctx.fill()
    pump(ctx, 1000, py + 14, 0.45, lights)
    for k in range(pins):
        rgb(ctx, hexc("#d8dde2")); ctx.rectangle(668 + k * 16, py - 40, 8, 44); ctx.fill()
    for k in range(n):                                                                               # the infected on the pier
        x = -60 + advance * 620 - k * 62
        if ramp_down > 0.5 and x > 640:
            continue
        if -80 < x < 660:
            zombie(ctx, k, x, py - 22, 250, t, face=1)
    for k in range(falling):                                                                         # walking off the end
        p = ((t * 0.9 + k * 0.37) % 1)
        ctx.save(); ctx.translate(680 + 60 * p, py - 20 + 420 * p * p); ctx.rotate(1.4 * p)
        zombie(ctx, k, 0, 0, 240, t, face=1); ctx.restore()
        if p > 0.75:
            rgb(ctx, (0.85, 0.93, 1.0), 0.8 * (1 - p) * 4); ctx.arc(740, py + 200, 40 + 120 * (p - 0.75) * 4, math.pi, 2 * math.pi); ctx.stroke()
    if lights > 0:
        rgb(ctx, (1, 0.9, 0.6), 0.07 * lights); ctx.paint()


def pin_close(ctx, t, out=0.0, rust=False, diesel=0.0, kick=0.0):
    rgb(ctx, hexc("#22262e")); ctx.paint()
    rgb(ctx, hexc("#7c838c")); ctx.rectangle(-100, 900, W + 200, 260); ctx.fill()                     # ramp plate
    rgb(ctx, hexc("#5a4a38")); ctx.rectangle(-100, 1160, W + 200, 800); ctx.fill()
    rgb(ctx, hexc("#3a4046")); rrect(ctx, 430, 860, 220, 340, 30); ctx.fill()                          # hinge block
    y = 760 - 520 * out + 14 * math.sin(t * 40) * kick
    rgb(ctx, hexc("#8a4a2a") if rust else hexc("#d8dde2")); rrect(ctx, 505, y, 70, 420, 24); ctx.fill(); ctx.arc(540, y, 62, 0, 6.283); ctx.fill()
    if rust:
        for k in range(14):
            r = random.Random(k); rgb(ctx, (0.35, 0.16, 0.08), 0.8); ctx.arc(505 + r.uniform(0, 70), y + r.uniform(0, 400), r.uniform(6, 16), 0, 6.283); ctx.fill()
    if diesel > 0:
        rgb(ctx, hexc("#c98a2a"), 0.9); ctx.set_line_width(18); ctx.move_to(820, 380); ctx.curve_to(760, 520, 600, 600, 560, y - 40 + 300 * diesel); ctx.stroke()
        fuel_can(ctx, 880, 520, 1.0)


def shed(ctx, t, running=1.0, plug=0.0):
    """The generator shed wall with the air intake grille."""
    vgrad(ctx, -300, H + 300, [(0, hexc("#2c3340")), (1, hexc("#161a22"))])
    sh = 6 * running * math.sin(t * 60)
    rgb(ctx, hexc("#3f6b4a")); rrect(ctx, 140 + sh, 560, 800, 760, 40); ctx.fill()
    rgb(ctx, hexc("#10141a")); rrect(ctx, 360 + sh, 760, 360, 300, 20); ctx.fill()                     # intake
    rgb(ctx, hexc("#5a6470"))
    for k in range(6):
        ctx.rectangle(360 + sh, 780 + k * 48, 360, 16); ctx.fill()
    if running > 0:                                                                                  # exhaust puffs + air being sucked in
        for k in range(5):
            p = (t * 1.2 + k * 0.2) % 1
            rgb(ctx, (0.6, 0.6, 0.62), 0.5 * (1 - p) * running); ctx.arc(860 + 60 * p, 540 - 300 * p, 30 + 60 * p, 0, 6.283); ctx.fill()
            rgb(ctx, (0.8, 0.9, 1.0), 0.5 * running); ctx.set_line_width(5)
            x = 150 + 180 * p; ctx.move_to(x, 860 + k * 30); ctx.line_to(x + 60, 880 + k * 16); ctx.stroke()
    if plug > 0:
        flipflop(ctx, lerp(-100, 540, plug), 910, 0.2, 1.0, 2.2)


def office(ctx, t, lit=1.0, wave=True):
    vgrad(ctx, -300, H + 300, [(0, hexc("#1a2030")), (1, hexc("#0e121a"))])
    rgb(ctx, hexc("#2a3344")); ctx.rectangle(-100, 300, W + 200, 1300); ctx.fill()
    if lit > 0:
        rgb(ctx, (1, 0.85, 0.5), lit)
    else:
        rgb(ctx, hexc("#0a0d14"))
    rrect(ctx, 240, 520, 600, 700, 20); ctx.fill()
    if lit > 0:
        ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD); glow(ctx, 540, 870, 800, (1, 0.8, 0.5), 0.35 * lit); ctx.restore()
    rgb(ctx, (0.04, 0.05, 0.08))
    ctx.arc(540, 800, 90, 0, 6.283); ctx.fill(); rrect(ctx, 420, 880, 240, 340, 60); ctx.fill()
    if wave:
        ctx.set_line_width(46); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.move_to(640, 950); ctx.line_to(760, 700 + 50 * math.sin(t * 8)); ctx.stroke()
    rgb(ctx, hexc("#1a2030")); ctx.set_line_width(22); rrect(ctx, 240, 520, 600, 700, 20); ctx.stroke()
    ctx.move_to(540, 520); ctx.line_to(540, 1220); ctx.stroke()
    text(ctx, "MARINA OFFICE", 540, 420, 70, (0.75, 0.8, 0.9))


def dinghy(ctx, t, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y + 6 * math.sin(t * 1.5)); ctx.scale(s, s)
    for ch, dx, f in ((TESS, -110, 1), (KAI, 110, -1)):
        ch.draw(ctx, dx, 20, 420, t, mode="sit", face=f, expr="determined", look=(f, 0.2), arm_f=(0.9 + 0.4 * math.sin(t * 2.2), 0.5), **(K if ch is KAI else {}))
    rgb(ctx, hexc("#d8d2c0")); ctx.move_to(-300, -40); ctx.line_to(300, -40); ctx.line_to(230, 70); ctx.line_to(-230, 70); ctx.close_path(); ctx.fill()
    rgb(ctx, hexc("#5a4a38")); ctx.set_line_width(14); a = 0.5 * math.sin(t * 2.2)
    ctx.move_to(0, -30); ctx.line_to(240 * math.cos(a) + 60, 150 + 60 * math.sin(a)); ctx.stroke()
    rgb(ctx, hexc("#b9b2a0")); ctx.arc(240 * math.cos(a) + 60, 150 + 60 * math.sin(a), 30, 0, 6.283); ctx.fill()        # rag-wrapped oar blade
    ctx.restore()


# ------------------------------------------------------------------ PART 1
def p1s1(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.6, focus=(540, 1100)):
        dock(ctx, t, 0.0)
        for k in range(4):                                             # sound rings rolling out over the water
            p = (t * 0.5 + k * 0.25) % 1
            rgb(ctx, (1, 1, 1), 0.5 * (1 - p)); ctx.set_line_width(6)
            ctx.save(); ctx.translate(250, 1200); ctx.scale(1, 0.35); ctx.arc(0, 0, 80 + 900 * p, math.pi, 2 * math.pi); ctx.restore(); ctx.stroke()
    shot_card(ctx, t, text, "DON'T START THE PUMP", 0.0, y=330, size=96)
    finish(ctx, t, d, fi=0.0)


def p1s2(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(540, 1100)):
        sky(ctx, "night", 900); town(ctx, t, 880); ocean(ctx, t, 880, night=True)
        rgb(ctx, hexc("#4a4034")); rrect(ctx, 520, 1330, 700, 70, 14); ctx.fill()
        pump(ctx, 820, 1335, 0.7)
        fishing_boat(ctx, t, lerp(-300, 330, ease_out(prog(t, 0, d))), 1420, 0.9)
    day_stamp(ctx, t, "DAY 3 - MIDNIGHT", 0.2)
    finish(ctx, t, d)


def p1s3(ctx, t, d):
    with camera(ctx, t, d, push=0.05, handheld=0.3, focus=(540, 1000), pan=(-100, 0)):
        dock(ctx, t, 0.0)
    big(ctx, "2 PUMPS", t, T1.at(3, 1)); big(ctx, "400 YARDS TO TOWN", t, T1.at(3, 2), y=470, size=96, col=(1, 0.8, 0.4))
    finish(ctx, t, d)


def p1s4(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 800)):
        dock(ctx, t, 0.0, pumps=False)
        close(FISH, ctx, 540, 880, 260, t, face=0, expr="tired", talk=talk(1, 4, "man", t), look=(0, 0.3))
    finish(ctx, t, d)


def p1s5(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1000)):
        shed(ctx, t, running=0.0)
        rgb(ctx, (0, 0, 0), 0.35); ctx.paint()
    for k, w in enumerate(("PUMP", "= GENERATOR", "= NOISE")):
        text(ctx, w, 540, 380 + k * 130, 110, (1, 1, 1) if k < 2 else (1, 0.5, 0.4), prog(t, T1.at(5, k), T1.at(5, k) + 0.15), outline=10)
    finish(ctx, t, d)


def p1s6(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 800)):
        dock(ctx, t, 0.0, pumps=False)
        close(KAI, ctx, 540, 880, 250, t, face=0, expr="determined", talk=talk(1, 6, "kai", t), **K)
    finish(ctx, t, d)


def p1s7(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1200)):
        dock(ctx, t, 0.0)
        h = KAI.draw(ctx, 520, DECK_Y + 320, 860, t, face=1, expr="happy", look=(1, 0.5), arm_f=(1.3, 0.5), **K)
        rgb(ctx, hexc("#d9d2b0")); ctx.set_line_width(22); ctx.arc(h["hand"][0] + 30, h["hand"][1] + 60, 70, 0, 6.283); ctx.stroke()
        fuel_can(ctx, 820, DECK_Y + 330, 1.1)
    finish(ctx, t, d)


def p1s8(ctx, t, d):
    with camera(ctx, t, d, push=0.03, handheld=0.2):
        siphon(ctx, t, flow=prog(t, T1.at(8, 3), T1.at(8, 3) + 0.3), down=ease(prog(t, T1.at(8, 2), T1.at(8, 2) + 0.6)))
    big(ctx, "NO POWER NEEDED", t, T1.at(8, 0) + 0.3, y=220, size=90)
    big(ctx, "CAN LOWER THAN TANK", t, T1.at(8, 2), y=1750, size=84, col=(1, 0.8, 0.4))
    finish(ctx, t, d)


def p1s9(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(540, 800), shake=0.3 if t < 0.3 else 0):
        dock(ctx, t, 0.0, pumps=False)
        close(TESS, ctx, 540, 880, 250, t, face=1, expr="angry", talk=talk(1, 9, "tess", t), look=(1, 0), arm_f=(1.5, 0.1))
    big(ctx, "NEVER BY MOUTH", t, T1.at(9, 1), y=1650, size=100, col=(1, 0.5, 0.4))
    finish(ctx, t, d)


def p1s10(ctx, t, d):
    with camera(ctx, t, d, push=0.03, handheld=0.2):
        siphon(ctx, t, flow=prog(t, T1.at(10, 0) + 2.0, d), thumb=t < T1.at(10, 0) + 2.0, down=ease(prog(t, 1.0, 2.0)))
    finish(ctx, t, d)


def p1s11(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.2, focus=(800, 1300)):
        siphon(ctx, t, flow=1.0, down=1.0)
    finish(ctx, t, d)


def p1s12(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1200)):
        dock(ctx, t, 0.0, pumps=False)
        TESS.draw(ctx, 400, DECK_Y + 320, 820, t, mode="idle", crouch=0.35, face=1, expr="determined", look=(1, 0.8), arm_f=(1.0, 0.6))
        fuel_can(ctx, 700, DECK_Y + 330, 1.2, wrapped=prog(t, 0.5, 1.0) > 0.5)
    finish(ctx, t, d)


def p1s13(ctx, t, d):
    lvl = lerp(0.25, 0.8, prog(t, 0, d))
    with camera(ctx, t, d, push=0.08, handheld=0.2, focus=(540, 900)):
        rgb(ctx, hexc("#141a26")); ctx.paint()
        rgb(ctx, hexc("#e9e6dd")); ctx.arc(540, 1000, 380, math.pi, 2 * math.pi); ctx.fill()
        rgb(ctx, hexc("#2a2a30")); ctx.set_line_width(22); ctx.arc(540, 1000, 380, math.pi, 2 * math.pi); ctx.stroke()
        text(ctx, "E", 240, 960, 90, (0.8, 0.2, 0.2)); text(ctx, "F", 840, 960, 90, (0.1, 0.1, 0.1))
        a = math.pi * (1 - lvl); rgb(ctx, (0.8, 0.2, 0.2)); ctx.set_line_width(16); ctx.move_to(540, 1000); ctx.line_to(540 + math.cos(a) * 300, 1000 - math.sin(a) * 300); ctx.stroke()
        for k in range(4):
            if t > T1.at(13, 0) + k * 0.35:
                fuel_can(ctx, 210 + k * 220, 1560, 0.8)
    finish(ctx, t, d)


def p1s14(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 800)):
        dock(ctx, t, 0.0, pumps=False)
        close(KAI, ctx, 540, 880, 250, t, face=0, expr="happy", talk=talk(1, 14, "kai", t), **K)
    finish(ctx, t, d)


def p1s15(ctx, t, d):
    on = 1.0 if t > 0.5 else 0.0
    with camera(ctx, t, d, push=0.06, handheld=0.4, focus=(540, 1000), shake=0.5 if 0.5 < t < 0.9 else 0):
        dock(ctx, t, on)
        KAI.draw(ctx, 440, DECK_Y + 300, 700, t, face=0, expr="happy", expr_to="shock", expr_k=on, look=(0, -1), **K)
        TESS.draw(ctx, 660, DECK_Y + 300, 640, t, face=0, expr="shock" if on else "neutral", look=(0, -1))
    finish(ctx, t, d)


def p1s16(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(540, 1000), shake=0.1):
        shed(ctx, t, running=1.0)
    finish(ctx, t, d)


def p1s17(ctx, t, d):
    with camera(ctx, t, d, push=0.20, handheld=0.3, focus=(540, 880)):
        dock(ctx, t, 1.0, heads=prog(t, T1.at(17, 1), d), pumps=False)
    big(ctx, "EVERY HEAD TURNED", t, T1.at(17, -1), y=400, size=100, col=(1, 0.5, 0.4))
    finish(ctx, t, d)


def p1s18(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 1300)):
        pier_side(ctx, t, n=8, advance=0.2 + 0.1 * t)
        rgb(ctx, (0, 0, 0), 0.5); ctx.paint()
    end_card(ctx, t, T1, 18, "STAY", "OR GO?", "COMMENT: STAY OR GO", "PART 2 NEXT")
    finish(ctx, t, d, fo=0.3)


# ------------------------------------------------------------------ PART 2
def p2s1(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.7, focus=(540, 1100)):
        pier_side(ctx, t, n=9, advance=0.15 + 0.25 * prog(t, 0, d))
    shot_card(ctx, t, text, "STAY OR GO?", 0.0, y=330, size=140)
    finish(ctx, t, d, fi=0.0)


def p2s2(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(540, 800)):
        dock(ctx, t, 1.0, pumps=False)
        close(FISH, ctx, 540, 880, 260, t, face=0, expr="angry", talk=talk(2, 2, "man", t), look=(-0.6, 0))
    finish(ctx, t, d)


def p2s3(ctx, t, d):
    with camera(ctx, t, d, push=0.14, handheld=0.3, focus=(540, 870)):
        office(ctx, t)
    finish(ctx, t, d)


def p2s4(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(540, 800)):
        dock(ctx, t, 1.0, pumps=False)
        close(TESS, ctx, 540, 880, 250, t, face=-1, expr="shock", talk=talk(2, 4, "tess", t), look=(-1, -0.2), arm_f=(1.6, 0.0))
    finish(ctx, t, d)


def p2s5(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.4, focus=(400, 1100)):
        pier_side(ctx, t, n=9, advance=0.35 + 0.1 * prog(t, 0, d))
    finish(ctx, t, d)


def p2s6(ctx, t, d):
    with camera(ctx, t, d, push=0.14, handheld=0.5, focus=(540, 1100)):
        sky(ctx, "night", 900); rgb(ctx, hexc("#5a4a38")); ctx.rectangle(-100, 1500, W + 200, 600); ctx.fill()
        for row in range(2):
            for k in range(6):
                zombie(ctx, k + row * 6, 60 + k * 190 + row * 90, 1650 + row * 180, 560 + row * 120, t, face=1 if k % 2 else -1)
        rgb(ctx, (1, 0.9, 0.6), 0.08); ctx.paint()
    big(ctx, "60", t, 0.1, y=330, size=220, col=(1, 0.5, 0.4))
    finish(ctx, t, d)


def p2s7(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 900)):
        dock(ctx, t, 1.0, pumps=False)
        close(KAI, ctx, 540, 1000, 240, t, face=1, expr="confused", expr_to="determined", expr_k=prog(t, T2.at(7, 2), T2.at(7, 2) + 0.3),
              look=(1, 0) if t < T2.at(7, 1) else (0, 1), **K)
    big(ctx, "IT'S FLOATING", t, T2.at(7, 2), y=1680, size=110, col=(0.6, 1, 0.7))
    finish(ctx, t, d)


def p2s8(ctx, t, d):
    with camera(ctx, t, d, push=0.22, handheld=0.2, focus=(700, 1400)):
        pier_side(ctx, t, n=9, advance=0.5)
        rgb(ctx, (1, 0.9, 0.3)); ctx.set_line_width(5); ctx.arc(680, 1390, 46, 0, 6.283); ctx.stroke()
    big(ctx, "1 RAMP", t, T2.at(8, 0) + 0.8, y=330); big(ctx, "2 STEEL PINS", t, T2.at(8, 1), y=470, col=(1, 0.8, 0.4))
    finish(ctx, t, d)


def p2s9(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.5, focus=(540, 800), shake=0.2):
        dock(ctx, t, 1.0, pumps=False)
        close(KAI, ctx, 540, 880, 260, t, face=1, expr="shock", talk=talk(2, 9, "kai", t), look=(1, 0.5), arm_f=(1.4, 0.4), **K)
    finish(ctx, t, d)


def p2s10(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 900)):
        pin_close(ctx, t, out=ease(prog(t, 0.3, 1.0)))
    finish(ctx, t, d)


def p2s11(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.5, focus=(540, 900)):
        pin_close(ctx, t, out=0.03 * abs(math.sin(t * 6)), rust=True, kick=0.6)
    big(ctx, "RUSTED SOLID", t, 0.3, y=330, size=110, col=(1, 0.5, 0.4))
    finish(ctx, t, d)


def p2s12(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.6, focus=(560, 1100), shake=0.15):
        pier_side(ctx, t, n=9, advance=0.62 + 0.22 * prog(t, 0, d), pins=1)
    text(ctx, "20 YARDS" if t < T2.at(12, 1) else "10", 540, 400, 150, (1, 0.5, 0.4), 1, outline=12)
    finish(ctx, t, d)


def p2s13(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 800)):
        pin_close(ctx, t, rust=True, diesel=prog(t, 0.3, 1.2))
    big(ctx, "DIESEL LOOSENS RUST", t, T2.at(13, 1), y=1700, size=88, col=(1, 0.8, 0.4))
    finish(ctx, t, d)


def p2s14(ctx, t, d):
    k1, k2 = T2.at(14, 1), T2.at(14, 2)
    with camera(ctx, t, d, push=0.06, handheld=0.5, focus=(700, 1150), shake=0.6 if 0 < t - k1 < 0.3 or 0 < t - k2 < 0.3 else 0):
        if t < k1:
            pin_close(ctx, t, rust=True, kick=1.0, out=0.05)
        elif t < k2:
            pin_close(ctx, t, rust=True, out=prog(t, k1, k1 + 0.25) * 1.6)
        else:
            pier_side(ctx, t, n=9, advance=0.86, pins=0, ramp_down=ease_out(prog(t, k2, k2 + 0.4)))
    finish(ctx, t, d)


def p2s15(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(680, 1200)):
        pier_side(ctx, t, n=9, advance=0.95, pins=0, ramp_down=1.0, falling=2)
    finish(ctx, t, d)


def p2s16(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(720, 1350)):
        pier_side(ctx, t, n=9, advance=1.0, pins=0, ramp_down=1.0, falling=4)
    big(ctx, "THEY CAN'T SWIM", t, T2.at(16, -1), y=330, size=100)
    finish(ctx, t, d)


def p2s17(ctx, t, d):
    with camera(ctx, t, d, push=0.14, handheld=0.3, focus=(300, 1230)):
        pier_side(ctx, t, n=9, advance=1.0, pins=0, ramp_down=1.0, falling=1)
        rgb(ctx, (1, 0.9, 0.3)); ctx.set_line_width(6); ctx.arc(105, 995, 90, 0, 6.283); ctx.stroke()
    finish(ctx, t, d)


def p2s18(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 870)):
        office(ctx, t)
        rgb(ctx, (0, 0, 0), 0.5); ctx.paint()
    end_card(ctx, t, T2, 18, "GO", "BACK?", "COMMENT: YES OR NO", "PART 3 NEXT")
    finish(ctx, t, d, fo=0.3)


# ------------------------------------------------------------------ PART 3
def p3s1(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.6, focus=(540, 870)):
        if t < T3.at(1, 1):
            office(ctx, t)
        else:
            pier_side(ctx, t, n=9, advance=1.0, pins=0, ramp_down=1.0, falling=2)
    shot_card(ctx, t, text, "GO BACK?", 0.0, y=330, size=150)
    finish(ctx, t, d, fi=0.0)


def p3s2(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(540, 800)):
        dock(ctx, t, 1.0, pumps=False)
        close(FISH, ctx, 540, 880, 260, t, face=0, expr="determined", talk=talk(3, 2, "man", t), arm_f=(1.4, 0.4))
    finish(ctx, t, d)


def p3s3(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 800)):
        dock(ctx, t, 1.0, pumps=False)
        close(TESS, ctx, 540, 880, 260, t, face=0, expr="angry", talk=talk(3, 3, "tess", t))
    finish(ctx, t, d)


def p3s4(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 950), shake=0.08):
        shed(ctx, t, running=1.0)
    finish(ctx, t, d)


def p3s5(ctx, t, d):
    with camera(ctx, t, d, push=0.20, handheld=0.2, focus=(540, 910), shake=0.06):
        shed(ctx, t, running=1.0)
        rgb(ctx, (1, 0.9, 0.3)); ctx.set_line_width(7); rrect(ctx, 340, 740, 400, 340, 30); ctx.stroke()
    big(ctx, "IT HAS TO BREATHE", t, T3.at(5, 1), y=330, size=100)
    finish(ctx, t, d)


def p3s6(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.2):
        shed(ctx, t, running=1.0)
        rgb(ctx, (0, 0, 0), 0.45); ctx.paint()
    rule_card(ctx, t, 0.15, [("BLOCK THE AIR INTAKE", T3.at(6, 0) + 0.2), ("IT DIES IN SECONDS", T3.at(6, 1))], title="ANY ENGINE")
    finish(ctx, t, d)


def p3s7(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(540, 1200)):
        sky(ctx, "night", 900); town(ctx, t, 880); ocean(ctx, t, 880, night=True)
        dinghy(ctx, t, lerp(250, 760, prog(t, 0, d)), 1300, 1.2)
        rgb(ctx, (1, 0.9, 0.6), 0.06); ctx.paint()
    big(ctx, "OARS WRAPPED IN RAGS", t, T3.at(7, 1), y=330, size=88)
    finish(ctx, t, d)


def p3s8(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 910), shake=0.06):
        shed(ctx, t, running=1.0, plug=ease(prog(t, 0.5, 1.4)))
    finish(ctx, t, d)


def p3s9(ctx, t, d):
    run_ = 1.0 - prog(t, T3.at(9, 0), T3.at(9, 2))
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 910), shake=0.4 * run_ * abs(math.sin(t * 9))):
        shed(ctx, t, running=run_ * (0.4 + 0.6 * abs(math.sin(t * 7))), plug=1.0)
    finish(ctx, t, d)


def p3s10(ctx, t, d):
    off = prog(t, 0.2, 0.4)
    with camera(ctx, t, d, push=0.05, handheld=0.2, focus=(540, 1000)):
        dock(ctx, t, 1.0 - off)
        rgb(ctx, (0, 0, 0.03), 0.45 * off); ctx.paint()
    finish(ctx, t, d)


def p3s11(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.2, focus=(400, 1100)):
        pier_side(ctx, 0.37, n=9, advance=1.0, pins=0, ramp_down=1.0, lights=0.0, office_lit=0.0)     # frozen: nothing to follow
        rgb(ctx, (0.02, 0.04, 0.1), 0.25); ctx.paint()
    for k, w in enumerate(("NO SOUND", "NO LIGHT")):
        text(ctx, w, 540, 380 + k * 140, 120, (1, 1, 1), prog(t, T3.at(11, 1 + k), T3.at(11, 1 + k) + 0.15), outline=11)
    finish(ctx, t, d)


def p3s12(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 800)):
        shed(ctx, t, running=0.0, plug=1.0); rgb(ctx, (0, 0, 0.04), 0.4); ctx.paint()
        close(KAI, ctx, 540, 900, 250, t, face=0, expr="happy", talk=talk(3, 12, "kai", t), dirt=0.5, **K)
    finish(ctx, t, d)


def p3s13(ctx, t, d):
    out = ease(prog(t, T3.at(13, 1), d))
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1000)):
        office(ctx, t, lit=0.0, wave=False)
        DANA.draw(ctx, lerp(540, 620, out), lerp(1500, 1750, out), 900, t, face=1, expr="fear", expr_to="happy", expr_k=out, look=(1, 0.3), crouch=0.4 * (1 - out))
    finish(ctx, t, d)


def p3s14(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 800)):
        office(ctx, t, lit=0.0, wave=False); rgb(ctx, (0, 0, 0.04), 0.35); ctx.paint()
        close(DANA, ctx, 540, 900, 260, t, face=0, expr="tired", look=(0, 0.2))
    big(ctx, "A SIGNAL", t, T3.at(14, 1), y=1560); big(ctx, "ALONE FOR 2 DAYS", t, T3.at(14, 2), y=1690, size=96, col=(1, 0.8, 0.4))
    finish(ctx, t, d)


def p3s15(ctx, t, d):
    sh = T3.at(15, 2)
    if t < sh:
        with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1100)):
            dock(ctx, t, 0.0, pumps=False)
            soft_shadow(ctx, 540, 1755, 360)
            KAI.draw(ctx, 540, 1750, 1000, t, face=0, expr="tired", torn=0.6, dirt=1.0, lost_shoe=True)
    else:
        shirt_insert(ctx, t, sh)
    finish(ctx, t, d)


def p3s16(ctx, t, d):
    k = T3.at(16, 3)
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 900)):
        dock(ctx, t, 0.0, pumps=False)
        if t < T3.at(16, 1):
            close(DANA, ctx, 540, 900, 260, t, face=-1, expr="neutral", expr_to="shock", expr_k=prog(t, 0.6, 1.2), look=(-1, 0))
        elif t < k:
            close(TESS, ctx, 540, 900, 260, t, face=1, expr="confused", look=(1, 0))
        else:
            close(DANA, ctx, 540, 900, 280, t, face=-1, expr="shock", talk=talk(3, 16, "woman", t), look=(-1, 0))
    finish(ctx, t, d)


def p3s17(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 1000)):
        dock(ctx, t, 0.0, pumps=False)
        DANA.draw(ctx, 330, 1760, 900, t, face=1, expr="happy", talk=talk(3, 17, "woman", t), look=(1, 0), arm_f=(1.2, 0.5))
        TESS.draw(ctx, 760, 1760, 860, t, face=-1, expr="neutral", expr_to="shock", expr_k=prog(t, T3.at(17, 1), T3.at(17, 1) + 0.3), look=(-1, 0))
    big(ctx, "SHE'S ALIVE", t, T3.at(17, 1) + 0.4, y=330, size=130, col=(0.6, 1, 0.7))
    finish(ctx, t, d)


def p3s18(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 1300)):
        pier_side(ctx, t, n=9, advance=1.0, pins=0, ramp_down=1.0, lights=0.0, office_lit=0.0)
        rgb(ctx, (0, 0, 0), 0.5); ctx.paint()
    end_card(ctx, t, T3, 18, "GO", "BACK?", "COMMENT: YES OR NO", "DAY 4 TOMORROW")
    finish(ctx, t, d, fo=0.4)


P1 = [globals()[f"p1s{i}"] for i in range(1, 19)]
P2 = [globals()[f"p2s{i}"] for i in range(1, 19)]
P3 = [globals()[f"p3s{i}"] for i in range(1, 19)]


# ------------------------------------------------------------------ sound
def gen_hum(d, seed, amt=1.0):
    t = np.arange(int(d * SR)) / SR
    return (band_noise(d, 50, 260, seed) * (0.6 + 0.4 * np.sin(2 * np.pi * 28 * t)) * 0.30 + np.sin(2 * np.pi * 58 * t) * 0.05) * amt


def sfx_for(tm, part):
    def sfx(i, d):
        t = np.arange(int(d * SR)) / SR
        x = surf(d, 0.5, i + part * 50) + band_noise(d, 60, 250, i) * 0.02            # quiet water lapping at night
        if part == 1:
            if i in (10, 11, 13):
                x += band_noise(d, 300, 1800, i) * 0.035                              # fuel trickling
            if i == 15:
                x += env_at(d, [0.5], 0.5) * band_noise(d, 60, 2500, 15) * 0.9 + gen_hum(d, 15) * (t > 0.5)
            if i in (16, 17, 18):
                x += gen_hum(d, i) + (moans(d, list(np.arange(0.5, d, 1.3)), i) if i > 16 else 0)
        elif part == 2:
            x += gen_hum(d, i, 0.7)
            if i in (1, 5, 6, 12, 15, 16, 17):
                x += moans(d, list(np.arange(0.2, d, 1.0)), i) * 1.5
            if i == 11:
                x += knocks(d, list(np.arange(0.3, d, 0.5)), 11) * 0.8
            if i == 14:
                x += knocks(d, [tm.at(14, 1)], 14) * 1.5 + env_at(d, [tm.at(14, 2) + 0.3], 0.7) * band_noise(d, 200, 5000, 14) * 0.9
            if i in (15, 16):
                x += env_at(d, list(np.arange(0.6, d, 1.1)), 0.5) * band_noise(d, 300, 5000, i) * 0.5
        else:
            if i <= 8:
                x += gen_hum(d, i, 0.8 if i not in (4, 5, 8) else 1.3)
            if i == 9:
                k0, k2 = tm.at(9, 0), tm.at(9, 2)
                x += gen_hum(d, 9, 1.3) * np.clip(1 - (t - k0) / max(0.2, k2 - k0), 0, 1) * (0.5 + 0.5 * np.abs(np.sin(t * 22)))
            if i in (1,):
                x += moans(d, list(np.arange(0.3, d, 1.0)), i) * 1.4
            if i in (10, 11):
                x *= 0.35
        return fades(x * 0.6, 0.03, 0.1)
    return sfx


def music1(durs):
    total, a = sum(durs), sum(durs[:14])
    return np.concatenate([B.drone_score(a, 31) * 0.7, B.drone_score(total - a, 32)])[: int(total * SR)]


def music2(durs):
    return B.drone_score(sum(durs), 33)


def music3(durs):
    total, a = sum(durs), sum(durs[:11])
    return np.concatenate([B.drone_score(a, 34), piano_score(total - a, 999, bpm=70, seed=13)])[: int(total * SR)]


PARTS = {1: (SIDS[1], P1, sfx_for(T1, 1), music1), 2: (SIDS[2], P2, sfx_for(T2, 2), music2), 3: (SIDS[3], P3, sfx_for(T3, 3), music3)}

if __name__ == "__main__":
    run(PARTS, {1: T1, 2: T2, 3: T3})
