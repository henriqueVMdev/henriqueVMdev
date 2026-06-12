#!/usr/bin/env python3
"""
COMMIT EXCHANGE — renders your GitHub contribution history as an animated
candlestick chart (trading-terminal style SVG).

Price model:
  - Each candle = 1 week of contributions.
  - Weekly return is proportional to commit delta vs previous week.
  - Green candle  -> you committed more than last week.
  - Red candle    -> you slowed down. The market punishes laziness.
  - Volume bars   = raw weekly contribution count.

Data source: GitHub GraphQL contributionsCalendar (needs GITHUB_TOKEN).
Falls back to --mock for local testing without a token.

Usage:
  GITHUB_TOKEN=... python generate_chart.py --user henriqueVMdev --out dist/commit-exchange.svg
  python generate_chart.py --mock --out dist/commit-exchange.svg
"""

import argparse
import hashlib
import json
import math
import os
import random
import sys
import urllib.request
from datetime import date, datetime, timedelta

# ── palette (hack theme, matches the profile) ────────────────────────────────
BG = "#0a0e12"
PANEL = "#11161c"
GRID = "#1b232d"
TEXT = "#9fb3c8"
DIM = "#52677d"
GREEN = "#39ff7a"
RED = "#ff5c57"
YELLOW = "#ffd866"
CYAN = "#56c8ff"

W, H = 860, 470
CHART_X, CHART_Y = 56, 64
CHART_W, CHART_H = 770, 270
VOL_Y, VOL_H = 352, 58
WEEKS = 52

