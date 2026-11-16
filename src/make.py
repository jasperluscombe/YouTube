"""One command for a finished, ready-to-upload Short (or all of them).

    python src/make.py stories/02_day_40_bunker.json
    python src/make.py all

Runs voice -> clips -> assemble, then writes out/<id>/upload.txt with the
title, description and tags to paste into the YouTube app.
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAGS = "POV, apocalypse, survival, future, what if, scifi, animated story, shorts"


def upload_text(s):
    return (f"TITLE:\n{s['title']} #shorts\n\n"
            f"DESCRIPTION:\n{s['scenes'][0]['narration']}\n\n{s['scenes'][-1]['narration']}\n\n"
            "New POV stories every day: apocalypse, survival and the far future. Follow for part 2.\n"
            "#shorts #pov #apocalypse #survival #whatif\n\n"
            f"TAGS:\n{TAGS}, {s['series']}\n\n"
            "SETTINGS: Not made for kids. Altered or synthetic content: YES (AI-generated animation and voice).\n")


def make(path):
    s = json.loads(pathlib.Path(path).read_text())
    print(f"== {s['id']}")
    for step in ("voice.py", "clips.py", "assemble.py"):
        subprocess.run([sys.executable, str(ROOT / "src" / step), str(path)], check=True)
    (ROOT / "out" / s["id"] / "upload.txt").write_text(upload_text(s))


if __name__ == "__main__":
    a = sys.argv[1]
    for p in (sorted((ROOT / "stories").glob("*.json")) if a == "all" else [pathlib.Path(a)]):
        make(p)
