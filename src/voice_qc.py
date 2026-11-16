"""Find shouted / glitched voice takes by loudness and brightness outliers.

    python src/voice_qc.py <story_id> [...]       # prints suspicious phrases
"""
import json, pathlib, sys

import numpy as np
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from voice import phrases, speaker


def stats(path):
    a, sr = sf.read(str(path), dtype="float32")
    if a.ndim > 1:
        a = a.mean(1)
    n = int(0.05 * sr)
    fr = a[: len(a) // n * n].reshape(-1, n)
    rms = np.sqrt((fr ** 2).mean(1) + 1e-12)
    voiced = rms > rms.max() * 0.1
    db = 20 * np.log10(rms[voiced] + 1e-9)
    spec = np.abs(np.fft.rfft(a))
    f = np.fft.rfftfreq(len(a), 1 / sr)
    centroid = float((spec * f).sum() / (spec.sum() + 1e-9))
    return {"loud": float(np.percentile(db, 95)), "peak_jump": float(db.max() - np.median(db)), "bright": centroid,
            "dur": len(a) / sr}


def scan(sid):
    st = json.loads((ROOT / "stories" / f"{sid}.json").read_text())
    rows = []
    for i, sc in enumerate(st["scenes"], 1):
        for k, p in enumerate(phrases(sc["narration"])):
            f = ROOT / "out" / sid / "cb" / f"s{i:02d}_{k:02d}.wav"
            if f.exists() and not speaker(p):          # character voices are judged separately (different timbre)
                rows.append((i, k, p, sc.get("drama"), stats(f)))
    L = np.array([r[4]["loud"] for r in rows]); B = np.array([r[4]["bright"] for r in rows]); J = np.array([r[4]["peak_jump"] for r in rows])
    lm, ls, bm, bs = np.median(L), L.std(), np.median(B), B.std()
    flagged = []
    for (i, k, p, dr, s) in rows:
        z = (s["loud"] - lm) / ls + (s["bright"] - bm) / bs
        if (s["loud"] - lm) > 4.5 or z > 3.2 or s["peak_jump"] > np.median(J) + 9:
            flagged.append((i, k, p, dr, s, round(z, 1)))
    return flagged, len(rows)


if __name__ == "__main__":
    for sid in sys.argv[1:]:
        fl, n = scan(sid)
        print(f"== {sid}: {len(fl)} of {n} phrases flagged")
        for i, k, p, dr, s, z in fl:
            print(f"  s{i:02d}_{k:02d} drama={dr} loud={s['loud']:.1f}dB jump={s['peak_jump']:.1f} bright={s['bright']:.0f}Hz z={z}  {p}")
