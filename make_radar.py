#!/usr/bin/env python3
"""Radar sweep: rotating beam detects skills as blips, pinging exactly when the sweep passes.
All animations share ONE CSS timeline (no SMIL) so sweep and pings can't drift apart."""
import math

W, H = 420, 470
CX, CY, R = 210, 252, 168
PERIOD = 6.0

GREEN, YELLOW, DIM, GRID, BG, PANEL, TEXT = "#39ff7a", "#ffd866", "#52677d", "#1b232d", "#0a0e12", "#11161c", "#9fb3c8"

BLIPS = [
    ("Python",      305, 0.30, GREEN, -10),
    ("FastAPI",      25, 0.52, GREEN, -10),
    ("PostgreSQL",   80, 0.68, GREEN,  16),
    ("Docker",      140, 0.50, GREEN, -10),
    ("Vue 3",       185, 0.72, GREEN, -10),
    ("Linux",       245, 0.60, GREEN, -10),
    ("Quant/Stats", 340, 0.84, GREEN,  16),
    ("Java",        115, 0.90, GREEN, -10),
    ("AWS",        280, 0.20, YELLOW, -10),
]

def pos(angle_deg, rfrac):
    a = math.radians(angle_deg)
    return CX + R * rfrac * math.cos(a), CY + R * rfrac * math.sin(a)

s = []
A = s.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="\'JetBrains Mono\',Consolas,monospace">')
A(f'''<defs>
<clipPath id="dish"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>
</defs>
<style>
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.sweep{{transform-origin:{CX}px {CY}px;animation:spin {PERIOD}s linear infinite}}
@keyframes ping{{0%{{transform:scale(1);opacity:.95}}14%{{transform:scale(4);opacity:0}}15%,100%{{transform:scale(1);opacity:0}}}}
.ping{{transform-box:fill-box;transform-origin:center;animation:ping {PERIOD}s linear infinite}}
@keyframes glow{{0%,3%{{opacity:1}}14%{{opacity:.45}}100%{{opacity:.45}}}}
.bl{{animation:glow {PERIOD}s linear infinite}}
.lbl{{font-size:10.5px}}
@media (prefers-reduced-motion: reduce){{ .sweep,.ping{{animation:none}} .ping{{opacity:0}} .bl{{animation:none;opacity:.8}} }}
</style>''')

A(f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>')
A(f'<rect width="{W}" height="34" rx="10" fill="{PANEL}"/><rect y="20" width="{W}" height="14" fill="{PANEL}"/>')
A(f'<circle cx="22" cy="17" r="6" fill="#ff5c57"/><circle cx="42" cy="17" r="6" fill="#ffd866"/><circle cx="62" cy="17" r="6" fill="{GREEN}"/>')
A(f'<text x="{W/2}" y="22" text-anchor="middle" font-size="12" fill="{DIM}">./skillscan --sweep --range max</text>')

for f in (0.25, 0.5, 0.75, 1.0):
    A(f'<circle cx="{CX}" cy="{CY}" r="{R*f:.0f}" fill="none" stroke="{GRID}" stroke-width="1"/>')
A(f'<line x1="{CX-R}" y1="{CY}" x2="{CX+R}" y2="{CY}" stroke="{GRID}"/>')
A(f'<line x1="{CX}" y1="{CY-R}" x2="{CX}" y2="{CY+R}" stroke="{GRID}"/>')
for d in range(0, 360, 30):
    x1, y1 = pos(d, 0.96); x2, y2 = pos(d, 1.0)
    A(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{DIM}" stroke-width="1"/>')

wx, wy = pos(-40, 1.0)
A(f'<g clip-path="url(#dish)">')
A(f'<g class="sweep">')
A(f'<path d="M{CX},{CY} L{CX+R},{CY} A{R},{R} 0 0,0 {wx:.1f},{wy:.1f} Z" fill="{GREEN}" opacity="0.13"/>')
A(f'<line x1="{CX}" y1="{CY}" x2="{CX+R}" y2="{CY}" stroke="{GREEN}" stroke-width="1.8"/>')
A('</g></g>')

for label, ang, rf, col, dy in BLIPS:
    x, y = pos(ang, rf)
    delay = (ang % 360) / 360.0 * PERIOD
    A(f'<circle class="ping" cx="{x:.1f}" cy="{y:.1f}" r="4" fill="none" stroke="{col}" stroke-width="1.4" style="animation-delay:{delay:.3f}s"/>')
    A(f'<circle class="bl" cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{col}" style="animation-delay:{delay:.3f}s;opacity:.45"/>')
    anchor = "start" if math.cos(math.radians(ang)) >= -0.2 else "end"
    lx = x + (8 if anchor == "start" else -8)
    A(f'<text class="lbl" x="{lx:.1f}" y="{y+dy+4:.1f}" text-anchor="{anchor}" fill="{col if col==YELLOW else TEXT}">{label}</text>')

A(f'<circle cx="{CX}" cy="{CY}" r="2.5" fill="{GREEN}"/>')
A(f'<text x="{W/2}" y="{H-16}" text-anchor="middle" font-size="10" fill="{DIM}">9 contacts · 8 locked · 1 acquiring (AWS)</text>')
A('</svg>')

open("assets/radar.svg", "w", encoding="utf-8").write("\n".join(s))
print(f"radar.svg: {len(chr(10).join(s))} bytes")
