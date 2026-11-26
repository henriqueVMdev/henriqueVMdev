#!/usr/bin/env python3
"""SOC panel: soma os achados de Semgrep, Trivy e gosec nos repos públicos e desenha um SVG
no tema do terminal. Só contagens vão pro SVG; arquivo, linha e regra ficam de fora.

Uso:
  python3 sec/sec_panel.py --reports reports --state prev-state.json --out dist
  python3 sec/sec_panel.py --mock --out dist      # teste local sem scan
"""
import argparse
import json
import os
import random
from datetime import datetime, timezone, date
from pathlib import Path
from xml.sax.saxutils import escape

BG, PANEL, GRID, TEXT, DIM = "#0a0e12", "#11161c", "#1b232d", "#9fb3c8", "#52677d"
GREEN, YELLOW, RED, CYAN, MAG = "#39ff7a", "#ffd866", "#ff5c57", "#56c8ff", "#ff6ac1"
LEVELS = ["critical", "high", "medium", "low"]
LEVEL_COLOR = {"critical": RED, "high": MAG, "medium": YELLOW, "low": CYAN}

SEV_MAP = {
    "CRITICAL": "critical",
    "ERROR": "high", "HIGH": "high",
    "WARNING": "medium", "MEDIUM": "medium",
    "INFO": "low", "LOW": "low", "UNKNOWN": "low",
}


def sev(raw):
    return SEV_MAP.get(str(raw or "").upper(), "low")


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def count_reports(reports_dir):
    """Lê reports/<repo>.<tool>.json e devolve contagens por severidade e por ferramenta."""
    total = {lvl: 0 for lvl in LEVELS}
    per_tool = {"semgrep": 0, "trivy": 0, "gosec": 0}
    repos, errors = set(), 0
    for f in sorted(Path(reports_dir).glob("*.json")):
        repo, _, tool = f.stem.rpartition(".")
        if tool not in per_tool:
            continue
        repos.add(repo)
        data = load_json(f)
        if data is None:
            errors += 1
            continue
        found = []
        if tool == "semgrep":
            found = [sev(r.get("extra", {}).get("severity")) for r in data.get("results", [])]
        elif tool == "trivy":
            for res in data.get("Results") or []:
                found += [sev(v.get("Severity")) for v in res.get("Vulnerabilities") or []]
                # segredo vazado conta sempre como crítico
                found += ["critical" for _ in res.get("Secrets") or []]
        elif tool == "gosec":
            found = [sev(i.get("severity")) for i in data.get("Issues") or []]
        for lvl in found:
            total[lvl] += 1
        per_tool[tool] += len(found)
    repo_list = Path(reports_dir, "repos.txt")
    if repo_list.exists():
        repos |= {r.strip() for r in repo_list.read_text().split() if r.strip()}
    return total, per_tool, len(repos), errors


def update_state(prev, total, today):
    state = dict(prev or {})
    state.setdefault("first_scan", today.isoformat())
    if total["critical"] > 0:
        state["last_critical"] = today.isoformat()
    hist = [h for h in state.get("history", []) if h.get("date") != today.isoformat()]
    hist.append({"date": today.isoformat(), **total})
    state["history"] = hist[-30:]
    since = date.fromisoformat(state.get("last_critical") or state["first_scan"])
    state["days_clean"] = 0 if total["critical"] > 0 else (today - since).days
    return state


