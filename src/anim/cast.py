"""Permanent cast of Last Light Stories. Import these instead of redefining them per story.

KAI - the channel's recurring hero.
  Regular white American guy who always wears his lucky Hawaiian shirt; works at a surf shop; sunny, kind, a little clumsy, never gives up.
  Catchphrase: "Could be worse." (it always gets worse)
  RUNNING GAG: every story wrecks him (torn shorts, a lost flip-flop, soot, mud, singed hair)
  but his red aloha shirt ALWAYS comes out spotless. Never draw damage on the shirt.
  The narrator can point it out at the end ("...and somehow, the shirt survived.").
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from rig import Character

KAI = Character(
    name="Kai", age="adult", skin="#f2c9a8", hair="#6b4a2e", hair_style="short",
    top="#c8302c", pattern="hibiscus", pattern_col="#f6eee0",
    pants="#6f8a6a", shorts=True, footwear="flipflops", shoes="#2b6cb0",
    face_shape="oval", eyes="round", brows=0.85, stubble=False, shades_on_head=True, seed=7.0,
)

if __name__ == "__main__":
    from rig import sheet
    out = sys.argv[1] if len(sys.argv) > 1 else "kai_sheet.png"
    sheet(KAI, out)
    print(out)
