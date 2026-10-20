# The Price of Arrival · Story Video

An auto-playing, narrated version of the data story, made for the Week 11 **Data-Driven Story** submission (under 5 minutes).

| File | What it is |
|---|---|
| `The_Price_of_Arrival_story.mp4` | Final video (4:24): 1920×1080, 30 fps, English narration, burned-in English subtitles, music and sound effects |
| `The_Price_of_Arrival_story_instrumental.mp4` | Same video with music and sound effects but **no narration**, so the team can record their own voices over it |
| `story-video.html` | The same animation as a self-contained web page. Open it in a browser, then click **Play**. It plays by itself. `Space` pauses, `←`/`→` skips 5 s |
| `subtitles.srt` | English subtitles as a separate file (for Canvas or YouTube captions) |
| `narration-script.md` | Full narration with timestamps, scene by scene |
| `source/` | Everything needed to rebuild the video (see below) |

## Story structure

| Time | Scene | Act |
|---|---|---|
| 0:00 | Opening: arrivals board flips from *RECORD HIGH* to *WHO ARRIVES?* | 01 Problem |
| 0:16 | Meet Mei: boarding pass, four questions, the A$710 → A$1,600 visa fee | 01 Problem |
| 0:43 | Head vs heart: news, agent and friends; Daniel and the caption standard | 01 Problem |
| 1:09 | Five public datasets; the shared 2019 = 100 starting line | 02 Data & Method |
| 1:30 | Q1 Headline: enrolments vs commencements (Fig 1) | 03 Insights |
| 1:59 | Q2 Where: SA4 map and field heatmap (Fig 2–3) | 03 Insights |
| 2:32 | Q3 When: visa grant rate and policy stamps; sector intake (Fig 4–5) | 03 Insights |
| 3:07 | Q4 Cost: CPI and rents, an index not a price tag (Fig 6) | 03 Insights |
| 3:31 | Aha: four lenses lock into one decision | 03 Insights |
| 3:44 | Mei's plan, what she can decide now, what she still needs | 04 Plan |
| 4:07 | Arrival in Sydney; credits and sources | 04 Plan |

### Benchmark improvements built in

The video applies the "Next improvement" column of the team's Graduate Story Benchmark:

- **Linear sequence and conflict.** Mei's four questions come back at every act change as an arrivals-board header, so the central question stays visible.
- **Dramatic elements.** One short student voice ("Rent here is out of control.") is labelled on screen as an example from empathy research, not statistical evidence.
- **Settings.** Every chart names its geographic scope (NSW, Sydney SA4s or national). The video says aloud that SA4 data shows where students study, not where they live.
- **Visual anchors.** Every figure has a full standalone caption with its source.
- **Data foundation.** Two limits appear on screen: lining up in time does not prove cause, and CPI is an index, not a price tag.
- **Resolution.** The ending gives two lists: what Mei can decide now, and what she still needs.
- **Story timings.** Dense charts get the most screen time, and the whole video stays under the 5-minute limit.

## Rebuilding

Requirements: Python 3 with `numpy`, `soundfile` and `kokoro-onnx`; the Kokoro model files `kokoro.onnx` (int8) and `voices.bin` in `../tts/` relative to the scripts; Node with Playwright and Chromium; `ffmpeg`.

```bash
cd source
python3 tts_timeline.py   # narration clips + build/timeline.json + build/subtitles.srt
bash assemble.sh          # music + sound effects, HTML, frame-by-frame render, both MP4s in build/
```

Edit the wording in `narration.py`. The timeline recalculates itself from the real length of each spoken line.

## Credits

Illustrations come from the DataLens storyboard. Narration is AI-generated with Kokoro TTS (Apache-2.0). The music and sound effects were synthesised for this video. Fonts: Shantell Sans, Figtree, IBM Plex Mono and Caveat (SIL Open Font License).

© 2026 DataLens. All rights reserved.
