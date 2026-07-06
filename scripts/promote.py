#!/usr/bin/env python3
"""promote.py — the C6 trust boundary: sandbox -> master, hashed and chained.

Nothing enters the master tenant unreviewed. Promotion is an explicit act:
the artifact is SHA-256-hashed, the hash is chained to the previous entry
(GENESIS -> ...), and the move is logged append-only. verify() checks the
whole chain. Pattern reused from a GeBüV-grade audit log (OR 958f context).

usage: promote.py <file-in-library/sandbox>     # promote after review
       promote.py --verify                      # check chain integrity
"""
from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SANDBOX = REPO / "library" / "sandbox"
MASTER = REPO / "library" / "master"
LOG = REPO / "library" / "promotion-log.jsonl"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _last_chain() -> str:
    if not LOG.exists():
        return "GENESIS"
    lines = LOG.read_text(encoding="utf-8").strip().splitlines()
    return json.loads(lines[-1])["chain"] if lines else "GENESIS"


def promote(name: str) -> None:
    src = SANDBOX / name
    if not src.exists():
        raise SystemExit(f"not in sandbox: {src}")
    file_hash = _sha(src)
    prev = _last_chain()
    chain = hashlib.sha256((prev + file_hash).encode()).hexdigest()
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "file": name,
        "sha256": file_hash,
        "prev": prev,
        "chain": chain,
        "act": "promoted sandbox->master (human-reviewed)",
    }
    shutil.move(str(src), MASTER / name)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"promoted {name}\n  sha256 {file_hash}\n  chain  {chain}")


def verify() -> None:
    if not LOG.exists():
        print("empty chain — nothing promoted yet.")
        return
    prev = "GENESIS"
    for i, line in enumerate(LOG.read_text(encoding="utf-8").strip().splitlines(), 1):
        e = json.loads(line)
        want = hashlib.sha256((prev + e["sha256"]).encode()).hexdigest()
        if e["prev"] != prev or e["chain"] != want:
            raise SystemExit(f"CHAIN BROKEN at entry {i}: {e['file']}")
        prev = e["chain"]
    print(f"chain intact: {i} entries, head {prev[:16]}…")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--verify":
        verify()
    elif len(sys.argv) == 2:
        promote(sys.argv[1])
    else:
        print(__doc__)
