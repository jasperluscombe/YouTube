"""Stitch finished 3-part stories into one long-form "full movie" for YouTube.

    python src/compile_movie.py out/movies/week1.mp4 "20_lights_at_914,21_lights_part2,22_lights_part3" "23_..,24_..,25_.."

Per story: Part 1 without its end card, Parts 2-3 without their "previously" recap and end cards,
then a chapter card before each story and an outro card asking which story was best.
Output is 16:9 (the vertical frame centred over a blurred, darkened copy of itself) because
long-form viewers watch on TV/desktop. Also writes <out>.chapters.txt for the description.
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = str(ROOT / "fonts" / "Anton-Regular.ttf")
W, H = 1920, 1080


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-1500:])


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


def scene_bounds(sid):
    """Start/end of every scene in the final video (scenes = per-scene clips, concatenated)."""
    tmp = ROOT / "out" / sid / "tmp"
    clips = sorted(p for p in tmp.glob("clip_[0-9][0-9].mp4"))
    t, out = 0.0, []
    for c in clips:
        d = dur(c); out.append((t, t + d)); t += d
    return out


WIDE = (f"split[a][b];[b]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=40,eq=brightness=-0.25[bg];"
        f"[a]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0,setsar=1,fps=30,format=yuv420p")


def segment(src, a, b, out):
    run(["ffmpeg", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(src), "-filter_complex", f"[0:v]{WIDE}[v]",
         "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
         "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k", str(out)])


def card(lines, out, secs=2.8):
    tmp = out.with_suffix(".txt")
    draws = []
    for k, (txt, size, col) in enumerate(lines):
        f = out.with_name(out.stem + f"_{k}.txt"); f.write_text(txt)
        y = f"(h/2)+({(k - (len(lines) - 1) / 2) * 1.3:.2f}*{size})-text_h/2"
        draws.append(f"drawtext=fontfile={FONT}:textfile={f}:fontsize={size}:fontcolor={col}:x=(w-text_w)/2:y={y}:"
                     f"alpha='min(1,t/0.4)*min(1,({secs}-t)/0.4)'")
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x07080b:s={W}x{H}:r=30:d={secs}",
         "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo", "-t", str(secs),
         "-vf", ",".join(draws) + ",format=yuv420p", "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-shortest", str(out)])


def main(out_path, groups):
    out = pathlib.Path(out_path); out.parent.mkdir(parents=True, exist_ok=True)
    work = out.with_suffix(""); work.mkdir(exist_ok=True)
    pieces, chapters, t = [], [], 0.0
    titles = []
    for n, g in enumerate(groups, 1):
        sids = g.split(",")
        series = json.loads((ROOT / "stories" / f"{sids[0]}.json").read_text()).get("series", f"Story {n}")
        titles.append(series)
        c = work / f"card_{n}.mp4"
        card([(f"STORY {n}", 60, "0xd9d9d9"), (series.upper(), 120, "0xffd27a")], c)
        pieces.append(c); chapters.append((t, f"Story {n}: {series}")); t += dur(c)
        for k, sid in enumerate(sids):
            b = scene_bounds(sid)
            src = ROOT / "out" / sid / f"{sid}.mp4"
            a = 0.0 if k == 0 else b[0][1]                     # drop the "previously" recap on parts 2-3
            z = b[-1][0]                                       # drop every end card
            seg = work / f"s{n}_{k + 1}.mp4"
            segment(src, a, z, seg)
            pieces.append(seg); t += dur(seg)
    o = work / "outro.mp4"
    card([("WHICH STORY WAS THE BEST?", 90, "0xffffff"), ("TELL ME IN THE COMMENTS", 60, "0xffd27a"),
          ("NEW STORIES EVERY DAY - SUBSCRIBE", 50, "0xd9d9d9")], o, secs=6)
    pieces.append(o)
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in pieces))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])
    ch = "\n".join(f"{int(s // 60)}:{int(s % 60):02d} {name}" for s, name in chapters)
    ch = "0:00 Intro\n" + ch if chapters[0][0] > 0 else ch
    out.with_suffix(".chapters.txt").write_text(ch + "\n")
    print(f"{out}  ({dur(out) / 60:.1f} min)\n{ch}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
