"""Generate narration clips with Kokoro TTS, then lay them out into a timeline.

Outputs (in build/):
  vo/<seg>.wav      trimmed narration per segment (24 kHz mono)
  timeline.json     scene + segment timings and subtitles
  subtitles.srt     English subtitles
"""
import hashlib, json, os, sys
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from narration import SCENES, CREDITS_SECONDS, GAP, VOICE, SPEED

TTS_DIR = os.path.join(HERE, "..", "tts")
BUILD = os.path.join(HERE, "build")
CACHE = os.path.join(BUILD, "tts_cache")
VO = os.path.join(BUILD, "vo")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(VO, exist_ok=True)
SR = 24000

_k = None
def kokoro():
    global _k
    if _k is None:
        from kokoro_onnx import Kokoro
        _k = Kokoro(os.path.join(TTS_DIR, "kokoro.onnx"), os.path.join(TTS_DIR, "voices.bin"))
    return _k

def tts(text):
    key = hashlib.md5(f"{VOICE}|{SPEED}|{text}".encode()).hexdigest()
    path = os.path.join(CACHE, key + ".wav")
    if not os.path.exists(path):
        audio, sr = kokoro().create(text, voice=VOICE, speed=SPEED, lang="en-us")
        assert sr == SR
        sf.write(path, audio, SR)
    a, _ = sf.read(path, dtype="float32")
    return a

def trim(a, thr=0.012, pad=0.04):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] - int(pad * SR))
    e = min(len(a), idx[-1] + int(pad * SR))
    return a[s:e]

def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def main():
    t = 0.0
    scenes, segs, order = {}, {}, []
    for sid, act, lead, tail, items in SCENES:
        start = t
        t += lead
        for i, (gid, say, sub) in enumerate(items):
            a = trim(tts(say))
            sf.write(os.path.join(VO, gid + ".wav"), a, SR)
            d = len(a) / SR
            segs[gid] = {"s": round(t, 3), "e": round(t + d, 3), "sub": sub, "scene": sid}
            order.append(gid)
            t += d
            if i < len(items) - 1:
                t += GAP
        t += tail
        scenes[sid] = {"s": round(start, 3), "e": round(t, 3), "act": act}
        print(f"{sid:6s} {start:7.2f} -> {t:7.2f}  ({t - start:5.2f}s)")
    scenes["credits"] = {"s": round(t, 3), "e": round(t + CREDITS_SECONDS, 3), "act": 4}
    t += CREDITS_SECONDS
    total = round(t, 3)
    print(f"TOTAL {total:.2f}s = {int(total // 60)}:{total % 60:05.2f}")
    tl = {"total": total, "scenes": scenes, "segs": segs, "order": order}
    with open(os.path.join(BUILD, "timeline.json"), "w") as f:
        json.dump(tl, f, indent=1)
    with open(os.path.join(BUILD, "subtitles.srt"), "w") as f:
        for n, gid in enumerate(order, 1):
            g = segs[gid]
            nxt = segs[order[n]]["s"] if n < len(order) else g["e"] + 0.4
            end = min(g["e"] + 0.3, nxt - 0.02)
            f.write(f"{n}\n{srt_time(g['s'])} --> {srt_time(end)}\n{g['sub']}\n\n")

if __name__ == "__main__":
    main()
