"""Narration with our own blended Kokoro voice.

    python src/voice.py --preview                 # say a test line with the blend
    python src/voice.py stories/01_the_last_kitten.json   # narrate every scene

Writes out/<story>/scene_XX.wav (24 kHz mono).
"""
import argparse, json, pathlib, sys

import numpy as np
import soundfile as sf
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SR = 24000


def load_cfg():
    return yaml.safe_load((ROOT / "channel.yaml").read_text())


def build_voice(pipeline, vcfg):
    """Weighted average of Kokoro voice style tensors = our own voice."""
    import torch

    blend = vcfg["blend"]
    total = sum(blend.values())
    mixed = sum(pipeline.load_voice(name) * (w / total) for name, w in blend.items())
    out = ROOT / vcfg["save_as"]
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(mixed, out)
    return mixed


def speak(pipeline, voice, text, speed):
    chunks = [audio for _, _, audio in pipeline(text, voice=voice, speed=speed)]
    return np.concatenate([np.asarray(c) for c in chunks]) if chunks else np.zeros(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story", nargs="?")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    from kokoro import KPipeline  # imported late so --help works without it

    vcfg = load_cfg()["voice"]
    pipeline = KPipeline(lang_code=vcfg["lang_code"])
    voice = build_voice(pipeline, vcfg)

    if args.preview or not args.story:
        line = "He was the smallest kitten in the box. Nobody chose him. Until the rain came."
        out = ROOT / "out" / "voice_preview.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        sf.write(out, speak(pipeline, voice, line, vcfg["speed"]), SR)
        print(f"preview -> {out}")
        return

    story = json.loads(pathlib.Path(args.story).read_text())
    outdir = ROOT / "out" / story["id"]
    outdir.mkdir(parents=True, exist_ok=True)
    for i, scene in enumerate(story["scenes"], 1):
        audio = speak(pipeline, voice, scene["narration"], vcfg["speed"])
        sf.write(outdir / f"scene_{i:02d}.wav", audio, SR)
        print(f"scene {i}: {len(audio) / SR:.1f}s")


if __name__ == "__main__":
    sys.exit(main())
