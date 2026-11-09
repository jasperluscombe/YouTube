# Whisker Tales: AI cat story Shorts

**Niche:** emotional AI-animated cat/kitten stories, 40-60s vertical Shorts.
AI animal stories, mostly cats, are the most-watched category of AI Shorts on YouTube.
Channels in that space have Shorts with 100M-700M views.

**Voice:** our own narrator, made by blending Kokoro-82M preset voices
(`af_heart` + `bf_emma` + `af_bella`). Kokoro is a free, Apache-2.0 TTS model that runs on CPU.
Change the blend weights in `channel.yaml` to reshape the voice.

## Make a video

```bash
pip install -r requirements.txt          # also: apt install espeak-ng ffmpeg
python src/voice.py --preview            # listen: out/voice_preview.wav
python src/voice.py stories/01_the_last_kitten.json
# put images in assets/images/01_the_last_kitten/scene_01.png ... (prompts are in the JSON)
python src/assemble.py stories/01_the_last_kitten.json
# -> out/01_the_last_kitten/01_the_last_kitten.mp4
```

`--silent` on `assemble.py` builds the video with no narration, to check the visuals.
Scenes with no image get a placeholder card that shows the image prompt.

## Story formula (what the top channels do)
1. Hook line: a small, wronged or lonely animal (first 3s)
2. Hardship / rejection
3. Turning point (storm, loss, stranger)
4. The animal acts selflessly
5. Emotional payoff + a one-line moral or question to drive comments

Keep it to 6-8 scenes and about 100-130 words. Keep one consistent character description in every image prompt.
