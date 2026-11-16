"""Contact sheet of a story part: python src/anim/contact.py <module> <part> <out.png> [frac]"""
import importlib, math, pathlib, sys
import cairo
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from engine import W, H

mod = importlib.import_module(sys.argv[1]); part = int(sys.argv[2]); out = sys.argv[3]
frac = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
sid, scenes, _, _ = mod.PARTS[part]
tm = {1: mod.T1, 2: mod.T2, 3: mod.T3}[part]
cols, sc = 5, 0.2
rows = math.ceil(len(scenes) / cols)
sheet = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(W * sc * cols), int(H * sc * rows))
sc_ctx = cairo.Context(sheet)
for k, fn in enumerate(scenes):
    d = tm.dur(k + 1)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    c.set_source_rgb(0, 0, 0); c.paint()
    fn(c, d * frac, d)
    c.set_source_rgb(1, 1, 0); c.select_font_face("Sans"); c.set_font_size(80); c.move_to(20, 90); c.show_text(str(k + 1))
    sc_ctx.save(); sc_ctx.translate((k % cols) * W * sc, (k // cols) * H * sc); sc_ctx.scale(sc, sc)
    sc_ctx.set_source_surface(s, 0, 0); sc_ctx.paint(); sc_ctx.restore()
sheet.write_to_png(out)
print(out)
