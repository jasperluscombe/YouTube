"""Zombie Outbreak Day 2: The Rescue Boat - Kai and Tess, Parts 1-3 (stories/38-40). Fast format.

    python src/anim/rescueboat.py <part 1|2|3> [scene numbers]

Sets: the coast guard boat (deck / from outside), the locked cabin door, the beach in the distance,
the anchor, people floating beside the boat, the fishing boat at sunset.
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
from gondola import radio
import boardwalk as B
from boardwalk import TESS, ZOMBIES, sky, ocean, sand, foam, zombie, close, underwater, shirt_insert, surf, moans

SIDS = {1: "38_boat_1", 2: "39_boat_2", 3: "40_boat_3"}
T1, T2, T3 = (Timing(SIDS[k]) for k in (1, 2, 3))
TM = {1: T1, 2: T2, 3: T3}
sys.path.insert(0, str(ROOT / "src"))
from voice import phrases, speaker  # noqa: E402

CAP = Character("Reyes", skin="#c99a72", hair="#2a2a2a", hair_style="cap", top="#e2622b", pants="#2b3140", footwear="shoes",
                shoes="#1c1c1c", face_shape="square", brows=1.1, seed=41.0)
DALE = Character("Dale", skin="#e2c2a6", hair="#6a5a48", hair_style="short", top="#7d8794", pants="#3a3f4a", footwear="shoes",
                 shoes="#2a2a2a", face_shape="oval", seed=42.0)
DALE_Z = Character("DaleZ", skin="#8fa58a", hair="#6a5a48", hair_style="short", top="#7d8794", pants="#3a3f4a", footwear="shoes",
                   shoes="#2a2a2a", face_shape="oval", eye_col="#f2f2ea", seed=42.0)
ENG = Character("Eng", skin="#8fa58a", hair="#1c1c1c", hair_style="buzz", top="#e2622b", pants="#2b3140", footwear="shoes",
                shoes="#1c1c1c", eye_col="#f2f2ea", seed=43.0)
FISH = Character("Fisher", age="elder", skin="#d9a982", hair="#d8d8d8", hair_style="cap", top="#3f6b4a", pants="#3b3b33", footwear="shoes",
                 shoes="#3a2a1a", face_shape="round", seed=44.0)
EXTRAS = [Character(f"S{k}", skin=sk, hair=hr, hair_style=hs, top=tp, pants="#3a3f4a", footwear="shoes", shoes="#2a2a2a", seed=60.0 + k)
          for k, (sk, hr, hs, tp) in enumerate((("#e8b896", "#3a2a20", "long", "#9a5a7a"), ("#a8775a", "#1c1410", "buzz", "#3d6a80"),
                                                ("#f0c8a8", "#b98a4e", "ponytail", "#6a994e"), ("#c99a72", "#2a1d14", "short", "#b0503a"),
                                                ("#e2b08a", "#5a3a22", "bun", "#5a5a8a")))]
K = dict(lost_shoe=True)                                 # Kai lost a flip-flop on Day 1
RAIN = Particles(260, 7, (0, 0, W, H), vel=(-80, 900), size=(1, 2.5), col=(0.8, 0.85, 0.95), alpha=0.5)
DECK_Y = 1420


def voice_of(part, i, who):
    """talk(t) for the phrases of scene i spoken by character `who` (lip-sync from the scene audio)."""
    st = json.loads((ROOT / "stories" / f"{SIDS[part]}.json").read_text())
    ps = phrases(st["scenes"][i - 1]["narration"])
    seg = TM[part].seg.get(i, [])
    wins = [(seg[k][1], seg[k][2]) for k, p in enumerate(ps) if speaker(p) == who and k < len(seg)]
    f = lipsync(ROOT / "out" / SIDS[part] / f"scene_{i:02d}.wav")
    return lambda t: f(t) if any(a <= t < b for a, b in wins) else 0.0


VO = {}


def talk(part, i, who, t):
    key = (part, i, who)
    if key not in VO:
        VO[key] = voice_of(part, i, who)
    return VO[key](t)


# ------------------------------------------------------------------ sets
def deck(ctx, t, mood="grey", rock=1.0, door=True, horizon=900, shore=0.0, door_open=0.0):
    """On the boat's deck looking across: sea behind a rail, cabin wall + door on the right."""
    ctx.save(); ctx.translate(540, 1200); ctx.rotate(0.012 * rock * math.sin(t * 1.1)); ctx.translate(-540, -1200)
    sky(ctx, mood, horizon + 20)
    ocean(ctx, t, horizon, night=mood == "night", y1=DECK_Y + 40)
    if shore > 0:                                                        # the beach on the horizon, growing
        h = 20 + 120 * shore
        rgb(ctx, hexc("#3a3a40" if mood == "night" else "#cbb07a")); ctx.rectangle(-200, horizon - h * 0.2, W + 400, h * 0.5); ctx.fill()
        for k in range(int(8 + 30 * shore)):
            r = random.Random(k); x = r.uniform(-100, W + 100); s = 16 + 60 * shore
            rgb(ctx, (0.25, 0.33, 0.28)); ctx.rectangle(x, horizon - h * 0.2 - s, s * 0.35, s); ctx.fill(); ctx.arc(x + s * 0.17, horizon - h * 0.2 - s, s * 0.2, 0, 6.283); ctx.fill()
    vgrad(ctx, DECK_Y, H + 300, [(0, hexc("#b9bec4")), (1, hexc("#7c838c"))], x=-200, w=W + 400)
    rgb(ctx, (0, 0, 0), 0.15); ctx.set_line_width(4)
    for k in range(10):
        ctx.move_to(-200, DECK_Y + 30 + k * k * 6); ctx.line_to(W + 200, DECK_Y + 30 + k * k * 6); ctx.stroke()
    rgb(ctx, hexc("#e8eef4")); ctx.rectangle(-200, DECK_Y - 220, W + 400, 14); ctx.fill()        # rail
    for k in range(8):
        ctx.rectangle(k * 170 - 40, DECK_Y - 220, 12, 230); ctx.fill()
    rgb(ctx, hexc("#e2622b")); ctx.rectangle(-200, DECK_Y - 12, W + 400, 22); ctx.fill()
    if door:
        cabin_door(ctx, t, 880, DECK_Y, 0.8, door_open)
    ctx.restore()


