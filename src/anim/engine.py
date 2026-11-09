"""Tiny 2D animation engine: cairo vector drawing -> ffmpeg, plus synthesized sound.

Everything is drawn in code each frame: a rigged character with walk/run/sit
cycles, parallax backgrounds, lights, particles and camera moves.
"""
import math, random, subprocess

import cairo
import numpy as np

W, H, FPS, SR = 1080, 1920, 30, 44100

# ---------- palette ----------
HOODIE = (0.93, 0.47, 0.16)
HOODIE_D = (0.72, 0.33, 0.10)
PANTS = (0.17, 0.19, 0.25)
PANTS_D = (0.12, 0.13, 0.18)
FACE = (0.09, 0.10, 0.15)
SHOE = (0.08, 0.08, 0.10)


# ---------- math ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def prog(t, a, b):
    """0..1 progress of t through [a, b]."""
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def wobble(t, seed=0.0, speed=1.0):
    """Smooth pseudo-noise in [-1, 1]."""
    x = t * speed + seed * 13.7
    return (math.sin(x * 1.7) + math.sin(x * 2.9 + 1.3) * 0.6 + math.sin(x * 4.3 + 2.1) * 0.3) / 1.9


# ---------- drawing helpers ----------
def rgb(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def vgrad(ctx, y0, y1, stops, x=0, w=W):
    g = cairo.LinearGradient(0, y0, 0, y1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *(c if len(c) == 4 else (*c, 1)))
    ctx.set_source(g)
    ctx.rectangle(x, y0, w, y1 - y0)
    ctx.fill()


def glow(ctx, x, y, r, c, a=0.6):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *c, a)
    g.add_color_stop_rgba(0.4, *c, a * 0.35)
    g.add_color_stop_rgba(1, *c, 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def cone(ctx, x, y, ang, spread, length, c, a=0.5):
    """Light beam from (x, y) pointing at angle ang (radians)."""
    g = cairo.RadialGradient(x, y, 0, x, y, length)
    g.add_color_stop_rgba(0, *c, a)
    g.add_color_stop_rgba(1, *c, 0)
    ctx.set_source(g)
    ctx.move_to(x, y)
    ctx.arc(x, y, length, ang - spread, ang + spread)
    ctx.close_path()
    ctx.fill()


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def text(ctx, s, x, y, size, c=(1, 1, 1), a=1.0, anchor="center", font="Anton", outline=0):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    tx = x - ext.width / 2 - ext.x_bearing if anchor == "center" else x
    ty = y - ext.height / 2 - ext.y_bearing
    ctx.move_to(tx, ty)
    ctx.text_path(s)
    if outline:
        ctx.set_source_rgba(0, 0, 0, a * 0.9)
        ctx.set_line_width(outline)
        ctx.stroke_preserve()
    rgb(ctx, c, a)
    ctx.fill()


def day_stamp(ctx, t, label, start=0.0):
    """Big 'DAY 10' title that slams in."""
    p = prog(t, start, start + 0.35)
    if p <= 0:
        return
    s = 1 + (1 - ease_out(p)) * 0.8
    ctx.save()
    ctx.translate(W / 2, 300)
    ctx.scale(s, s)
    text(ctx, label, 0, 0, 170, (1, 1, 1), ease(p), outline=14)
    ctx.restore()


def skyline(seed, n, base_y, hmin, hmax, wmin, wmax, broken=False):
    r = random.Random(seed)
    out, x = [], -60
    while x < W + 60:
        w = r.uniform(wmin, wmax)
        h = r.uniform(hmin, hmax)
        wins = [(r.random(), r.random()) for _ in range(int(w * h / 2600))]
        cut = [r.uniform(0, 0.35) * h for _ in range(3)] if broken else None
        out.append((x, w, h, wins, cut))
        x += w + r.uniform(-8, 18)
    return out


def draw_skyline(ctx, bld, base_y, col, win_col=None, win_a=0.0, t=0.0, offset=0.0):
    for i, (x, w, h, wins, cut) in enumerate(bld):
        x = x + offset
        rgb(ctx, col)
        if cut:
            ctx.move_to(x, base_y)
            ctx.line_to(x, base_y - h + cut[0])
            ctx.line_to(x + w * 0.35, base_y - h + cut[1])
            ctx.line_to(x + w * 0.6, base_y - h)
            ctx.line_to(x + w, base_y - h + cut[2])
            ctx.line_to(x + w, base_y)
            ctx.close_path()
        else:
            ctx.rectangle(x, base_y - h, w, h)
        ctx.fill()
        if win_col and win_a > 0:
            for k, (u, v) in enumerate(wins):
                flick = 0.6 + 0.4 * math.sin(t * 3 + k * 7.1 + i)
                rgb(ctx, win_col, win_a * flick)
                ctx.rectangle(x + 6 + u * (w - 18), base_y - h + 10 + v * (h - 30), 7, 10)
                ctx.fill()


class Particles:
    """Drifting dust / ash / rain."""

    def __init__(self, n, seed, box=(0, 0, W, H), vel=(0, 30), size=(2, 5), col=(1, 1, 1), alpha=0.5):
        r = random.Random(seed)
        self.p = [(r.uniform(box[0], box[2]), r.uniform(box[1], box[3]), r.uniform(*size),
                   r.uniform(0.6, 1.4), r.uniform(0, 6.28)) for _ in range(n)]
        self.box, self.vel, self.col, self.alpha = box, vel, col, alpha

    def draw(self, ctx, t):
        x0, y0, x1, y1 = self.box
        for (x, y, s, sp, ph) in self.p:
            px = x0 + (x - x0 + self.vel[0] * sp * t + math.sin(t + ph) * 12) % (x1 - x0)
            py = y0 + (y - y0 + self.vel[1] * sp * t) % (y1 - y0)
            rgb(ctx, self.col, self.alpha * (0.5 + 0.5 * math.sin(t * 2 + ph)))
            ctx.arc(px, py, s, 0, 6.283)
            ctx.fill()


# ---------- the character ----------
def _limb(ctx, x, y, a1, l1, a2, l2, face, width, col, cap_r=None):
    kx, ky = x + face * math.sin(a1) * l1, y + math.cos(a1) * l1
    ex, ey = kx + face * math.sin(a2) * l2, ky + math.cos(a2) * l2
    rgb(ctx, col)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(x, y)
    ctx.line_to(kx, ky)
    ctx.line_to(ex, ey)
    ctx.stroke()
    return ex, ey


def person(ctx, x, y, s, mode="idle", phase=0.0, face=1, lean=0.0, head_turn=0.0,
           arm_f=None, arm_b=None, breathe=0.0, back_view=False, crouch=0.0):
    """Faceless figure in an orange hoodie. (x, y) = point between the feet on the ground.
    s = full height in px. mode: idle | walk | run | sit. phase drives the cycles.
    arm_f / arm_b = (shoulder_angle, elbow_angle) overrides, radians from straight down, + = forward."""
    u = s
    leg1, leg2 = 0.235 * u, 0.225 * u
    arm1, arm2 = 0.17 * u, 0.16 * u
    bob = 0.0
    if mode == "walk":
        th_f, th_b = 0.45 * math.sin(phase), -0.45 * math.sin(phase)
        kn_f = -0.55 * max(0, math.sin(phase + 1.6))
        kn_b = -0.55 * max(0, math.sin(phase + 1.6 + math.pi))
        ar_f, ar_b = (-0.5 * math.sin(phase), 0.3), (0.5 * math.sin(phase), 0.3)
        bob = abs(math.sin(phase)) * 0.015 * u
        lean += 0.05
    elif mode == "run":
        th_f, th_b = 0.85 * math.sin(phase), -0.85 * math.sin(phase)
        kn_f = -1.2 * max(0, math.sin(phase + 1.3))
        kn_b = -1.2 * max(0, math.sin(phase + 1.3 + math.pi))
        ar_f, ar_b = (-0.9 * math.sin(phase), 1.4), (0.9 * math.sin(phase), 1.4)
        bob = abs(math.sin(phase)) * 0.04 * u
        lean += 0.22
    elif mode == "sit":
        th_f = th_b = 1.45
        kn_f = kn_b = -1.45
        ar_f, ar_b = (0.5, 0.9), (0.35, 0.8)
    else:
        th_f, th_b = 0.06, -0.06
        kn_f = kn_b = 0.0
        ar_f, ar_b = (0.08 + breathe * 0.02, 0.12), (-0.06, 0.1)
    if arm_f:
        ar_f = arm_f
    if arm_b:
        ar_b = arm_b

    hip_h = (leg1 + leg2) * (1 - crouch * 0.35)
    if mode == "sit":
        hip = (x, y - 0.27 * u)
    else:
        hip = (x, y - hip_h * 0.97 - bob)
    torso = 0.33 * u
    sh = (hip[0] + face * math.sin(lean) * torso, hip[1] - math.cos(lean) * torso - breathe * 0.006 * u)

    # back limbs (darker, behind body)
    _limb(ctx, hip[0], hip[1], th_b, leg1, th_b + kn_b, leg2, face, 0.085 * u, PANTS_D)
    _limb(ctx, sh[0], sh[1] + 0.02 * u, ar_b[0], arm1, ar_b[0] + ar_b[1], arm2, face, 0.07 * u, HOODIE_D)

    # torso (hoodie)
    tw = 0.12 * u
    ctx.save()
    ctx.translate(hip[0], hip[1])
    ctx.rotate(face * lean)
    rgb(ctx, HOODIE)
    rrect(ctx, -tw, -torso - 0.03 * u, tw * 2, torso + 0.08 * u, 0.06 * u)
    ctx.fill()
    rgb(ctx, HOODIE_D, 0.55)       # pocket / shading
    rrect(ctx, -tw * 0.7, -torso * 0.38, tw * 1.4, torso * 0.3, 0.025 * u)
    ctx.fill()
    ctx.restore()

    # front leg + shoe
    fx, fy = _limb(ctx, hip[0], hip[1], th_f, leg1, th_f + kn_f, leg2, face, 0.088 * u, PANTS)
    for (lx, ly) in [(fx, fy)]:
        rgb(ctx, SHOE)
        ctx.save()
        ctx.translate(lx + face * 0.025 * u, ly)
        ctx.scale(1, 0.55)
        ctx.arc(0, 0, 0.05 * u, 0, 6.283)
        ctx.fill()
        ctx.restore()

    # head (hood + faceless shadow)
    hx = sh[0] + face * math.sin(lean) * 0.06 * u
    hy = sh[1] - 0.105 * u
    rgb(ctx, HOODIE)
    ctx.arc(hx, hy, 0.105 * u, 0, 6.283)
    ctx.fill()
    if not back_view:
        off = face * (0.035 + head_turn * 0.03) * u
        rgb(ctx, FACE)
        ctx.save()
        ctx.translate(hx + off, hy + 0.012 * u)
        ctx.scale(0.62, 0.78)
        ctx.arc(0, 0, 0.085 * u, 0, 6.283)
        ctx.fill()
        ctx.restore()
    else:
        rgb(ctx, HOODIE_D, 0.6)
        ctx.arc(hx + head_turn * 0.03 * u, hy + 0.01 * u, 0.06 * u, 0, 6.283)
        ctx.fill()

    # front arm on top
    hand = _limb(ctx, sh[0], sh[1] + 0.02 * u, ar_f[0], arm1, ar_f[0] + ar_f[1], arm2, face, 0.072 * u, HOODIE)
    return {"hand": hand, "head": (hx, hy), "hip": hip}


# ---------- overlays ----------
_VIG = None


def vignette(ctx, strength=0.75):
    global _VIG
    if _VIG is None:
        _VIG = cairo.RadialGradient(W / 2, H / 2, H * 0.25, W / 2, H / 2, H * 0.75)
        _VIG.add_color_stop_rgba(0, 0, 0, 0, 0)
        _VIG.add_color_stop_rgba(1, 0, 0, 0, 1)
    ctx.save()
    ctx.set_source(_VIG)
    ctx.paint_with_alpha(strength)
    ctx.restore()


def grain(ctx, t, n=260, a=0.05):
    r = random.Random(int(t * FPS))
    for _ in range(n):
        ctx.set_source_rgba(1, 1, 1, r.uniform(0, a))
        ctx.rectangle(r.uniform(0, W), r.uniform(0, H), 2, 2)
        ctx.fill()


def fade(ctx, t, dur, fin=0.25, fout=0.25):
    a = max(1 - prog(t, 0, fin), prog(t, dur - fout, dur))
    if a > 0:
        ctx.set_source_rgba(0, 0, 0, a)
        ctx.paint()


# ---------- render ----------
def render(draw, dur, out_path):
    """Call draw(ctx, t, dur) for every frame and encode to H.264."""
    n = int(round(dur * FPS))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                           "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(out_path)],
                          stdin=subprocess.PIPE)
    for f in range(n):
        ctx = cairo.Context(surf)
        ctx.set_antialias(cairo.ANTIALIAS_GOOD)
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        draw(ctx, f / FPS, dur)
        surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close()
    ff.wait()


