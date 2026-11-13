#!/usr/bin/env python3
"""Builds terminal.svg, the animated header of the profile README.

    python3 scripts/build.py <dir with buddy's base frames (*.webp)>

A README image cannot run scripts or load anything, so everything is inside the
one file: the text on a fixed character grid, CSS keyframes for the typing, and
buddy's frames tinted to the phosphor and embedded as PNG.
"""
import base64
import io
import sys
from html import escape
from pathlib import Path

from PIL import Image

BG, SURFACE, DIM, MUTED, FG, ACCENT = "#000b00", "#07200f", "#2b8a4c", "#3fa864", "#5df08a", "#9dff70"
W, PAD, CW, LH, FS, TOP = 840, 28, 9, 22, 15, 46
PROMPT = "dan@dlk25:~$"
SPRITE = 80

# (seconds when the prompt shows, command, output lines)
STEPS = [
    (0.0, "whoami", ["dan · developer at Bas Kommunikasjon · Oslo, Norway"]),
    (2.2, "cat about.md", [
        "I turn marketing problems into code: email templates, CRM journeys,",
        "the web pages around them, and the small tools that get a campaign",
        "out the door without anyone copying and pasting at midnight.",
        "Side projects in the evenings, with Claude Code as a pair.",
    ]),
    (5.6, "ls projects/", ["touchtype/   gamesounds/   dlk25.com/"]),
    (8.0, "buddy", []),
]
TYPE_AFTER, PER_CHAR, OUT_AFTER = 0.5, 0.07, 0.35