def render(total, per_tool, n_repos, errors, state, versions, now):
    W, H = 860, 400
    crit = total["critical"]
    alert = crit > 0
    status_col = RED if alert else GREEN
    status_txt = "ALERT" if alert else "MONITORING"
    days = state["days_clean"]
    hist = state["history"]

    s = []
    A = s.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
      f'font-size="13" font-family="\'JetBrains Mono\',\'Fira Code\',Consolas,monospace">')
    A(f'''<style>
.t{{fill:{TEXT};white-space:pre}}
.d{{fill:{DIM}}}
@keyframes fill{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
.bar{{transform-box:fill-box;transform-origin:left;animation:fill 1.4s ease-out .4s backwards}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
.dot{{animation:pulse 1.6s ease-in-out infinite}}
@keyframes draw{{from{{stroke-dashoffset:1200}}to{{stroke-dashoffset:0}}}}
.spark{{stroke-dasharray:1200;animation:draw 2.4s ease-out .6s backwards}}
@keyframes sweep{{from{{transform:translateY(-10px)}}to{{transform:translateY({H}px)}}}}
.scan{{animation:sweep 6s linear infinite;opacity:.05}}
@media (prefers-reduced-motion: reduce){{.bar,.dot,.spark,.scan{{animation:none}}}}
</style>''')
    A(f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>')
    A(f'<rect width="{W}" height="34" rx="10" fill="{PANEL}"/><rect y="20" width="{W}" height="14" fill="{PANEL}"/>')
    A(f'<circle cx="22" cy="17" r="6" fill="#ff5c57"/><circle cx="42" cy="17" r="6" fill="#ffd866"/><circle cx="62" cy="17" r="6" fill="{GREEN}"/>')
    A(f'<text x="{W//2}" y="22" text-anchor="middle" font-size="12" fill="{DIM}">soc@henrique: ~/watch</text>')
    A(f'<rect class="scan" x="0" width="{W}" height="3" fill="{GREEN}"/>')

    A(f'<text class="t" x="20" y="62"><tspan fill="{GREEN}">soc@henrique</tspan><tspan class="d">:</tspan>'
      f'<tspan fill="{CYAN}">~/watch</tspan><tspan class="d">$ </tspan>./seccheck --repos public --tools semgrep,trivy,gosec</text>')

    # painel esquerdo: status e dias sem crítico
    A(f'<rect x="20" y="82" width="250" height="200" rx="6" fill="{PANEL}" stroke="{GRID}"/>')
    A(f'<circle class="dot" cx="42" cy="106" r="6" fill="{status_col}"/>')
    A(f'<text class="t" x="56" y="111" fill="{status_col}" font-weight="bold">{status_txt}</text>')
    A(f'<text x="145" y="196" text-anchor="middle" font-size="64" font-weight="bold" fill="{status_col}">{days}</text>')
    A(f'<text class="t d" x="145" y="226" text-anchor="middle">dias sem achado crítico</text>')
    A(f'<text class="t d" x="145" y="262" text-anchor="middle" font-size="11">{n_repos} repos públicos varridos</text>')

    # painel direito: barras por severidade
    A(f'<rect x="290" y="82" width="550" height="200" rx="6" fill="{PANEL}" stroke="{GRID}"/>')
    A(f'<text class="t d" x="310" y="108" xml:space="preserve">SEVERITY      COUNT</text>')
    peak = max(max(total.values()), 1)
    for i, lvl in enumerate(LEVELS):
        y = 134 + i * 36
        col = LEVEL_COLOR[lvl]
        w = 0 if total[lvl] == 0 else max(4, int(300 * total[lvl] / peak))
        A(f'<text class="t" x="310" y="{y}" fill="{col}">{lvl.upper()}</text>')
        A(f'<text class="t" x="455" y="{y}" text-anchor="end">{total[lvl]}</text>')
        A(f'<rect x="475" y="{y-11}" width="300" height="12" rx="2" fill="{GRID}"/>')
        if w:
            A(f'<rect class="bar" x="475" y="{y-11}" width="{w}" height="12" rx="2" fill="{col}" '
              f'style="animation-delay:{0.4 + i*0.15:.2f}s"/>')

    # sparkline do total de achados nos últimos 30 dias
    sx, sy, sw, sh = 20, 314, 520, 46
    A(f'<text class="t d" x="{sx}" y="{sy-4}" font-size="11">achados totais, últimos 30 dias</text>')
    A(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="4" fill="{PANEL}" stroke="{GRID}"/>')
    totals = [sum(h.get(l, 0) for l in LEVELS) for h in hist]
    if len(totals) >= 2:
        top = max(max(totals), 1)
        pts = []
        for i, v in enumerate(totals):
            x = sx + 8 + (sw - 16) * i / (len(totals) - 1)
            y = sy + sh - 8 - (sh - 16) * v / top
            pts.append(f"{x:.1f},{y:.1f}")
        A(f'<polyline class="spark" points="{" ".join(pts)}" fill="none" stroke="{GREEN}" stroke-width="1.6"/>')
    else:
        A(f'<text class="t d" x="{sx + sw/2}" y="{sy + 28}" text-anchor="middle" font-size="11">coletando histórico...</text>')

    # rodapé: ferramentas e horário
    tools = "  ".join(f"{k} {per_tool[k]}" for k in ("semgrep", "trivy", "gosec"))
    A(f'<text class="t" x="560" y="{sy+12}" font-size="11"><tspan class="d">por ferramenta</tspan></text>')
    A(f'<text class="t" x="560" y="{sy+30}" font-size="11">{escape(tools)}</text>')
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    extra = f"  ·  {errors} scan com erro" if errors else ""
    A(f'<text class="t d" x="560" y="{sy+48}" font-size="10">última varredura {stamp}{escape(extra)}</text>')
    A(f'<text class="t d" x="20" y="{H-12}" font-size="10">{escape(versions)}  ·  só contagens; detalhe de achado não é publicado</text>')
    A('</svg>')
    return "\n".join(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", default="reports")
    ap.add_argument("--state", default="prev-state.json")
    ap.add_argument("--out", default="dist")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    if args.mock:
        rnd = random.Random(7)
        total = {"critical": 0, "high": 3, "medium": 11, "low": 27}
        per_tool = {"semgrep": 18, "trivy": 23, "gosec": 0}
        n_repos, errors = 14, 0
        prev = {"first_scan": "2026-11-01", "history": [
            {"date": f"2026-11-{d:02d}", "critical": 0, "high": rnd.randint(2, 6),
             "medium": rnd.randint(8, 16), "low": rnd.randint(20, 35)} for d in range(1, 26)]}
    else:
        total, per_tool, n_repos, errors = count_reports(args.reports)
        prev = load_json(args.state) or {}

    state = update_state(prev, total, now.date())
    versions = os.environ.get("SCANNER_VERSIONS", "semgrep · trivy · gosec")
    svg = render(total, per_tool, n_repos, errors, state, versions, now)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sec-panel.svg").write_text(svg, encoding="utf-8")
    (out / "sec-state.json").write_text(json.dumps(state, indent=1), encoding="utf-8")
    print(f"repos={n_repos} total={total} per_tool={per_tool} errors={errors} days_clean={state['days_clean']}")


if __name__ == "__main__":
    main()
