"""Hear That? - horror, Parts 1-3 (stories/29-31). First story built on the cinema toolkit.

    python src/anim/hearthat.py <part 1|2|3> [scene numbers]
"""
import math, pathlib, random, sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import *  # noqa
from cinema import (camera, fog, god_rays, soft_shadow, backlight, depth_haze, dust, flicker_dim,
                    silhouette_glow, shot_card)
from lighthouse import end_card, finish, wind
from nightshift import rule_card
from story import Timing, run
import lights as L

T1, T2, T3 = Timing("29_hearthat_1"), Timing("30_hearthat_2"), Timing("31_hearthat_3")
SP = 470
FLOOR = 1350
FIRE = (1.0, 0.62, 0.3)
MOON = (0.65, 0.75, 1.0)
EMBER = (1.0, 0.45, 0.15)
SNOW = Particles(160, 5, (0, 0, W, H), vel=(-40, 120), size=(1.5, 4), col=(0.9, 0.93, 1.0), alpha=0.7)
STORM = Particles(260, 6, (0, 0, W, H), vel=(-420, 260), size=(1.5, 4.5), col=(0.95, 0.97, 1.0), alpha=0.8)


# ------------------------------------------------------------------ sets
def room(ctx, wall=("#15130f", "#221d17"), floor=("#1a1611", "#0a0907")):
    vgrad(ctx, -300, FLOOR, [(0, hexc(wall[0])), (1, hexc(wall[1]))])
    vgrad(ctx, FLOOR, H + 300, [(0, hexc(floor[0])), (1, hexc(floor[1]))])
    rgb(ctx, (0, 0, 0), 0.25); ctx.set_line_width(3)
    for k in range(9):                                  # floorboards in perspective
        ctx.move_to(k * 140 - 100, FLOOR); ctx.line_to(k * 260 - 700, H + 300); ctx.stroke()


def vent(ctx, t, x=540, y=900, w=520, h=300, glow_a=0.35):
    """Floor/wall vent grille; faint furnace glow and dust breathing through the slats."""
    rgb(ctx, hexc("#2b2722")); rrect(ctx, x - w / 2 - 30, y - h / 2 - 30, w + 60, h + 60, 18); ctx.fill()
    rgb(ctx, hexc("#050403")); ctx.rectangle(x - w / 2, y - h / 2, w, h); ctx.fill()
    breath = 0.5 + 0.5 * math.sin(t * 1.3)
    glow(ctx, x, y + h * 0.2, w * 0.7, EMBER, glow_a * (0.6 + 0.4 * breath))
    for k in range(9):
        yy = y - h / 2 + 15 + k * (h - 20) / 9
        rgb(ctx, hexc("#3a342d")); ctx.rectangle(x - w / 2, yy, w, 14); ctx.fill()
        rgb(ctx, (1, 0.9, 0.75), 0.06); ctx.rectangle(x - w / 2, yy, w, 3); ctx.fill()
    for sx in (x - w / 2 - 12, x + w / 2 + 12):
        rgb(ctx, hexc("#5a524a")); ctx.arc(sx, y - h / 2 - 12, 9, 0, 6.283); ctx.fill(); ctx.arc(sx, y + h / 2 + 12, 9, 0, 6.283); ctx.fill()
    Particles(40, 9, (x - w / 2, y - h / 2 - 500, x + w / 2, y - h / 2), vel=(6, -70 - 60 * breath), size=(1.2, 2.6),
              col=(1, 0.9, 0.8), alpha=0.4).draw(ctx, t)


def farmhouse(ctx, t, lit=1.0, x=540, base=1250):
    rgb(ctx, hexc("#07080c"))
    ctx.move_to(x - 330, base); ctx.line_to(x - 330, base - 330); ctx.line_to(x - 20, base - 560); ctx.line_to(x + 300, base - 330)
    ctx.line_to(x + 300, base); ctx.close_path(); ctx.fill()
    ctx.rectangle(x + 160, base - 640, 60, 180); ctx.fill()                          # chimney
    rgb(ctx, (0.85, 0.9, 1.0), 0.85)                                                  # snow on the roof
    ctx.move_to(x - 350, base - 320); ctx.line_to(x - 20, base - 575); ctx.line_to(x + 320, base - 320)
    ctx.line_to(x + 300, base - 300); ctx.line_to(x - 20, base - 545); ctx.line_to(x - 330, base - 300); ctx.close_path(); ctx.fill()
    if lit > 0:
        wx, wy = x - 160, base - 230
        glow(ctx, wx + 50, wy + 60, 260, FIRE, 0.5 * lit)
        rgb(ctx, (1, 0.72, 0.4), lit); ctx.rectangle(wx, wy, 100, 120); ctx.fill()
        rgb(ctx, hexc("#07080c")); ctx.rectangle(wx + 46, wy, 8, 120); ctx.fill(); ctx.rectangle(wx, wy + 56, 100, 8); ctx.fill()
        god_rays(ctx, t, wx + 50, wy + 60, angle=math.pi * 0.62, length=700, spread=0.25, n=5, col=FIRE, alpha=0.1 * lit)
    rgb(ctx, hexc("#121318")); ctx.rectangle(x + 40, base - 200, 90, 200); ctx.fill()


def snow_ground(ctx, y=1250):
    vgrad(ctx, y, H + 300, [(0, hexc("#5a6274")), (0.3, hexc("#2c3140")), (1, hexc("#0c0e14"))])
    rgb(ctx, (0.85, 0.9, 1.0), 0.18)
    for k in range(7):
        ctx.save(); ctx.translate(k * 170 + 40, y + 20 + (k % 3) * 12); ctx.scale(3.0, 0.35); ctx.arc(0, 0, 60, 0, 6.283); ctx.restore(); ctx.fill()


