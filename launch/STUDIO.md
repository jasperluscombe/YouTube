# Last Light Studio rulebook (adapted from the owner's studio brief, 2026-11-11)

Priorities, in order: storytelling, retention, professional 2D animation, natural narration, visual consistency,
sound and editing, platform optimisation, consistent publishing, learning from analytics.
Read with launch/FORMULA.md (story formula + titles), launch/CINEMA.md (camera, light, depth) and launch/REVIEW_*.md.

## Fixed decisions (owner)
- 3 posts a day = ONE story told in 3 parts (1/3 12:00 PM, 2/3 4:30 PM, 3/3 finale 8:30 PM ET). No teasers.
- Core genres: survival and horror. Any experiment stays inside them (psychological horror, mystery, a twist, a
  survival drama with betrayal...). Every story keeps the formula: ordinary person + companion, one place,
  one REAL survival rule, a two-word question.
- Fully automated: no approval needed; send the owner an FYI.

## Length
Each part (each video) 1:30-3:00, ideally 2:00-2:30 -> about 260-330 narrated words per part.
Never pad. Every scene must move the story.

## Story (5 stages across the 3 parts)
Hook (first 1-10 s, a question in the viewer's head; never "hey guys"/"today I'll tell you") -> setup -> escalation
-> climax -> ending with a final revelation that recontextualises the story. Natural spoken language, no plot
holes, consistent timeline, original (never a rewritten Reddit/viral script). Fiction is never presented as a
real event; the survival rule is real and accurate.

## Characters (src/anim/rig.py)
- Every human is a rig `Character` (face, eyes that blink and look, brows, mouth, hair, outfit, outlines).
  The old faceless `person()` is for distant crowd extras only.
- Before writing scenes, define every character in the story JSON under "characters": name, age, skin, hair,
  hair_style, top/top2, pants, shoes, face_shape, eyes, extras, personality. Never change them mid-story.
- Render a reference sheet (rig.sheet) per main character and check it before animating.
- Expressions must follow the narration (expr / expr_to / expr_k to blend). No frozen faces.
- Lip-sync any character who speaks: `talk = lipsync(scene_wav)`, pass talk(t). Eyes look at what matters.
- Animals keep engine.dog()/lighthouse.cat().

## Storyboard
18-25 scenes per part. Each scene in the story JSON has: narration, visual, characters, expressions, movement,
camera (wide/medium/close-up/extreme close-up/OTS/POV/insert), camera_move, background, lighting, transition.
Wide shots establish places; close-ups for emotion; vary shot size on every cut.

## Voice
Chatterbox narrator (MIT licence, inaudible watermark kept); drama 0.7-0.85, slower and quieter for suspense,
`~` for whispered lines. Automatic voice QC + retakes (make_story.py). Spell unusual names phonetically if needed.

## Captions
Correct spelling and punctuation, synced to phrase timings, bottom third away from platform UI and faces,
one consistent style.

## Sound
Room tone in every scene, motivated effects (doors, footsteps, notifications), silence before scares,
music under narration (synthesised in code: no copyright issues). Whoosh/braam/riser layer from assemble.py.

## Quality control (report honestly what was checked)
Claude cannot listen to audio or play video, so QC is by measurement: voice_qc (shouting/stretch), loudness
and clipping (volumedetect), duration, caption timing, contact sheets of every scene before rendering, and sampled
frames from every finished video. Never claim a check that wasn't done. Fix and re-render before scheduling.

## Publishing & analytics
Buffer -> YouTube, TikTok, Instagram (launch/buffer.json). One day ahead (free plan: 10 queued posts).
Titles: launch/FORMULA.md pattern. Sundays: weekly full movie (src/compile_movie.py) + one trailer Short.
Analytics available: Buffer per-post views, avg watch time, reactions, comments. Drop-off curves need YouTube
Analytics access (not connected). Never fabricate numbers. Log learnings in launch/REVIEW_*.md.
