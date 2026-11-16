"""Shared runner for multi-part animated stories.

A story module defines PARTS = {1: (sid, scenes, sfx_fn, music_fn), ...} and calls run(PARTS).
    python src/anim/<module>.py <part> [scene numbers]
Scene functions get (ctx, t, d); timing helpers come from timing(sid).
"""
import json, pathlib, sys
from multiprocessing import Pool

import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import render, save_wav  # noqa

ROOT = pathlib.Path(__file__).resolve().parents[2]


class Timing:
    """Phrase start times from voice.py, so visuals hit the words."""

    def __init__(self, sid):
        self.out = ROOT / "out" / sid
        self.seg = {}
        for p in self.out.glob("scene_*.json"):
            self.seg[int(p.stem.split("_")[1])] = json.loads(p.read_text())

    def at(self, i, k):
        s = self.seg.get(i, [["", 0, 5]])
        return s[k][1] if -len(s) <= k < len(s) else s[-1][1]

    def dur(self, i):
        f = self.out / f"scene_{i:02d}.wav"
        return sf.info(str(f)).duration + 0.3 if f.exists() else 6.0


_JOB = {}


def _job(args):
    sid, i = args
    scenes, sfx_fn, tm = _JOB[sid]
    d = tm.dur(i)
    outdir = ROOT / "assets" / "clips" / sid
    save_wav(outdir / f"scene_{i:02d}.sfx.wav", sfx_fn(i, d))
    render(scenes[i - 1], d, outdir / f"scene_{i:02d}.mp4")
    return f"{sid} scene {i} ({d:.1f}s)"


def run(parts, timings):
    part = int(sys.argv[1])
    sid, scenes, sfx_fn, music_fn = parts[part]
    tm = timings[part]
    only = [int(a) for a in sys.argv[2:]] or range(1, len(scenes) + 1)
    outdir = ROOT / "assets" / "clips" / sid
    outdir.mkdir(parents=True, exist_ok=True)
    durs = [tm.dur(i) for i in range(1, len(scenes) + 1)]
    save_wav(outdir / "music.wav", music_fn(durs))
    _JOB[sid] = (scenes, sfx_fn, tm)
    with Pool(4) as p:
        for r in p.imap_unordered(_job, [(sid, i) for i in only]):
            print("  rendered", r, flush=True)