GQL = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch_weekly(user: str, token: str):
    """Returns list of (week_start_date, total_contributions) for ~52 weeks."""
    body = json.dumps({"query": GQL, "variables": {"login": user}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "commit-exchange",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    out = []
    for w in weeks:
        days = w["contributionDays"]
        start = days[0]["date"]
        total = sum(d["contributionCount"] for d in days)
        out.append((start, total))
    return out[-WEEKS:]


def mock_weekly():
    rng = random.Random(42)
    base = date.today() - timedelta(weeks=WEEKS)
    out = []
    level = 8
    for i in range(WEEKS):
        level = max(0, level + rng.randint(-6, 7))
        # simulate a hot streak and a vacation
        if 30 <= i <= 36:
            level += rng.randint(5, 15)
        if 14 <= i <= 16:
            level = rng.randint(0, 2)
        out.append(((base + timedelta(weeks=i)).isoformat(), level))
    return out


def jitter(seed: str, lo: float, hi: float) -> float:
    """Deterministic pseudo-random in [lo, hi] — same data => same chart."""
    h = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
    return lo + (h / 0xFFFFFFFF) * (hi - lo)


def build_candles(weekly):
    """Synthesize OHLC from weekly contribution counts."""
    candles = []
    price = 100.0
    prev = weekly[0][1]
    for wk_date, c in weekly:
        ret = (c - prev) / max(prev, 3)          # relative momentum
        ret = max(-0.28, min(0.28, ret * 0.6))   # clamp: no -100% weeks
        o = price
        cl = max(12.0, price * (1.0 + ret))
        body_hi, body_lo = max(o, cl), min(o, cl)
        wick = (body_hi - body_lo) * 0.5 + price * 0.012
        hi = body_hi + wick * jitter(wk_date + "h", 0.2, 1.0)
        lo = max(8.0, body_lo - wick * jitter(wk_date + "l", 0.2, 1.0))
        candles.append({"date": wk_date, "o": o, "h": hi, "l": lo, "c": cl, "v": c})
        price = cl
        prev = c
    return candles


def fmt(x: float) -> str:
    return f"{x:,.2f}"


def render(candles, user: str) -> str:
    pmin = min(c["l"] for c in candles)
    pmax = max(c["h"] for c in candles)
    pad = (pmax - pmin) * 0.08 or 1
    pmin, pmax = pmin - pad, pmax + pad
    vmax = max(max(c["v"] for c in candles), 1)

    def py(p):  # price -> y
        return CHART_Y + CHART_H * (1 - (p - pmin) / (pmax - pmin))

    n = len(candles)
    step = CHART_W / n
    cw = max(3.0, step * 0.62)

    last = candles[-1]
    first = candles[0]
    chg = (last["c"] - first["o"]) / first["o"] * 100
    chg_color = GREEN if chg >= 0 else RED
    total_commits = sum(c["v"] for c in candles)
    ath = max(candles, key=lambda c: c["v"])
    green_weeks = sum(1 for c in candles if c["c"] >= c["o"])

    e = []
    A = e.append

    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="\'JetBrains Mono\',Consolas,monospace">')
    A(f"""<style>
.t{{font-size:12px;fill:{TEXT}}} .dim{{fill:{DIM}}} .g{{fill:{GREEN}}} .r{{fill:{RED}}} .y{{fill:{YELLOW}}} .c{{fill:{CYAN}}}
@keyframes pop{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
.k{{transform-origin:center;transform-box:fill-box;animation:pop .35s cubic-bezier(.2,.9,.3,1.2) backwards}}
@keyframes vol{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
.vb{{transform-origin:bottom;transform-box:fill-box;animation:vol .4s ease-out backwards}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
.bl{{animation:blink 1.1s step-end infinite}}
@keyframes xh{{0%{{transform:translateX(0)}}100%{{transform:translateX({CHART_W}px)}}}}
.xhair{{animation:xh 9s linear infinite alternate;opacity:.35}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
.fd{{animation:fade .5s ease-out 5.2s backwards}}
@media (prefers-reduced-motion: reduce){{.k,.vb,.bl,.xhair,.fd{{animation:none}}}}
</style>""")

    A(f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>')

    # header
    A(f'<text x="20" y="24" font-size="15" class="g" font-weight="bold">{user.upper()}/CMT</text>')
    A(f'<text x="20" y="41" font-size="10" class="dim">PERP · 1W · COMMIT EXCHANGE</text>')
    A(f'<text x="{W-20}" y="24" text-anchor="end" font-size="16" fill="{chg_color}" font-weight="bold">{fmt(last["c"])}</text>')
    sign = "+" if chg >= 0 else ""
    A(f'<text x="{W-20}" y="40" text-anchor="end" font-size="11" fill="{chg_color}">{sign}{chg:.2f}% · 52W</text>')
    A(f'<line x1="16" y1="50" x2="{W-16}" y2="50" stroke="{GRID}"/>')

    # grid + price axis
    for i in range(5):
        gy = CHART_Y + CHART_H * i / 4
        gp = pmax - (pmax - pmin) * i / 4
        A(f'<line x1="{CHART_X}" y1="{gy:.1f}" x2="{CHART_X+CHART_W}" y2="{gy:.1f}" stroke="{GRID}" stroke-dasharray="2 4"/>')
        A(f'<text x="{CHART_X-8}" y="{gy+4:.1f}" text-anchor="end" font-size="10" class="dim">{gp:.0f}</text>')

    # crosshair sweep
    A(f'<g class="xhair"><line x1="{CHART_X}" y1="{CHART_Y}" x2="{CHART_X}" y2="{CHART_Y+CHART_H}" stroke="{CYAN}" stroke-width="1" stroke-dasharray="3 3"/></g>')

    # candles
    for i, c in enumerate(candles):
        x = CHART_X + i * step + step / 2
        up = c["c"] >= c["o"]
        col = GREEN if up else RED
        d = 0.06 * i
        body_top = py(max(c["o"], c["c"]))
        body_h = max(1.5, abs(py(c["o"]) - py(c["c"])))
        A(f'<g class="k" style="animation-delay:{d:.2f}s">')
        A(f'<line x1="{x:.1f}" y1="{py(c["h"]):.1f}" x2="{x:.1f}" y2="{py(c["l"]):.1f}" stroke="{col}" stroke-width="1"/>')
        A(f'<rect x="{x-cw/2:.1f}" y="{body_top:.1f}" width="{cw:.1f}" height="{body_h:.1f}" fill="{col}" rx="1"/>')
        A("</g>")

    # last price line + blinking marker
    ly = py(last["c"])
    A(f'<line x1="{CHART_X}" y1="{ly:.1f}" x2="{CHART_X+CHART_W}" y2="{ly:.1f}" stroke="{chg_color}" stroke-width="0.7" stroke-dasharray="5 4" opacity="0.6"/>')
    A(f'<circle class="bl" cx="{CHART_X+CHART_W-4:.1f}" cy="{ly:.1f}" r="3.4" fill="{chg_color}"/>')

    # volume
    A(f'<text x="{CHART_X}" y="{VOL_Y-6}" font-size="10" class="dim">VOL (commits/week)</text>')
    for i, c in enumerate(candles):
        x = CHART_X + i * step + step / 2
        vh = max(1.0, VOL_H * c["v"] / vmax)
        col = GREEN if c["c"] >= c["o"] else RED
        d = 0.06 * i
        A(f'<rect class="vb" style="animation-delay:{d:.2f}s" x="{x-cw/2:.1f}" y="{VOL_Y+VOL_H-vh:.1f}" width="{cw:.1f}" height="{vh:.1f}" fill="{col}" opacity="0.55"/>')

    # footer stats
    fy = VOL_Y + VOL_H + 32
    A(f'<line x1="16" y1="{fy-18}" x2="{W-16}" y2="{fy-18}" stroke="{GRID}"/>')
    A(f'<g class="fd">')
    A(f'<text x="20" y="{fy}" class="t"><tspan class="dim">VOL 52W</tspan> <tspan class="c">{total_commits}</tspan></text>')
    A(f'<text x="200" y="{fy}" class="t"><tspan class="dim">ATH WEEK</tspan> <tspan class="y">{ath["v"]} @ {ath["date"]}</tspan></text>')
    A(f'<text x="510" y="{fy}" class="t"><tspan class="dim">GREEN WEEKS</tspan> <tspan class="g">{green_weeks}/{n}</tspan></text>')
    A(f'<text x="{W-20}" y="{fy}" text-anchor="end" class="t"><tspan class="dim">funding paid in</tspan> <tspan class="g">commits</tspan> <tspan class="bl g">█</tspan></text>')
    A("</g>")

    A("</svg>")
    return "\n".join(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_USER", "henriqueVMdev"))
    ap.add_argument("--out", default="dist/commit-exchange.svg")
    ap.add_argument("--mock", action="store_true", help="render with fake data (no token)")
    args = ap.parse_args()

    if args.mock:
        weekly = mock_weekly()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            print("ERROR: GITHUB_TOKEN not set (or use --mock)", file=sys.stderr)
            sys.exit(1)
        weekly = fetch_weekly(args.user, token)

    candles = build_candles(weekly)
    svg = render(candles, args.user)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        f.write(svg)
    print(f"wrote {args.out} ({len(svg)} bytes, {len(candles)} candles)")


if __name__ == "__main__":
    main()
