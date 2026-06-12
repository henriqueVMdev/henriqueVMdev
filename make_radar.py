#!/usr/bin/env python3
"""Radar sweep: rotating beam detects skills as blips, each pings when the sweep passes it."""
import math

W, H = 420, 470
CX, CY, R = 210, 252, 168
PERIOD = 6.0  # seconds per rotation

GREEN, YELLOW, DIM, GRID, BG, PANEL, TEXT = "#39ff7a", "#ffd866", "#52677d", "#1b232d", "#0a0e12", "#11161c", "#9fb3c8"

# (label, angle_deg [0=right, CW], radius_frac, color, dy_label)
BLIPS = [
    ("Python",      305, 0.30, GREEN, -10),
    ("FastAPI",      25, 0.52, GREEN, -10),
    ("PostgreSQL",   80, 0.68, GREEN,  16),
    ("Docker",      140, 0.50, GREEN, -10),
    ("Vue 3",       185, 0.72, GREEN, -10),
    ("Linux",       245, 0.60, GREEN, -10),
    ("Quant/Stats", 340, 0.84, GREEN,  16),
    ("Java",        115, 0.90, YELLOW, -10),
]

def pos(angle_deg, rfrac):
    a = math.radians(angle_deg)
    return CX + R * rfrac * math.cos(a), CY + R * rfrac * math.sin(a)

s = []
A = s.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="\'JetBrains Mono\',Consolas,monospace">')
A(f'''<defs>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{GREEN}" stop-opacity="0.55"/>
  <stop offset="1" stop-color="{GREEN}" stop-opacity="0"/>
</linearGradient>
<clipPath id="dish"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>
</defs>
<style>
@keyframes ping{{0%{{r:4;opacity:.9}}12%{{r:15;opacity:0}}13%,100%{{r:4;opacity:0}}}}
@keyframes glow{{0%,2%{{opacity:1}}10%{{opacity:.45}}100%{{opacity:.45}}}}
.lbl{{font-size:10.5px}}
@media (prefers-reduced-motion: reduce){{ .anim{{display:none}} circle.bl{{opacity:.8!important;animation:none!important}} }}
</style>''')

A(f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>')
A(f'<rect width="{W}" height="34" rx="10" fill="{PANEL}"/><rect y="20" width="{W}" height="14" fill="{PANEL}"/>')
A(f'<circle cx="22" cy="17" r="6" fill="#ff5c57"/><circle cx="42" cy="17" r="6" fill="#ffd866"/><circle cx="62" cy="17" r="6" fill="{GREEN}"/>')
A(f'<text x="{W/2}" y="22" text-anchor="middle" font-size="12" fill="{DIM}">./skillscan --sweep --range max</text>')

# rings + cross
for f in (0.25, 0.5, 0.75, 1.0):
    A(f'<circle cx="{CX}" cy="{CY}" r="{R*f:.0f}" fill="none" stroke="{GRID}" stroke-width="1"/>')
A(f'<line x1="{CX-R}" y1="{CY}" x2="{CX+R}" y2="{CY}" stroke="{GRID}"/>')
A(f'<line x1="{CX}" y1="{CY-R}" x2="{CX}" y2="{CY+R}" stroke="{GRID}"/>')
# degree ticks
for d in range(0, 360, 30):
    x1, y1 = pos(d, 0.96); x2, y2 = pos(d, 1.0)
    A(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{DIM}" stroke-width="1"/>')

# rotating sweep beam (wedge + leading edge), clipped to dish
A(f'<g clip-path="url(#dish)" class="anim">')
A(f'<g><animateTransform attributeName="transform" type="rotate" from="0 {CX} {CY}" to="360 {CX} {CY}" dur="{PERIOD}s" repeatCount="indefinite"/>')
A(f'<path d="M{CX},{CY} L{CX+R},{CY} A{R},{R} 0 0,0 {CX+R*math.cos(math.radians(-40)):.1f},{CY+R*math.sin(math.radians(-40)):.1f} Z" fill="url(#beam)" opacity="0.5" transform="rotate(0)"/>')
A(f'<line x1="{CX}" y1="{CY}" x2="{CX+R}" y2="{CY}" stroke="{GREEN}" stroke-width="1.6"/>')
A('</g></g>')

# blips: ping ring + dot that glows right after the sweep passes
for label, ang, rf, col, dy in BLIPS:
    x, y = pos(ang, rf)
    delay = (ang % 360) / 360.0 * PERIOD
    A(f'<circle class="anim" cx="{x:.1f}" cy="{y:.1f}" r="4" fill="none" stroke="{col}" style="animation:ping {PERIOD}s linear infinite;animation-delay:{delay:.2f}s"/>')
    A(f'<circle class="bl" cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{col}" style="animation:glow {PERIOD}s linear infinite;animation-delay:{delay:.2f}s;opacity:.45"/>')
    anchor = "start" if math.cos(math.radians(ang)) >= -0.2 else "end"
    lx = x + (8 if anchor == "start" else -8)
    A(f'<text class="lbl" x="{lx:.1f}" y="{y+dy+4:.1f}" text-anchor="{anchor}" fill="{col if col==YELLOW else TEXT}">{label}</text>')

A(f'<circle cx="{CX}" cy="{CY}" r="2.5" fill="{GREEN}"/>')
A(f'<text x="{W/2}" y="{H-16}" text-anchor="middle" font-size="10" fill="{DIM}">8 contacts · 7 locked · 1 acquiring (Java)</text>')
A('</svg>')

open("assets/radar.svg", "w").write("\n".join(s))
print(f"radar.svg: {len(chr(10).join(s))} bytes")
