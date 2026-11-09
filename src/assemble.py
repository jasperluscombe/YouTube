"""Build a vertical Short from a story: images + narration + burned-in captions.

    python src/assemble.py stories/01_the_last_kitten.json
    python src/assemble.py stories/01_the_last_kitten.json --silent   # test without TTS

Images:  assets/images/<story id>/scene_01.png ... (generate from each scene's
         image_prompt in any image/video generator). Missing images get a
         placeholder card so the pipeline always runs.
Audio:   out/<story id>/scene_XX.wav from src/voice.py.
Output:  out/<story id>/<story id>.mp4
"""
import argparse, json, pathlib, subprocess, textwrap

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("--silent", action="store_true", help="fake audio (~2.6 words/sec) to test visuals")
    args = ap.parse_args()

    fmt = yaml.safe_load((ROOT / "channel.yaml").read_text())["format"]
    W, H, FPS = fmt["width"], fmt["height"], fmt["fps"]
    story = json.loads(pathlib.Path(args.story).read_text())
    sid = story["id"]
    outdir = ROOT / "out" / sid
    outdir.mkdir(parents=True, exist_ok=True)
    imgdir = ROOT / "assets" / "images" / sid

    clips = []
    for i, scene in enumerate(story["scenes"], 1):
        wav = outdir / f"scene_{i:02d}.wav"
        if args.silent:
            secs = max(2.0, len(scene["narration"].split()) / 2.6)
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{secs:.2f}", str(wav)])
        dur = duration(wav) + 0.25
        frames = int(dur * FPS)

        img = next((p for ext in ("png", "jpg", "jpeg", "webp")
                    if (p := imgdir / f"scene_{i:02d}.{ext}").exists()), None)
        if img is None:
            img = outdir / f"placeholder_{i:02d}.png"
            label = outdir / f"label_{i:02d}.txt"
            label.write_text(textwrap.fill(f"SCENE {i}\n" + scene["image_prompt"], 34))
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x2b2233:s={W}x{H}",
                 "-vf", f"drawtext=fontfile={FONT}:textfile={label}:fontcolor=0x9a8fa6:fontsize=40:"
                        "x=(w-text_w)/2:y=h*0.2:line_spacing=12",
                 "-frames:v", "1", str(img)])

        cap = outdir / f"cap_{i:02d}.txt"
        cap.write_text(textwrap.fill(scene["narration"], 26))
        # slow Ken Burns zoom + caption in the lower third (clear of Shorts UI)
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"zoompan=z='min(zoom+0.0006,1.12)':d={frames}:s={W}x{H}:fps={FPS}:"
              "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
              f"drawtext=fontfile={FONT}:textfile={cap}:fontcolor=white:fontsize=58:"
              "borderw=6:bordercolor=black:line_spacing=14:x=(w-text_w)/2:y=h*0.62")
        clip = outdir / f"clip_{i:02d}.mp4"
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-i", str(wav), "-vf", vf,
             "-t", f"{dur:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-ar", "44100", "-ac", "2", str(clip)])
        clips.append(clip)

    lst = outdir / "clips.txt"
    lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
    final = outdir / f"{sid}.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(final)])
    total = duration(final)
    print(f"{final}  ({total:.1f}s)" + ("  ⚠ over Shorts limit" if total > fmt["max_seconds"] else ""))


if __name__ == "__main__":
    main()