def night_snow_sky(ctx, t, y=1250):
    vgrad(ctx, -300, y, [(0, hexc("#04050a")), (0.7, hexc("#121624")), (1, hexc("#262c3c"))])
    for k in range(60):
        r = random.Random(k)
        rgb(ctx, (1, 1, 1), 0.25 + 0.25 * math.sin(t + k)); ctx.arc(r.uniform(0, W), r.uniform(0, 700), r.uniform(0.8, 1.8), 0, 6.283); ctx.fill()
    glow(ctx, 820, 330, 300, MOON, 0.18)
    rgb(ctx, hexc("#dfe5f2")); ctx.arc(820, 330, 48, 0, 6.283); ctx.fill()


def fireplace(ctx, t, x=820, y=FLOOR):
    rgb(ctx, hexc("#2a231c")); ctx.rectangle(x - 200, y - 420, 400, 420); ctx.fill()
    rgb(ctx, hexc("#0a0806")); ctx.rectangle(x - 130, y - 260, 260, 260); ctx.fill()
    fl = 0.8 + 0.2 * wobble(t, 2, 7)
    glow(ctx, x, y - 90, 700 * fl, FIRE, 0.45)
    r = random.Random(int(t * 18))
    for k in range(10):
        rgb(ctx, (1, r.uniform(0.35, 0.75), 0.1), 0.7)
        ctx.save(); ctx.translate(x + r.uniform(-80, 80), y - 50 - r.uniform(0, 110)); ctx.scale(0.45, 1)
        ctx.arc(0, 0, r.uniform(16, 36), 0, 6.283); ctx.restore(); ctx.fill()
    rgb(ctx, hexc("#3a3027")); ctx.rectangle(x - 230, y - 440, 460, 30); ctx.fill()


def hallway(ctx, t, door_open=0.0, lamp=0.6):
    room(ctx)
    rgb(ctx, hexc("#0b0907")); ctx.move_to(250, FLOOR); ctx.line_to(440, 640); ctx.line_to(640, 640); ctx.line_to(830, FLOOR); ctx.close_path(); ctx.fill()
    rgb(ctx, hexc("#2c251e")); ctx.rectangle(460, 660, 160, 260); ctx.fill()           # basement door
    if door_open > 0:
        rgb(ctx, (0, 0, 0)); ctx.rectangle(460, 660, 160 * min(1, door_open * 1.2), 260); ctx.fill()
        rgb(ctx, hexc("#3a3128")); ctx.move_to(460, 660); ctx.line_to(460 - 60 * door_open, 640); ctx.line_to(460 - 60 * door_open, 940); ctx.line_to(460, 920); ctx.close_path(); ctx.fill()
    rgb(ctx, hexc("#8a7a60")); ctx.arc(600, 800, 6, 0, 6.283); ctx.fill()
    glow(ctx, 540, 600, 260, (1, 0.8, 0.55), 0.35 * lamp)
    rgb(ctx, (1, 0.85, 0.6), lamp); ctx.arc(540, 590, 10, 0, 6.283); ctx.fill()
    depth_haze(ctx, 600, 1000, (0.05, 0.045, 0.04), 0.5)


def photo_frame(ctx, t):
    rgb(ctx, hexc("#120f0c")); ctx.paint()
    glow(ctx, 760, 1000, 600, FIRE, 0.35 + 0.08 * wobble(t, 1, 6))
    rgb(ctx, hexc("#4a3a28")); rrect(ctx, 280, 520, 520, 660, 16); ctx.fill()
    rgb(ctx, hexc("#d8ccb4")); ctx.rectangle(320, 560, 440, 580); ctx.fill()
    rgb(ctx, (0.55, 0.5, 0.45)); ctx.arc(540, 760, 90, 0, 6.283); ctx.fill()          # sepia portrait
    rrect(ctx, 420, 860, 240, 280, 60); ctx.fill()
    rgb(ctx, (0.45, 0.4, 0.35)); ctx.arc(540, 730, 100, math.pi, 2 * math.pi); ctx.fill()
    rgb(ctx, hexc("#2a2219")); ctx.rectangle(0, 1180, W, 40); ctx.fill()


def basement_stairs(ctx, t, beam=0.0, ghost=0.0):
    rgb(ctx, hexc("#060504")); ctx.paint()
    for k in range(9):
        y = 650 + k * 120; w = 300 + k * 70
        rgb(ctx, hexc("#211b15")); ctx.rectangle(540 - w / 2, y, w, 26); ctx.fill()
        rgb(ctx, hexc("#120e0b")); ctx.rectangle(540 - w / 2, y + 26, w, 94); ctx.fill()
    if beam > 0:
        ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
        cone(ctx, 540, 1900, -math.pi / 2 + 0.05 * math.sin(t * 2), 0.16, 1500, (1, 0.95, 0.8), 0.35 * beam); ctx.restore()
    if ghost > 0:                                           # a figure at the bottom, barely there
        ctx.push_group()
        person(ctx, 540, 780, 300, "idle", face=1, pal=((0.1, 0.1, 0.12),) * 4)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(ghost)


def furnace(ctx, t, crack=1.0, smoke=0.0):
    room(ctx, wall=("#100d0b", "#1a1511"), floor=("#141210", "#070605"))
    rgb(ctx, hexc("#3a3631")); rrect(ctx, 290, 560, 500, 790, 24); ctx.fill()
    rgb(ctx, hexc("#2a2622")); ctx.rectangle(330, 600, 420, 300); ctx.fill()
    rgb(ctx, hexc("#4a453f")); ctx.set_line_width(56); ctx.move_to(540, 560); ctx.line_to(540, 330); ctx.line_to(1000, 330); ctx.stroke()
    pulse = 0.7 + 0.3 * math.sin(t * 3) * math.sin(t * 1.1)
    g = crack * pulse
    glow(ctx, 540, 1050, 520, EMBER, 0.45 * g)
    rgb(ctx, (1, 0.55, 0.15), g); ctx.set_line_width(7)
    ctx.move_to(470, 950); ctx.line_to(510, 1010); ctx.line_to(490, 1060); ctx.line_to(560, 1130); ctx.line_to(540, 1180); ctx.stroke()
    for k in range(6):
        rgb(ctx, (1, 0.5, 0.15), 0.6 * g); ctx.rectangle(360 + k * 60, 1250, 36, 12); ctx.fill()
    if smoke > 0:
        Particles(40, 4, (300, 300, 1080, 1200), vel=(-60, 15), size=(30, 70), col=(0.35, 0.33, 0.3), alpha=0.12 * smoke).draw(ctx, t)


