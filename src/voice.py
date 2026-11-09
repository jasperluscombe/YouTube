"""Narration with our own blended Kokoro voice (ONNX: runs on CPU, no GPU or torch).

    python src/voice.py --preview
    python src/voice.py stories/20_lights_at_914.json

Dramatic delivery: each line is split into sentences and beats ("..."), each spoken
separately, then joined with deliberate pauses. The timing of every phrase is saved to
out/<story>/scene_XX.json so captions land exactly on the words.
Writes out/<story>/scene_XX.wav
"""
import argparse, json, pathlib, re, subprocess, urllib.request

import numpy as np
import soundfile as sf
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = ["kokoro-v1.0.int8.onnx", "voices-v1.0.bin"]
OUT_SR = 44100

POLISH = ("highpass=f=70,equalizer=f=160:t=q:w=1:g=3,equalizer=f=3000:t=q:w=1.2:g=2.5,"
          "acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,"
          "aecho=0.8:0.5:22|37:0.12|0.07")

# pause (seconds) after a phrase, by how it ends
PAUSE = {"...": 0.75, "…": 0.75, ".": 0.5, "?": 0.6, "!": 0.45, ",": 0.0, "": 0.3}


def ensure_models():
    MODELS.mkdir(exist_ok=True)
    for f in FILES:
        if not (MODELS / f).exists():
            print(f"downloading {f} ...")
            urllib.request.urlretrieve(BASE + f, MODELS / f)


def load():
    from kokoro_onnx import Kokoro
    ensure_models()
    vcfg = yaml.safe_load((ROOT / "channel.yaml").read_text())["voice"]
    tts = Kokoro(str(MODELS / FILES[0]), str(MODELS / FILES[1]))
    total = sum(vcfg["blend"].values())
    style = sum(tts.get_voice_style(n) * (w / total) for n, w in vcfg["blend"].items())
    lang = "en-us" if vcfg["lang_code"] == "a" else "en-gb"
    return tts, style, vcfg


def phrases(text):
    """Split into spoken beats, keeping the ending punctuation."""
    parts = re.findall(r".+?(?:\.\.\.|…|[.!?](?=\s|$)|$)", text.strip())
    return [p.strip() for p in parts if p.strip()]


def trim(a, sr, thresh=0.01):
    idx = np.where(np.abs(a) > thresh)[0]
    if not len(idx):
        return a
    return a[max(0, idx[0] - int(0.02 * sr)): idx[-1] + int(0.06 * sr)]


def speak_line(tts, style, speed, lang, text):
    """Returns (audio @OUT_SR, [(phrase, start, end), ...])."""
    chunks, segs, t = [], [], 0.0
    for p in phrases(text):
        say = p.rstrip(".…") if p.endswith(("...", "…")) else p
        a, sr = tts.create(say, voice=style, speed=speed, lang=lang)
        a = trim(np.asarray(a, dtype=np.float32), sr)
        if sr != OUT_SR:
            a = np.interp(np.linspace(0, len(a), int(len(a) * OUT_SR / sr), endpoint=False),
                          np.arange(len(a)), a).astype(np.float32)
        end = next((k for k in ("...", "…", "?", "!", ".", ",") if p.endswith(k)), "")
        gap = np.zeros(int(PAUSE[end] * OUT_SR), dtype=np.float32)
        segs.append((p, t, t + len(a) / OUT_SR))
        chunks += [a, gap]
        t += (len(a) + len(gap)) / OUT_SR
    return np.concatenate(chunks), segs


def write(path, audio, polish):
    sf.write(path, audio, OUT_SR)
    if polish:
        tmp = path.with_suffix(".raw.wav")
        path.rename(tmp)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af", POLISH,
                        "-ar", str(OUT_SR), str(path)], check=True)
        tmp.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story", nargs="?")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    tts, style, vcfg = load()
    lang = "en-us" if vcfg["lang_code"] == "a" else "en-gb"

    if args.preview or not args.story:
        out = ROOT / "out" / "voice_preview.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        a, _ = speak_line(tts, style, vcfg["speed"], lang,
                          "Every night, at exactly nine fourteen... every light in the city turns on. For one minute.")
        write(out, a, vcfg.get("polish"))
        print(f"preview -> {out}")
        return

    story = json.loads(pathlib.Path(args.story).read_text())
    outdir = ROOT / "out" / story["id"]
    outdir.mkdir(parents=True, exist_ok=True)
    for i, scene in enumerate(story["scenes"], 1):
        a, segs = speak_line(tts, style, vcfg["speed"] * scene.get("speed", 1.0), lang, scene["narration"])
        write(outdir / f"scene_{i:02d}.wav", a, vcfg.get("polish"))
        (outdir / f"scene_{i:02d}.json").write_text(json.dumps(segs))
        print(f"  scene {i}: {len(a) / OUT_SR:.1f}s")


if __name__ == "__main__":
    main()
