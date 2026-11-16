"""Generate an animated clip for every scene with a fal.ai video model.

    python src/clips.py stories/02_day_40_bunker.json

Saves assets/clips/<id>/scene_XX.mp4 and skips clips that already exist (so you never
pay twice) and scenes that use the free "alert" screen. The model is set in channel.yaml.
Auth: FAL_KEY env var, or the session's network secret for queue.fal.run.
"""
import json, os, pathlib, sys, time, urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEY = os.environ.get("FAL_KEY", "proxy-injected")


def call(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Key {KEY}", "Content-Type": "application/json"},
                                 method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def generate(model, args, prompt, dest):
    job = call(f"https://queue.fal.run/{model}", {"prompt": prompt, **args})
    while True:
        time.sleep(8)
        st = call(job["status_url"])
        if st["status"] == "COMPLETED":
            break
        if st["status"] not in ("IN_QUEUE", "IN_PROGRESS"):
            raise RuntimeError(st)
    res = call(job["response_url"])
    urllib.request.urlretrieve(res["video"]["url"], dest)


def main(path):
    vcfg = yaml.safe_load((ROOT / "channel.yaml").read_text())["video"]
    story = json.loads(pathlib.Path(path).read_text())
    outdir = ROOT / "assets" / "clips" / story["id"]
    outdir.mkdir(parents=True, exist_ok=True)
    for i, sc in enumerate(story["scenes"], 1):
        dest = outdir / f"scene_{i:02d}.mp4"
        if sc.get("alert") or dest.exists():
            continue
        print(f"  clip {i}/{len(story['scenes'])} ...", flush=True)
        generate(vcfg["model"], vcfg.get("args", {}), sc["visual"], dest)


if __name__ == "__main__":
    main(sys.argv[1])
