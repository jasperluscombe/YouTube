# Year Zero: POV apocalypse, survival & future stories

**Niche:** AI-generated first-person Shorts that put the viewer *inside* another world:
waking up as the last human, surviving day 40 in a bunker, a normal day in the year 3000.
Everything is written in second person ("you") so people imagine living it.

**Series** (rotate them):
| Series | Example |
|---|---|
| Last Human | POV: You wake up as the last human (2087) |
| Day __ of ____ | Day 40 underground: then the radio came back on |
| POV: Year ____ | POV: a normal day in the year 3000 |
| What If ____ | What if the sun went out? Hour by hour |

**Voice:** our own deep cinematic narrator, made by blending Kokoro-82M voices
(`am_onyx` + `am_michael` + `am_fenrir`, at 0.9× speed). Kokoro is free (Apache-2.0) and runs on CPU.
Change the blend in `channel.yaml`.

## Make a video
```bash
pip install -r requirements.txt          # also: apt install espeak-ng ffmpeg
python src/voice.py --preview            # listen: out/voice_preview.wav
python src/voice.py stories/01_last_human_2087.json
# put images/clips in assets/images/01_last_human_2087/scene_01.png ... (prompts are in the JSON)
python src/assemble.py stories/01_last_human_2087.json
```
`--silent` builds the video with no narration, to check the visuals.
Scenes with no image get a placeholder card that shows the image prompt.

## Script formula
1. **Hook (first 3s):** drop them into the world. "You wake up in a glass pod. The year is 2087."
2. **Escalate:** each scene shows one strange, specific detail of daily life or survival.
3. **Twist:** something that changes the picture (the robot waited 40 years; the sky is green).
4. **End on a question:** "Do you go north or stay?" Asking for a choice drives comments.

7 scenes, about 100–120 words, under 50s. Every image prompt shares one POV style line, so the shots match.

## Upload order (batch 1 + 2, rotates series, one per day)
| # | Story | Series |
|---|---|---|
| 1 | 01_last_human_2087 | Last Human |
| 2 | 04_what_if_sun_went_out | What If |
| 3 | 02_day_40_bunker | Day __ |
| 4 | 03_pov_year_3000 | POV Year |
| 5 | 06_last_human_offline | Last Human |
| 6 | 18_what_if_earth_stopped | What If |
| 7 | 10_day_3_internet_gone | Day __ |
| 8 | 16_pov_wake_up_2075 | POV Year |
| 9 | 08_last_human_ai_city | Last Human |
| 10 | 19_what_if_oceans_vanished | What If |
| 11 | 12_day_12_everyone_asleep | Day __ |
| 12 | 15_pov_year_10000 | POV Year |
| 13 | 05_last_human_in_orbit | Last Human |
| 14 | 17_what_if_moon_vanished | What If |
| 15 | 09_day_365_flood | Day __ |
| 16 | 13_pov_2200_mars_teen | POV Year |
| 17 | 07_woke_up_too_early | Last Human |
| 18 | 11_day_100_ice_age | Day __ |
| 19 | 14_pov_2500_earth_reserve | POV Year |

After ~10 uploads, check which series gets the most views per video and make more of that one.
