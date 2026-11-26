#!/usr/bin/env python3
"""Valida a flag mandada numa issue e atualiza o hall of fame no README.

Lê tudo de variável de ambiente (nunca interpolado em shell):
  ISSUE_BODY, ISSUE_USER, ISSUE_USER_TYPE
Compara o sha256 da flag com ctf/flag.sha256, então a resposta não fica em texto no repo.
Escreve em GITHUB_OUTPUT: result=correct|repeat|wrong|nope|invalid e rank=N.
"""
import hashlib
import hmac
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
HASH_FILE = ROOT / "ctf" / "flag.sha256"
START, END = "<!-- HOF:START -->", "<!-- HOF:END -->"
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
FLAG_RE = re.compile(r"HVM\{[^\s{}]{1,80}\}")
ENTRY_RE = re.compile(r"^\d+\. \[@([A-Za-z0-9-]+)\]\(https://github\.com/[A-Za-z0-9-]+\) · \d{4}-\d{2}-\d{2}$")


def output(**kv):
    path = os.environ.get("GITHUB_OUTPUT")
    lines = "".join(f"{k}={v}\n" for k, v in kv.items())
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(lines)
    print(lines, end="")


def read_hof(text):
    block = text.split(START, 1)[1].split(END, 1)[0]
    return [m.group(1) for line in block.splitlines() if (m := ENTRY_RE.match(line.strip()))]


def write_hof(text, entries):
    if entries:
        body = "\n".join(entries)
    else:
        body = "<sub><code>ninguém achou ainda. o primeiro nome fica aqui pra sempre</code></sub>"
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{START}\n{body}\n{END}{tail}"


def main():
    user = os.environ.get("ISSUE_USER", "")
    if os.environ.get("ISSUE_USER_TYPE", "User") != "User" or not LOGIN_RE.match(user):
        output(result="invalid")
        return

    body = os.environ.get("ISSUE_BODY", "")[:5000]
    candidates = FLAG_RE.findall(body)
    if not candidates:
        output(result="nope")
        return

    expected = HASH_FILE.read_text().strip()
    ok = any(hmac.compare_digest(hashlib.sha256(c.encode()).hexdigest(), expected) for c in candidates[:5])
    if not ok:
        output(result="wrong")
        return

    text = README.read_text(encoding="utf-8")
    current = read_hof(text)
    if user.lower() in (u.lower() for u in current):
        output(result="repeat", rank=[u.lower() for u in current].index(user.lower()) + 1)
        return

    block = text.split(START, 1)[1].split(END, 1)[0]
    entries = [line.strip() for line in block.splitlines() if ENTRY_RE.match(line.strip())]
    rank = len(entries) + 1
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries.append(f"{rank}. [@{user}](https://github.com/{user}) · {today}")
    README.write_text(write_hof(text, entries), encoding="utf-8")
    output(result="correct", rank=rank)


if __name__ == "__main__":
    main()
