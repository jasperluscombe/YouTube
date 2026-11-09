"""Channel branding + episode thumbnails, drawn with the same engine as the videos.

    python src/anim/brand.py      # -> launch/avatar.png, launch/banner.png, launch/thumb_ep1_*.png
"""
import math, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import engine as E
from engine import *  # noqa
import lights as L

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "launch"
OUT.mkdir(exist_ok=True)
CHANNEL = "LAST LIGHT"
SUB = "STORIES"


def canvas(w, h):
    E.W, E.H = w, h          # engine helpers read the module size
    E._VIG = None
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(s)
    c.set_source_rgb(0, 0, 0); c.paint()
    return s, c


def avatar():
    s, c = canvas(800, 800)
    vgrad(c, 0, 800, [(0, hexc("#05070f")), (1, hexc("#1b2140"))], w=800)
    glow(c, 400, 330, 420, (1, 0.75, 0.35), 0.45)
    # one lit window in a dark tower
    rgb(c, hexc("#0b0e1a")); c.rectangle(250, 120, 300, 700); c.fill()
    rgb(c, (1, 0.86, 0.55)); c.rectangle(345, 220, 110, 140); c.fill()
    rgb(c, hexc("#2a2420")); c.set_line_width(8); c.rectangle(345, 220, 110, 140); c.stroke()
    # you + Biscuit on the ledge, from behind
    rgb(c, hexc("#20232c")); c.rectangle(0, 640, 800, 160); c.fill()
    L.sit_back(c, 330, 640, 330)
    dog(c, 480, 640, 100, "back")
    vignette(c, 0.5)
    # circle crop is done by YouTube; keep content centred
    s.write_to_png(str(OUT / "avatar.png"))


def banner():
    W_, H_ = 2560, 1440
    s, c = canvas(W_, H_)
    vgrad(c, 0, H_, [(0, hexc("#03050c")), (0.6, hexc("#0e1428")), (1, hexc("#1a2036"))], w=W_)
    for k in range(260):
        x = (k * 977) % W_; y = (k * 613) % 900
        rgb(c, (1, 1, 1), 0.2 + 0.5 * ((k * 37) % 10) / 10); c.arc(x, y, 1.5 + (k % 3), 0, 6.283); c.fill()
    city = skyline(77, 0, 1440, 200, 700, 70, 170)
    import random
    r = random.Random(5)
    for (x, w, h, wins, cut) in [(x * 2.4, w * 2.4, h, wins, cut) for (x, w, h, wins, cut) in city]:
        rgb(c, hexc("#080a12")); c.rectangle(x, 1440 - h, w, h); c.fill()
        for (u, v) in wins:
            if r.random() < 0.06:
                rgb(c, (1, 0.82, 0.45), 0.9); c.rectangle(x + 8 + u * (w - 24), 1440 - h + 12 + v * (h - 30), 10, 13); c.fill()
    glow(c, W_ / 2, 720, 900, (1, 0.7, 0.35), 0.18)
    # safe area for all devices: centre 1546 x 423
    text(c, CHANNEL, W_ / 2, 655, 200, (1, 0.85, 0.5), outline=14)
    text(c, "ANIMATED SURVIVAL MYSTERIES  •  NEW EPISODES DAILY", W_ / 2, 805, 58, (0.9, 0.92, 1), outline=6)
    vignette(c, 0.5)
    s.write_to_png(str(OUT / "banner.png"))


def thumb(w, h, name):
    s, c = canvas(w, h)
    sx = w / 1080
    c.save(); c.scale(sx, sx) if h > w else c.scale(w / 1080, w / 1080)
    if h > w:
        L.window_scene(c, 0, lit=1, sign_up=1, sign_lines=["DON'T", "COME HERE"], zoom=1.25)
        rgb(c, (0, 0, 0), 0.0)
        dog(c, 830, 1880, 300, "sit", face=-1, head_up=1)
        L.sit_back(c, 230, 1920, 520)
        text(c, "9:14 PM", 540, 260, 230, (1, 0.35, 0.3), outline=18)
        text(c, "EVERY LIGHT TURNS ON", 540, 450, 78, (1, 1, 1), outline=10)
    c.restore()
    if w > h:   # 16:9 version
        c.save(); c.translate(w * 0.62, 0); c.scale(h / 1920 * 1.35, h / 1920 * 1.35); c.translate(-540, -420)
        L.window_scene(c, 0, lit=1, sign_up=1, sign_lines=["DON'T", "COME HERE"], zoom=1.0)
        c.restore()
        g = cairo.LinearGradient(0, 0, w * 0.6, 0)
        g.add_color_stop_rgba(0, 0.02, 0.03, 0.06, 1); g.add_color_stop_rgba(1, 0.02, 0.03, 0.06, 0)
        c.set_source(g); c.rectangle(0, 0, w, h); c.fill()
        text(c, "9:14 PM", 330, 230, 170, (1, 0.35, 0.3), anchor="center", outline=14)
        text(c, "EVERY LIGHT", 330, 400, 92, (1, 1, 1), outline=10)
        text(c, "TURNS ON", 330, 500, 92, (1, 0.85, 0.5), outline=10)
        dog(c, 1150, 715, 140, "sit", face=-1, head_up=1)
    vignette(c, 0.45)
    s.write_to_png(str(OUT / name))


if __name__ == "__main__":
    avatar(); banner()
    thumb(1080, 1920, "thumb_ep1_vertical.png")
    thumb(1280, 720, "thumb_ep1_16x9.png")
    print("ok")
