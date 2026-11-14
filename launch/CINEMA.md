# Cinematic standard (every scene of every story)

The look comes from light, depth, camera, editing and sound. Use src/anim/cinema.py in every scene.

## Every scene
1. **Camera:** wrap the scene in `camera(ctx, t, d, ...)`. Always a little `handheld` (0.3-0.7).
   `push` (0.05-0.12) on reveals and emotional beats; `shake` on impacts/bangs; never a dead-still frame.
2. **Depth in layers:** far background, then `depth_haze`, then midground, then characters, then foreground
   atmosphere (`fog`, `dust`, `god_rays`). Far things are hazier and darker.
3. **Motivated light:** each scene has ONE key light (window, lamp, screen, fire, moon). Show its source,
   cast `god_rays`/`glow` from it, `backlight` characters against it, and leave the rest dark.
4. **Grounded characters:** `soft_shadow` under every character/object that touches the floor.
5. **Grade:** set `"grade"` on the story JSON (`night`, `horror`, `warm`, `storm`; per-scene override allowed).
   assemble.py adds bloom, grade, lens fringe, vignette and grain automatically.

## Shots and editing
- Vary shot size on every cut: wide (max one per part) -> medium -> close-up (character 900px+ tall,
  partial frame) -> insert (a hand, a door handle, a bottle, a screen) -> POV.
- Scenes 3-6 seconds; something visibly changes every 2-3 seconds (camera move, new text, light change).
- First frame of Part 1 = motion + danger + the two-word question on screen. Title card follows automatically.
- Big text cards (`shot_card`) for key words: numbers, rules, the question.

## Sound
- assemble.py adds whooshes on every cut, a braam on the title, a riser and impact into the end card.
- Scene sfx: always a room tone/ambience bed; a hard silence for 0.5-1s right before a scare or reveal.
- Horror: whispers (`~` lines and scene `"whispers"`), breathing, creaks; music minimal.

## Build
`python src/make_story.py <anim_module> <sid1> <sid2> <sid3>` runs voice, automatic voice QC and retakes,
animation, assembly, and writes out/<sid>/report.json. Fix anything report.json flags before scheduling.
