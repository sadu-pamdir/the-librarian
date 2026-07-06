#!/usr/bin/env python3
"""compile.py — the C3 compile step (ingestion is deliberate, not per-query).

Pull one article from the archive layer (kiwix-serve), strip it to clean text,
write a compiled-wiki page with frontmatter, and register it in the
knowledge-map. Stdlib only.

usage: compile.py '<search term>' <book> [page-slug]
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "librarian"))
import librarian  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
COMPILED = REPO / "compiled-wiki"
KMAP = COMPILED / "knowledge-map.md"


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: compile.py '<search term>' <book> [page-slug]")
        raise SystemExit(1)
    term, book = sys.argv[1], sys.argv[2]
    slug = sys.argv[3] if len(sys.argv) > 3 else re.sub(r"\W+", "-", term.lower()).strip("-")

    ans = librarian.archive_search(term, book)
    if ans is None:
        print(f"no archive hit for '{term}' in book '{book}' — is kiwix-serve running?")
        raise SystemExit(2)

    src = ans.route[-1].replace("C1 archive page: ", "")
    today = datetime.date.today().isoformat()
    page_name = f"{slug}.md"
    page = COMPILED / page_name
    page.write_text(
        f"---\n"
        f"topic: {term}\n"
        f"source_of_record: {src} (book: {book})\n"
        f"compiled: {today}\n"
        f"---\n\n"
        f"# {term}\n\n"
        f"{ans.passage}\n\n"
        f"> Source of record: `{src}` — immutable ZIM snapshot, book `{book}`.\n",
        encoding="utf-8",
    )

    kmap = KMAP.read_text(encoding="utf-8")
    row = f"| {term} | {page_name} | {src} (book: {book}) |"
    if row not in kmap:
        kmap = kmap.rstrip() + "\n" + row + "\n"
        KMAP.write_text(kmap, encoding="utf-8")
    print(f"compiled: {page} \nregistered in knowledge-map.")


if __name__ == "__main__":
    main()
