"""Build a whole 3-part story with quality gates, in one command.

    python src/make_story.py <anim_module> <sid1> <sid2> <sid3> [--from voice|qc|anim|assemble]

Steps (each part):
  1. voice      Chatterbox narration (+ whispers), phrase timings
  2. qc         find shouted / stretched takes, mark them for a calmer retake, re-voice (max 2 rounds)
  3. anim       render every animated scene with src/anim/<anim_module>.py <part>
  4. assemble   finishing pass, captions, title card, sound hits, music, loudness
  5. report     length, loudness, flagged leftovers -> out/<sid>/report.json
Stops with a clear error if any step fails, so a broken story never reaches Buffer.
"""
import json, pathlib, subprocess, sys

import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from voice import phrases                 # noqa: E402
from voice_qc import scan                 # noqa: E402

PY = sys.executable
STEPS = ["voice", "qc", "anim", "assemble"]


def sh(*cmd):
    print("  $", " ".join(map(str, cmd)), flush=True)
    subprocess.run(list(map(str, cmd)), check=True, cwd=ROOT)


def bad_takes(sid):
    """Takes that are clearly shouted (loud/bright outliers) or stretched for their word count."""
    story = json.loads((ROOT / "stories" / f"{sid}.json").read_text())
    bad = set()
    flagged, _ = scan(sid)
    for i, k, p, dr, s, z in flagged:
        if z >= 2.5 or s["loud"] > -7:
            bad.add((i, k))
    for i, sc in enumerate(story["scenes"], 1):
        for k, p in enumerate(phrases(sc["narration"])):
            f = ROOT / "out" / sid / "cb" / f"s{i:02d}_{k:02d}.wav"
            if f.exists():
                d, w = sf.info(str(f)).duration, len(p.split())
                if d / max(w, 1) > 1.1 and d > 1.8:
                    bad.add((i, k))
    return sorted(bad)


def qc(sid, rounds=2):
    for r in range(rounds):
        bad = bad_takes(sid)
        print(f"  qc round {r + 1}: {len(bad)} bad take(s) in {sid}", flush=True)
        if not bad:
            return []
        for i, k in bad:
            f = ROOT / "out" / sid / "cb" / f"s{i:02d}_{k:02d}.wav"
            f.unlink(missing_ok=True)
            f.with_suffix(".retry").write_text(str(0.7 - 0.1 * r))
        sh(PY, "src/voice.py", f"stories/{sid}.json")
    return bad_takes(sid)


def loudness(path):
    out = subprocess.run(["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "mean_volume" in line:
            return float(line.split(":")[1].split()[0])
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    start = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--from=")), "voice")
    module, sids = args[0], args[1:]
    todo = STEPS[STEPS.index(start):]
    for part, sid in enumerate(sids, 1):
        print(f"== {sid}", flush=True)
        if "voice" in todo:
            sh(PY, "src/voice.py", f"stories/{sid}.json")
        left = qc(sid) if "qc" in todo else []
        if "anim" in todo:
            sh(PY, f"src/anim/{module}.py", part)
        if "assemble" in todo:
            sh(PY, "src/assemble.py", f"stories/{sid}.json")
        final = ROOT / "out" / sid / f"{sid}.mp4"
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(final)],
                                   capture_output=True, text=True).stdout or 0)
        rep = {"sid": sid, "seconds": round(dur, 1), "mean_db": loudness(final), "leftover_bad_takes": left,
               "ok": 60 <= dur <= 179 and not left}
        (ROOT / "out" / sid / "report.json").write_text(json.dumps(rep, indent=2))
        print("  report:", rep, flush=True)
        if dur > 179:
            sys.exit(f"{sid} is {dur:.0f}s: over the 3-minute Shorts limit. Trim the script.")


if __name__ == "__main__":
    main()
