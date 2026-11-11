"""Expressive 2D character rig: outlined cartoon characters with faces, emotions, blinking,
eye direction and lip-sync to the narration.

    from rig import Character, lipsync
    MAYA = Character(name="Maya", age="adult", skin="#c98d66", hair="#2b1a12", hair_style="ponytail",
                     top="#3f6fb5", pants="#2a2d36", shoes="#1a1a1a")
    talk = lipsync(path_to_scene_wav)                 # call once per scene
    MAYA.draw(ctx, x, y, 520, t, mode="walk", phase=t*6, face=1, expr="fear", talk=talk(t), look=(1, 0))

Expressions: neutral happy sad fear shock angry suspicious confused determined tired.
Modes: idle walk run sit crouch. face=1 faces right, -1 left, 0 faces the camera.
A character sheet (src/anim/rig.py --sheet NAME) renders every expression for consistency checks.
"""
import math, random
from dataclasses import dataclass, field

import cairo
import numpy as np

from engine import hexc, ease, wobble, clamp

OUTLINE = (0.09, 0.07, 0.07)


def _rgb(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


def _col(c):
    return hexc(c) if isinstance(c, str) else c


def _shade(c, k=0.78):
    return tuple(v * k for v in c)


# ---------------------------------------------------------------- expressions
#            brow_l  brow_r  (raise, tilt)   eye_open  lid_droop  mouth: curve, open, width
EXPR = {
    "neutral":    dict(brow=(0.0, 0.0),   eye=1.0, droop=0.0, curve=0.05,  open=0.0, width=1.0),
    "happy":      dict(brow=(0.2, 0.15),  eye=0.8, droop=0.0, curve=0.9, open=0.0, width=1.2),
    "sad":        dict(brow=(0.1, -0.5),  eye=0.85, droop=0.35, curve=-0.45, open=0.0, width=0.9),
    "fear":       dict(brow=(0.45, -0.45), eye=1.3, droop=0.0, curve=-0.25, open=0.35, width=0.9),
    "shock":      dict(brow=(0.6, 0.0),   eye=1.45, droop=0.0, curve=0.0,  open=0.8, width=0.75),
    "angry":      dict(brow=(-0.25, 0.6), eye=0.85, droop=0.25, curve=-0.35, open=0.1, width=1.1),
    "suspicious": dict(brow=(-0.1, 0.35), eye=0.55, droop=0.4, curve=-0.1, open=0.0, width=0.9),
    "confused":   dict(brow=(0.3, -0.3),  eye=1.05, droop=0.0, curve=-0.1, open=0.05, width=0.8),
    "determined": dict(brow=(-0.15, 0.4), eye=0.9, droop=0.15, curve=0.05, open=0.0, width=1.0),
    "tired":      dict(brow=(-0.05, -0.2), eye=0.6, droop=0.55, curve=-0.1, open=0.0, width=0.9),
}


def blend_expr(a, b, k):
    ea, eb = EXPR[a], EXPR[b]
    out = {}
    for key in ea:
        va, vb = ea[key], eb[key]
        out[key] = tuple(x + (y - x) * k for x, y in zip(va, vb)) if isinstance(va, tuple) else va + (vb - va) * k
    return out


def blink_amount(t, seed=0):
    """0 open .. 1 closed; a quick blink every 2.5-5 s."""
    r = random.Random(int(seed * 1000))
    period = 2.5 + r.random() * 2.5
    ph = (t + r.random() * period) % period
    return max(0.0, 1 - abs(ph - 0.08) / 0.08) if ph < 0.16 else 0.0


def lipsync(wav_path, fps=30):
    """Return talk(t) -> 0..1 mouth openness from the narration loudness (smoothed)."""
    try:
        import soundfile as sf
        a, sr = sf.read(str(wav_path), dtype="float32")
    except Exception:
        return lambda t: 0.0
    if a.ndim > 1:
        a = a.mean(1)
    hop = int(sr / fps)
    n = len(a) // hop
    env = np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(1)) if n else np.zeros(1)
    env = env / (np.percentile(env, 95) + 1e-6)
    env = np.convolve(env, np.ones(2) / 2, mode="same")
    env = np.clip((env - 0.12) * 1.3, 0, 1)

    def talk(t):
        i = int(t * fps)
        return float(env[i]) if 0 <= i < len(env) else 0.0
    return talk


