#!/usr/bin/env python3
"""Bake the classic donut.c torus into an animated ASCII SVG (frame cycling via CSS)."""
import math

COLS, ROWS = 64, 24
FRAMES = 16
LUM = ".,-~:;=!*#$@"

def frame(A, B):
    z = [0.0] * (COLS * ROWS)
    out = [" "] * (COLS * ROWS)
    cA, sA, cB, sB = math.cos(A), math.sin(A), math.cos(B), math.sin(B)
    theta = 0.0
    while theta < 2 * math.pi:
        ct, st = math.cos(theta), math.sin(theta)
        phi = 0.0
        while phi < 2 * math.pi:
            cp, sp = math.cos(phi), math.sin(phi)
            h = ct + 2
            D = 1 / (sp * h * sA + st * cA + 5)
            t = sp * h * cA - st * sA
            x = int(COLS / 2 + (COLS * 0.47) * D * (cp * h * cB - t * sB))
            y = int(ROWS / 2 + (ROWS * 0.56) * D * (cp * h * sB + t * cB))
            o = x + COLS * y
            N = int(8 * ((st * sA - sp * ct * cA) * cB - sp * ct * sA - st * cA - cp * ct * sB))
            if 0 <= y < ROWS and 0 <= x < COLS and D > z[o]:
                z[o] = D
                out[o] = LUM[max(N, 0)]
            phi += 0.02
        theta += 0.07
    return ["".join(out[i * COLS:(i + 1) * COLS]) for i in range(ROWS)]

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

frames = [frame(i * 2 * math.pi / FRAMES * 1.0, i * 2 * math.pi / FRAMES * 0.5) for i in range(FRAMES)]

W, H = 420, 470
FW = 6.2   # char width
FH = 16    # line height
x0 = (W - COLS * FW) / 2
y0 = 70
dur = FRAMES * 0.14

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="\'JetBrains Mono\',Consolas,monospace">')
svg.append(f'''<style>
.f{{opacity:0}}
@keyframes cyc{{0%,{100/FRAMES:.3f}%{{opacity:1}}{100/FRAMES+0.01:.3f}%,100%{{opacity:0}}}}
.f{{animation:cyc {dur:.2f}s step-end infinite}}
@media (prefers-reduced-motion: reduce){{.f{{animation:none}}.f0{{opacity:1}}}}
</style>''')
svg.append(f'<rect width="{W}" height="{H}" rx="10" fill="#0a0e12"/>')
svg.append(f'<rect width="{W}" height="34" rx="10" fill="#11161c"/><rect y="20" width="{W}" height="14" fill="#11161c"/>')
svg.append('<circle cx="22" cy="17" r="6" fill="#ff5c57"/><circle cx="42" cy="17" r="6" fill="#ffd866"/><circle cx="62" cy="17" r="6" fill="#39ff7a"/>')
svg.append(f'<text x="{W/2}" y="22" text-anchor="middle" font-size="12" fill="#52677d">cc donut.c -o donut &amp;&amp; ./donut</text>')

for fi, fr in enumerate(frames):
    delay = fi * dur / FRAMES
    svg.append(f'<g class="f f{fi}" style="animation-delay:{delay:.2f}s" font-size="11" fill="#39ff7a">')
    for li, line in enumerate(fr):
        if line.strip():
            svg.append(f'<text x="{x0:.1f}" y="{y0 + li * FH:.1f}" xml:space="preserve" textLength="{COLS*FW:.0f}">{esc(line)}</text>')
    svg.append('</g>')

svg.append(f'<text x="{W/2}" y="{H-16}" text-anchor="middle" font-size="10" fill="#52677d">a1k0n, 2006 — rendered in pure SVG, zero JS</text>')
svg.append('</svg>')

open("assets/donut.svg", "w").write("\n".join(svg))
print(f"donut.svg: {len(chr(10).join(svg))} bytes, {FRAMES} frames")