def motel(ctx, t, vent_on=False):
    room(ctx, wall=("#0e1018", "#171a26"), floor=("#12141c", "#06070a"))
    neon = 0.7 + 0.3 * (math.sin(t * 9) > -0.8)
    rgb(ctx, (0.9, 0.2, 0.5), 0.25 * neon); ctx.rectangle(700, 300, 260, 520); ctx.fill()
    god_rays(ctx, t, 830, 560, angle=math.pi * 0.75, length=900, spread=0.25, n=5, col=(0.9, 0.3, 0.6), alpha=0.07 * neon)
    rgb(ctx, hexc("#2a2c3a")); rrect(ctx, 120, 1060, 760, 220, 30); ctx.fill()
    rgb(ctx, hexc("#d8d6e0"), 0.5); rrect(ctx, 140, 1030, 220, 80, 30); ctx.fill()
    rgb(ctx, hexc("#3c4256")); rrect(ctx, 300, 1000, 520, 120, 50); ctx.fill()
    dog(ctx, 760, 1080, 110, "sit", face=-1, wag=0)
    if vent_on:
        vent(ctx, t, 540, 230, 260, 120, glow_a=0.15)


# ------------------------------------------------------------------ PART 1
def p1s1(ctx, t, d):
    with camera(ctx, t, d, push=0.14, handheld=0.5, focus=(540, 900)):
        rgb(ctx, hexc("#0c0a08")); ctx.paint()
        vent(ctx, t, 540, 980, 860, 480, glow_a=0.45)
        dust(ctx, t, (100, 300, 1000, 1500), light=(540, 1050))
    rgb(ctx, (0, 0, 0), 0.0)
    shot_card(ctx, t, text, "HEAR THAT?", 0.0, y=330, size=170, col=(1, 0.9, 0.75))
    flicker_dim(ctx, t, 0.3)
    finish(ctx, t, d, v=0.95, fi=0.0)


def p1s2(ctx, t, d):
    with camera(ctx, t, d, push=0.07, handheld=0.4, focus=(540, 1050)):
        night_snow_sky(ctx, t)
        rgb(ctx, hexc("#0d0f16")); ctx.move_to(0, 1150); ctx.curve_to(300, 1080, 700, 1120, W, 1060); ctx.line_to(W, 1250); ctx.line_to(0, 1250); ctx.fill()
        depth_haze(ctx, 900, 1250, (0.15, 0.17, 0.24), 0.4)
        farmhouse(ctx, t)
        snow_ground(ctx)
        soft_shadow(ctx, 540, 1255, 700, 0.4)
        fog(ctx, t, 1180, 1400, (0.6, 0.65, 0.75), 0.2)
        SNOW.draw(ctx, t)
    finish(ctx, t, d, v=0.8)


def p1s3(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(540, 1250)):
        room(ctx)
        fireplace(ctx, t)
        soft_shadow(ctx, 470, FLOOR + 5, 420)
        backlight(ctx, 470, 1200, 380, FIRE, 0.25)
        dog(ctx, 470, FLOOR, 240, "stand", face=1, wag=0.3 * math.sin(t * 2), head_up=0.2)
        dust(ctx, t, (300, 600, 1080, 1350), light=(820, 1250), col=(1, 0.8, 0.6))
    shot_card(ctx, t, text, "MOOSE", T1.at(3, 0) + 0.3, y=360, size=130, col=(1, 0.8, 0.55))
    finish(ctx, t, d, v=0.8)


def bedroom(ctx, t, sit=0.0):
    room(ctx, wall=("#0d1016", "#161b24"))
    rgb(ctx, hexc("#05070c")); ctx.rectangle(640, 420, 280, 380); ctx.fill()
    god_rays(ctx, t, 780, 600, angle=math.pi * 0.7, length=1200, spread=0.2, n=6, col=MOON, alpha=0.08)
    rgb(ctx, hexc("#2a2f3e")); ctx.set_line_width(14); ctx.rectangle(640, 420, 280, 380); ctx.stroke()
    rgb(ctx, hexc("#222634")); rrect(ctx, 120, 1120, 720, 230, 24); ctx.fill()
    rgb(ctx, hexc("#3a4058")); rrect(ctx, 260, 1080, 560, 120, 40); ctx.fill()
    if sit > 0:
        person(ctx, 300, 1250, SP * 0.9, "sit", face=1, lean=-0.1 + 0.2 * sit, head_turn=-0.6 * sit)


def p1s4(ctx, t, d):
    with camera(ctx, t, d, push=0.05, handheld=0.4, focus=(540, 1150)):
        bedroom(ctx, t, sit=ease(min(1, t / 1.0)))
    flicker_dim(ctx, t, 0.2)
    finish(ctx, t, d, v=0.9)


def p1s5(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.5, focus=(540, 800)):
        hallway(ctx, t, lamp=0.5)
        fog(ctx, t, 1200, 1500, (0.35, 0.32, 0.3), 0.18)
    flicker_dim(ctx, t, 0.35, seed=2)
    finish(ctx, t, d, v=0.95)


