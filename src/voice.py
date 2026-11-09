"""Narration with our own blended Kokoro voice (ONNX: runs on CPU, no GPU or torch).

    python src/voice.py --preview
    python src/voice.py stories/01_last_human_2087.json

Model files are downloaded to models/ on first run (from the kokoro-onnx GitHub releases).
Writes out/<story>/scene_XX.wav
"""
import argparse, json, pathlib, urllib.request

import numpy as np
import soundfile as sf
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = ["kokoro-v1.0.int8.onnx", "voices-v1.0.bin"]


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
    # Weighted average of voice style vectors = our own narrator voice.
    style = sum(tts.get_voice_style(n) * (w / total) for n, w in vcfg["blend"].items())
    lang = "en-us" if vcfg["lang_code"] == "a" else "en-gb"
    return tts, style, vcfg["speed"], lang


def speak(tts, style, speed, lang, text):
    audio, sr = tts.create(text, voice=style, speed=speed, lang=lang)
    return np.asarray(audio), sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story", nargs="?")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    tts, style, speed, lang = load()

    if args.preview or not args.story:
        line = ("It's day forty. The radio went silent three weeks ago. "
                "Tonight, for the first time, you see a light on the horizon.")
        out = ROOT / "out" / "voice_preview.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        audio, sr = speak(tts, style, speed, lang, line)
        sf.write(out, audio, sr)
        print(f"preview -> {out}")
        return

    story = json.loads(pathlib.Path(args.story).read_text())
    outdir = ROOT / "out" / story["id"]
    outdir.mkdir(parents=True, exist_ok=True)
    for i, scene in enumerate(story["scenes"], 1):
        audio, sr = speak(tts, style, speed, lang, scene["narration"])
        sf.write(outdir / f"scene_{i:02d}.wav", audio, sr)
        print(f"  scene {i}: {len(audio) / sr:.1f}s")


if __name__ == "__main__":
    main()