def cabin_door(ctx, t, x, y, s=1.0, opened=0.0, knock=(), hands=False, handle=0.0):
    """Cabin wall with a round-window door; base at (x, y)."""
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rgb(ctx, hexc("#dfe5ea")); ctx.rectangle(-330, -1250, 700, 1250); ctx.fill()
    rgb(ctx, hexc("#e2622b")); ctx.rectangle(-330, -1250, 700, 60); ctx.fill()
    if opened > 0:
        rgb(ctx, (0.02, 0.02, 0.03)); rrect(ctx, -190, -860, 380, 860, 40); ctx.fill()
    dx = -190 - 340 * opened
    rgb(ctx, hexc("#9aa5ae")); rrect(ctx, dx, -860, 380, 860, 40); ctx.fill()
    rgb(ctx, hexc("#6c7780")); ctx.set_line_width(10); rrect(ctx, dx, -860, 380, 860, 40); ctx.stroke()
    rgb(ctx, hexc("#101418")); ctx.arc(dx + 190, -600, 95, 0, 6.283); ctx.fill()
    rgb(ctx, hexc("#6c7780")); ctx.set_line_width(14); ctx.arc(dx + 190, -600, 95, 0, 6.283); ctx.stroke()
    if hands:
        rgb(ctx, hexc("#8fa58a"), 0.9)
        for hx in (-40, 40):
            rrect(ctx, dx + 190 + hx - 22, -630 + 8 * math.sin(t * 5 + hx), 44, 60, 16); ctx.fill()
    ctx.save(); ctx.translate(dx + 330, -430); ctx.rotate(handle)
    rgb(ctx, hexc("#3a4046")); rrect(ctx, -90, -14, 110, 28, 14); ctx.fill(); ctx.arc(0, 0, 22, 0, 6.283); ctx.fill(); ctx.restore()
    for kt in knock:
        p = (t - kt) / 0.35
        if 0 <= p < 1:
            rgb(ctx, (1, 1, 1), 0.8 * (1 - p)); ctx.set_line_width(7); ctx.arc(dx + 190, -520, 60 + 220 * p, 0, 6.283); ctx.stroke()
    ctx.restore()


def boat_ext(ctx, t, x, y, s=1.0, zombies=0, bob=1.0):
    """The coast guard boat from the side; waterline at (x, y)."""
    ctx.save(); ctx.translate(x, y + 8 * bob * math.sin(t * 1.4)); ctx.rotate(0.02 * bob * math.sin(t * 1.1)); ctx.scale(s, s)
    rgb(ctx, hexc("#dfe5ea")); rrect(ctx, -60, -330, 300, 200, 20); ctx.fill()                        # cabin
    rgb(ctx, hexc("#27323c")); rrect(ctx, -30, -300, 240, 70, 14); ctx.fill()
    rgb(ctx, hexc("#3a4046")); ctx.rectangle(60, -420, 10, 100); ctx.fill()
    for k in range(zombies):
        zombie(ctx, k, -330 + k * 90, -130, 240, t, walk=False, face=1 if k % 2 else -1)
    rgb(ctx, hexc("#f4f6f8")); ctx.move_to(-470, -140); ctx.line_to(430, -140); ctx.line_to(360, 30); ctx.line_to(-380, 30); ctx.close_path(); ctx.fill()
    rgb(ctx, hexc("#e2622b")); ctx.move_to(-455, -110); ctx.line_to(418, -110); ctx.line_to(400, -70); ctx.line_to(-438, -70); ctx.close_path(); ctx.fill()
    text(ctx, "COAST GUARD", -40, -20, 44, hexc("#27323c"))
    rgb(ctx, hexc("#e8eef4")); ctx.set_line_width(6); ctx.move_to(-460, -200); ctx.line_to(-80, -200); ctx.stroke()
    ctx.restore()


def crowd(ctx, t, n=5, y=DECK_Y + 250, expr="fear", s=520, x0=90, dx=150, look=(0, 0), skip=()):
    for k in range(n):
        if k in skip:
            continue
        x = x0 + k * dx
        soft_shadow(ctx, x, y + 5, 180)
        EXTRAS[k % len(EXTRAS)].draw(ctx, x, y + (k % 2) * 30, s, t + k, face=1 if k % 2 else -1, expr=expr, look=look)


def tarp(ctx, x, y, w, h, sag=0.3, col="#3b6ea5", a=1.0):
    rgb(ctx, hexc(col), a); ctx.move_to(x - w / 2, y); ctx.curve_to(x - w / 4, y + h * sag * 3, x + w / 4, y + h * sag * 3, x + w / 2, y)
    ctx.line_to(x + w / 2, y - 26); ctx.curve_to(x + w / 4, y + h * sag * 3 - 40, x - w / 4, y + h * sag * 3 - 40, x - w / 2, y - 26); ctx.fill()


