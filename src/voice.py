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
MAX_DRAMA = 0.85   # above this Chatterbox can tip into shouting (found by src/voice_qc.py)
PAUSE = {"...": 1.0, "…": 1.0, ".": 0.7, "?": 0.9, "!": 0.6, ",": 0.0, "": 0.35}


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


def speaker(p):
    """'[kai] Lie flat.' -> 'kai' (a character speaks this phrase in their own voice); '' = the narrator."""
    m = re.match(r"\s*~?\s*\[(\w+)\]", p)
    return m.group(1).lower() if m else ""


def say_text(p):
    p = re.sub(r"^\s*\[\w+\]\s*", "", p.lstrip("~").strip())
    p = p.lstrip("~").strip()
    return p.rstrip(".…") if p.endswith(("...", "…")) else p


def whisperize(a, sr, seed=0):
    """Turn voiced speech into a breathy whisper: keep each frame's spectral shape, replace the
    vocal-cord buzz with noise (random phase), tilt toward the hiss band."""
    n, hop = 1024, 256
    a = np.asarray(a, dtype=np.float32)
    if len(a) < n:
        return a * 0.5
    win = np.hanning(n).astype(np.float32)
    frames = 1 + (len(a) - n) // hop
    rng = np.random.default_rng(seed)
    out = np.zeros(len(a) + n, dtype=np.float32)
    norm = np.zeros(len(a) + n, dtype=np.float32)
    f = np.fft.rfftfreq(n, 1 / sr)
    tilt = np.clip((f - 300) / 2500, 0.15, 1.2).astype(np.float32)
    for k in range(frames):
        seg = a[k * hop:k * hop + n] * win
        mag = np.abs(np.fft.rfft(seg)) * tilt
        ph = rng.uniform(0, 2 * np.pi, len(mag))
        y = np.fft.irfft(mag * np.exp(1j * ph), n).astype(np.float32) * win
        out[k * hop:k * hop + n] += y
        norm[k * hop:k * hop + n] += win ** 2
    out = out[:len(a)] / np.maximum(norm[:len(a)], 1e-3)
    rms_in = np.sqrt((a ** 2).mean()) + 1e-9
    rms_out = np.sqrt((out ** 2).mean()) + 1e-9
    out = out * (0.6 * rms_in / rms_out)          # whispers sit a little under normal speech
    return np.clip(out, -0.98, 0.98).astype(np.float32)


