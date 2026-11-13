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

## Kai - the channel's recurring hero (src/anim/cast.py KAI)
- Every story stars Kai: a regular, basic white American guy (short brown side-swept hair, fair skin) in his lucky red Hawaiian shirt; works at a surf shop, sunny, kind, a little clumsy, never gives up.
  Catchphrase "Could be worse." - and then it gets worse. He is the "ordinary person" of the formula;
  each story still gives him a new companion and a new trap (one place) and a real survival rule.
- RUNNING GAG: every story wrecks him (torn shorts via torn=, dirt=, soot=, lost_shoe=, singed hair) but his
  red aloha shirt ALWAYS comes out spotless. Never damage the shirt. Pay it off near the end of Part 3 with a
  beat like "...and somehow, the shirt survived." plus a quick insert of the pristine shirt.
- Tone: genuinely tense survival/horror with warm humour from Kai's optimism. Never mock his culture: he's
  a capable, likeable guy; humour comes from his luck and the situations.
- Narration switches from "you" to third person about Kai ("Kai had worked at the surf shop for six years...").
- The weekly full movie becomes "Kai's Worst Week" (each story a chapter).

## Length and pace (changed 2026-11-13 after launch/RESEARCH_2026-11-13.md)
Each part is **55-80 seconds: 150-190 narrated words, 16-20 scenes** (a new picture about every 3 s).
Every story file carries `"pace": {"tempo": 1.12, "pause": 0.4, "cfg": 0.5}` and `"title_card": false`; drama 0.6-0.7.
Never pad. No backstory, no mood-setting lines. If a line is not a decision, a consequence or a reveal, cut it.

## Story (what the breakout videos do)
- **Line 1 is a decision the viewer has a stake in**: "If <disaster> happens while you're at <specific place>,
  don't <the obvious thing>. <Do the surprising thing>." Never a vague mystery question, never a greeting.
- Then a chain: decision -> consequence -> new problem, every 1-2 lines. At least **4 smart, true survival moves per
  part** (the "I should have thought of that" feeling), with **specific numbers** (40 infected, 30 minutes, 28 floors).
- Kai is the one living it (third person), but the lesson is always usable by the viewer.
- **The last story line of Parts 1 and 2 is the cliffhanger.** The end card is one short line ("Paddle out? Part two is next.").
  Part 3 ends on a reveal, then the shirt gag, then one line asking for a comment + follow.
- Natural spoken language, no plot holes, original. Fiction is never presented as real; survival facts are real and accurate.

## Characters (src/anim/rig.py)
- Every human is a rig `Character` drawn in the **flat style** (the default, chosen by the user): no black outlines, flat colours, simple dark dot eyes that blink and look around, small brows and a simple mouth for expressions, no nose. `style="outline"` exists but is not used.
  The old faceless `person()` is for distant crowd extras only.
- Before writing scenes, define every character in the story JSON under "characters": name, age, skin, hair,
  hair_style, top/top2, pants, shoes, face_shape, eyes, extras, personality. Never change them mid-story.
- Render a reference sheet (rig.sheet) per main character and check it before animating.
- Expressions must follow the narration (expr / expr_to / expr_k to blend). No frozen faces.
- Lip-sync any character who speaks: `talk = lipsync(scene_wav)`, pass talk(t). Eyes look at what matters.
- Animals keep engine.dog()/lighthouse.cat().

## Storyboard
16-20 scenes per part. Each scene in the story JSON has: narration, visual, characters, expressions, movement,
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
