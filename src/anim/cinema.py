"""Cinematic toolkit for scene modules: camera, atmosphere and light.

Typical scene:
    def s3(ctx, t, d):
        with camera(ctx, t, d, push=0.06, handheld=0.6, focus=(540, 1100)):
            ...draw background...
            depth_haze(ctx, 600, 1250, (0.05, 0.07, 0.1), 0.5)       # far layers fade into the air
            ...draw midground...
            soft_shadow(ctx, 540, 1300, 260)
            backlight(ctx, 540, 1000, 420, (1, 0.8, 0.5))            # halo behind the character
            person(ctx, 540, 1300, 430, ...)
            god_rays(ctx, t, 820, 140, angle=2.0, length=1600)       # light through a window
            fog(ctx, t, 1050, 1500, (0.6, 0.65, 0.7), 0.25)         # low ground fog
            dust(ctx, t, (300, 200, 1000, 1200), light=(820, 140))
        flicker_dim(ctx, t, amount=0.25)                              # unstable power
        finish(ctx, t, d)                                             # vignette + grain + fades (from lighthouse)

All helpers draw with cairo onto the current context; they cost a few ms each per frame.
"""
import math, random
from contextlib import contextmanager

import cairo

from engine import W, H, clamp, ease, glow, wobble


@contextmanager
def camera(ctx, t, d, push=0.0, handheld=0.0, focus=(W / 2, H / 2), pan=(0.0, 0.0), roll=0.0, shake=0.0):
    """Wrap a scene in camera motion.
    push: zoom-in amount over the shot (0.06 = 6%); negative pulls out.
    handheld: 0..1 slow organic drift; shake: 0..1 violent jitter (impacts).
    pan: (dx, dy) pixels travelled over the shot; roll: max tilt in radians."""
    ctx.save()
    p = ease(t / d) if d > 0 else 0
    z = 1 + push * p
    hx = (wobble(t, 1.3, 0.7) * 10 + wobble(t, 4.1, 2.3) * 3) * handheld
    hy = (wobble(t, 2.7, 0.6) * 8 + wobble(t, 5.9, 2.1) * 3) * handheld
    sx = wobble(t, 7.7, 45) * 22 * shake
    sy = wobble(t, 8.3, 41) * 22 * shake
    fx, fy = focus
    ctx.translate(fx + hx + sx - pan[0] * p, fy + hy + sy - pan[1] * p)
    ctx.rotate(roll * wobble(t, 3.3, 0.4) + 0.004 * handheld * wobble(t, 9.1, 0.5))
    ctx.scale(z * (1 + 0.012 * handheld), z * (1 + 0.012 * handheld))
    ctx.translate(-fx, -fy)
    try:
        yield
    finally:
        ctx.restore()


def fog(ctx, t, y0, y1, col=(0.7, 0.72, 0.78), alpha=0.25, speed=18, seed=0, puffs=9):
    """Drifting layer of soft fog between y0 and y1."""
    r = random.Random(seed)
    for k in range(puffs):
        rx = r.uniform(180, 420)
        x = (r.uniform(0, W + 2 * rx) + t * speed * r.uniform(0.6, 1.4)) % (W + 2 * rx) - rx
        y = r.uniform(y0, y1) + math.sin(t * 0.3 + k) * 15
        a = alpha * (0.6 + 0.4 * math.sin(t * 0.4 + k * 1.7))
        g = cairo.RadialGradient(x, y, 0, x, y, rx)
        g.add_color_stop_rgba(0, *col, a)
        g.add_color_stop_rgba(1, *col, 0)
        ctx.save(); ctx.translate(x, y); ctx.scale(1.0, 0.45); ctx.translate(-x, -y)
        ctx.set_source(g); ctx.arc(x, y, rx, 0, 2 * math.pi); ctx.fill()
        ctx.restore()


def god_rays(ctx, t, x, y, angle=math.pi / 2, length=1500, spread=0.35, n=7, col=(1.0, 0.88, 0.65), alpha=0.22, seed=0):
    """Shafts of light from (x, y) towards `angle`, gently shimmering (additive)."""
    r = random.Random(seed)
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    for k in range(n):
        a0 = angle + r.uniform(-spread, spread)
        w = r.uniform(0.015, 0.05)
        shimmer = 0.6 + 0.4 * math.sin(t * r.uniform(0.3, 0.9) + k * 2.1)
        g = cairo.RadialGradient(x, y, 0, x, y, length)
        g.add_color_stop_rgba(0, *col, alpha * shimmer)
        g.add_color_stop_rgba(0.6, *col, alpha * shimmer * 0.35)
        g.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(g)
        ctx.move_to(x, y); ctx.arc(x, y, length, a0 - w, a0 + w); ctx.close_path(); ctx.fill()
    ctx.restore()