def stretch(a, sr, tempo):
    """Speed speech up/down without changing pitch (ffmpeg atempo)."""
    if abs(tempo - 1.0) < 0.01:
        return a
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0",
                        "-af", f"atempo={tempo:.3f}", "-f", "f32le", "-ar", str(sr), "-ac", "1", "pipe:1"],
                       input=a.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def speak_line(tts, style, speed, lang, text, synth=None, tempo=1.0, pause=1.0):
    """Returns (audio @OUT_SR, [(phrase, start, end), ...]).
    synth(phrase) -> (audio, sr) overrides Kokoro (used for Chatterbox)."""
    chunks, segs, t = [], [], 0.0
    for p in phrases(text):
        say = say_text(p)
        a, sr = synth(p) if synth else tts.create(say, voice=style, speed=speed, lang=lang)
        a = trim(np.asarray(a, dtype=np.float32), sr)
        a = stretch(a, sr, tempo)
        if speaker(p) and len(a) > sr // 10:   # character voices: match the narrator's level (they clone louder)
            n = int(0.05 * sr); fr = a[: len(a) // n * n].reshape(-1, n)
            lvl = 20 * np.log10(np.percentile(np.sqrt((fr ** 2).mean(1) + 1e-12), 95) + 1e-9)
            a = np.clip(a * 10 ** ((-17.0 - lvl) / 20), -0.98, 0.98)
        if p.startswith("~"):          # whispered line
            a = whisperize(a, sr, seed=len(p))
        if sr != OUT_SR:
            a = np.interp(np.linspace(0, len(a), int(len(a) * OUT_SR / sr), endpoint=False),
                          np.arange(len(a)), a).astype(np.float32)
        end = next((k for k in ("...", "…", "?", "!", ".", ",") if p.endswith(k)), "")
        gap = np.zeros(int(PAUSE[end] * pause * OUT_SR), dtype=np.float32)
        segs.append((p, t, t + len(a) / OUT_SR))
        chunks += [a, gap]
        t += (len(a) + len(gap)) / OUT_SR
    return np.concatenate(chunks), segs


def chatterbox_batch(story, outdir, vcfg):
    """Voice every phrase of the story in one Chatterbox run; returns a lookup synth()."""
    cb = vcfg.get("chatterbox", {})
    work = outdir / "cb"
    work.mkdir(exist_ok=True)
    jobs, table = [], {}
    for i, scene in enumerate(story["scenes"], 1):
        for k, p in enumerate(phrases(scene["narration"])):
            out = work / f"s{i:02d}_{k:02d}.wav"
            table[p] = table.get(p) or out
            if not out.exists():
                retry = out.with_suffix(".retry")
                override = retry.read_text().strip() if retry.exists() else ""
                drama = float(override) if override else min(scene.get("drama", cb.get("exaggeration", 0.6)), MAX_DRAMA)
                who = cb.get("voices", {}).get(speaker(p))
                jobs.append({"text": say_text(p), "out": str(out), "exaggeration": drama, **({"voice_ref": str(ROOT / who)} if who else {}),
                             "cfg": story.get("pace", {}).get("cfg", cb.get("cfg", 0.35)), "temperature": cb.get("temperature", 0.8),
                             "seed": cb.get("seed", 7) + (7919 * (1 + int(round(drama * 100))) if retry.exists() else 0)})   # new seed per retake level
    for i, scene in enumerate(story["scenes"], 1):       # ghost whispers layered under the scene
        for k, w in enumerate(scene.get("whispers", [])):
            txt = w["text"] if isinstance(w, dict) else w
            out = work / f"w{i:02d}_{k:02d}.wav"
            table["W:" + txt] = out
            if not out.exists():
                jobs.append({"text": txt, "out": str(out), "exaggeration": 0.5, "cfg": 0.5, "temperature": 0.8, "seed": 100 + k})
    if jobs:
        spec = work / "jobs.json"
        spec.write_text(json.dumps({"voice_ref": str(ROOT / cb["voice_ref"]) if cb.get("voice_ref") else None,
                                    "jobs": jobs}))
        print(f"  chatterbox: {len(jobs)} phrases (CPU, this takes a while) ...", flush=True)
        subprocess.run([cb.get("python", "/root/tts-venv/bin/python"), str(ROOT / "src" / "tts_chatterbox.py"),
                        str(spec)], check=True, env={**__import__("os").environ, "HF_HUB_OFFLINE": "1"})

    def synth(p):
        a, sr = sf.read(table[p], dtype="float32")
        return a, sr
    return synth


WHISPER_FX = ("highpass=f=250,aecho=0.8:0.85:60|140|260:0.45|0.3|0.2,"
              "volume=0.9")


def ghost_track(scene, dur, synth, path):
    """Mix a scene's ghost whispers onto a silent track of the scene's length."""
    ws = scene.get("whispers", [])
    if not ws:
        return
    track = np.zeros(int((dur + 2) * OUT_SR), dtype=np.float32)
    for k, w in enumerate(ws):
        txt = w["text"] if isinstance(w, dict) else w
        at = w.get("at") if isinstance(w, dict) else None
        if at is None:
            at = dur * (k + 0.5) / len(ws)
        a, sr = synth("W:" + txt)
        a = whisperize(trim(np.asarray(a, dtype=np.float32), sr), sr, seed=200 + k)
        if sr != OUT_SR:
            a = np.interp(np.linspace(0, len(a), int(len(a) * OUT_SR / sr), endpoint=False), np.arange(len(a)), a).astype(np.float32)
        i = int(at * OUT_SR)
        j = min(len(track), i + len(a))
        track[i:j] += a[: j - i] * 0.55
    raw = path.with_suffix(".raw.wav")
    sf.write(raw, track, OUT_SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", WHISPER_FX, "-ar", str(OUT_SR), str(path)], check=True)
    raw.unlink()


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
    synth = chatterbox_batch(story, outdir, vcfg) if vcfg.get("engine") == "chatterbox" else None
    for i, scene in enumerate(story["scenes"], 1):
        pace = story.get("pace", {})        # {"tempo": 1.12, "pause": 0.4, "cfg": 0.5} = the fast 60-80s format
        a, segs = speak_line(tts, style, vcfg["speed"] * scene.get("speed", 1.0), lang, scene["narration"], synth,
                             tempo=pace.get("tempo", 1.0), pause=pace.get("pause", 1.0))
        write(outdir / f"scene_{i:02d}.wav", a, vcfg.get("polish"))
        (outdir / f"scene_{i:02d}.json").write_text(json.dumps(segs))
        if synth and scene.get("whispers"):
            ghost_track(scene, len(a) / OUT_SR, synth, outdir / f"scene_{i:02d}.whisper.wav")
        print(f"  scene {i}: {len(a) / OUT_SR:.1f}s")


if __name__ == "__main__":
    main()
