# The Last Light formula (every story)

1. **One ordinary person: Kai** (see STUDIO.md). No powers, no special training. A nurse, a delivery driver, a kid's dad.
   Give them one companion or relationship that carries the feeling (a dog, a cat, a stranger, a child).
2. **Trapped in one place.** One location for the whole story: a lighthouse rock, a stalled lift, a snowed-in
   diner, a sinking car, a mountain hut. The place is the antagonist; keep the geography simple and clear.
3. **One real survival rule.** A true, checkable piece of survival knowledge that the plot turns on:
   introduced in Part 1 or 2, tested in Part 2, and it saves them in Part 3. Say it plainly on screen as a
   "RULE" card. It must be accurate (stick to well-established guidance, no made-up numbers).
   Examples: the rule of threes (3 minutes without air, 3 hours without shelter in harsh weather, 3 days
   without water, 3 weeks without food); cold-water shock (the first minute is about controlling your
   breathing; don't thrash); STOP when lost (Stop, Think, Observe, Plan); stay with the vehicle in a
   blizzard; signal in threes (three fires, whistles or flashes = distress); don't eat snow for water
   unless you melt it first.
4. **A two-word question.** The hook and the comment prompt are a two-word question
   ("Would you?", "Who's there?", "Stay or go?", "Trust her?"). Part 1 opens on it, each end card asks it,
   and viewers answer it in the comments.

## Across the 3 parts
- **1/3:** person + place + the trap snaps shut. The two-word question. Cliffhanger.
- **2/3:** things get worse; the survival rule is introduced (RULE card). Cliffhanger.
- **3/3:** the rule saves them. Emotional payoff. Final two-word question + "New story tomorrow".

## Tools for atmosphere
- **Whispering:** start a narration phrase with `~` to whisper it (e.g. `~Don't turn around.`). Add
  `"whispers": ["come closer", {"text": "we see you", "at": 3.5}]` to a scene for echoing ghost whispers
  layered under the narration (`at` = seconds into the scene; omitted = spread evenly). Use for horror/creepy beats.

## Titles (from the yt-viral outlier study, 2026-11-11)
The niche's biggest outliers (21-149x their channel median) all name ONE specific shelter, usually with a threat
and a time span: "Zombie Outbreak: 100 Days Trapped On A Zombie Cruise Ship", "Surviving a Blizzard Inside a
Giant Hollow-Tree Cottage", "Trapped In a Farm Day 1 To Day 100". So every part title is:
`<Threat>: <time> Trapped In <specific place> <emotional detail> (N/3) #shorts`  (max 100 chars)
e.g. "Zombie Outbreak: 7 Days Trapped In A Pharmacy With My Little Sister (1/3) #shorts".
The two-word question stays in the video, the end card and the pinned/comment prompt, not the title.

## Weekly full movie (Sundays)
Every outlier in the niche is long-form (19-73 min). Each Sunday, stitch the week's stories into one
16:9 long video with `python src/compile_movie.py out/movies/<week>.mp4 "<sid1,sid2,sid3>" ...`,
titled like "7 Survival Stories: Trapped In A Pharmacy, A Lighthouse, A Whispering Farmhouse... (Full Movie)",
with the chapter list from <out>.chapters.txt in the description.
