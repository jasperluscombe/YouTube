"""Schedule a finished 3-part story on YouTube, TikTok (and Instagram) through Buffer.

    python src/buffer_post.py launch/EP_lights_upload.json 20_lights_at_914 21_lights_part2 22_lights_part3
    python src/buffer_post.py --channels          # list connected channels
    python src/buffer_post.py --queue             # list scheduled posts

Buffer only takes videos by public URL, so each video (and its cover) is pushed to the
media/ folder of this repo's project branch and linked from raw.githubusercontent.com.
Auth: the Buffer API key is a network secret injected by the session proxy (no env var).
Posts whose time has already passed are skipped.
"""
import datetime as dt, json, pathlib, shutil, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.buffer.com"
REPO = "jasperluscombe/YouTube"
CFG = ROOT / "launch" / "buffer.json"   # {"organization": id, "channels": {"youtube": id, "tiktok": id, "instagram": id|null}}


def gql(query, variables=None):
    req = urllib.request.Request(API, data=json.dumps({"query": query, "variables": variables or {}}).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer proxy-injected"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read())
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


def git(*a, cwd=None):
    return subprocess.run(["git", *a], cwd=cwd or MEDIA_DIR, check=True, capture_output=True, text=True).stdout


BRANCH = "claude/zealous-keller-z4hm7z"   # the branch this project is allowed to push to


def publish_media(files):
    """Commit files under media/ on the project branch and push; return their raw URLs."""
    mdir = ROOT / "media"
    mdir.mkdir(exist_ok=True)
    for f in files:
        shutil.copy2(f, mdir / pathlib.Path(f).name)
    git("add", "media", cwd=ROOT)
    if git("status", "--porcelain", "media", cwd=ROOT).strip():
        git("commit", "-qm", "media: videos and covers for Buffer", cwd=ROOT)
    for k in range(4):
        try:
            git("push", "-q", "origin", BRANCH, cwd=ROOT); break
        except subprocess.CalledProcessError:
            import time; time.sleep(2 ** (k + 1))
    return {pathlib.Path(f).name: f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/media/{pathlib.Path(f).name}" for f in files}


def create(channel, text, due, video_url, thumb_url, meta):
    q = """mutation($i: CreatePostInput!){ createPost(input:$i){
             __typename ... on PostActionSuccess { post { id dueAt status channelService } }
             ... on MutationError { message } } }"""
    inp = {"channelId": channel, "text": text, "schedulingType": "automatic", "mode": "customScheduled",
           "dueAt": due, "needsApproval": False, "aiAssisted": True,
           "assets": [{"video": {"url": video_url, **({"metadata": {"thumbnailOffset": thumb_url}} if thumb_url is not None else {})}}], "metadata": meta}
    return gql(q, {"i": inp})["createPost"]


def strip_shorts(s):
    return s.replace(" #shorts", "").replace("#shorts ", "")


def main(kit_path, sids):
    cfg = json.loads(CFG.read_text())
    kit = json.loads(pathlib.Path(kit_path).read_text())
    parts = list(kit.values())
    vids = [ROOT / "out" / sid / f"{sid}.mp4" for sid in sids]
    urls = publish_media([str(v) for v in vids])
    now = dt.datetime.now(dt.timezone.utc)
    for k, (m, v) in enumerate(zip(parts, vids)):
        due = m["publish_at"]
        if dt.datetime.fromisoformat(due.replace("Z", "+00:00")) <= now + dt.timedelta(minutes=10):
            print(f"skip part {k + 1}: {due} has passed"); continue
        vurl = urls[v.name]
        cover = m.get("cover_ms")
        tiktok_text = strip_shorts(m["title"]) + "\n\n" + strip_shorts(m["description"])
        jobs = [("youtube", m["description"], {"youtube": {"title": m["title"][:100], "privacy": "public", "categoryId": "24",
                                                             "madeForKids": False, "isAiGenerated": True, "notifySubscribers": True}}),
                ("tiktok", tiktok_text[:2200], {"tiktok": {"title": strip_shorts(m["title"])[:90], "isAiGenerated": True}}),
                ("instagram", tiktok_text[:2200], {"instagram": {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": True,
                                                                 "firstComment": m.get("comment", "")}})]
        for svc, text, meta in jobs:
            ch = cfg["channels"].get(svc)
            if not ch:
                continue
            r = create(ch, text, due, vurl, cover if svc in ("tiktok", "instagram") else None, meta)
            print(f"part {k + 1} {svc}: {r}")


if __name__ == "__main__":
    if sys.argv[1] == "--channels":
        org = json.loads(CFG.read_text())["organization"]
        print(json.dumps(gql("query($o:OrganizationId!){ channels(input:{organizationId:$o}){ id name service } }", {"o": org}), indent=1))
    elif sys.argv[1] == "--queue":
        org = json.loads(CFG.read_text())["organization"]
        d = gql("""query($o:OrganizationId!){ posts(first:30, input:{organizationId:$o, filter:{status:[scheduled]}}){
                    edges{ node{ id dueAt status channelService text error{ message } } } } }""", {"o": org})
        for e in d["posts"]["edges"]:
            n = e["node"]; print(n["dueAt"], n["channelService"], n["status"], (n.get("error") or {}).get("message", ""), n["text"][:40].replace("\n", " "))
    else:
        main(sys.argv[1], sys.argv[2:])