def bucket(ctx, x, y, s=1.0, full=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rgb(ctx, hexc("#c43a2a")); ctx.move_to(-80, -160); ctx.line_to(80, -160); ctx.line_to(60, 0); ctx.line_to(-60, 0); ctx.fill()
    rgb(ctx, hexc("#5fb0e0")); ctx.save(); ctx.translate(0, -160 + 40 * (1 - full)); ctx.scale(1, 0.25); ctx.arc(0, 0, 76, 0, 6.283); ctx.restore(); ctx.fill()
    ctx.restore()


def anchor(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rgb(ctx, hexc("#3a4046")); ctx.set_line_width(26); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(0, -160); ctx.line_to(0, 110); ctx.stroke()
    ctx.arc(0, 20, 110, 0.15, math.pi - 0.15); ctx.stroke()
    ctx.move_to(-70, -110); ctx.line_to(70, -110); ctx.stroke()
    ctx.set_line_width(14); ctx.arc(0, -190, 30, 0, 6.283); ctx.stroke()
    ctx.restore()


def sea_cut(ctx, t, depth, anchor_d, rope_extra=0.0, tight=0.0):
    """Side cut-away: boat on the surface, the anchor on its rope, the seabed below."""
    vgrad(ctx, -300, 520, [(0, hexc("#5a6472")), (1, hexc("#9aa3ae"))])
    vgrad(ctx, 520, H + 300, [(0, hexc("#1f6f8a")), (1, hexc("#05202e"))])
    rgb(ctx, hexc("#3b3326")); ctx.rectangle(-100, 520 + depth, W + 200, H); ctx.fill()
    rgb(ctx, hexc("#544a36"))
    for k in range(9):
        ctx.arc(k * 140 + 30, 520 + depth + 10, 60, math.pi, 2 * math.pi); ctx.fill()
    boat_ext(ctx, t, 430, 530, 0.8, bob=1 - tight)
    ay = 520 + anchor_d
    rgb(ctx, hexc("#d8c79a")); ctx.set_line_width(9); ctx.move_to(700, 500); ctx.line_to(700, ay - 150 * 0.8); ctx.stroke()
    if rope_extra > 0:                                                    # belts / lines / tarp knotted in
        for k, col in enumerate(("#3b6ea5", "#5a3a22", "#e2622b", "#2a2a2a")):
            yy = 560 + k * 110
            if yy < ay - 160:
                rgb(ctx, hexc(col)); ctx.set_line_width(16); ctx.move_to(700, yy); ctx.line_to(700, yy + 70); ctx.stroke()
                rgb(ctx, hexc("#d8c79a")); ctx.arc(700, yy, 13, 0, 6.283); ctx.fill()
    anchor(ctx, 700, ay, 0.8)
    Particles(40, 5, (0, 560, W, H), vel=(8, -30), size=(1.5, 3.5), col=(0.7, 0.9, 1.0), alpha=0.3).draw(ctx, t)


def float_person(ctx, ch, x, y, s, t, jacket=None, trousers=False, **kw):
    """Head and shoulders above the water, with a life jacket or an inflated pair of trousers."""
    bob = 10 * math.sin(t * 1.6 + x * 0.02)
    wl = y + bob + 0.1 * s                                                # waterline
    ctx.save(); ctx.rectangle(x - s, wl - 2 * s, 2 * s, 2 * s); ctx.clip()  # only what is above the water is drawn
    ch.draw(ctx, x, y + bob + 0.62 * s, s, t, face=kw.pop("face", 0), **kw)
    if jacket:
        rgb(ctx, hexc(jacket)); rrect(ctx, x - 0.15 * s, y + bob - 0.02 * s, 0.3 * s, 0.14 * s, 0.05 * s); ctx.fill()
    if trousers:                                                          # the air-filled legs bob beside the shoulders
        rgb(ctx, hexc("#4a5568"))
        for sg in (-1, 1):
            ctx.save(); ctx.translate(x + sg * 0.2 * s, wl - 0.03 * s); ctx.rotate(sg * 0.5); ctx.scale(0.5, 1); ctx.arc(0, 0, 0.11 * s, 0, 6.283); ctx.restore(); ctx.fill()
    ctx.restore()
    rgb(ctx, (0.85, 0.93, 1.0), 0.7); ctx.set_line_width(5)
    ctx.move_to(x - 0.3 * s, wl); ctx.curve_to(x - 0.1 * s, wl - 0.02 * s, x + 0.1 * s, wl + 0.02 * s, x + 0.3 * s, wl); ctx.stroke()


def big(ctx, words, t, t0, y=330, size=120, col=(1, 1, 1)):
    text(ctx, words, 540, y, size, col, prog(t, t0, t0 + 0.2), outline=11)


# ------------------------------------------------------------------ PART 1
def p1s1(ctx, t, d):
    with camera(ctx, t, d, push=0.14, handheld=0.7, focus=(540, 1000)):
        deck(ctx, t, "grey", door=False)
        crowd(ctx, t, 5, s=480, x0=60, dx=240, skip=(2,))
        h = DALE.draw(ctx, 540, DECK_Y + 330, 760, t, face=1, expr="suspicious", look=(-1, 0), arm_f=(0.9, 1.2))
        rgb(ctx, hexc("#7d8794")); ctx.arc(h["hand"][0], h["hand"][1], 40, 0, 6.283); ctx.fill()      # sleeve pulled over his hand
    shot_card(ctx, t, text, "COUNT THE ARMS", 0.0, y=330, size=118)
    finish(ctx, t, d, fi=0.0)


def p1s2(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(540, 1000)):
        sky(ctx, "dawn", 1100); ocean(ctx, t, 1000, night=False)
        B.cliffs(ctx, t, 1.0)
        boat_ext(ctx, t, lerp(1300, 560, ease_out(prog(t, 0, d))), 1250, 0.9)
    finish(ctx, t, d)


def p1s3(ctx, t, d):
    with camera(ctx, t, d, push=0.05, handheld=0.3, focus=(540, 1200), pan=(120, 0)):
        deck(ctx, t, "day")
        crowd(ctx, t, 5, expr="tired", s=460, x0=40, dx=130)
        CAP.draw(ctx, 700, DECK_Y + 260, 620, t, face=-1, expr="determined", look=(-1, 0))
    big(ctx, "11 SURVIVORS", t, T1.at(3, 0)); big(ctx, "1 LOCKED CABIN", t, T1.at(3, 2), y=470, col=(1, 0.8, 0.4))
    finish(ctx, t, d)


def p1s4(ctx, t, d):
    die = T1.at(4, 1)
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 800), shake=0.5 if 0 < t - die < 0.4 else 0):
        deck(ctx, t, "day", door=False)
        close(KAI, ctx, 540, 860, 250, t, face=0, expr="happy", expr_to="shock", expr_k=prog(t, die, die + 0.2), talk=talk(1, 4, "kai", t), **K)
    finish(ctx, t, d)


def p1s5(ctx, t, d):
    with camera(ctx, t, d, push=-0.08, handheld=0.3, focus=(540, 1100)):
        sky(ctx, "grey", 900); ocean(ctx, t, 800, night=False)
        rgb(ctx, hexc("#cbb07a")); ctx.rectangle(-100, 780, W + 200, 26); ctx.fill()
        boat_ext(ctx, t, 540, 1350, 0.8)
    big(ctx, "1 MILE OUT", t, T1.at(5, 1), y=400)
    finish(ctx, t, d)


def p1s6(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 800)):
        deck(ctx, t, "grey", door=False)
        close(CAP, ctx, 540, 860, 260, t, face=0, expr="determined", talk=talk(1, 6, "man", t), arm_f=(1.4, 0.3))
    finish(ctx, t, d)


def p1s7(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 900)):
        rgb(ctx, hexc("#2a3140")); ctx.paint(); glow(ctx, 540, 900, 700, (0.5, 0.6, 0.8), 0.25)
        radio(ctx, t, 1.0)
    big(ctx, "STATIC", t, T1.at(7, 1), y=1650, col=(1, 0.5, 0.4))
    finish(ctx, t, d)


def p1s8(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 1000)):
        deck(ctx, t, "day", door=False)
        glow(ctx, 540, 200, 500, (1, 0.95, 0.7), 0.5)
        rgb(ctx, hexc("#dfe5ea")); rrect(ctx, 400, DECK_Y - 320, 280, 460, 30); ctx.fill()                # empty water cooler
        rgb(ctx, hexc("#bfe3f5"), 0.5); rrect(ctx, 430, DECK_Y - 520, 220, 220, 60); ctx.fill()
        rgb(ctx, hexc("#3a4046")); ctx.rectangle(520, DECK_Y - 200, 40, 50); ctx.fill()
    big(ctx, "11 PEOPLE", t, T1.at(8, 1)); big(ctx, "0 WATER", t, T1.at(8, 2), y=470, col=(1, 0.5, 0.4))
    finish(ctx, t, d)