def p1s6(ctx, t, d):
    growl = math.sin(t * 25) * 0.05 * (t > T1.at(6, 1))
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 1200), shake=0.08 * (t > T1.at(6, 1))):
        rgb(ctx, hexc("#070605")); ctx.paint()
        rgb(ctx, hexc("#1c1712")); ctx.rectangle(0, FLOOR, W, H); ctx.fill()
        rgb(ctx, (0, 0, 0)); ctx.rectangle(380, 520, 420, FLOOR - 520); ctx.fill()     # stairwell opening
        glow(ctx, 590, 420, 400, (1, 0.8, 0.55), 0.18)
        soft_shadow(ctx, 380, FLOOR + 4, 420)
        dog(ctx, 380, FLOOR, 300 + 6 * math.sin(t * 20) * (growl != 0), "stand", face=1, head_up=-0.2, bark=0.25 * (growl != 0))
    finish(ctx, t, d, v=0.95)


def p1s7(ctx, t, d):
    lvl = ease(t / d)
    with camera(ctx, t, d, push=0.05, handheld=0.3, focus=(540, 900)):
        rgb(ctx, hexc("#0c0f16")); ctx.paint()
        rgb(ctx, hexc("#1a1e2a")); rrect(ctx, 200, 380, 680, 900, 20); ctx.fill()
        ctx.save(); ctx.rectangle(230, 410, 620, 840); ctx.clip()
        night_snow_sky(ctx, t)
        STORM.draw(ctx, t)
        top = lerp(1250, 620, lvl)
        rgb(ctx, (0.85, 0.9, 1.0)); ctx.move_to(230, 1260)
        for x in range(230, 860, 40):
            ctx.line_to(x, top + 20 * math.sin(x * 0.02 + 1))
        ctx.line_to(850, 1260); ctx.close_path(); ctx.fill()
        ctx.restore()
        rgb(ctx, hexc("#2a2f3e")); ctx.set_line_width(18); ctx.move_to(540, 400); ctx.line_to(540, 1260); ctx.stroke(); ctx.move_to(220, 830); ctx.line_to(860, 830); ctx.stroke()
    shot_card(ctx, t, text, "3 FEET", T1.at(7, 1), y=300, size=150)
    finish(ctx, t, d)


def p1s8(ctx, t, d):
    with camera(ctx, t, d, push=0.1, handheld=0.6, focus=(540, 900), roll=0.02):
        room(ctx, wall=("#12141a", "#1c1f27"))
        rgb(ctx, hexc("#8d9099"), 0.5); rrect(ctx, 260, 360, 560, 620, 20); ctx.fill()
        rgb(ctx, hexc("#2a2d36")); ctx.set_line_width(16); rrect(ctx, 260, 360, 560, 620, 20); ctx.stroke()
        backlight(ctx, 540, 700, 420, (0.8, 0.85, 1.0), 0.2)
        rgb(ctx, hexc("#d5d6db")); rrect(ctx, 220, 1080, 640, 160, 20); ctx.fill()
        for k in range(2):                                   # doubled image = headache
            ctx.push_group()
            person(ctx, 540 + k * 14 * math.sin(t * 2), 1500, 880, "idle", face=1, head_turn=0.1, arm_f=(2.3, 0.7))
            ctx.pop_group_to_source(); ctx.paint_with_alpha(1.0 if k == 0 else 0.3)
    flicker_dim(ctx, t, 0.15)
    finish(ctx, t, d, v=0.9)


def p1s9(ctx, t, d):
    with camera(ctx, t, d, push=0.18, handheld=0.4, focus=(540, 900)):
        rgb(ctx, hexc("#0a0908")); ctx.paint()
        vent(ctx, t, glow_a=0.45)
    shot_card(ctx, t, text, "YOUR NAME", T1.at(9, 0) + 1.2, y=330, size=140, col=(1, 0.85, 0.7))
    flicker_dim(ctx, t, 0.35)
    finish(ctx, t, d, v=0.95)


def p1s10(ctx, t, d):
    with camera(ctx, t, d, push=0.1, handheld=0.3, focus=(540, 860)):
        photo_frame(ctx, t)
        dust(ctx, t, (200, 400, 900, 1300), light=(760, 1000))
    finish(ctx, t, d, v=0.9)


def p1s11(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.3, focus=(400, 1300)):
        room(ctx)
        rgb(ctx, hexc("#2c251e")); ctx.rectangle(720, 700, 260, FLOOR - 700); ctx.fill()
        rgb(ctx, (0, 0, 0)); ctx.rectangle(720, FLOOR - 6, 260, 6); ctx.fill()
        glow(ctx, 300, 900, 500, FIRE, 0.18)
        soft_shadow(ctx, 360, FLOOR + 4, 380)
        dog(ctx, 360, FLOOR, 160, "sit", face=1, head_up=0.0, wag=0)
    finish(ctx, t, d, v=0.95)


def p1s12(ctx, t, d):
    op = ease(prog(t, T1.at(12, -1) + 0.4, d - 0.3))
    with camera(ctx, t, d, push=0.2, handheld=0.4, focus=(540, 790)):
        hallway(ctx, t, door_open=op, lamp=0.4 * (1 - 0.6 * op))
        fog(ctx, t, 1150, 1450, (0.3, 0.28, 0.26), 0.2)
    flicker_dim(ctx, t, 0.4, seed=4)
    finish(ctx, t, d, v=1.0)


def p1s13(ctx, t, d):
    with camera(ctx, t, d, push=0.05, handheld=0.4, focus=(540, 790)):
        hallway(ctx, t, door_open=1.0, lamp=0.15)
    rgb(ctx, (0, 0, 0), 0.45); ctx.paint()
    end_card(ctx, t, T1, 13, "HEAR", "THAT?", "COMMENT: YES OR NO", "PART 2 IS UP NEXT")
    finish(ctx, t, d, fo=0.25)


# ------------------------------------------------------------------ PART 2
def p2s1(ctx, t, d):
    with camera(ctx, t, d, push=0.15, handheld=0.5, focus=(540, 790)):
        hallway(ctx, t, door_open=1.0, lamp=0.3)
    shot_card(ctx, t, text, "HEAR THAT?", 0.0, y=330, size=170, col=(1, 0.9, 0.75))
    flicker_dim(ctx, t, 0.35)
    finish(ctx, t, d, v=1.0, fi=0.0)


