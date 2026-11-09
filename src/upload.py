"""Upload a finished Short to YouTube and schedule it (YouTube Data API v3).

    python src/upload.py out/21_lights_part2/21_lights_part2.mp4 launch/EP_lights_upload.json part2
    python src/upload.py --check            # verify the account connection only

Credentials come from environment variables the channel owner saves in the cloud
environment settings (never in the repo or chat): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
See launch/CONNECT_YOUTUBE.md.

Upload kit JSON: {"<key>": {"title", "description", "tags", "publish_at" (RFC3339), "comment"}}
"""
import json, os, sys, urllib.parse, urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"


def access_token():
    missing = [k for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN") if not os.environ.get(k)]
    if missing:
        sys.exit(f"missing environment variables: {', '.join(missing)} (see launch/CONNECT_YOUTUBE.md)")
    body = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                   "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=body), timeout=60) as r:
        return json.loads(r.read())["access_token"]


def call(method, url, token, body=None, headers=None, raw=None):
    h = {"Authorization": f"Bearer {token}", **(headers or {})}
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if body is not None:
        h["Content-Type"] = "application/json; charset=UTF-8"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.headers, (json.loads(r.read() or b"{}"))


def channel(token):
    _, d = call("GET", f"{API}/channels?part=snippet,statistics&mine=true", token)
    return d["items"][0] if d.get("items") else None


def upload(path, meta, token):
    status = {"selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}
    if meta.get("publish_at"):
        status.update(privacyStatus="private", publishAt=meta["publish_at"])
    else:
        status["privacyStatus"] = meta.get("privacy", "public")
    body = {"snippet": {"title": meta["title"][:100], "description": meta["description"],
                        "tags": meta.get("tags", []), "categoryId": "24"}, "status": status}
    size = os.path.getsize(path)
    hdrs, _ = call("POST", UPLOAD, token, body, {"X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
    with open(path, "rb") as f:
        _, video = call("PUT", hdrs["Location"], token, raw=f.read(), headers={"Content-Type": "video/mp4"})
    vid = video["id"]
    print(f"uploaded {path} -> https://youtube.com/shorts/{vid}  status={video['status']}")
    if meta.get("comment"):
        try:
            call("POST", f"{API}/commentThreads?part=snippet", token,
                 {"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": meta["comment"]}}}})
        except Exception as e:  # comments open only once the video is public; retried by the daily run
            print("  comment not posted yet:", e)
    return vid


if __name__ == "__main__":
    tok = access_token()
    if sys.argv[1] == "--check":
        ch = channel(tok)
        print("connected:", ch["snippet"]["title"] if ch else "no channel on this account")
        sys.exit()
    kit = json.load(open(sys.argv[2]))
    upload(sys.argv[1], kit[sys.argv[3]], tok)
