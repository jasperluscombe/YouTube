"""Per-post Buffer metrics for sent posts: python src/metrics.py  (prints a table + per-story totals)."""
import collections, json, pathlib, urllib.request

ORG = json.loads((pathlib.Path(__file__).resolve().parent.parent / "launch" / "buffer.json").read_text())["organization"]


def q(query, v):
    req = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": query, "variables": v}).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer proxy-injected"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def rows():
    r = q('query($o:OrganizationId!){ posts(first:100, input:{organizationId:$o, filter:{status:[sent]}}){ edges{ node{ channelService dueAt text metrics{ name value } } } } }', {"o": ORG})
    out = []
    for e in r["data"]["posts"]["edges"]:
        n = e["node"]; m = {x["name"]: x["value"] for x in (n["metrics"] or [])}
        out.append(dict(date=n["dueAt"][:16], platform=n["channelService"], views=m.get("Video Views", m.get("Views", 0)) or 0,
                        watch=m.get("Avg. Watch Time (sec)", "-"), comments=m.get("Comments", 0) or 0, reactions=m.get("Reactions", m.get("Likes", 0)) or 0,
                        title=n["text"].split("\n")[0][:60], all=m))
    return sorted(out, key=lambda x: (x["date"], x["platform"]))


if __name__ == "__main__":
    rs = rows()
    for x in rs:
        print(x["date"], x["platform"][:9].ljust(9), str(x["views"]).rjust(6), str(x["watch"]).rjust(6), str(x["comments"]).rjust(3), str(x["reactions"]).rjust(4), "|", x["title"])
    tot = collections.Counter()
    for x in rs:
        tot[(x["date"][:10], x["platform"])] += float(x["views"] or 0)
    print("\nper day/platform:"); [print(k, int(v)) for k, v in sorted(tot.items())]