def p2s2(ctx, t, d):
    fall = ease(prog(t, T2.at(2, -1), T2.at(2, -1) + 0.6))
    with camera(ctx, t, d, push=0.05, handheld=0.5, focus=(540, 1250)):
        room(ctx)
        glow(ctx, 900, 900, 600, FIRE, 0.15)
        info = person(ctx, 640, FLOOR, SP, "idle", face=-1, arm_f=(1.5, -0.1))
        hx, hy = info["hand"]
        rgb(ctx, hexc("#2b2b2b")); rrect(ctx, hx - 50, hy - 16, 60, 30, 6); ctx.fill()
        ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
        cone(ctx, hx - 50, hy, math.pi + 0.15, 0.18, 900, (1, 0.95, 0.8), 0.3); ctx.restore()
        soft_shadow(ctx, 300, FLOOR + 4, 380)
        dog(ctx, 300, FLOOR + 40 * fall, 180, "stand" if fall < 0.5 else "sit", face=1, head_up=-0.3 * fall)
    finish(ctx, t, d, v=0.95)


def p2s3(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.6, focus=(540, 900), pan=(0, -120)):
        basement_stairs(ctx, t, beam=1.0)
        dust(ctx, t, (300, 500, 800, 1600), light=(540, 1100))
    finish(ctx, t, d, v=1.0)


def p2s4(ctx, t, d):
    with camera(ctx, t, d, push=0.1, handheld=0.4, focus=(540, 1000)):
        furnace(ctx, t)
        fog(ctx, t, 1150, 1450, (0.3, 0.25, 0.2), 0.2)
        dust(ctx, t, (200, 400, 900, 1300), light=(540, 1050), col=(1, 0.7, 0.4))
    finish(ctx, t, d, v=0.95)


def p2s5(ctx, t, d):
    with camera(ctx, t, d, push=0.04, handheld=0.9, focus=(540, 1200), roll=0.05):
        furnace(ctx, t, crack=0.8)
        for k in range(2):
            ctx.push_group()
            person(ctx, 820 + k * 20 * math.sin(t * 1.5), FLOOR, SP, "idle", face=-1, lean=-0.2, arm_f=(1.4, 0.2), head_turn=0.3)
            ctx.pop_group_to_source(); ctx.paint_with_alpha(1.0 if k == 0 else 0.35)
    finish(ctx, t, d, v=0.95)


def p2s6(ctx, t, d):
    with camera(ctx, t, d, handheld=0.3):
        furnace(ctx, t, crack=0.6)
    rgb(ctx, (0, 0, 0), 0.6); ctx.paint()
    rule_card(ctx, t, T2.at(6, 0), [("THE QUIET KILLER", T2.at(6, -1))], title="CARBON MONOXIDE")
    finish(ctx, t, d, fi=0.0)


def p2s7(ctx, t, d):
    with camera(ctx, t, d, handheld=0.3):
        furnace(ctx, t, crack=0.6)
    rgb(ctx, (0, 0, 0), 0.6); ctx.paint()
    seg = T2.seg.get(7, [])
    tk = lambda k: seg[min(k, len(seg) - 1)][1] if seg else 0.5 + k
    rule_card(ctx, t, -1, [("NO SMELL. NO COLOUR.", tk(0)), ("HEADACHE, DIZZY, CONFUSED", tk(1)),
                           ("SOME HEAR THINGS", tk(2)), ("PETS GET SICK FIRST", tk(3))], title="CARBON MONOXIDE")
    finish(ctx, t, d, fi=0.0)


def p2s8(ctx, t, d):
    k = min(2, int(t / max(0.1, d / 3)))
    with camera(ctx, t, d, push=0.1, handheld=0.6):
        if k == 0:
            room(ctx, wall=("#12141a", "#1c1f27")); person(ctx, 540, 1500, 880, "idle", face=1, arm_f=(2.3, 0.7))
        elif k == 1:
            room(ctx); glow(ctx, 700, 1000, 500, FIRE, 0.15); dog(ctx, 540, FLOOR, 220, "sit", face=1, head_up=-0.4)
        else:
            rgb(ctx, hexc("#0a0908")); ctx.paint(); vent(ctx, t, glow_a=0.5)
    flicker_dim(ctx, t, 0.4)
    finish(ctx, t, d, v=1.0, fi=0.0, fo=0.0)


def p2s9(ctx, t, d):
    with camera(ctx, t, d, push=0.1, handheld=0.4, focus=(800, 600), pan=(-200, 0)):
        rgb(ctx, hexc("#16120f")); ctx.paint()
        rgb(ctx, hexc("#2a231c")); ctx.rectangle(700, 0, 140, H); ctx.fill()             # wall section
        rgb(ctx, hexc("#4a453f")); ctx.set_line_width(56); ctx.move_to(0, 600); ctx.line_to(770, 600); ctx.stroke()
        rgb(ctx, hexc("#0b0d14")); ctx.rectangle(840, 0, 240, H); ctx.fill()             # outside
        rgb(ctx, (0.85, 0.9, 1.0)); ctx.move_to(840, 380)
        for y in range(380, H, 60):
            ctx.line_to(840 + 120 + 30 * math.sin(y * 0.03), y)
        ctx.line_to(1080, H); ctx.line_to(1080, 380); ctx.fill()
        STORM.draw(ctx, t)
        glow(ctx, 770, 600, 220, EMBER, 0.2)
    shot_card(ctx, t, text, "BURIED", T2.at(9, -1) + 0.4, y=1500, size=150, col=(0.8, 0.9, 1))
    finish(ctx, t, d)


def p2s10(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 900)):
        furnace(ctx, t, smoke=ease(t / d))
        fog(ctx, t, 300, 1300, (0.32, 0.3, 0.28), 0.15 * ease(t / d), puffs=12)
    finish(ctx, t, d, v=1.0)


