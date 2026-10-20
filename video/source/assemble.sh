#!/usr/bin/env bash
# Full build after tts_timeline.py: audio mix -> html -> frames -> mp4 (+ instrumental)
set -euo pipefail
cd "$(dirname "$0")"
B=build
python3 mix_audio.py
ffmpeg -y -loglevel error -i $B/mix.wav -c:a aac -b:a 192k $B/mix.m4a
ffmpeg -y -loglevel error -i $B/music_sfx.wav -c:a aac -b:a 192k $B/music_sfx.m4a
python3 build_html.py $B/render.html
python3 build_html.py $B/story-video.html $B/mix.m4a
rm -rf $B/frames
node render.js $B/render.html $B/frames 30 4
ffmpeg -y -loglevel error -f concat -safe 0 -i $B/frames/parts.txt -c copy $B/video_only.mp4
for v in story:mix instrumental:music_sfx; do
  name=${v%%:*}; a=${v##*:}
  ffmpeg -y -loglevel error -i $B/video_only.mp4 -i $B/$a.m4a -map 0:v -map 1:a -c:v copy -c:a copy -shortest -movflags +faststart $B/$name.mp4
done
ffprobe -v error -show_entries format=duration,size -of default=nw=1 $B/story.mp4
echo ASSEMBLE_DONE