def soft_shadow(ctx, x, y, w, alpha=0.55):
    """Blurred contact shadow under a character or object at ground point (x, y)."""
    g = cairo.RadialGradient(x, y, 0, x, y, w / 2)
    g.add_color_stop_rgba(0, 0, 0, 0, alpha)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.18); ctx.translate(-x, -y)
    ctx.set_source(g); ctx.arc(x, y, w / 2, 0, 2 * math.pi); ctx.fill(); ctx.restore()


def backlight(ctx, x, y, r, col=(1, 0.85, 0.6), alpha=0.35):
    """Halo behind a subject so it separates from a dark background (draw BEFORE the subject)."""
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    glow(ctx, x, y, r, col, alpha)
    ctx.restore()


def depth_haze(ctx, y0, y1, col=(0.06, 0.08, 0.12), alpha=0.55):
    """Atmospheric perspective: tint everything drawn so far between y0..y1 toward the air colour.
    Call after far layers, before near ones."""
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0, *col, 0)
    g.add_color_stop_rgba(1, *col, alpha)
    ctx.set_source(g); ctx.rectangle(0, y0, W, y1 - y0); ctx.fill()


def dust(ctx, t, box=(0, 0, W, H), n=70, light=None, col=(1, 0.95, 0.85), seed=3):
    """Floating dust motes; brighter near `light` (x, y) so they read as lit by it."""
    x0, y0, x1, y1 = box
    r = random.Random(seed)
    for k in range(n):
        bx, by = r.uniform(x0, x1), r.uniform(y0, y1)
        sp = r.uniform(4, 14)
        x = x0 + (bx - x0 + math.sin(t * 0.5 + k) * 25 + t * sp * 0.4) % (x1 - x0)
        y = y0 + (by - y0 - t * sp) % (y1 - y0)
        a = 0.25
        if light:
            dd = math.hypot(x - light[0], y - light[1])
            a = 0.08 + 0.6 * clamp(1 - dd / 700)
        ctx.set_source_rgba(*col, a * (0.6 + 0.4 * math.sin(t * 2 + k)))
        ctx.arc(x, y, r.uniform(1.2, 3.2), 0, 2 * math.pi); ctx.fill()


def flicker_dim(ctx, t, amount=0.25, seed=0.0):
    """Unstable-power flicker: occasionally dims the whole frame."""
    f = math.sin(t * 23 + seed) * math.sin(t * 7.3 + seed * 2)
    if f > 0.6:
        ctx.set_source_rgba(0, 0, 0, amount * (f - 0.6) / 0.4)
        ctx.paint()


def lightning_flash(ctx, t, times, col=(0.85, 0.9, 1.0)):
    """Full-frame flash decaying after each time in `times`; returns its strength 0..1."""
    f = max([math.exp(-(t - b) * 9) for b in times if t >= b] + [0])
    if f > 0.02:
        ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
        ctx.set_source_rgba(*col, 0.6 * f); ctx.paint(); ctx.restore()
    return f


def silhouette_glow(ctx, x, y, s, col=(1, 0.9, 0.7), alpha=0.5):
    """Rim-light suggestion for a figure lit from behind (draw AFTER the figure, additive)."""
    ctx.save(); ctx.set_operator(cairo.OPERATOR_ADD)
    for k, (dx, dy, r) in enumerate(((0, -0.9, 0.16), (0.12, -0.6, 0.22), (-0.12, -0.6, 0.22))):
        glow(ctx, x + dx * s, y + dy * s, r * s, col, alpha * 0.4)
    ctx.restore()


def shot_card(ctx, t, text_fn, words, t0, y=H * 0.42, size=150, col=(1, 1, 1)):
    """Punchy on-screen text that slams in (scale + fade) at t0; text_fn = engine.text."""
    p = clamp((t - t0) / 0.22)
    if p <= 0:
        return
    ctx.save(); ctx.translate(W / 2, y); s = 1 + (1 - p) ** 2 * 0.8; ctx.scale(s, s)
    text_fn(ctx, words, 0, 0, size, col, p, outline=12)
    ctx.restore()