def p2s11(ctx, t, d):
    with camera(ctx, t, d, push=-0.08, handheld=1.0, focus=(540, 900), roll=0.06):
        for k in range(3):
            ctx.push_group()
            ctx.translate(18 * k * math.sin(t * 1.3 + k), 0)
            basement_stairs(ctx, t, beam=0.6)
            ctx.pop_group_to_source(); ctx.paint_with_alpha(1.0 if k == 0 else 0.3)
    finish(ctx, t, d, v=1.0)


def p2s12(ctx, t, d):
    with camera(ctx, t, d, push=0.22, handheld=0.5, focus=(540, 700)):
        basement_stairs(ctx, t, beam=0.4, ghost=0.35 * ease(prog(t, T2.at(12, -1) - 0.5, d)))
        rgb(ctx, (1, 0.85, 0.6), 0.25); ctx.rectangle(440, 330, 200, 260); ctx.fill()     # doorway at the top
        ctx.push_group()
        person(ctx, 540, 590, 240, "idle", face=1, pal=((0.05, 0.05, 0.06),) * 4)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(0.8 * prog(t, T2.at(12, -1), d))
    flicker_dim(ctx, t, 0.4, seed=5)
    finish(ctx, t, d, v=1.0)


def p2s13(ctx, t, d):
    with camera(ctx, t, d, handheld=0.4):
        basement_stairs(ctx, t, beam=0.3)
    rgb(ctx, (0, 0, 0), 0.45); ctx.paint()
    end_card(ctx, t, T2, 13, "GET", "OUT?", "COMMENT: YES OR NO", "PART 3 IS UP NEXT")
    finish(ctx, t, d, fo=0.25)


# ------------------------------------------------------------------ PART 3
def p3s1(ctx, t, d):
    with camera(ctx, t, d, push=0.1, handheld=0.9, focus=(540, 1200), roll=0.05):
        furnace(ctx, t, smoke=0.8)
        person(ctx, 540, FLOOR, SP, "sit", face=-1, lean=0.4, breathe=math.sin(t * 5))
    shot_card(ctx, t, text, "GET OUT.", 0.0, y=330, size=170, col=(1, 0.5, 0.4))
    finish(ctx, t, d, v=1.0, fi=0.0)


def p3s2(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.8, focus=(540, 1100), pan=(0, -200)):
        basement_stairs(ctx, t, beam=0.5)
        person(ctx, 540, 1300 - 200 * (t / d), 330, "idle", face=1, crouch=0.9, lean=0.6, back_view=True)
    finish(ctx, t, d, v=1.0)


def p3s3(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.5, focus=(540, 1250)):
        room(ctx)
        rgb(ctx, hexc("#2c251e")); ctx.rectangle(820, 640, 240, FLOOR - 640); ctx.fill()
        backlight(ctx, 540, 1200, 420, (0.8, 0.85, 1.0), 0.15)
        soft_shadow(ctx, 640, FLOOR + 4, 400)
        dog(ctx, 640, FLOOR, 170, "sit", face=-1, head_up=-0.4)
        person(ctx, 380, FLOOR, SP, "idle", face=1, crouch=0.7, arm_f=(1.2, 0.3))
    finish(ctx, t, d, v=0.95)


def p3s4(ctx, t, d):
    op = ease(prog(t, T3.at(4, -1), T3.at(4, -1) + 0.5))
    with camera(ctx, t, d, push=0.06, handheld=0.6, focus=(700, 1100), shake=0.25 * op * (t < T3.at(4, -1) + 1)):
        room(ctx)
        ctx.save(); ctx.rectangle(720, 560, 300, FLOOR - 560); ctx.clip()
        rgb(ctx, (0.75, 0.8, 0.95)); ctx.paint(); STORM.draw(ctx, t)
        ctx.restore()
        rgb(ctx, hexc("#2c251e")); ctx.rectangle(720, 560, 300 * (1 - op), FLOOR - 560); ctx.fill()
        if op > 0:
            god_rays(ctx, t, 870, 700, angle=math.pi * 0.85, length=1400, spread=0.3, n=7, col=(0.8, 0.88, 1.0), alpha=0.18 * op)
        person(ctx, lerp(300, 560, ease(t / d)), FLOOR, SP, "walk", phase=t * 3, face=1, lean=0.3, arm_b=(-0.8, 0.3))
        dog(ctx, lerp(150, 410, ease(t / d)), FLOOR, 150, "sit", face=1, head_up=-0.4)
    finish(ctx, t, d, v=0.8)


def p3s5(ctx, t, d):
    with camera(ctx, t, d, push=0.08, handheld=0.4, focus=(540, 1250)):
        night_snow_sky(ctx, t); snow_ground(ctx)
        farmhouse(ctx, t, lit=0.6, x=820, base=1150)
        soft_shadow(ctx, 420, 1405, 420)
        person(ctx, 420, 1400, SP, "sit", face=1, breathe=math.sin(t * 2.5), head_turn=0.4)
        dog(ctx, 600, 1400, 150, "sit", face=-1, head_up=0.0)
        for k in range(3):
            p = ((t * 0.6 + k / 3) % 1)
            rgb(ctx, (1, 1, 1), 0.35 * (1 - p)); ctx.arc(470 + p * 60, 1020 - p * 80, 18 + 30 * p, 0, 6.283); ctx.fill()
        SNOW.draw(ctx, t)
    finish(ctx, t, d, v=0.7)


def p3s6(ctx, t, d):
    with camera(ctx, t, d, push=0.05, handheld=0.2, focus=(540, 1050)):
        night_snow_sky(ctx, t)
        farmhouse(ctx, t, lit=0.0)
        snow_ground(ctx)
        SNOW.draw(ctx, t)
    finish(ctx, t, d, v=0.8)