def p1s9(ctx, t, d):
    lift = ease(prog(t, 0.4, 1.4))
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(540, 1000)):
        deck(ctx, t, "day", door=False)
        h = EXTRAS[1].draw(ctx, 520, DECK_Y + 300, 820, t, face=1, expr="tired", look=(1, 0.5), arm_f=(0.6 + 0.9 * lift, 0.9 * lift))
        rgb(ctx, hexc("#f4f6f8")); rrect(ctx, h["hand"][0] - 30, h["hand"][1] - 80, 70, 90, 12); ctx.fill()
        rgb(ctx, hexc("#2b8fb3")); ctx.rectangle(h["hand"][0] - 24, h["hand"][1] - 60, 58, 20); ctx.fill()
    finish(ctx, t, d)


def p1s10(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(540, 800), shake=0.3 if t < 0.3 else 0):
        deck(ctx, t, "day", door=False)
        close(TESS, ctx, 540, 860, 250, t, face=1, expr="angry", talk=talk(1, 10, "tess", t), look=(1, 0), arm_f=(1.5, 0.1))
    if t > T1.at(10, 1):
        rule_card(ctx, t, T1.at(10, 1), [("3.5% SALT", T1.at(10, 1) + 0.2), ("DRIES YOU OUT FASTER", T1.at(10, 2)), ("THAN NOTHING", T1.at(10, 2) + 0.5)], title="SEAWATER")
    finish(ctx, t, d)


def p1s11(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 700)):
        deck(ctx, t, "grey", door=False)
        for k in range(6):                                              # rain clouds rolling in
            r = random.Random(k); x = (r.uniform(0, W) + t * 40) % (W + 400) - 200
            rgb(ctx, (0.22, 0.24, 0.3), 0.9); ctx.save(); ctx.translate(x, 150 + r.uniform(0, 250)); ctx.scale(2.2, 0.8); ctx.arc(0, 0, 130, 0, 6.283); ctx.restore(); ctx.fill()
        close(KAI, ctx, 420, 1000, 220, t, face=1, expr="happy", look=(0.6, -1), arm_f=(2.4, 0.1), **K)
    finish(ctx, t, d)


def p1s12(ctx, t, d):
    fill = prog(t, T1.at(12, 2), d)
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1100)):
        deck(ctx, t, "grey", door=False)
        tarp(ctx, 540, 1050, 760, 260, 0.35)
        rgb(ctx, hexc("#5fb0e0"), 0.9 * fill); ctx.save(); ctx.translate(540, 1050 + 150); ctx.scale(1, 0.25); ctx.arc(0, 0, 120 + 100 * fill, 0, 6.283); ctx.restore(); ctx.fill()
        for x, ch, f in ((140, KAI, 1), (940, TESS, -1)):
            ch.draw(ctx, x, DECK_Y + 250, 640, t, face=f, expr="determined", look=(f, -0.3), arm_f=(2.0, 0.2), **(K if ch is KAI else {}))
        RAIN.draw(ctx, t)
    big(ctx, "FIRST RAIN RINSES THE SALT", t, T1.at(12, 1), y=330, size=84)
    finish(ctx, t, d)


def p1s13(ctx, t, d):
    with camera(ctx, t, d, push=0.07, handheld=0.3, focus=(540, 1200)):
        deck(ctx, t, "grey", door=False)
        crowd(ctx, t, 5, expr="happy", s=470, x0=70, dx=235)
        bucket(ctx, 400, DECK_Y + 330, 1.3); bucket(ctx, 680, DECK_Y + 330, 1.3)
    finish(ctx, t, d)


def p1s14(ctx, t, d):
    with camera(ctx, t, d, push=0.16, handheld=0.4, focus=(540, 1000)):
        deck(ctx, t, "grey", door=False)
        h = DALE.draw(ctx, 540, 2250, 1700, t, face=1, expr="suspicious", look=(-0.8, 0.3), arm_f=(0.9, 1.1))
        rgb(ctx, hexc("#7d8794")); ctx.arc(h["hand"][0], h["hand"][1], 95, 0, 6.283); ctx.fill()
    finish(ctx, t, d)


def p1s15(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 800)):
        deck(ctx, t, "grey", door=False)
        close(TESS, ctx, 540, 900, 250, t, face=1, expr="suspicious", look=(1, 0.1))
    big(ctx, "10 SHOWED THEIR ARMS", t, T1.at(15, 1), y=330, size=92); big(ctx, "1 WOULDN'T", t, T1.at(15, 2), y=450, col=(1, 0.5, 0.4))
    finish(ctx, t, d)


def p1s16(ctx, t, d):
    k0 = T1.at(16, -1) + 0.5
    kn = [k0, k0 + 0.35, k0 + 0.7]
    with camera(ctx, t, d, push=0.12, handheld=0.4, focus=(540, 1000), shake=0.3 if any(0 < t - k < 0.15 for k in kn) else 0):
        rgb(ctx, hexc("#dfe5ea")); ctx.paint()
        cabin_door(ctx, t, 540, 1750, 1.35, knock=kn)
        rgb(ctx, (0, 0, 0.05), 0.25); ctx.paint()
    finish(ctx, t, d)


def p1s17(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 900)):
        rgb(ctx, hexc("#dfe5ea")); ctx.paint()
        cabin_door(ctx, t, 620, 1750, 1.2, knock=[0.3, 0.65, 1.4, 1.75])
        CAP.draw(ctx, 420, 1800, 1150, t, face=-1, expr="fear", talk=talk(1, 17, "man", t), look=(-1, 0), arm_f=(1.5, 0.1), arm_b=(-1.3, 0.1))
    finish(ctx, t, d)


def p1s18(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 1300)):
        rgb(ctx, hexc("#dfe5ea")); ctx.paint()
        cabin_door(ctx, t, 540, 1900, 1.2, knock=[0.3, 0.65, 1.3, 1.65], hands=True)
        rgb(ctx, (0, 0, 0), 0.5); ctx.paint()
    end_card(ctx, t, T1, 18, "OPEN", "IT?", "COMMENT: YES OR NO", "PART 2 NEXT")
    finish(ctx, t, d, fo=0.3)


# ------------------------------------------------------------------ PART 2
def p2s1(ctx, t, d):
    kn = list(np.arange(0.1, d, 0.9))
    with camera(ctx, t, d, push=0.12, handheld=0.6, focus=(540, 1000), shake=0.3 if any(0 < t - k < 0.15 for k in kn) else 0):
        rgb(ctx, hexc("#dfe5ea")); ctx.paint()
        cabin_door(ctx, t, 540, 1750, 1.35, knock=kn, hands=True)
        rgb(ctx, (0, 0, 0.05), 0.2); ctx.paint()
    shot_card(ctx, t, text, "OPEN IT?", 0.0, y=330, size=150)
    finish(ctx, t, d, fi=0.0)


