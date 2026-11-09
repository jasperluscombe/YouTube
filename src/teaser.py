"""Cut a teaser Short from an assembled episode: a run of scenes + a "full episode" banner.

    python src/teaser.py stories/20_lights_at_914.json 9-14 sign
    -> out/<id>/<id>_teaser_sign.mp4

Uses the per-scene clips assemble.py already made (voice, sfx, captions included).
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = str(ROOT / "fonts" / "Anton-Regular.ttf")


def main(story_path, rng, name):
    s = json.loads(pathlib.Path(story_path).read_text())
    a, b = map(int, rng.split("-"))
    tmp = ROOT / "out" / s["id"] / "tmp"
    lst = tmp / f"teaser_{name}.txt"
    lst.write_text("".join(f"file 'clip_{i:02d}.mp4'\n" for i in range(a, b + 1)))
    joined = tmp / f"teaser_{name}_raw.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(joined)],
                               capture_output=True, text=True).stdout)
    (tmp / "t_top.txt").write_text(s.get("series", "").upper() + "  •  PART 1")
    (tmp / "t_end.txt").write_text("FULL EPISODE ON MY CHANNEL")
    vf = (f"drawbox=x=0:y=110:w=iw:h=86:color=black@0.55:t=fill,"
          f"drawtext=fontfile={FONT}:textfile={tmp}/t_top.txt:fontsize=56:fontcolor=white:x=(w-text_w)/2:y=124,"
          f"drawbox=x=150:y=1000:w=780:h=130:color=0xc4302b@0.95:t=fill:enable='gte(t,{dur - 3.5:.2f})',"
          f"drawtext=fontfile={FONT}:textfile={tmp}/t_end.txt:fontsize=64:fontcolor=white:x=(w-text_w)/2:y=1030:"
          f"enable='gte(t,{dur - 3.5:.2f})'")
    out = ROOT / "out" / s["id"] / f"{s['id']}_teaser_{name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-vf", vf, "-c:v", "libx264", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
    print(f"{out} ({dur:.1f}s)")


if __name__ == "__main__":
    main(*sys.argv[1:4])