def p3s7(ctx, t, d):
    with camera(ctx, t, d, push=0.12, handheld=0.8, focus=(540, 900)):
        rgb(ctx, hexc("#0c0e14")); ctx.paint()
        SNOW.draw(ctx, t)
        glow(ctx, 540, 900, 600, (0.6, 0.8, 1), 0.3)
        rgb(ctx, hexc("#0a0a0c")); rrect(ctx, 330, 520, 420, 800, 50); ctx.fill()
        rgb(ctx, (0.2, 0.75, 0.4)); rrect(ctx, 355, 560, 370, 720, 30); ctx.fill()
        text(ctx, "911", 540, 820, 160, (1, 1, 1))
        text(ctx, "CALLING...", 540, 960, 56, (1, 1, 1), 0.6 + 0.4 * math.sin(t * 4))
        for side in (-1, 1):
            rgb(ctx, hexc("#c49a7a")); ctx.arc(540 + side * 230, 1150, 70, 0, 6.283); ctx.fill()
    finish(ctx, t, d, v=0.8)


def p3s8(ctx, t, d):
    lift = ease(prog(t, 0.3, T3.at(8, 1)))
    with camera(ctx, t, d, push=0.12, handheld=0.3, focus=(540, 1250)):
        night_snow_sky(ctx, t); snow_ground(ctx, 1150)
        backlight(ctx, 540, 1150, 500, (0.9, 0.9, 1.0), 0.15)
        dog(ctx, 540, 1450, 380, "sit", face=1, head_up=0.6 * lift - 0.3, wag=math.sin(t * 9) * prog(t, T3.at(8, -1), T3.at(8, -1) + 0.3))
        SNOW.draw(ctx, t)
    finish(ctx, t, d, v=0.7)


def p3s9(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.4, focus=(540, 1100)):
        night_snow_sky(ctx, t); snow_ground(ctx)
        farmhouse(ctx, t, lit=0.0, x=760, base=1180)
        rgb(ctx, hexc("#8a1c18")); rrect(ctx, 60, 1080, 520, 220, 16); ctx.fill(); rrect(ctx, 420, 980, 160, 160, 12); ctx.fill()
        rgb(ctx, hexc("#111111"))
        ctx.arc(160, 1310, 50, 0, 6.283); ctx.fill(); ctx.arc(470, 1310, 50, 0, 6.283); ctx.fill()
        on = (t * 2.5) % 1 < 0.5
        glow(ctx, 470, 960, 160, (1, 0.2, 0.15) if on else (0.2, 0.4, 1), 0.9)
        ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
        rgb(ctx, (1, 0.15, 0.1) if on else (0.15, 0.3, 1), 0.12); ctx.paint(); ctx.restore()
        for k in range(2):
            person(ctx, 680 + k * 170, 1380, 400, "walk", phase=t * 4 + k, face=-1, pal=((0.75, 0.6, 0.15), (0.6, 0.45, 0.1), (0.2, 0.2, 0.2), (0.15, 0.15, 0.15)))
        SNOW.draw(ctx, t)
    finish(ctx, t, d, v=0.7)


def p3s10(ctx, t, d):
    with camera(ctx, t, d, push=-0.08, handheld=0.2, focus=(540, 1050)):
        night_snow_sky(ctx, t); farmhouse(ctx, t, lit=0.0); snow_ground(ctx)
        on = (t * 2.5) % 1 < 0.5
        ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
        rgb(ctx, (1, 0.15, 0.1) if on else (0.15, 0.3, 1), 0.08); ctx.paint(); ctx.restore()
        SNOW.draw(ctx, t)
    shot_card(ctx, t, text, "NO GHOSTS.", 0.3, y=330, size=150)
    finish(ctx, t, d, v=0.8)


def p3s11(ctx, t, d):
    with camera(ctx, t, d, handheld=0.2):
        night_snow_sky(ctx, t); farmhouse(ctx, t, lit=0.0); snow_ground(ctx)
    rgb(ctx, (0, 0, 0), 0.6); ctx.paint()
    seg = T3.seg.get(11, [])
    tk = lambda k: seg[min(k, len(seg) - 1)][1] if seg else 0.5 + k
    rule_card(ctx, t, 0.0, [("EVERYONE SICK AT ONCE?", 0.2), ("GET OUT. GET AIR.", tk(1) if len(seg) > 1 else 2),
                            ("CALL FOR HELP.", tk(1) + 1.0 if len(seg) > 1 else 3), ("GET A CO ALARM.", tk(len(seg) - 1))],
              title="CARBON MONOXIDE")
    finish(ctx, t, d, fi=0.0)


def p3s12(ctx, t, d):
    with camera(ctx, t, d, push=0.06, handheld=0.2, focus=(540, 1100)):
        motel(ctx, t)
    finish(ctx, t, d, v=0.8)


def p3s13(ctx, t, d):
    with camera(ctx, t, d, push=0.25, handheld=0.4, focus=(540, 300)):
        motel(ctx, t, vent_on=True)
    rgb(ctx, (0, 0, 0), 0.3 * ease(t / d)); ctx.paint()
    flicker_dim(ctx, t, 0.4)
    finish(ctx, t, d, v=1.0)


def p3s14(ctx, t, d):
    with camera(ctx, t, d, handheld=0.3, focus=(540, 300)):
        motel(ctx, t, vent_on=True)
    rgb(ctx, (0, 0, 0), 0.55); ctx.paint()
    end_card(ctx, t, T3, 14, "HEAR", "THAT?", "COMMENT: YES OR NO", "NEW STORY TOMORROW")
    finish(ctx, t, d, fo=0.4)


P1 = [p1s1, p1s2, p1s3, p1s4, p1s5, p1s6, p1s7, p1s8, p1s9, p1s10, p1s11, p1s12, p1s13]
P2 = [p2s1, p2s2, p2s3, p2s4, p2s5, p2s6, p2s7, p2s8, p2s9, p2s10, p2s11, p2s12, p2s13]
P3 = [p3s1, p3s2, p3s3, p3s4, p3s5, p3s6, p3s7, p3s8, p3s9, p3s10, p3s11, p3s12, p3s13, p3s14]