def p2s2(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 800)):
        deck(ctx, t, "grey", door=False)
        close(KAI, ctx, 540, 860, 250, t, face=1, expr="suspicious", talk=talk(2, 2, "kai", t), look=(1, 0), **K)
    finish(ctx, t, d)


def p2s3(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 800)):
        deck(ctx, t, "grey", door=False)
        close(CAP, ctx, 540, 860, 260, t, face=-1, expr="sad", talk=talk(2, 3, "man", t), look=(-0.5, 0.8))
    finish(ctx, t, d)


def p2s4(ctx, t, d):
    with camera(ctx, t, d, push=0.14, handheld=0.3, focus=(540, 950)):
        rgb(ctx, hexc("#dfe5ea")); ctx.paint()
        cabin_door(ctx, t, 540, 1750, 1.5, hands=True)
        rgb(ctx, (0, 0, 0.05), 0.25); ctx.paint()
    finish(ctx, t, d)


def p2s5(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 900)):
        deck(ctx, t, "grey", door=False, shore=0.25 + 0.2 * prog(t, 0, d))
        TESS.draw(ctx, 330, DECK_Y + 300, 820, t, face=1, expr="fear", look=(1, -0.3), arm_f=(1.7, 0.0))
    finish(ctx, t, d)


def p2s6(ctx, t, d):
    p = prog(t, 0, d)
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 1000)):
        sky(ctx, "grey", 620); ocean(ctx, t, 600, night=False, y1=1500)
        sand(ctx, 1500, night=False); foam(ctx, t, 1490, 0.8)
        for k in range(9):
            zombie(ctx, k, 60 + k * 125, 1700, 300, t, walk=False, face=1 if k % 2 else -1)
        boat_ext(ctx, t, 540, lerp(820, 1000, p), 0.55)
        rgb(ctx, (1, 1, 1), 0.7); ctx.set_line_width(8)
        for k in range(3):
            y = 1100 + ((t * 120 + k * 110) % 330)
            ctx.move_to(500, y); ctx.line_to(540, y + 40); ctx.line_to(580, y); ctx.stroke()
    big(ctx, "THE TIDE TURNED", t, 0.2, y=330, size=100)
    finish(ctx, t, d)


def p2s7(ctx, t, d):
    with camera(ctx, t, d, push=0.14, handheld=0.3, focus=(540, 1300)):
        sky(ctx, "grey", 1000); ocean(ctx, t, 950, night=False, y1=1300)
        sand(ctx, 1300, night=False); foam(ctx, t, 1290, 0.8)
        for row in range(3):
            for k in range(9):
                zombie(ctx, k + row * 9, 40 + k * 125 + row * 50, 1500 + row * 150, 300 + row * 60, t, walk=False, face=1 if (k + row) % 2 else -1)
    big(ctx, "HUNDREDS", t, T2.at(7, -1), y=400, col=(1, 0.5, 0.4))
    finish(ctx, t, d)


def p2s8(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.2, focus=(540, 900)):
        deck(ctx, t, "grey", door=False, shore=0.5)
        rgb(ctx, (0, 0, 0), 0.45); ctx.paint()
    for k, w in enumerate(("NO ENGINE", "NO OARS", "1 HOUR")):
        text(ctx, w, 540, 600 + k * 200, 150, (1, 1, 1) if k < 2 else (1, 0.5, 0.4), prog(t, T2.at(8, k), T2.at(8, k) + 0.15), outline=12)
    finish(ctx, t, d)


def p2s9(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.4, focus=(540, 1000)):
        deck(ctx, t, "grey", door=False, shore=0.55)
        anchor(ctx, 800, DECK_Y + 150, 1.3)
        close(KAI, ctx, 360, 900, 230, t, face=1, expr="determined", talk=talk(2, 9, "kai", t), look=(1, 0.4), arm_f=(1.5, 0.2), **K)
    finish(ctx, t, d)


def p2s10(ctx, t, d):
    drop = ease(prog(t, 0.2, 1.6))
    with camera(ctx, t, d, push=0.03, handheld=0.2):
        sea_cut(ctx, t, 1150, lerp(80, 780, drop))
    big(ctx, "ROPE MUST REACH THE BOTTOM", t, T2.at(10, 1), y=300, size=80)
    finish(ctx, t, d)


def p2s11(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.2, focus=(700, 1400)):
        sea_cut(ctx, t, 1150, 780 + 12 * math.sin(t * 2))
        rgb(ctx, (1, 0.4, 0.3)); ctx.set_line_width(8)
        ctx.move_to(860, 1420); ctx.line_to(860, 1660); ctx.stroke(); ctx.move_to(830, 1420); ctx.line_to(890, 1420); ctx.stroke(); ctx.move_to(830, 1660); ctx.line_to(890, 1660); ctx.stroke()
    big(ctx, "20 FT SHORT", t, T2.at(11, 1), y=300, col=(1, 0.5, 0.4))
    finish(ctx, t, d)


def p2s12(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 1200)):
        deck(ctx, t, "grey", door=False, shore=0.6)
        for k, col in enumerate(("#d8c79a", "#5a3a22", "#3b6ea5", "#2a2a2a")):                # the patchwork rope laid across the deck
            if t > T2.at(12, min(k, 3)) - 0.2:
                rgb(ctx, hexc(col)); ctx.set_line_width(22); ctx.move_to(60 + k * 250, DECK_Y + 330); ctx.line_to(290 + k * 250, DECK_Y + 330 + 20 * math.sin(k)); ctx.stroke()
                rgb(ctx, hexc("#f4f6f8")); ctx.arc(60 + k * 250, DECK_Y + 330, 20, 0, 6.283); ctx.fill()
        KAI.draw(ctx, 300, DECK_Y + 250, 700, t, mode="idle", crouch=0.5, face=1, expr="determined", look=(0.5, 1), arm_f=(0.9, 0.6), **K)
        TESS.draw(ctx, 760, DECK_Y + 250, 640, t, mode="idle", crouch=0.5, face=-1, expr="determined", look=(-0.5, 1), arm_f=(0.9, 0.6))
    finish(ctx, t, d)


def p2s13(ctx, t, d):
    hit = T2.at(13, 1)
    with camera(ctx, t, d, push=0.03, handheld=0.2, shake=0.5 if 0 < t - hit < 0.35 else 0):
        sea_cut(ctx, t, 1150, lerp(780, 1040, ease(prog(t, 0.0, T2.at(13, 0) + 0.8))), rope_extra=1.0, tight=prog(t, hit, hit + 0.3))
    big(ctx, "STOPPED", t, T2.at(13, 2), y=300, col=(0.6, 1, 0.7))
    finish(ctx, t, d)