# ---------- sound ----------
def silence(dur):
    return np.zeros(int(dur * SR), dtype=np.float32)


def band_noise(dur, lo, hi, seed=0):
    n = int(dur * SR)
    spec = np.fft.rfft(np.random.default_rng(seed).standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    x = np.fft.irfft(spec, n)
    return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)


def tone(dur, freq, kind="sine"):
    n = int(dur * SR)
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,)) if np.ndim(freq) else np.full(n, freq)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if kind == "saw":
        return (2 * ((ph / (2 * np.pi)) % 1) - 1).astype(np.float32)
    return np.sin(ph).astype(np.float32)


def env_at(dur, times, length, shape="thump"):
    """Sum of short envelopes at given times (seconds)."""
    out = silence(dur)
    k = int(length * SR)
    e = np.exp(-np.linspace(0, 6, k)).astype(np.float32)
    for t in times:
        i = int(t * SR)
        if 0 <= i < len(out):
            j = min(len(out), i + k)
            out[i:j] += e[: j - i]
    return out


def drone(dur, root=55.0, seed=0):
    t = np.arange(int(dur * SR)) / SR
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t + seed)
    x = (np.sin(2 * np.pi * root * t) * 0.5 + np.sin(2 * np.pi * root * 1.5 * t) * 0.25 * lfo
         + np.sin(2 * np.pi * root * 2.01 * t) * 0.15)
    x += band_noise(dur, 60, 400, seed) * 0.15
    return (x * 0.5).astype(np.float32)


def fades(x, fin=0.15, fout=0.3):
    n = len(x)
    a, b = int(fin * SR), int(fout * SR)
    x = x.copy()
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[n - b:] *= np.linspace(1, 0, b)
    return x


def save_wav(path, x):
    import soundfile as sf
    x = np.clip(x, -1, 1)
    sf.write(path, np.stack([x, x], 1), SR)
