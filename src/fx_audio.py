"""Cinematic sound-design layer: whooshes on cuts, braams and sub-drops on big moments.

Used by assemble.py to build a 'hits' track over the whole timeline:
    hits_track(total_seconds, cut_times, impact_times) -> mono float32 @ 44.1 kHz
"""
import numpy as np

SR = 44100


def _noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def _lowpass(x, cutoff):
    """FFT brick-wall lowpass with a soft knee (fine for sound design)."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    spec *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(spec, len(x)).astype(np.float32)


def whoosh(dur=0.55, seed=0):
    """Air swish that swells into the cut (peak at the end)."""
    n = int(dur * SR)
    t = np.linspace(0, 1, n, dtype=np.float32)
    x = _noise(n, seed)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((f - 1800) / 1400) ** 2) + 0.3 * np.exp(-((f - 500) / 400) ** 2)
    x = np.fft.irfft(spec, n).astype(np.float32)
    env = t ** 2.2 * (1 - np.clip((t - 0.92) / 0.08, 0, 1))
    return x / (np.abs(x).max() + 1e-9) * env * 0.55


def sub_drop(dur=1.6, f0=70.0, f1=28.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 3.5)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (x * np.exp(-t * 1.6) * np.minimum(1, t * 80)).astype(np.float32) * 0.9


def braam(dur=2.4, root=43.65, seed=1):
    """Low brassy 'BRAAM': detuned saws, lowpassed, soft-clipped, slow decay."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n, dtype=np.float32)
    for k, det in enumerate((1.0, 1.006, 0.994, 2.0, 1.498)):
        ph = (root * det * t + k * 0.13) % 1.0
        x += (2 * ph - 1) * (0.55 if det < 1.9 else 0.25)
    x = _lowpass(x, 900)
    x = np.tanh(x * 1.8)
    env = np.minimum(1, t * 25) * np.exp(-t * 0.9)
    return (x * env * 0.5).astype(np.float32)


def impact(seed=2):
    """Short hit: noise crack + body thump."""
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    crack = _lowpass(_noise(n, seed), 3500) * np.exp(-t * 30)
    body = np.sin(2 * np.pi * (90 - 40 * t) * t) * np.exp(-t * 7)
    return ((crack * 0.6 + body) * 0.6).astype(np.float32)


def riser(dur=2.5, seed=3):
    """Rising tension noise into a moment."""
    n = int(dur * SR)
    t = np.linspace(0, 1, n, dtype=np.float32)
    x = _noise(n, seed)
    out = np.zeros(n, dtype=np.float32)
    for k in range(8):                      # sweep the band upward in steps
        a, b = int(k * n / 8), int((k + 1) * n / 8)
        out[a:b] = _lowpass(x[a:b], 400 + 900 * k)
    return out / (np.abs(out).max() + 1e-9) * t ** 2 * 0.35


def _place(track, clip, at):
    i = int(at * SR)
    if i < 0:
        clip, i = clip[-i:], 0
    j = min(len(track), i + len(clip))
    if j > i:
        track[i:j] += clip[: j - i]


def hits_track(total, cut_times, impact_times=(), braam_times=(), riser_into=()):
    """Whoosh into every cut, sub-drop + impact at impact_times, braam at braam_times,
    riser ending exactly at each riser_into time."""
    track = np.zeros(int((total + 3) * SR), dtype=np.float32)
    for k, c in enumerate(cut_times):
        w = whoosh(seed=k)
        _place(track, w * 0.7, c - len(w) / SR + 0.05)
    for k, c in enumerate(impact_times):
        _place(track, sub_drop(), c)
        _place(track, impact(seed=10 + k) * 0.8, c)
    for c in braam_times:
        _place(track, braam(), c)
        _place(track, sub_drop(2.0) * 0.8, c)
    for c in riser_into:
        r = riser()
        _place(track, r, c - len(r) / SR)
    return track[: int(total * SR)]
