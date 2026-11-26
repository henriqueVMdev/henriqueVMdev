#!/usr/bin/env python3
"""Boot terminal: lines appear one by one (CSS only, no SMIL), cursor blinks at the end.
Edit LINES and run `python3 make_terminal.py` to regenerate assets/terminal.svg."""
from xml.sax.saxutils import escape

W = 860
X = 20
PROMPT = [("g", "henrique@vps"), ("dim", ":"), ("c", "~/ops"), ("dim", "$ ")]

# each entry: (gap_before_px, delay_s, [(css_class, text), ...]); "P" = prompt prefix
LINES = [
    (0,  0.4, ["P", ("", "whoami --verbose")]),
    (26, 1.6, [("m", "  name    "), ("", "Henrique V. Melo")]),
    (22, 2.1, [("m", "  role    "), ("", "DevSecOps intern "), ("dim", "@ "), ("y", "Netglobe Cybersecurity"), ("dim", "  # a partir de dez/2026")]),
    (22, 2.6, [("m", "  antes   "), ("", "Dev Fullstack "), ("dim", "@ "), ("", "HRB Imports"), ("dim", "  # autopeças no Mercado Livre")]),
    (22, 3.1, [("m", "  base    "), ("", "Hortolândia, SP "), ("dim", "→ destino: "), ("y", "anywhere")]),

    (36, 4.0, ["P", ("", 'docker ps --format "{{.Names}}  {{.Status}}"')]),
    (26, 5.0, [("c", "  myrias-api      "), ("g", "Up (healthy)"), ("dim", "   # Spring Boot, prod")]),
    (22, 5.4, [("c", "  myrias-web      "), ("g", "Up (healthy)"), ("dim", "   # Vue 3")]),
    (22, 5.8, [("c", "  postgres        "), ("g", "Up (healthy)")]),
    (22, 6.2, [("c", "  redis-queue     "), ("g", "Up (healthy)"), ("dim", "   # fila de jobs distribuída")]),
    (22, 6.6, [("c", "  llm-agent       "), ("y", "Paused      "), ("dim", "   # esperando um humano aprovar")]),

    (36, 7.6, ["P", ("", "nmap -sV skills/")]),
    (26, 8.4, [("dim", "  PORT      STATE     SERVICE")]),
    (22, 8.9, [("", "  8080/tcp  "), ("g", "open      "), ("", "Java 21 "), ("dim", "/ "), ("", "Spring Boot 3 "), ("dim", "/ "), ("", "PostgreSQL "), ("dim", "/ "), ("", "Redis")]),
    (22, 9.3, [("", "  8000/tcp  "), ("g", "open      "), ("", "Python "), ("dim", "/ "), ("", "FastAPI "), ("dim", "/ "), ("", "scraping")]),
    (22, 9.7, [("", "  5173/tcp  "), ("g", "open      "), ("", "Vue 3 "), ("dim", "/ "), ("", "Angular "), ("dim", "/ "), ("", "TypeScript")]),
    (22, 10.1, [("", "  2375/tcp  "), ("g", "open      "), ("", "Docker "), ("dim", "/ "), ("", "Linux "), ("dim", "/ "), ("", "GitHub Actions")]),
    (22, 10.6, [("", "  9090/tcp  "), ("y", "filtered  "), ("", "Go "), ("dim", "(aprendendo)")]),
    (22, 11.0, [("", "   443/tcp  "), ("y", "filtered  "), ("", "AppSec "), ("dim", "(PortSwigger, OWASP)")]),

    (36, 12.0, ["P", ("CURSOR", "")]),
]

y = 64
rows = []
for i, (gap, delay, parts) in enumerate(LINES, 1):
    y += gap
    spans = []
    for part in parts:
        if part == "P":
            spans += [f'<tspan class="{c}">{escape(t)}</tspan>' for c, t in PROMPT]
        elif part[0] == "CURSOR":
            spans.append('<tspan class="cursor g">█</tspan>')
        elif part[0]:
            spans.append(f'<tspan class="{part[0]}">{escape(part[1])}</tspan>')
        else:
            spans.append(escape(part[1]))
    rows.append((i, delay, y, "".join(spans)))

H = y + 40
last_delay = LINES[-1][1]

css_lines = "\n".join(f"    .l{i}{{animation:show .01s {d}s forwards}}" for i, d, _, _ in rows)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="'JetBrains Mono','Fira Code',Consolas,monospace">
  <style>
    .bg{{fill:#0a0e12}}
    .chrome{{fill:#11161c}}
    .t{{font-size:14px;fill:#9fb3c8;white-space:pre}}
    .g{{fill:#39ff7a}}
    .dim{{fill:#52677d}}
    .y{{fill:#ffd866}}
    .c{{fill:#56c8ff}}
    .m{{fill:#ff6ac1}}
    .r{{fill:#ff5c57}}

    .line{{opacity:0}}
    @keyframes show{{to{{opacity:1}}}}
{css_lines}

    @keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
    @keyframes curon{{to{{opacity:1}}}}
    .cursor{{opacity:0;animation:curon .01s {last_delay + 0.2:.1f}s forwards, blink 1s step-end infinite {last_delay + 0.3:.1f}s}}

    @keyframes sweep{{from{{transform:translateY(-40px)}}to{{transform:translateY({H + 10}px)}}}}
    .scan{{animation:sweep 7s linear infinite;opacity:.05}}

    @media (prefers-reduced-motion: reduce){{ .line{{opacity:1;animation:none}} .scan{{display:none}} .cursor{{opacity:1;animation:none}} }}
  </style>

  <rect class="bg" width="{W}" height="{H}" rx="10"/>
  <rect class="chrome" width="{W}" height="34" rx="10"/>
  <rect class="chrome" y="20" width="{W}" height="14"/>
  <circle cx="22" cy="17" r="6" fill="#ff5c57"/>
  <circle cx="42" cy="17" r="6" fill="#ffd866"/>
  <circle cx="62" cy="17" r="6" fill="#39ff7a"/>
  <text x="{W // 2}" y="22" text-anchor="middle" font-size="12" class="dim">henrique@vps: ~/ops</text>

  <rect class="scan g" x="0" width="{W}" height="3"/>

  <g class="t">
''' + "\n".join(f'    <text class="line l{i}" x="{X}" y="{yy}" xml:space="preserve">{body}</text>' for i, _, yy, body in rows) + '''
  </g>
</svg>
'''

open("assets/terminal.svg", "w", encoding="utf-8").write(svg)
print(f"terminal.svg: {len(svg)} bytes, {W}x{H}")