def p2s14(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1000)):
        sky(ctx, "grey", 620); ocean(ctx, t, 600, night=False, y1=1500)
        sand(ctx, 1500, night=False); foam(ctx, t, 1490, 0.8)
        for k in range(9):
            zombie(ctx, k, 60 + k * 125, 1720, 320, t, walk=False, face=1 if k % 2 else -1)
        boat_ext(ctx, t, 540, 1150, 0.6, bob=0.4)
    big(ctx, "200 YARDS", t, 0.1, y=330)
    finish(ctx, t, d)


def p2s15(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 1100), pan=(-160, 0)):
        deck(ctx, t, "grey", door=False, shore=0.7)
        crowd(ctx, t, 3, expr="happy", s=460, x0=60, dx=170)
        DALE.draw(ctx, 820, DECK_Y + 300, 760, t + 0.02 * math.sin(t * 40), face=-1, expr="tired", look=(0, 1), arm_f=(0.9, 1.1))
    finish(ctx, t, d)


def p2s16(ctx, t, d):
    turn = prog(t, T2.at(16, 2), d)
    with camera(ctx, t, d, push=0.18, handheld=0.4, focus=(540, 850)):
        deck(ctx, t, "grey", door=False)
        ch = DALE_Z if turn > 0.6 else DALE
        close(ch, ctx, 540 + 5 * math.sin(t * 45), 880, 320, t, face=0, expr="tired", expr_to="shock", expr_k=turn, look=(0, 0))
        if 0 < turn <= 0.6:                                             # skin going grey before the eyes turn
            rgb(ctx, (0.56, 0.65, 0.54), 0.5 * turn); ctx.arc(540, 880, 330, 0, 6.283); ctx.fill()
        for k in range(5):                                             # sweat
            r = random.Random(k); rgb(ctx, (0.8, 0.9, 1.0), 0.8); ctx.arc(540 + r.uniform(-220, 220), 760 + ((t * 140 + k * 70) % 320), 9, 0, 6.283); ctx.fill()
    finish(ctx, t, d)


def p2s17(ctx, t, d):
    turn = 1.2 * ease(prog(t, T2.at(17, 1), d))
    with camera(ctx, t, d, push=0.16, handheld=0.3, focus=(700, 1100)):
        rgb(ctx, hexc("#dfe5ea")); ctx.paint()
        cabin_door(ctx, t, 540, 1750, 1.5, knock=[0.2, 0.55] if t < T2.at(17, 1) else (), handle=turn)
        rgb(ctx, (0, 0, 0.05), 0.25); ctx.paint()
    finish(ctx, t, d)


def p2s18(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 1300)):
        sky(ctx, "grey", 620); ocean(ctx, t, 600, night=False, y1=1500)
        sand(ctx, 1500, night=False)
        for k in range(9):
            zombie(ctx, k, 60 + k * 125, 1720, 320, t, walk=False, face=-1)
        boat_ext(ctx, t, 540, 1250, 0.6)
        rgb(ctx, (0, 0, 0), 0.5); ctx.paint()
    end_card(ctx, t, T2, 18, "JUMP", "IN?", "COMMENT: YES OR NO", "PART 3 NEXT")
    finish(ctx, t, d, fo=0.3)


# ------------------------------------------------------------------ PART 3
def p3s1(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.9, focus=(540, 1000), shake=0.2):
        deck(ctx, t, "dusk", shore=0.7, door_open=0.3 * prog(t, T3.at(1, 2), d))
        crowd(ctx, t, 3, expr="shock", s=440, x0=40, dx=130)
        DALE_Z.draw(ctx, 520, DECK_Y + 300, 700, t, face=-1, expr="shock", arm_f=(1.45, 0.1), arm_b=(1.3, 0.1))
    shot_card(ctx, t, text, "JUMP IN?", 0.0, y=330, size=150)
    finish(ctx, t, d, fi=0.0)


def p3s2(ctx, t, d):
    lunge = ease_out(prog(t, 0.2, 0.7))
    with camera(ctx, t, d, push=0.16, handheld=0.8, focus=(540, 900), shake=0.5):
        deck(ctx, t, "dusk", door=False)
        close(DALE_Z, ctx, lerp(900, 560, lunge), 900, lerp(200, 330, lunge), t, face=-1, expr="shock", arm_f=(1.5, 0.1), arm_b=(1.4, 0.1))
    finish(ctx, t, d)


def p3s3(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.6, focus=(540, 1000)):
        deck(ctx, t, "dusk", door=False)
        if t < T3.at(3, 1):
            close(TESS, ctx, 540, 900, 260, t, face=1, expr="shock", talk=talk(3, 3, "tess", t), look=(1, 0))
        else:
            h = KAI.draw(ctx, 420, DECK_Y + 320, 900, t, face=1, expr="determined", look=(1, 0), arm_f=(1.5, 0.3), **K)
            tarp(ctx, h["hand"][0] + 150, h["hand"][1] - 60, 420, 200, 0.5)
    finish(ctx, t, d)


def p3s4(ctx, t, d):
    push = ease(prog(t, T3.at(4, 0) + 0.6, d))
    with camera(ctx, t, d, push=0.08, handheld=0.7, focus=(540, 1000), shake=0.3):
        deck(ctx, t, "dusk", door=False)
        KAI.draw(ctx, lerp(300, 420, push), DECK_Y + 300, 800, t, face=1, expr="angry", look=(1, 0), arm_f=(1.6, 0.0), arm_b=(1.4, 0.0), **K)
        zx = lerp(680, 860, push)
        DALE_Z.draw(ctx, zx, DECK_Y + 300, 800, t, face=-1, expr="shock", lean=-0.3 * push)
        rgb(ctx, hexc("#3b6ea5")); rrect(ctx, zx - 170, DECK_Y - 520, 340, 420, 120); ctx.fill()             # tarp over his head
    finish(ctx, t, d)


def p3s5(ctx, t, d):
    sp = prog(t, 0.2, 1.0)
    with camera(ctx, t, d, push=0.06, handheld=0.5, focus=(540, 1100), shake=0.4 if 0.3 < t < 0.7 else 0):
        sky(ctx, "dusk", 900); ocean(ctx, t, 850, night=False)
        boat_ext(ctx, t, 300, 1150, 0.9)
        for k in range(12):                                           # splash
            a = -math.pi * k / 11; r = 60 + 300 * sp
            rgb(ctx, (0.9, 0.96, 1.0), 0.9 * (1 - sp)); ctx.arc(820 + math.cos(a) * r * 0.7, 1200 + math.sin(a) * r, 26 * (1 - sp) + 6, 0, 6.283); ctx.fill()
    finish(ctx, t, d)