# ---------------------------------------------------------------- character
@dataclass
class Character:
    name: str
    age: str = "adult"              # adult | child | elder
    skin: str = "#d9a07a"
    hair: str = "#3a2418"
    hair_style: str = "short"       # short | long | ponytail | bun | buzz | bald | cap | hood
    top: str = "#c4632f"            # jacket / shirt colour
    top2: str = ""                  # accent (collar, stripes)
    pants: str = "#2b2f3a"
    shoes: str = "#16171a"
    face_shape: str = "round"       # round | oval | square
    eyes: str = "round"             # round | narrow
    brows: float = 1.0              # brow thickness multiplier
    beard: bool = False
    glasses: bool = False
    seed: float = 0.0
    style: str = "flat"             # flat = the channel's original look (no outlines, simple dot eyes) | outline
    pattern: str = ""               # "" | "hibiscus" (aloha shirt print)
    pattern_col: str = "#f4efe4"
    shorts: bool = False            # bare shins below the knee
    footwear: str = "shoes"         # shoes | flipflops | barefoot
    shades_on_head: bool = False
    stubble: bool = False
    extras: dict = field(default_factory=dict)

    # proportions per age
    def prop(self):
        if self.age == "child":
            return dict(head=0.185, torso=0.27, leg=0.38, arm=0.29, width=0.25)
        if self.age == "elder":
            return dict(head=0.145, torso=0.31, leg=0.42, arm=0.31, width=0.27)
        return dict(head=0.145, torso=0.30, leg=0.45, arm=0.31, width=0.27)

    # ---- drawing helpers
    def _limb(self, ctx, x, y, a1, l1, a2, l2, face, width, col):
        kx, ky = x + face * math.sin(a1) * l1, y + math.cos(a1) * l1
        ex, ey = kx + face * math.sin(a2) * l2, ky + math.cos(a2) * l2
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        for w, c in (((width, col),) if self.style == "flat" else ((width * 1.28, OUTLINE), (width, col))):
            _rgb(ctx, c); ctx.set_line_width(w)
            ctx.move_to(x, y); ctx.line_to(kx, ky); ctx.line_to(ex, ey); ctx.stroke()
        return (kx, ky), (ex, ey)

    def _blob(self, ctx, path_fn, fill, lw):
        path_fn(); _rgb(ctx, fill)
        if self.style == "flat":
            ctx.fill(); return
        ctx.fill_preserve(); _rgb(ctx, OUTLINE); ctx.set_line_width(lw); ctx.stroke()

    def draw(self, ctx, x, y, s, t=0.0, mode="idle", phase=0.0, face=1, expr="neutral", expr_to=None, expr_k=0.0,
             talk=0.0, look=(0.0, 0.0), head_turn=0.0, lean=0.0, breathe=None, arm_f=None, arm_b=None,
             crouch=0.0, hold=None, torn=0.0, dirt=0.0, lost_shoe=False, soot=0.0):
        """(x, y) = ground point between the feet; s = full height in px."""
        P = self.prop()
        lw = max(2.0, s * 0.011)
        skin, hair = _col(self.skin), _col(self.hair)
        top, pants, shoes = _col(self.top), _col(self.pants), _col(self.shoes)
        f = face if face != 0 else 1
        breathe = math.sin(t * 2.2 + self.seed) if breathe is None else breathe
        leg1 = leg2 = P["leg"] * s / 2
        arm1, arm2 = P["arm"] * s * 0.52, P["arm"] * s * 0.48
        bob = 0.0
        # gait
        if mode == "walk":
            th_f, th_b = 0.42 * math.sin(phase), -0.42 * math.sin(phase)
            kn_f, kn_b = -0.6 * max(0, math.sin(phase + 1.6)), -0.6 * max(0, math.sin(phase + 1.6 + math.pi))
            ar_f, ar_b = (-0.45 * math.sin(phase), 0.35), (0.45 * math.sin(phase), 0.35)
            bob = abs(math.sin(phase)) * 0.015 * s; lean += 0.04
        elif mode == "run":
            th_f, th_b = 0.85 * math.sin(phase), -0.85 * math.sin(phase)
            kn_f, kn_b = -1.25 * max(0, math.sin(phase + 1.3)), -1.25 * max(0, math.sin(phase + 1.3 + math.pi))
            ar_f, ar_b = (-0.95 * math.sin(phase), 1.5), (0.95 * math.sin(phase), 1.5)
            bob = abs(math.sin(phase)) * 0.04 * s; lean += 0.2
        elif mode == "sit":
            th_f = th_b = 1.45; kn_f = kn_b = -1.45
            ar_f, ar_b = (0.55, 0.9), (0.4, 0.8)
        else:
            th_f, th_b = 0.06 + 1.0 * crouch, -0.06 + 0.8 * crouch
            kn_f = kn_b = -1.9 * crouch
            ar_f, ar_b = (0.1 + 0.02 * breathe, 0.15), (-0.08, 0.12)
        if arm_f: ar_f = arm_f
        if arm_b: ar_b = arm_b
        if mode == "sit":
            hip = (x, y - 0.27 * s)
        elif mode == "idle":
            hh = leg1 * math.cos(th_f) + leg2 * math.cos(th_f + kn_f)
            hip = (x, y - hh * 0.98)
        else:
            hip = (x, y - (leg1 + leg2) * 0.97 - bob)
        torso = P["torso"] * s
        tw = P["width"] * s / 2
        sh = (hip[0] + f * math.sin(lean) * torso, hip[1] - math.cos(lean) * torso - breathe * 0.004 * s)

        # back limbs
        if self.shorts:                                   # bare leg, then the shorts over the thigh only
            self._limb(ctx, hip[0], hip[1], th_b, leg1, th_b + kn_b, leg2, f, 0.068 * s, _shade(skin, 0.85))
            self._limb(ctx, hip[0], hip[1], th_b, leg1 * 0.85, th_b + kn_b, 0.001, f, 0.092 * s, _shade(pants, 0.7))
        else:
            self._limb(ctx, hip[0], hip[1], th_b, leg1, th_b + kn_b, leg2, f, 0.085 * s, _shade(pants, 0.7))
        self._limb(ctx, sh[0], sh[1] + 0.03 * s, ar_b[0], arm1, ar_b[0] + ar_b[1], arm2, f, 0.068 * s, _shade(top, 0.7))
        # torso
        ctx.save(); ctx.translate(hip[0], hip[1]); ctx.rotate(f * lean)
        def body():
            ctx.move_to(-tw * 0.82, 0.04 * s); ctx.curve_to(-tw * 0.95, -torso * 0.4, -tw * 1.05, -torso * 0.75, -tw * 0.95, -torso + 0.06 * s)
            ctx.curve_to(-tw * 0.85, -torso - 0.03 * s, tw * 0.85, -torso - 0.03 * s, tw * 0.95, -torso + 0.06 * s)
            ctx.curve_to(tw * 1.05, -torso * 0.75, tw * 0.95, -torso * 0.4, tw * 0.82, 0.04 * s); ctx.close_path()
        self._blob(ctx, body, top, lw)
        if self.top2:
            _rgb(ctx, _col(self.top2)); ctx.rectangle(-tw * 0.18, -torso + 0.02 * s, tw * 0.36, torso * 0.9); ctx.fill()
        if self.pattern == "hibiscus":
            body(); ctx.save(); ctx.clip()
            r = random.Random(42)                         # fixed layout: the shirt always looks identical
            pc = _col(self.pattern_col)
            for k in range(9):
                fx_, fy_ = r.uniform(-tw, tw), r.uniform(-torso, 0.02 * s)
                fr = r.uniform(0.022, 0.034) * s
                for pet in range(5):
                    a = pet * 2 * math.pi / 5 + k
                    _rgb(ctx, pc); ctx.save(); ctx.translate(fx_ + math.cos(a) * fr * 0.7, fy_ + math.sin(a) * fr * 0.7)
                    ctx.rotate(a); ctx.scale(1.0, 0.6); ctx.arc(0, 0, fr * 0.7, 0, 2 * math.pi); ctx.restore(); ctx.fill()
                _rgb(ctx, (0.98, 0.82, 0.25)); ctx.arc(fx_, fy_, fr * 0.28, 0, 2 * math.pi); ctx.fill()
                _rgb(ctx, (0.15, 0.45, 0.25)); ctx.save(); ctx.translate(fx_ + fr * 1.3, fy_ + fr * 0.6); ctx.rotate(0.6 + k)
                ctx.scale(1.0, 0.4); ctx.arc(0, 0, fr * 0.7, 0, 2 * math.pi); ctx.restore(); ctx.fill()
            ctx.restore()
            if self.style != "flat":
                body(); _rgb(ctx, OUTLINE); ctx.set_line_width(lw); ctx.stroke()
            _rgb(ctx, (1, 1, 1), 0.25)                     # collar
            ctx.move_to(-tw * 0.35, -torso + 0.01 * s); ctx.line_to(0, -torso + 0.09 * s); ctx.line_to(tw * 0.35, -torso + 0.01 * s); ctx.close_path(); ctx.fill()
        _rgb(ctx, (0, 0, 0), 0.12); ctx.rectangle(0, -torso + 0.03 * s, tw * 0.9, torso); ctx.fill()  # side shade
        ctx.restore()
        # front leg + shoe
        if self.shorts:                                   # bare leg, then the shorts over the thigh only
            knee, foot = self._limb(ctx, hip[0], hip[1], th_f, leg1, th_f + kn_f, leg2, f, 0.072 * s, skin)
            self._limb(ctx, hip[0], hip[1], th_f, leg1 * 0.85, th_f + kn_f, 0.001, f, 0.098 * s, pants)
        else:
            knee, foot = self._limb(ctx, hip[0], hip[1], th_f, leg1, th_f + kn_f, leg2, f, 0.09 * s, pants)
        if torn > 0:                                      # rips and frayed edges on the shorts/trousers
            r = random.Random(int(self.seed * 100) + 7)
            for k in range(int(2 + 4 * torn)):
                u = r.uniform(0.15, 0.85)
                px, py = hip[0] + (knee[0] - hip[0]) * u + r.uniform(-0.02, 0.02) * s, hip[1] + (knee[1] - hip[1]) * u
                _rgb(ctx, skin); ctx.save(); ctx.translate(px, py); ctx.rotate(r.uniform(0, 3))
                ctx.move_to(-0.025 * s, 0); ctx.line_to(0, -0.012 * s); ctx.line_to(0.025 * s, 0.004 * s); ctx.line_to(0.004 * s, 0.014 * s)
                ctx.close_path()
                if self.style == "flat":
                    ctx.fill()
                else:
                    ctx.fill_preserve(); _rgb(ctx, OUTLINE); ctx.set_line_width(lw * 0.6); ctx.stroke()
                ctx.restore()
        if dirt > 0:
            r = random.Random(int(self.seed * 100) + 9)
            for k in range(int(6 * dirt)):
                _rgb(ctx, (0.25, 0.18, 0.1), 0.45); ctx.arc(hip[0] + r.uniform(-0.08, 0.08) * s, hip[1] + r.uniform(0.02, 0.4) * s,
                                                            r.uniform(0.01, 0.025) * s, 0, 2 * math.pi); ctx.fill()
        def shoe():
            ctx.save(); ctx.translate(foot[0] + f * 0.03 * s, foot[1]); ctx.scale(1.0, 0.5 if self.footwear == "shoes" else 0.28)
            ctx.arc(0, 0, 0.055 * s, 0, 2 * math.pi); ctx.restore()
        if self.footwear == "barefoot" or lost_shoe:
            self._blob(ctx, lambda: (ctx.save(), ctx.translate(foot[0] + f * 0.025 * s, foot[1] - 0.008 * s), ctx.scale(1.0, 0.45),
                                     ctx.arc(0, 0, 0.045 * s, 0, 2 * math.pi), ctx.restore()), skin, lw)
        else:
            self._blob(ctx, shoe, shoes, lw)
            if self.footwear == "flipflops":
                _rgb(ctx, OUTLINE); ctx.set_line_width(lw * 0.9)
                ctx.move_to(foot[0], foot[1] - 0.02 * s); ctx.line_to(foot[0] + f * 0.04 * s, foot[1]); ctx.stroke()
        # head
        hr = P["head"] * s
        neck = (sh[0], sh[1] - 0.02 * s)
        hx = neck[0] + f * math.sin(lean) * 0.05 * s + head_turn * 0.02 * s
        hy = neck[1] - hr * 0.95
        self._head(ctx, hx, hy, hr, t, face, expr, expr_to, expr_k, talk, look, head_turn, skin, hair, lw, soot)
        # front arm + hand on top
        _, hand = self._limb(ctx, sh[0], sh[1] + 0.03 * s, ar_f[0], arm1, ar_f[0] + ar_f[1], arm2, f, 0.072 * s, top)
        self._blob(ctx, lambda: ctx.arc(hand[0], hand[1], 0.035 * s, 0, 2 * math.pi), skin, lw)
        return {"hand": hand, "head": (hx, hy), "hip": hip, "head_r": hr}

    def _head(self, ctx, hx, hy, r, t, face, expr, expr_to, expr_k, talk, look, head_turn, skin, hair, lw, soot=0.0):
        e = blend_expr(expr, expr_to, expr_k) if expr_to else EXPR[expr]
        side = 0.0 if face == 0 else face * (0.28 + 0.08 * head_turn)     # 3/4 view offset of the features
        # hair behind (long styles)
        if self.hair_style in ("long", "ponytail"):
            def back():
                ctx.save(); ctx.translate(hx - side * r * 0.8, hy + r * 0.35); ctx.scale(1.05, 1.25)
                ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore()
            self._blob(ctx, back, _shade(hair, 0.85), lw)
            if self.hair_style == "ponytail":
                self._blob(ctx, lambda: (ctx.save(), ctx.translate(hx - (side or 0.3) * r * 1.6, hy + r * 0.2),
                                         ctx.scale(0.45, 1.0), ctx.arc(0, 0, r * 0.7, 0, 2 * math.pi), ctx.restore()),
                           _shade(hair, 0.85), lw)
        if self.hair_style == "hood":
            self._blob(ctx, lambda: ctx.arc(hx, hy + r * 0.05, r * 1.22, 0, 2 * math.pi), _col(self.top), lw)
        # face
        sx, sy = {"round": (1.0, 1.0), "oval": (0.9, 1.1), "square": (1.0, 1.02)}[self.face_shape]
        def facepath():
            ctx.save(); ctx.translate(hx, hy); ctx.scale(sx, sy); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore()
        self._blob(ctx, facepath, skin, lw)
        # ear on the far side from the features
        if face != 0:
            self._blob(ctx, lambda: (ctx.save(), ctx.translate(hx - face * r * 0.82, hy + r * 0.08), ctx.scale(0.55, 0.8),
                                     ctx.arc(0, 0, r * 0.28, 0, 2 * math.pi), ctx.restore()), skin, lw)
        # cheek shading
        _rgb(ctx, (0, 0, 0), 0.08)
        ctx.save(); ctx.translate(hx - side * r * 1.2, hy); ctx.scale(0.5, 1); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore(); ctx.fill()
        # hair on top
        hs = self.hair_style
        if hs == "curly":
            rr = random.Random(5)
            for k in range(11):
                a = math.pi * (1.05 + 0.9 * k / 10)
                self._blob(ctx, lambda a=a: ctx.arc(hx + math.cos(a) * r * 0.92, hy + math.sin(a) * r * 0.9, r * rr.uniform(0.26, 0.34), 0, 2 * math.pi), hair, lw)
            _rgb(ctx, hair); ctx.arc(hx, hy - r * 0.35, r * 0.85, math.pi, 2 * math.pi); ctx.fill()
        if self.shades_on_head:
            for ex in (-0.32, 0.32):
                self._blob(ctx, lambda ex=ex: (ctx.save(), ctx.translate(hx + ex * r + (face or 0) * r * 0.15, hy - r * 0.88),
                                               ctx.scale(1.0, 0.6), ctx.arc(0, 0, r * 0.24, 0, 2 * math.pi), ctx.restore()), (0.95, 0.75, 0.2), lw * 1.2)
                _rgb(ctx, (0.1, 0.35, 0.45)); ctx.save(); ctx.translate(hx + ex * r + (face or 0) * r * 0.15, hy - r * 0.88)
                ctx.scale(1.0, 0.6); ctx.arc(0, 0, r * 0.17, 0, 2 * math.pi); ctx.restore(); ctx.fill()
            _rgb(ctx, (1, 1, 1), 0.35); ctx.arc(hx - r * 0.38 + (face or 0) * r * 0.15, hy - r * 0.93, r * 0.06, 0, 2 * math.pi); ctx.fill()
        if hs in ("short", "long", "ponytail", "bun", "buzz"):
            def cap():
                ctx.save(); ctx.translate(hx, hy); ctx.scale(sx, sy)
                ctx.arc(0, 0, r * 1.04, math.pi * 1.02, math.pi * 1.98)
                ctx.curve_to(r * 0.95, -r * 0.35, r * 0.3 * (face or 1), -r * 0.72, -r * 0.1 * (face or 1), -r * 0.6)
                ctx.curve_to(-r * 0.5, -r * 0.5, -r * 0.9, -r * 0.25, -r * 1.02, -r * 0.15)
                ctx.close_path(); ctx.restore()
            self._blob(ctx, cap, hair if hs != "buzz" else _shade(hair, 1.1), lw)
            _rgb(ctx, (1, 1, 1), 0.12); ctx.save(); ctx.translate(hx - r * 0.3, hy - r * 0.75); ctx.scale(1.6, 0.5)
            ctx.arc(0, 0, r * 0.18, 0, 2 * math.pi); ctx.restore(); ctx.fill()
            if hs == "bun":
                self._blob(ctx, lambda: ctx.arc(hx - (face or 0) * r * 0.4, hy - r * 1.05, r * 0.38, 0, 2 * math.pi), hair, lw)
        elif hs == "cap":
            self._blob(ctx, lambda: (ctx.arc(hx, hy - r * 0.15, r * 1.02, math.pi, 2 * math.pi), ctx.close_path()), _col(self.top), lw)
            self._blob(ctx, lambda: (ctx.save(), ctx.translate(hx + (face or 0) * r * 0.8, hy - r * 0.18), ctx.scale(1.0, 0.25),
                                     ctx.arc(0, 0, r * 0.6, 0, 2 * math.pi), ctx.restore()), _shade(_col(self.top), 0.8), lw)
        elif hs == "hood":
            _rgb(ctx, _col(self.top)); ctx.set_line_width(r * 0.28)
            ctx.arc(hx, hy + r * 0.05, r * 1.08, math.pi * 1.05, math.pi * 1.95); ctx.stroke()
        fx = hx + side * r
        # eyes
        blink = blink_amount(t, self.seed)
        open_ = max(0.05, e["eye"] * (1 - blink))
        lx, ly = look
        er = r * (0.25 if self.age == "child" else 0.21)
        for k, ex in enumerate((-0.36, 0.36)):
            persp = 1.0 if face == 0 else (0.82 if (ex < 0) == (face > 0) else 1.0)
            cx, cy = fx + ex * r * persp * (0.85 if face else 1), hy - r * 0.05
            if self.style == "flat":
                ed = er * 0.62
                px = cx + (lx * 0.35 + (side * 0.4 if face else 0)) * ed
                py = cy + ly * 0.3 * ed
                ctx.save(); ctx.translate(px, py); ctx.scale(persp * 0.85, max(0.08, open_ * 1.15))
                _rgb(ctx, (0.08, 0.07, 0.09)); ctx.arc(0, 0, ed, 0, 2 * math.pi); ctx.fill(); ctx.restore()
                if open_ > 0.35:
                    _rgb(ctx, (1, 1, 1), 0.8); ctx.arc(px + ed * 0.3, py - ed * 0.35 * open_, ed * 0.22, 0, 2 * math.pi); ctx.fill()
                if e["droop"] > 0 and open_ > 0.2:
                    _rgb(ctx, skin); ctx.rectangle(px - ed * 1.3, py - ed * 1.6, ed * 2.6, ed * (0.7 + 1.1 * e["droop"])); ctx.fill()
                raise_, tilt = e["brow"]
                by = cy - er * (1.35 + 0.8 * raise_)
                x_in, x_out = (cx + er * 0.8, cx - er * 0.8) if ex < 0 else (cx - er * 0.8, cx + er * 0.8)
                _rgb(ctx, (0.08, 0.07, 0.09), 0.9); ctx.set_line_width(max(2, r * 0.07) * self.brows); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                ctx.move_to(x_out, by - er * 0.3 * tilt); ctx.line_to(x_in, by + er * 0.55 * tilt); ctx.stroke()
                continue
            ctx.save(); ctx.translate(cx, cy); ctx.scale(persp * (0.8 if self.eyes == "narrow" else 1.0), open_)
            _rgb(ctx, (0.98, 0.97, 0.95)); ctx.arc(0, 0, er, 0, 2 * math.pi); ctx.fill_preserve()
            _rgb(ctx, OUTLINE); ctx.set_line_width(lw * 0.8 / max(open_, 0.3)); ctx.stroke()
            ctx.restore()
            if open_ > 0.2:
                px = cx + (lx * 0.45 + (side * 0.6 if face else 0)) * er
                py = cy + ly * 0.4 * er * open_
                _rgb(ctx, (0.12, 0.09, 0.08)); ctx.arc(px, py, er * 0.55 * min(1, open_ + 0.2), 0, 2 * math.pi); ctx.fill()
                _rgb(ctx, (1, 1, 1), 0.9); ctx.arc(px + er * 0.2, py - er * 0.22, er * 0.15, 0, 2 * math.pi); ctx.fill()
            if e["droop"] > 0 and open_ > 0.2:                               # heavy upper lid
                _rgb(ctx, skin); ctx.rectangle(cx - er * 1.2, cy - er * 1.3, er * 2.4, er * (0.3 + 1.0 * e["droop"])); ctx.fill()
                _rgb(ctx, OUTLINE); ctx.set_line_width(lw * 0.8)
                ctx.move_to(cx - er, cy - er * (1.0 - 1.0 * e["droop"])); ctx.line_to(cx + er, cy - er * (1.0 - 1.0 * e["droop"])); ctx.stroke()
            # brows: raise moves both up; tilt raises the inner ends (+) or outer ends (-)
            raise_, tilt = e["brow"]
            inner = -1 if ex < 0 else 1
            by = cy - er * (1.55 + 0.9 * raise_)
            x_in, x_out = cx + inner * er * 0.2 * (-1), cx + inner * -er * 1.1 * (-1)
            x_in, x_out = (cx + er * 0.95, cx - er * 1.0) if ex < 0 else (cx - er * 0.95, cx + er * 1.0)
            _rgb(ctx, _shade(hair, 0.65)); ctx.set_line_width(lw * 2.6 * self.brows); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(x_out, by - er * 0.3 * tilt); ctx.line_to(x_in, by + er * 0.55 * tilt); ctx.stroke()   # tilt>0 inner down (angry), <0 inner up (sad/fear)
        # nose
        _rgb(ctx, _shade(skin, 0.75), 0.0 if self.style == "flat" else 1.0); ctx.set_line_width(lw * 0.9)
        ctx.move_to(fx + side * r * 0.25, hy + r * 0.05); ctx.line_to(fx + side * r * 0.35 + r * 0.04 * (face or 0), hy + r * 0.28)
        ctx.line_to(fx + side * r * 0.1, hy + r * 0.3); ctx.stroke()
        # mouth: expression curve + speech opening
        mw = r * 0.38 * e["width"]
        my = hy + r * 0.52
        op = clamp(e["open"] + talk * 0.75)
        mcx = fx + side * r * 0.15
        if op > 0.08:
            h = r * 0.32 * op
            ctx.save(); ctx.translate(mcx, my + h * 0.3); ctx.scale(mw * (1 - 0.3 * op) / (r * 0.3), h / (r * 0.3))
            ctx.arc(0, 0, r * 0.3, 0, 2 * math.pi); ctx.restore()
            if self.style == "flat":
                _rgb(ctx, (0.12, 0.06, 0.07)); ctx.fill()
            else:
                _rgb(ctx, (0.35, 0.08, 0.1)); ctx.fill_preserve(); _rgb(ctx, OUTLINE); ctx.set_line_width(lw); ctx.stroke()
            if op > 0.3 and self.style != "flat":
                _rgb(ctx, (0.95, 0.93, 0.9)); ctx.rectangle(mcx - mw * 0.45, my - h * 0.05, mw * 0.9, h * 0.22); ctx.fill()
        else:
            c = e["curve"]
            _rgb(ctx, OUTLINE); ctx.set_line_width(max(2, r * 0.06) if self.style == "flat" else lw * 1.1); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(mcx - mw, my - c * r * 0.12)
            ctx.curve_to(mcx - mw * 0.4, my + c * r * 0.22, mcx + mw * 0.4, my + c * r * 0.22, mcx + mw, my - c * r * 0.12)
            ctx.stroke()
        if self.beard:
            _rgb(ctx, _shade(hair, 0.9), 0.9)
            ctx.save(); ctx.translate(hx + side * r * 0.3, hy + r * 0.62); ctx.scale(1.0, 0.55); ctx.arc(0, 0, r * 0.62, 0, math.pi); ctx.restore(); ctx.fill()
        if self.stubble and self.style != "flat":
            rs = random.Random(3)
            _rgb(ctx, _shade(skin, 0.72), 0.55)            # soft stubble shadow along the jaw
            ctx.save(); ctx.translate(hx + side * r * 0.25, hy + r * 0.8); ctx.scale(1.0, 0.22)
            ctx.arc(0, 0, r * 0.66, 0.05, math.pi - 0.05); ctx.restore(); ctx.fill()
        if soot > 0:
            rs = random.Random(11)
            for k in range(int(10 * soot)):
                _rgb(ctx, (0.1, 0.09, 0.08), 0.22 if self.style == "flat" else 0.35)
                ctx.arc(hx + rs.uniform(-0.7, 0.7) * r, hy + rs.uniform(-0.6, 0.7) * r, rs.uniform(0.06, 0.16) * r * (0.7 if self.style == "flat" else 1), 0, 2 * math.pi); ctx.fill()
        if self.glasses:
            _rgb(ctx, OUTLINE); ctx.set_line_width(lw)
            for ex in (-0.36, 0.36):
                ctx.arc(fx + ex * r * 0.85, hy - r * 0.05, er * 1.35, 0, 2 * math.pi); ctx.stroke()


def sheet(char, path, size=520):
    """Character reference sheet: front/left/right + every expression."""
    from engine import W
    exprs = list(EXPR)
    cols = 5
    rows = 1 + math.ceil(len(exprs) / cols)
    sw, shh = 1500, 520 * rows + 120
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, shh)
    c = cairo.Context(s); c.set_source_rgb(0.93, 0.92, 0.9); c.paint()
    c.select_font_face("Anton"); c.set_font_size(54); c.set_source_rgb(0.1, 0.1, 0.1); c.move_to(30, 70); c.show_text(char.name.upper())
    for k, fc in enumerate((0, 1, -1)):
        char.draw(c, 250 + k * 450, 600, 480, t=0.5, face=fc)
    for k, ex in enumerate(exprs):
        cx = 150 + (k % cols) * 300; cy = 620 + (1 + k // cols) * 520
        c.save(); c.translate(cx, cy); c.scale(0.55, 0.55); c.translate(-cx, -cy)
        char.draw(c, cx, cy + 300, 900, t=0.5, face=0, expr=ex)
        c.restore()
        c.set_font_size(36); c.set_source_rgb(0.2, 0.2, 0.2); c.move_to(cx - 70, cy + 230); c.show_text(ex)
    s.write_to_png(path)