# ------------------------------------------------------------------ sound
def roomtone(d, seed):
    t = np.arange(int(d * SR)) / SR
    return band_noise(d, 40, 220, seed) * 0.05 + np.sin(2 * np.pi * 50 * t) * 0.01


def creaks(d, times, seed=0):
    x = silence(d)
    for k, c in enumerate(times):
        i, n = int(c * SR), int(0.45 * SR)
        if i + n > len(x):
            continue
        tt = np.arange(n) / SR
        f = 180 + 120 * np.sin(np.pi * tt / 0.45) + np.random.default_rng(seed + k).uniform(-30, 30)
        saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
        x[i:i + n] += saw * np.sin(np.pi * tt / 0.45) ** 2 * 0.06
    return x


def furnace_rumble(d, seed):
    t = np.arange(int(d * SR)) / SR
    return band_noise(d, 25, 160, seed) * (0.25 + 0.1 * np.sin(2 * np.pi * 0.3 * t)) + np.sin(2 * np.pi * 38 * t) * 0.06


def breathing(d, rate=0.35, amt=0.12, seed=0):
    t = np.arange(int(d * SR)) / SR
    env = np.clip(np.sin(2 * np.pi * rate * t), 0, 1) ** 2
    return band_noise(d, 400, 2500, seed) * env * amt


def siren(d):
    t = np.arange(int(d * SR)) / SR
    f = np.where((t * 0.8) % 1 < 0.5, 700, 950)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.06


def sfx_for(tm, part):
    def sfx(i, d):
        t = np.arange(int(d * SR)) / SR
        x = roomtone(d, i + 10 * part)
        outside = (part == 1 and i in (2, 7)) or (part == 3 and i >= 5 and i <= 11)
        if outside:
            x = wind(d, 1.0, i) * 1.2 + band_noise(d, 2000, 7000, i) * 0.03
        if part == 1:
            if i in (1, 9):
                x += furnace_rumble(d, i) * 0.5
            if i in (4, 5, 12):
                x += creaks(d, [1.0 + k * 1.7 for k in range(int(d / 1.7))], i)
            if i == 6:
                g = tm.at(6, 1)
                x += band_noise(d, 60, 260, 66) * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t)) * 0.35 * (t > g)
            if i == 12:
                op = tm.at(12, -1) + 0.4
                x += creaks(d, [op], 99) * 3
            if i == 3:
                x += band_noise(d, 1500, 8000, 3) * 0.04 * (np.random.default_rng(3).random(len(t)) > 0.995)
        elif part == 2:
            if i in (3,):
                x += creaks(d, [0.4 + k * 0.6 for k in range(int(d / 0.6))], 3) * 1.5
                x *= np.where(t > tm.at(3, -1), 0.2, 1.0)               # the whispering stops: near silence
            if i in (4, 5, 6, 7, 10):
                x += furnace_rumble(d, i)
            if i in (5, 8, 11, 12):
                x += breathing(d, 0.45, 0.1, i) + L.heart(d, 96) * 0.5
            if i == 9:
                x += wind(d, 1.0, 9) * 0.8
        else:
            if i in (1, 2, 3):
                x += breathing(d, 0.5, 0.14, i) + L.heart(d, 110) * 0.5
            if i == 4:
                op = tm.at(4, -1)
                x = np.where(t < op, x, wind(d, 1.6, 4) * 1.4) + env_at(d, [op], 0.4) * band_noise(d, 100, 3000, 44) * 0.8
            if i == 5:
                x += breathing(d, 0.3, 0.18, 5)
            if i == 6:
                x *= 0.5
            if i == 7:
                x += env_at(d, list(np.arange(0.8, d, 3.0)), 1.0) * tone(d, 440) * 0.04
            if i in (9, 10):
                x += siren(d)
            if i == 12:
                x = roomtone(d, 12) * 0.6 + band_noise(d, 100, 400, 12) * 0.02
            if i == 13:
                x = roomtone(d, 13) * 0.3                              # near silence before the last whisper
        return fades(x * 0.6, 0.03, 0.1)
    return sfx


def drone_score(total, seed=0):
    """Horror bed: low detuned drone + sparse high glints + slow pulse (no melody)."""
    t = np.arange(int(total * SR)) / SR
    x = (np.sin(2 * np.pi * 36.7 * t) * 0.25 + np.sin(2 * np.pi * 37.3 * t) * 0.25
         + np.sin(2 * np.pi * 55.0 * t) * 0.1 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t)))
    x += band_noise(total, 60, 300, seed) * 0.08
    glints = env_at(total, list(np.random.default_rng(seed).uniform(2, max(3, total - 2), int(total / 9))), 2.5)
    x += glints * np.sin(2 * np.pi * 1661 * t) * 0.02
    return fades(x.astype(np.float32) * 0.6, 2.0, 2.0)


def music1(durs):
    return drone_score(sum(durs), 1)


def music2(durs):
    return drone_score(sum(durs), 2)


def music3(durs):
    total = sum(durs)
    a = sum(durs[:4])                      # tense until the door opens
    b = sum(durs[:11])                     # warm while safe
    tense = drone_score(a, 3)
    warm = piano_score(b - a, b + 100, bpm=64, seed=7)
    tail = drone_score(total - b, 4) * 0.6
    return np.concatenate([tense, warm, tail])[: int(total * SR)]


PARTS = {1: ("29_hearthat_1", P1, sfx_for(T1, 1), music1), 2: ("30_hearthat_2", P2, sfx_for(T2, 2), music2),
         3: ("31_hearthat_3", P3, sfx_for(T3, 3), music3)}

if __name__ == "__main__":
    run(PARTS, {1: T1, 2: T2, 3: T3})
