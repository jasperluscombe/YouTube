"""Chatterbox TTS worker (runs inside its own venv: /root/tts-venv).

    /root/tts-venv/bin/python src/tts_chatterbox.py jobs.json

jobs.json: {"voice_ref": "voices/narrator_ref.wav" | null,
            "jobs": [{"text": "...", "out": "path.wav", "exaggeration": 0.6, "cfg": 0.4}, ...]}
One model load for the whole batch. Writes 24 kHz mono wavs.
"""
import json, sys

import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

torch.set_num_threads(max(1, torch.get_num_threads()))
spec = json.load(open(sys.argv[1]))
model = ChatterboxTTS.from_pretrained(device="cpu")
if spec.get("voice_ref"):
    model.prepare_conditionals(spec["voice_ref"], exaggeration=spec["jobs"][0].get("exaggeration", 0.5))
for j in spec["jobs"]:
    torch.manual_seed(j.get("seed", 7))
    wav = model.generate(j["text"], exaggeration=j.get("exaggeration", 0.5),
                         cfg_weight=j.get("cfg", 0.5), temperature=j.get("temperature", 0.8))
    ta.save(j["out"], wav, model.sr)
    print("ok", j["out"], flush=True)
