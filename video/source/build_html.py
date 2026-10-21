"""Assemble the self-contained auto-play HTML from the template.

usage: python3 build_html.py OUT.html [AUDIO.m4a]
"""
import base64, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
audio = sys.argv[2] if len(sys.argv) > 2 else None

tpl = open(os.path.join(HERE, "story.template.html"), encoding="utf8").read()
fonts = open(os.path.join(HERE, "fonts_embedded.css"), encoding="utf8").read()
tl = json.load(open(os.path.join(HERE, "build", "timeline.json")))

imgs = {}
adir = os.path.join(HERE, "assets")
for f in sorted(os.listdir(adir)):
    k, ext = os.path.splitext(f)
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    imgs[k] = f"data:{mime};base64," + base64.b64encode(open(os.path.join(adir, f), "rb").read()).decode()

aud = ""
if audio:
    aud = "data:audio/mp4;base64," + base64.b64encode(open(audio, "rb").read()).decode()

html = (tpl.replace("/*FONTS*/", fonts)
           .replace("__IMG__", json.dumps(imgs))
           .replace("__TL__", json.dumps(tl))
           .replace("__AUDIO__", aud))
open(out, "w", encoding="utf8").write(html)
print(out, f"{len(html)/1e6:.2f} MB", f"total {tl['total']:.2f}s")