def tinted(path: Path) -> Image.Image:
    """Grey times the phosphor, alpha kept: the same sum as the site's filter."""
    im = Image.open(path).convert("RGBA")
    grey = im.convert("RGB").convert("L", (0.2923, 0.9834, 0.0993, -12.75))
    fg = [int(FG[i : i + 2], 16) for i in (1, 3, 5)]
    bands = [grey.point(lambda v, c=c: v * c // 255) for c in fg]
    return Image.merge("RGBA", (*bands, im.getchannel("A")))


def data_uri(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.quantize(colors=48, method=Image.Quantize.FASTOCTREE).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def row(y: int, col: int, text: str, cls: str, delay: float, typed: bool = False) -> str:
    xs = " ".join(str(PAD + (col + i) * CW) for i in range(len(text)))
    if typed:
        body = "".join(
            f'<tspan class="a" style="animation-delay:{delay + i * PER_CHAR:.2f}s">{escape(ch)}</tspan>'
            for i, ch in enumerate(text)
        )
        return f'<text class="{cls}" x="{xs}" y="{y}">{body}</text>'
    return f'<text class="{cls} a" style="animation-delay:{delay:.2f}s" x="{xs}" y="{y}">{escape(text)}</text>'


def main() -> None:
    frames = Path(sys.argv[1])
    strip = Image.new("RGBA", (8 * 160, 160))
    for i in range(8):
        strip.paste(tinted(frames / f"walk-{i}.webp").resize((160, 160), Image.NEAREST), (i * 160, 0))
    still = {n: data_uri(tinted(frames / f"{n}.webp")) for n in ("idle", "blink", "wave-0", "wave-1")}

    out, line, t = [], 0, 0.0
    for shown, cmd, lines in STEPS:
        y = TOP + line * LH
        out.append(row(y, 0, PROMPT, "p", shown))
        out.append(row(y, len(PROMPT) + 1, cmd, "c", shown + TYPE_AFTER, typed=True))
        t = shown + TYPE_AFTER + len(cmd) * PER_CHAR + OUT_AFTER
        for i, text in enumerate(lines):
            out.append(row(y + (i + 1) * LH, 0, text, "o", t))
        line += len(lines) + 2
    line -= 1  # buddy prints nothing; the next prompt follows directly

    y = TOP + line * LH
    out.append(row(y, 0, PROMPT, "p", t))
    cx = PAD + (len(PROMPT) + 1) * CW
    out.append(f'<rect class="cur" style="animation-delay:{t:.2f}s" x="{cx}" y="{y - 13}" width="{CW}" height="17"/>')

    floor = y + 14
    H = floor + SPRITE + 18
    walk0, walk = t + 0.3, 4.0
    arrive = walk0 + walk
    wave_end = arrive + 2.0
    stop = 400
    bubble = "hi. the rest is at dlk25.com"
    bx, by = SPRITE + 12, 30
    bw = len(bubble) * CW + 20

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">dan@dlk25: a terminal session</title>
<desc id="d">whoami: Dan, developer at Bas Kommunikasjon in Oslo, Norway. He turns marketing problems into code: email templates, CRM journeys, the web pages around them and small tools. Projects: touchtype, gamesounds and dlk25.com. Then buddy, a small pixel figure, walks in and waves.</desc>
<style>
text {{ font: {FS}px ui-monospace, "JetBrains Mono", "SF Mono", SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; white-space: pre; }}
.p {{ fill: {MUTED}; }} .c {{ fill: {ACCENT}; }} .o {{ fill: {FG}; }} .b {{ fill: {ACCENT}; }}
.a {{ opacity: 0; animation: on .01s linear both; }}
.cur {{ fill: {FG}; opacity: 0; animation: cur 1.1s step-end infinite; }}
.walker {{ animation: walk {walk}s linear {walk0:.2f}s both; }}
.strip {{ animation: cycle .8s steps(8) infinite; }}
.walking {{ opacity: 0; animation: hold {walk}s linear {walk0:.2f}s; }}
.w0 {{ opacity: 0; animation: flip .5s step-end {arrive:.2f}s 4; }}
.w1 {{ opacity: 0; animation: flop .5s step-end {arrive:.2f}s 4; }}
.idle {{ opacity: 0; animation: on .01s linear {wave_end:.2f}s both; }}
.blink {{ opacity: 0; animation: blink 4.3s step-end {wave_end + 1.5:.2f}s infinite; }}
.say {{ opacity: 0; animation: on .2s linear {arrive + 0.3:.2f}s both; }}
image {{ image-rendering: pixelated; }}
@keyframes on {{ to {{ opacity: 1; }} }}
@keyframes hold {{ from, to {{ opacity: 1; }} }}
@keyframes cur {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
@keyframes walk {{ from {{ transform: translateX(-{SPRITE + 10}px); }} to {{ transform: translateX({stop}px); }} }}
@keyframes cycle {{ to {{ transform: translateX(-{8 * SPRITE}px); }} }}
@keyframes flip {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
@keyframes flop {{ 0% {{ opacity: 0; }} 50% {{ opacity: 1; }} }}
@keyframes blink {{ 0% {{ opacity: 1; }} 4% {{ opacity: 0; }} }}
@media (prefers-reduced-motion: reduce) {{
  .a, .idle, .say {{ animation: none; opacity: 1; }}
  .cur {{ animation: none; opacity: 1; }}
  .walker {{ animation: none; transform: translateX({stop}px); }}
  .strip, .walking, .w0, .w1, .blink {{ animation: none; opacity: 0; }}
}}
</style>
<defs>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="2" fill="#000" opacity=".22"/></pattern>
<radialGradient id="tube" cx="50%" cy="45%" r="75%"><stop offset="0" stop-color="{SURFACE}"/><stop offset="1" stop-color="{BG}"/></radialGradient>
<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="2.2" result="b"/><feColorMatrix in="b" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 .55 0"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="screen"><rect width="{W}" height="{H}" rx="12"/></clipPath>
</defs>
<g clip-path="url(#screen)">
<rect width="{W}" height="{H}" fill="url(#tube)"/>
<g filter="url(#glow)">
{chr(10).join(out)}
</g>
<rect width="{W}" height="{H}" fill="url(#scan)"/>
<g filter="url(#glow)">
<g class="walker">
<svg x="0" y="{floor}" width="{SPRITE}" height="{SPRITE}" viewBox="0 0 {SPRITE} {SPRITE}" class="walking"><image class="strip" width="{8 * SPRITE}" height="{SPRITE}" href="{data_uri(strip)}"/></svg>
<image class="w0" y="{floor}" width="{SPRITE}" height="{SPRITE}" href="{still['wave-0']}"/>
<image class="w1" y="{floor}" width="{SPRITE}" height="{SPRITE}" href="{still['wave-1']}"/>
<image class="idle" y="{floor}" width="{SPRITE}" height="{SPRITE}" href="{still['idle']}"/>
<image class="blink" y="{floor}" width="{SPRITE}" height="{SPRITE}" href="{still['blink']}"/>
<g class="say" transform="translate({bx} {floor + by})">
<rect x=".5" y="-18.5" width="{bw}" height="28" rx="4" fill="{BG}" stroke="{DIM}"/>
<text class="b" x="{" ".join(str(10 + i * CW) for i in range(len(bubble)))}" y="0">{escape(bubble)}</text>
</g>
</g>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{SURFACE}"/>
</g>
</svg>
'''
    Path(__file__).resolve().parent.parent.joinpath("terminal.svg").write_text(svg)
    print(f"terminal.svg: {W}x{H}, {len(svg) // 1024} KB")


if __name__ == "__main__":
    main()
