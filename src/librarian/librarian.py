#!/usr/bin/env python3
"""the-librarian — reference implementation of the C1-C4 answer path.

Navigate, don't generate:
    intent -> knowledge-map (C4) -> compiled page (C3) or refuted wing (C7)
           -> fallback: archive search via kiwix-serve (C2 over C1)
    Every answer carries a citation. No citation -> labeled UNSOURCED.
    A hit in the refuted wing is a first-class result: the librarian answers
    "documented falsehood, refuted by [source]" instead of staying silent.

Stdlib only. No dependencies, by design.
"""
from __future__ import annotations

import html
import html.parser
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KNOWLEDGE_MAP = REPO / "compiled-wiki" / "knowledge-map.md"
COMPILED = REPO / "compiled-wiki"
KIWIX = "http://127.0.0.1:8181"


@dataclass
class Answer:
    status: str          # "compiled" | "refuted" | "archive" | "unsourced"
    passage: str
    citation: str        # file/section or archive URL — the source of record
    route: list[str]     # hops taken, for the audit log


# ---------------------------------------------------------------- C4: index
def load_map() -> list[dict]:
    """knowledge-map.md is a human-readable table: | Topic | Page | Source |"""
    rows = []
    if not KNOWLEDGE_MAP.exists():
        return rows
    for line in KNOWLEDGE_MAP.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if m and m.group(1).lower() not in ("topic", "claim", "---", ""):
            topic, page, source = (g.strip() for g in m.groups())
            if page and not topic.startswith("(") and not set(topic) <= {"-", " "}:
                rows.append({"topic": topic, "page": page, "source": source})
    return rows


def route_compiled(question: str) -> dict | None:
    """Deterministic routing: keyword overlap question <-> topic. No embeddings
    needed for the core loop; a recall layer may be added later, optionally."""
    q = set(re.findall(r"\w+", question.lower()))
    best, score = None, 0
    for row in load_map():
        t = set(re.findall(r"\w+", row["topic"].lower()))
        s = len(q & t)
        if s > score:
            best, score = row, s
    return best if score >= 1 else None


# ------------------------------------------------------- C2/C1: archive layer
class _Text(html.parser.HTMLParser):
    SKIP = {"script", "style", "nav", "header", "footer"}

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.parts.append(data.strip())


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def archive_search(question: str, lang: str | None = None) -> Answer | None:
    """Full-text search on kiwix-serve, then fetch the top hit.

    kiwix-serve refuses cross-language search over multiple books, so we
    filter by language: explicit lang wins, otherwise deu first, then eng.
    """
    for try_lang in ([lang] if lang else ["deu", "eng"]):
        params = {"pattern": question, "pageLength": "3", "format": "xml",
                  "books.filter.lang": try_lang}
        url = f"{KIWIX}/search?{urllib.parse.urlencode(params)}"
        try:
            xml = _get(url)
        except OSError:
            return None
        if "<item>" in xml:
            break
    else:
        return None
    items = re.findall(r"<item>(.*?)</item>", xml, flags=re.S)
    if not items:
        return None
    first = items[0]
    link = re.search(r"<link>([^<]+)</link>", first)
    ttl = re.search(r"<title>([^<]+)</title>", first)
    if not link:
        return None
    path = html.unescape(link.group(1))
    page_url = KIWIX + path
    parser = _Text()
    parser.feed(_get(page_url))
    text = " ".join(parser.parts)
    passage = text[:900] + ("…" if len(text) > 900 else "")
    title = html.unescape(ttl.group(1)) if ttl else path
    return Answer(
        status="archive",
        passage=passage,
        citation=f"{page_url} (ZIM archive, immutable snapshot) — '{title}'",
        route=["C4 knowledge-map: no compiled page", f"C2 kiwix search: {url}",
               f"C1 archive page: {path}"],
    )


# ----------------------------------------------------------------- C3: pages
def compiled_answer(row: dict) -> Answer | None:
    page = COMPILED / row["page"]
    if not page.exists():
        return None
    text = page.read_text(encoding="utf-8")
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S).strip()
    passage = body[:900] + ("…" if len(body) > 900 else "")
    return Answer(
        status="compiled",
        passage=passage,
        citation=f"compiled-wiki/{row['page']} (source of record: {row['source']})",
        route=[f"C4 knowledge-map: topic '{row['topic']}'",
               f"C3 compiled page: {row['page']}"],
    )


# ----------------------------------------------------- C7: the refuted wing
def _frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
    return fm


def refuted_answer(row: dict) -> Answer | None:
    """A refuted-wing hit is a first-class result, not a failure mode."""
    page = COMPILED / row["page"]
    if not page.exists():
        return None
    text = page.read_text(encoding="utf-8")
    fm = _frontmatter(text)
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S).strip()
    status = fm.get("status", "refuted")
    passage = (
        f"DOCUMENTED FALSEHOOD (status: {status}, claim type: "
        f"{fm.get('type', '?')}) — claim: {fm.get('claim', row['topic'])!r}. "
        + body[:700] + ("…" if len(body) > 700 else "")
    )
    return Answer(
        status="refuted",
        passage=passage,
        citation=(f"compiled-wiki/{row['page']} (refuted by: "
                  f"{fm.get('refuted-by', row['source'])}; last-checked: "
                  f"{fm.get('last-checked', '?')})"),
        route=[f"C4 knowledge-map (refuted wing): claim '{row['topic']}'",
               f"C7 refuted page: {row['page']}"],
    )


# ------------------------------------------------------------------ the loop
def ask(question: str, lang: str | None = None) -> Answer:
    row = route_compiled(question)
    if row:
        if row["page"].startswith("refuted/"):
            ans = refuted_answer(row)
        else:
            ans = compiled_answer(row)
        if ans:
            return ans
    ans = archive_search(question, lang)
    if ans:
        return ans
    return Answer(
        status="unsourced",
        passage="No source of record found. A model may synthesize an answer, "
                "but it MUST be labeled as unsourced synthesis.",
        citation="NONE — this is the honest failure mode, not a bug.",
        route=["C4 miss", "C1/C2 miss"],
    )


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: librarian.py '<question>' [deu|eng]")
        raise SystemExit(1)
    lang = sys.argv[2] if len(sys.argv) > 2 else None
    ans = ask(sys.argv[1], lang)
    print(json.dumps(asdict(ans), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
