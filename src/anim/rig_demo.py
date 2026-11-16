"""Rig demo: expressive characters + lip-sync in a cinematic scene (for review)."""
import math, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import *  # noqa
from cinema import camera, soft_shadow, backlight, dust, god_rays
from rig import Character, lipsync
from nightshift import store, counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
WAV = ROOT / "out" / "27_nightshift_2" / "cb" / "s13_00.wav"      # "Mia whispers, I'm thirsty."
SAM = Character("Sam", skin="#d9a07a", hair="#3a2418", hair_style="short", top="#c4632f", top2="#e8e2d6", seed=1)
MIA = Character("Mia", age="child", skin="#e8b896", hair="#6b3a1e", hair_style="ponytail", top="#d6577f", pants="#3b4466", seed=2)
talk = lipsync(WAV)


def scene(ctx, t, d):
    worry = ease(prog(t, 1.2, 2.2))
    with camera(ctx, t, d, push=0.12, handheld=0.5, focus=(540, 1050)):
        store(ctx, t, light=0.6, seed=9)
        soft_shadow(ctx, 330, 1405, 360); soft_shadow(ctx, 740, 1405, 300)
        backlight(ctx, 540, 1000, 500, (0.8, 0.9, 1.0), 0.15)
        SAM.draw(ctx, 330, 1400, 760, t, mode="idle", face=1, expr="neutral", expr_to="fear", expr_k=worry,
                 look=(1.0, 0.3), head_turn=0.3, arm_f=(0.5 + 0.4 * worry, 0.6))
        MIA.draw(ctx, 740, 1400, 560, t, mode="idle", face=-1, expr="tired", talk=talk(t - 0.3), look=(-1.0, -0.4))
        dust(ctx, t, (100, 300, 1000, 1400), light=(540, 300))
    vignette(ctx, 0.8); grain(ctx, t)


def wide(ctx, t, d):
    with camera(ctx, t, d, push=0.05, handheld=0.4, focus=(540, 1250)):
        store(ctx, t, light=0.7, seed=4)
        for k, (ch, x, sz, ph) in enumerate(((SAM, 300, 520, 0), (MIA, 520, 390, 1))):
            soft_shadow(ctx, x + t * 90, 1405, 260)
            ch.draw(ctx, x + t * 90, 1400, sz, t, mode="walk", phase=t * 6 + ph, face=1,
                    expr="determined" if ch is SAM else "neutral", look=(1, 0))
    vignette(ctx, 0.8); grain(ctx, t)


if __name__ == "__main__":
    out = ROOT / "out" / "rig_demo"; out.mkdir(parents=True, exist_ok=True)
    render(wide, 3.0, out / "a.mp4")
    render(scene, 4.2, out / "b.mp4")
    (out / "l.txt").write_text("file 'a.mp4'\nfile 'b.mp4'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(out / "l.txt"), "-c", "copy", str(out / "v.mp4")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out / "v.mp4"), "-itsoffset", "3.3", "-i", str(WAV),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-af", "apad", "-shortest", str(out / "rig_demo.mp4")], check=True)
    print(out / "rig_demo.mp4")
