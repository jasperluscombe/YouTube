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
current = None
for j in sorted(spec["jobs"], key=lambda j: j.get("voice_ref") or ""):      # group by voice: one re-conditioning per voice
    ref = j.get("voice_ref") or spec.get("voice_ref")
    if ref and ref != current:
        model.prepare_conditionals(ref, exaggeration=j.get("exaggeration", 0.5)); current = ref
    torch.manual_seed(j.get("seed", 7))
    wav = model.generate(j["text"], exaggeration=j.get("exaggeration", 0.5),
                         cfg_weight=j.get("cfg", 0.5), temperature=j.get("temperature", 0.8))
    ta.save(j["out"], wav, model.sr)
    print("ok", j["out"], flush=True)