def p3s6(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 1000)):
        underwater(ctx, t)
        rgb(ctx, hexc("#3b3326")); ctx.rectangle(-100, 1650, W + 200, 400); ctx.fill()
        DALE_Z.draw(ctx, 540, 1660, 760, t * 0.3, face=0, expr="neutral", look=(0, -1), breathe=0.0)
        rgb(ctx, (0.02, 0.15, 0.22), 0.35); ctx.paint()
    big(ctx, "THEY CAN'T SWIM", t, T3.at(6, 1), y=330, size=100)
    finish(ctx, t, d)


def p3s7(ctx, t, d):
    op = ease_out(prog(t, 0.2, 0.6))
    with camera(ctx, t, d, push=0.12, handheld=0.7, focus=(540, 1000), shake=0.6 if 0.2 < t < 0.7 else 0.1):
        rgb(ctx, hexc("#dfe5ea")); ctx.paint()
        cabin_door(ctx, t, 540, 1750, 1.35, opened=op)
        if op > 0.3:
            ENG.draw(ctx, 520, 1760, 1050, t, face=0, expr="shock", arm_f=(1.45, 0.1), arm_b=(-1.45, -0.1))
    finish(ctx, t, d)


def p3s8(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.6, focus=(540, 800), shake=0.2):
        deck(ctx, t, "dusk", door=False)
        close(CAP, ctx, 540, 860, 270, t, face=0, expr="shock", talk=talk(3, 8, "man", t), arm_f=(2.2, 0.2))
    finish(ctx, t, d)


def p3s9(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(540, 1100)):
        deck(ctx, t, "dusk", door=False)
        for k in range(4):
            rgb(ctx, hexc("#f08a24")); rrect(ctx, 150 + k * 210, DECK_Y + 60, 160, 220, 40); ctx.fill()
            rgb(ctx, hexc("#1c1c1c")); ctx.rectangle(150 + k * 210, DECK_Y + 150, 160, 22); ctx.fill()
    big(ctx, "11 PEOPLE", t, T3.at(9, 0)); big(ctx, "4 LIFE JACKETS", t, T3.at(9, 1), y=470, col=(1, 0.5, 0.4))
    finish(ctx, t, d)


def p3s10(ctx, t, d):
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 900)):
        deck(ctx, t, "dusk", door=False)
        close(KAI, ctx, 540, 1150, 240, t, face=0, expr="confused", expr_to="happy", expr_k=prog(t, T3.at(10, 1), T3.at(10, 1) + 0.3), look=(0.3, -0.8), **K)
        p = ease_out(prog(t, T3.at(10, 1), T3.at(10, 1) + 0.4))
        if p > 0:
            ctx.save(); ctx.translate(560, 480); ctx.scale(p, p)
            rgb(ctx, (1, 1, 1), 0.95); ctx.arc(0, 0, 290, 0, 6.283); ctx.fill(); ctx.arc(-170, 290, 36, 0, 6.283); ctx.fill()
            rgb(ctx, hexc("#4a5568"))
            for sg in (-1, 1):
                ctx.save(); ctx.translate(sg * 80, 10); ctx.rotate(sg * 0.2); rrect(ctx, -50, -190, 100, 360, 50); ctx.fill(); ctx.restore()
            rrect(ctx, -140, -210, 280, 110, 30); ctx.fill()
            ctx.restore()
    finish(ctx, t, d)


def p3s11(ctx, t, d):
    with camera(ctx, t, d, push=0.03, handheld=0.2):
        sky(ctx, "dusk", 900); ocean(ctx, t, 850, night=False)
        rgb(ctx, (0, 0, 0), 0.45); ctx.paint()
    rule_card(ctx, t, 0.15, [("TIE THE LEGS", T3.at(11, 0) + 0.3), ("FILL THEM WITH AIR", T3.at(11, 1)), ("HOLD THE WAIST UNDER", T3.at(11, 2))], title="TROUSERS FLOAT")
    finish(ctx, t, d)


def floaters(ctx, t, y=1150, n=6):
    for k in range(n):
        ch = [KAI, TESS, CAP] + EXTRAS
        c = ch[k % len(ch)]
        float_person(ctx, c, 110 + k * 172, y + (k % 2) * 90, 330, t, jacket="#f08a24" if k in (1, 4) else None, trousers=k not in (1, 4),
                     expr="fear" if k % 2 else "determined", **(K if c is KAI else {}))


def p3s12(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 1200)):
        sky(ctx, "dusk", 900); ocean(ctx, t, 850, night=False)
        floaters(ctx, t)
    big(ctx, "7 FLOATS", t, T3.at(12, 1), y=400, col=(0.6, 1, 0.7))
    finish(ctx, t, d)


def p3s13(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.4, focus=(540, 1100)):
        sky(ctx, "dusk", 760); ocean(ctx, t, 720, night=False)
        boat_ext(ctx, t, 560, 1050, 1.0, zombies=5, bob=0.5)
        floaters(ctx, t, y=1400)
    finish(ctx, t, d)


def p3s14(ctx, t, d):
    seq = [T3.at(14, 1) + k * 0.28 for k in range(3)] + [T3.at(14, 3) + k * 0.28 for k in range(3)]
    fl = max([1 - abs(t - s - 0.08) / 0.1 for s in seq] + [0])
    with camera(ctx, t, d, push=0.10, handheld=0.3, focus=(540, 1000)):
        sky(ctx, "dusk", 800); ocean(ctx, t, 760, night=False)
        float_person(ctx, TESS, 540, 1250, 760, t, trousers=True, face=1, expr="determined", look=(1, -0.3), arm_f=(2.3, 0.2))
        px, py = 720, 760
        rgb(ctx, (0.08, 0.08, 0.1)); rrect(ctx, px - 45, py - 80, 90, 160, 16); ctx.fill()
        rgb(ctx, (1, 1, 1), clamp(fl)); rrect(ctx, px - 37, py - 70, 74, 140, 10); ctx.fill()
        if fl > 0:
            ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD); glow(ctx, px, py, 500, (1, 1, 0.95), 0.7 * clamp(fl)); ctx.restore()
    big(ctx, "3 FLASHES = HELP", t, T3.at(14, 1), y=330, size=100)
    finish(ctx, t, d)


def p3s15(ctx, t, d):
    seq = [0.5 + k * 0.28 for k in range(3)]
    fl = clamp(max([1 - abs(t - s - 0.08) / 0.1 for s in seq] + [0]))
    with camera(ctx, t, d, push=0.14, handheld=0.3, focus=(540, 800)):
        sky(ctx, "dusk", 900); ocean(ctx, t, 850, night=False)
        rgb(ctx, hexc("#1c2a22")); ctx.move_to(440, 850); ctx.line_to(660, 850); ctx.line_to(630, 890); ctx.line_to(470, 890); ctx.fill()
        ctx.rectangle(520, 790, 70, 60); ctx.fill()
        ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD); glow(ctx, 555, 800, 60 + 340 * fl, (1, 1, 0.9), 0.3 + 0.7 * fl); ctx.restore()
    finish(ctx, t, d)


