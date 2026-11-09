"""Build a vertical Short: animated clips + narration + big word-by-word captions.

    python src/assemble.py stories/02_day_40_bunker.json [--silent]

Per scene, the visual is the first that exists:
  1. "alert" in the scene JSON -> an emergency-broadcast screen drawn here (free)
  2. assets/clips/<id>/scene_XX.mp4   (animated clip from src/clips.py)
  3. assets/images/<id>/scene_XX.png  (still, with slow zoom)
  4. a placeholder card showing the visual prompt
Audio: out/<id>/scene_XX.wav from src/voice.py.  Output: out/<id>/<id>.mp4
"""
import argparse, json, pathlib, re, subprocess, textwrap

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = str(ROOT / "fonts" / "Anton-Regular.ttf")
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-1500:])


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def chunks(text):
    """Split narration into 1-3 word caption pops, breaking at punctuation."""
    words, out, cur = text.split(), [], []
    for w in words:
        cur.append(w)
        if len(cur) == 3 or re.search(r"[.,!?:;…]$", w) or (len(cur) == 2 and len(w) > 7):
            out.append(" ".join(cur)); cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def caption_filters(text, dur, tmp, prefix):
    """drawtext filters timed by character share of the scene's audio."""
    parts = chunks(text)
    weights = [len(p) + 3 for p in parts]
    total, t, f = sum(weights), 0.0, []
    for k, (p, w) in enumerate(zip(parts, weights)):
        d = dur * w / total
        tf = tmp / f"{prefix}_{k:02d}.txt"
        tf.write_text(re.sub(r"[.,;:]$", "", p).upper())
        f.append(f"drawtext=fontfile={FONT}:textfile={tf}:fontsize=118:fontcolor=white:"
                 f"borderw=9:bordercolor=black:shadowx=0:shadowy=8:shadowcolor=black@0.6:"
                 f"x=(w-text_w)/2:y=h*0.6:enable='between(t,{t:.3f},{t + d:.3f})'")
        t += d
    return f


def alert_source(alert, W, H, tmp, i):
    """Emergency-broadcast screen: red panel, flashing header, scrolling ticker, scanlines."""
    (tmp / f"a_head_{i}.txt").write_text(alert.get("header", "EMERGENCY ALERT"))
    (tmp / f"a_l1_{i}.txt").write_text(alert["line1"])
    (tmp / f"a_l2_{i}.txt").write_text(alert.get("line2", ""))
    (tmp / f"a_tick_{i}.txt").write_text(("   •   ".join([alert["ticker"]] * 3)).upper())
    py = int(H * 0.27)
    return (f"color=c=0x1a0f12:s={W}x{H}:r=30,"
            f"drawbox=x=0:y={py}:w={W}:h={int(H*0.24)}:color=0xb3261e:t=fill,"
            f"drawbox=x=0:y={py}:w={W}:h=110:color=0xe0442b:t=fill:enable='lt(mod(t,1),0.6)',"
            f"drawtext=fontfile={FONT}:textfile={tmp}/a_head_{i}.txt:fontsize=72:fontcolor=0xffd9c9:"
            f"x=(w-text_w)/2:y={py + 18},"
            f"drawtext=fontfile={FONT}:textfile={tmp}/a_l1_{i}.txt:fontsize=150:fontcolor=0xffe3dc:"
            f"x=(w-text_w)/2:y={py + 140},"
            f"drawtext=fontfile={FONT}:textfile={tmp}/a_l2_{i}.txt:fontsize=150:fontcolor=0xffb21e:"
            f"x=(w-text_w)/2:y={py + 290},"
            f"drawbox=x=0:y={py + int(H*0.24) + 10}:w={W}:h=90:color=0x3a1416:t=fill,"
            f"drawtext=fontfile={FONT}:textfile={tmp}/a_tick_{i}.txt:fontsize=62:fontcolor=0xf2d2c8:"
            f"x=w-mod(t*260\\,w+text_w):y={py + int(H*0.24) + 22},"
            f"drawgrid=w={W}:h=6:t=2:c=black@0.35,noise=alls=12:allf=t")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("--silent", action="store_true", help="fake audio to test visuals")
    args = ap.parse_args()

    fmt = yaml.safe_load((ROOT / "channel.yaml").read_text())["format"]
    W, H, FPS = fmt["width"], fmt["height"], fmt["fps"]
    story = json.loads(pathlib.Path(args.story).read_text())
    sid = story["id"]
    outdir = ROOT / "out" / sid
    tmp = outdir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    clips = []
    for i, scene in enumerate(story["scenes"], 1):
        wav = outdir / f"scene_{i:02d}.wav"
        if args.silent:
            secs = max(2.0, len(scene["narration"].split()) / 2.6)
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{secs:.2f}", str(wav)])
        speech = duration(wav)
        dur = speech + 0.3
        caps = ",".join(caption_filters(scene["narration"], speech, tmp, f"c{i:02d}"))
        fit = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"

        vid = ROOT / "assets" / "clips" / sid / f"scene_{i:02d}.mp4"
        img = next((p for e in ("png", "jpg", "webp")
                    if (p := ROOT / "assets" / "images" / sid / f"scene_{i:02d}.{e}").exists()), None)
        if scene.get("alert"):
            inputs = ["-f", "lavfi", "-i", alert_source(scene["alert"], W, H, tmp, i)]
            vf = caps
        elif vid.exists():
            inputs = ["-stream_loop", "-1", "-i", str(vid)]
            vf = f"{fit},{caps}"
        elif img:
            inputs = ["-loop", "1", "-i", str(img)]
            vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
                  f"zoompan=z='min(zoom+0.0006,1.12)':d={int(dur*FPS)}:s={W}x{H}:fps={FPS},{caps}")
        else:
            label = tmp / f"label_{i:02d}.txt"
            label.write_text(textwrap.fill(f"SCENE {i}: " + scene["visual"].split(";")[0], 34))
            inputs = ["-f", "lavfi", "-i", f"color=c=0x14181c:s={W}x{H}:r={FPS}"]
            vf = (f"drawtext=fontfile={SANS}:textfile={label}:fontcolor=0x6f8796:fontsize=40:"
                  f"x=(w-text_w)/2:y=h*0.18:line_spacing=12,{caps}")

        clip = tmp / f"clip_{i:02d}.mp4"
        run(["ffmpeg", "-y", *inputs, "-i", str(wav), "-map", "0:v", "-map", "1:a",
             "-vf", vf, "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-ar", "44100", "-ac", "2",
             "-af", "apad", str(clip)])
        clips.append(clip)

    lst = tmp / "clips.txt"
    lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
    final = outdir / f"{sid}.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(final)])
    total = duration(final)
    print(f"{final}  ({total:.1f}s)" + ("  ⚠ over Shorts limit" if total > fmt["max_seconds"] else ""))


if __name__ == "__main__":
    main()