def p3s16(ctx, t, d):
    sh = T3.at(16, 3)
    if t < sh:
        with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1100)):
            sky(ctx, "dusk", 1000); ocean(ctx, t, 950, night=False)
            rgb(ctx, hexc("#3b4a3a")); ctx.rectangle(-100, DECK_Y, W + 200, H); ctx.fill()
            soft_shadow(ctx, 540, 1755, 360)
            KAI.draw(ctx, 540, 1750, 1000, t, face=0, expr="tired", torn=0.8, dirt=0.4, **K)
            for k in range(8):                                        # dripping
                r = random.Random(k); rgb(ctx, (0.7, 0.9, 1.0), 0.8); ctx.arc(540 + r.uniform(-120, 120), 1300 + ((t * 300 + k * 90) % 420), 7, 0, 6.283); ctx.fill()
    else:
        shirt_insert(ctx, t, sh)
    finish(ctx, t, d)


def p3s17(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.3, focus=(540, 1100)):
        sky(ctx, "dusk", 1000); ocean(ctx, t, 950, night=False)
        rgb(ctx, hexc("#cbb07a")); ctx.rectangle(-100, 935, W + 200, 20); ctx.fill()
        rgb(ctx, hexc("#3a4046")); ctx.rectangle(700, 860, 240, 80); ctx.fill(); ctx.rectangle(760, 760, 20, 110); ctx.fill()     # the marina on the horizon
        rgb(ctx, hexc("#3b4a3a")); ctx.rectangle(-100, DECK_Y, W + 200, H); ctx.fill()
        TESS.draw(ctx, 330, 1720, 760, t, face=1, expr="confused", talk=talk(3, 17, "tess", t), look=(1, 0))
        FISH.draw(ctx, 740, 1720, 800, t, face=-1, expr="neutral", talk=talk(3, 17, "man", t), look=(0.6, -0.3), arm_b=(-1.5, 0.1) if t > T3.at(17, 1) else None)
    finish(ctx, t, d)


def p3s18(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.3, focus=(540, 1300)):
        sky(ctx, "night", 760); ocean(ctx, t, 720, night=True)
        boat_ext(ctx, t, 540, 1250, 0.9, zombies=5)
        rgb(ctx, (0, 0, 0), 0.45); ctx.paint()
    end_card(ctx, t, T3, 18, "JUMP", "IN?", "COMMENT: YES OR NO", "DAY 3 TOMORROW")
    finish(ctx, t, d, fo=0.4)


P1 = [globals()[f"p1s{i}"] for i in range(1, 19)]
P2 = [globals()[f"p2s{i}"] for i in range(1, 19)]
P3 = [globals()[f"p3s{i}"] for i in range(1, 19)]


# ------------------------------------------------------------------ sound
def knocks(d, times, seed=0):
    x = silence(d)
    for k, c in enumerate(times):
        i, n = int(c * SR), int(0.14 * SR)
        if 0 <= i and i + n <= len(x):
            tt = np.arange(n) / SR
            x[i:i + n] += (np.sin(2 * np.pi * 140 * tt) * 0.7 + band_noise(0.14, 200, 1500, seed + k)[:n] * 0.4) * np.exp(-tt * 35) * 0.9
    return x


def sfx_for(tm, part):
    def sfx(i, d):
        t = np.arange(int(d * SR)) / SR
        x = surf(d, 0.8, i + part * 40) + wind(d, 0.5, i) + band_noise(d, 60, 250, i) * 0.03       # sea + hull creak bed
        if part == 1:
            if i == 4:
                die = tm.at(4, 1)
                x += band_noise(d, 50, 180, 4) * 0.3 * (t < die) + env_at(d, [die, die + 0.25], 0.2) * band_noise(d, 80, 400, 5) * 0.8
            if i == 7:
                x += band_noise(d, 800, 5000, 7) * 0.1
            if i in (11, 12, 13):
                x += band_noise(d, 1500, 9000, i) * (0.05 if i == 11 else 0.12)
            if i == 16:
                k0 = tm.at(16, -1) + 0.5; x = x * 0.5 + knocks(d, [k0, k0 + 0.35, k0 + 0.7])
            if i in (17, 18):
                x += knocks(d, [0.3, 0.65, 1.4, 1.75], i) * 0.8
        elif part == 2:
            if i in (1, 4):
                x += knocks(d, list(np.arange(0.1, d, 0.9)), i) + moans(d, [0.6], i)
            if i in (7, 14, 18):
                x += moans(d, list(np.arange(0.3, d, 1.2)), i) * 1.4
            if i == 13:
                hit = tm.at(13, 1); x += env_at(d, [hit], 0.6) * band_noise(d, 40, 220, 13) * 1.2
            if i == 16:
                x += moans(d, [tm.at(16, 2)], 16) * 2
            if i == 17:
                x = x * 0.5 + knocks(d, [0.2, 0.55]) + env_at(d, [tm.at(17, 1) + 0.3], 0.8) * band_noise(d, 1800, 4000, 17) * 0.15
        else:
            if i in (1, 2, 4, 7, 13, 18):
                x += moans(d, list(np.arange(0.2, d, 1.1)), i) * 1.6
            if i == 5:
                x += env_at(d, [0.3], 0.7) * band_noise(d, 300, 6000, 5) * 0.9
            if i == 6:
                x = band_noise(d, 40, 500, 6) * 0.12
            if i == 7:
                x += env_at(d, [0.2], 0.4) * band_noise(d, 80, 1200, 7) * 1.0
            if i in (12, 13, 14):
                x += band_noise(d, 400, 2500, i) * 0.03
        return fades(x * 0.6, 0.03, 0.1)
    return sfx


def music1(durs):
    a = sum(durs[:3])
    return np.concatenate([piano_score(a, a + 100, bpm=84, seed=6), B.drone_score(sum(durs) - a, 21)])[: int(sum(durs) * SR)]


def music2(durs):
    return B.drone_score(sum(durs), 22)


def music3(durs):
    total, a = sum(durs), sum(durs[:13])
    return np.concatenate([B.drone_score(a, 23), piano_score(total - a, 999, bpm=72, seed=12)])[: int(total * SR)]


PARTS = {1: (SIDS[1], P1, sfx_for(T1, 1), music1), 2: (SIDS[2], P2, sfx_for(T2, 2), music2), 3: (SIDS[3], P3, sfx_for(T3, 3), music3)}

if __name__ == "__main__":
    run(PARTS, {1: T1, 2: T2, 3: T3})
