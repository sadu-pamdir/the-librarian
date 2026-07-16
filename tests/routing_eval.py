#!/usr/bin/env python3
"""Routing evaluation for the librarian answer path — v0.2 (refuted wing).

Categories:
  A refuted-hit      paraphrases of seeded refuted claims -> status must be "refuted"
  B compiled-hit     paraphrases of compiled topics       -> status must be "compiled"
  C pair-split       chakra measurement vs. map phrasing  -> correct wing of the pair
  D false-positive   near-miss probes                     -> must NOT be "refuted"
  E archive          general knowledge, not compiled      -> "archive" (kiwix up) or "unsourced"
  F nonsense         garbage/underspecified               -> must NOT be "refuted" or "compiled"

Run:  python3 tests/routing_eval.py            (needs kiwix-serve for full E marks;
                                                E passes with "unsourced" too, noted)
Stdlib only, like everything here.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "librarian"))
from librarian import ask  # noqa: E402

R, C, A = "refuted", "compiled", "archive"

# (category, question, rule)
# rule: "refuted" -> status==refuted; "compiled:<page>" -> status==compiled & page in citation
#       "not-refuted" -> status != refuted; "archive-or-unsourced" -> status in {archive, unsourced}
#       "refuted:<page>" -> refuted & page in citation
CASES = [
    # ---- A: refuted hits — MMR/autism (10)
    ("A", "Does the MMR vaccine cause autism?", "refuted:mmr-vaccine-autism"),
    ("A", "Is there a link between MMR vaccine and autism?", "refuted:mmr-vaccine-autism"),
    ("A", "MMR vaccine autism connection", "refuted:mmr-vaccine-autism"),
    ("A", "did wakefield prove the mmr vaccine causes autism", "refuted:mmr-vaccine-autism"),
    ("A", "vaccine causes autism true or false", "refuted:mmr-vaccine-autism"),
    ("A", "Can the MMR jab give my child autism?", "refuted:mmr-vaccine-autism"),
    ("A", "autism caused by MMR vaccination?", "refuted:mmr-vaccine-autism"),
    ("A", "is the mmr autism study real", "refuted:mmr-vaccine-autism"),
    ("A", "Verursacht die MMR Impfung Autismus?", "refuted:mmr-vaccine-autism"),
    ("A", "MMR Autismus Zusammenhang bewiesen?", "refuted:mmr-vaccine-autism"),
    # ---- A: refuted hits — 2+2=5 (10)
    ("A", "is 2 plus 2 equal to 5?", "refuted:two-plus-two-equals-five"),
    ("A", "does 2 plus 2 equal 5", "refuted:two-plus-two-equals-five"),
    ("A", "2 plus 2 equals 5 proof", "refuted:two-plus-two-equals-five"),
    ("A", "can 2 plus 2 be 5 in any system", "refuted:two-plus-two-equals-five"),
    ("A", "why do people say 2 plus 2 equals 5", "refuted:two-plus-two-equals-five"),
    ("A", "2 + 2 = 5 ever true?", "refuted:two-plus-two-equals-five"),
    ("A", "orwell said 2 plus 2 equals 5, is it true", "refuted:two-plus-two-equals-five"),
    ("A", "ist 2 plus 2 gleich 5", "refuted:two-plus-two-equals-five"),
    ("A", "prove that 2 plus 2 equals 5", "refuted:two-plus-two-equals-five"),
    ("A", "2 plus 2 equals 5 or 4", "refuted:two-plus-two-equals-five"),
    # ---- A: refuted/unsupported — chakras as anatomy (10)
    ("A", "are chakras measurable anatomy organs?", "refuted:chakras-as-measurable-anatomy"),
    ("A", "can you measure chakras with instruments, anatomy proof?", "refuted:chakras-as-measurable-anatomy"),
    ("A", "chakras measurable anatomical structures evidence", "refuted:chakras-as-measurable-anatomy"),
    ("A", "do chakras exist as physical measurable organs", "refuted:chakras-as-measurable-anatomy"),
    ("A", "chakras anatomy dissection organs found?", "refuted:chakras-as-measurable-anatomy"),
    ("A", "has science found measurable chakras in anatomy", "refuted:chakras-as-measurable-anatomy"),
    ("A", "sind chakras messbare organe anatomy", "refuted:chakras-as-measurable-anatomy"),
    ("A", "chakras as measurable organs in the body", "refuted:chakras-as-measurable-anatomy"),
    ("A", "measurable chakra anatomy scientific evidence", "refuted:chakras-as-measurable-anatomy"),
    ("A", "physically measurable chakras organs yes or no", "refuted:chakras-as-measurable-anatomy"),
    # ---- B: compiled hits (20)
    ("B", "Wie funktioniert die Photosynthese?", "compiled:photosynthese"),
    ("B", "Photosynthese einfach erklaert", "compiled:photosynthese"),
    ("B", "Was passiert bei der Photosynthese in Pflanzen?", "compiled:photosynthese"),
    ("B", "Photosynthese Chlorophyll Licht", "compiled:photosynthese"),
    ("B", "Erklaere Photosynthese", "compiled:photosynthese"),
    ("B", "photosynthese und zucker", "compiled:photosynthese"),
    ("B", "Wie wandelt Photosynthese Licht um?", "compiled:photosynthese"),
    ("B", "Was ist Photovoltaik?", "compiled:photovoltaik"),
    ("B", "Photovoltaik Anlage wie funktioniert das", "compiled:photovoltaik"),
    ("B", "Photovoltaik Solarzellen Strom", "compiled:photovoltaik"),
    ("B", "Photovoltaik Wirkungsgrad", "compiled:photovoltaik"),
    ("B", "Strom aus Photovoltaik erklaert", "compiled:photovoltaik"),
    ("B", "Photovoltaik auf dem Dach sinnvoll?", "compiled:photovoltaik"),
    ("B", "what do the chakra traditions describe as an experiential map?", "compiled:chakras-experiential-map"),
    ("B", "chakras experiential map meaning", "compiled:chakras-experiential-map"),
    ("B", "chakra system as map of experience traditions", "compiled:chakras-experiential-map"),
    ("B", "experiential map chakras yoga traditions", "compiled:chakras-experiential-map"),
    ("B", "chakras across traditions experiential", "compiled:chakras-experiential-map"),
    ("B", "is the chakra map attested in several traditions", "compiled:chakras-experiential-map"),
    ("B", "chakras as experiential map not anatomy", "compiled:chakras-experiential-map"),
    # ---- C: pair split (14) — measurement phrasing -> refuted wing; map phrasing -> compiled
    ("C", "chakras measurable organs", "refuted:chakras-as-measurable-anatomy"),
    ("C", "chakra anatomy measurable", "refuted:chakras-as-measurable-anatomy"),
    ("C", "measure chakras anatomy", "refuted:chakras-as-measurable-anatomy"),
    ("C", "chakras organs anatomy", "refuted:chakras-as-measurable-anatomy"),
    ("C", "anatomical chakras measurable proof", "refuted:chakras-as-measurable-anatomy"),
    ("C", "chakras physical organs measurable science", "refuted:chakras-as-measurable-anatomy"),
    ("C", "measurable anatomy of chakras", "refuted:chakras-as-measurable-anatomy"),
    ("C", "chakras experiential map", "compiled:chakras-experiential-map"),
    ("C", "chakra traditions map", "compiled:chakras-experiential-map"),
    ("C", "experiential chakra map traditions", "compiled:chakras-experiential-map"),
    ("C", "chakras map of experience", "compiled:chakras-experiential-map"),
    ("C", "chakra map across traditions", "compiled:chakras-experiential-map"),
    ("C", "chakras traditions experiential meaning", "compiled:chakras-experiential-map"),
    ("C", "map chakras traditions coherent", "compiled:chakras-experiential-map"),
    # ---- D: false-positive probes (25) — must NOT land in the refuted wing
    ("D", "how do vaccines work?", "not-refuted"),
    ("D", "what vaccines does a child need", "not-refuted"),
    ("D", "history of vaccination", "not-refuted"),
    ("D", "what causes autism research overview", "not-refuted"),
    ("D", "autism early signs in children", "not-refuted"),
    ("D", "measles symptoms and treatment", "not-refuted"),
    ("D", "is the flu vaccine effective", "not-refuted"),
    ("D", "covid vaccine side effects", "not-refuted"),
    ("D", "what is 2 plus 2", "not-refuted"),
    ("D", "is 3 plus 4 equal to 7", "not-refuted"),
    ("D", "what is 5 times 5", "not-refuted"),
    ("D", "why does 1 plus 1 equal 2", "not-refuted"),
    ("D", "peano axioms explained", "not-refuted"),
    ("D", "basic arithmetic for kids", "not-refuted"),
    ("D", "what are human organs", "not-refuted"),
    ("D", "anatomy of the heart", "not-refuted"),
    ("D", "organ donation how does it work", "not-refuted"),
    ("D", "yoga for beginners", "not-refuted"),
    ("D", "meditation techniques overview", "not-refuted"),
    ("D", "kundalini yoga practice", "not-refuted"),
    ("D", "energy consumption of the human body", "not-refuted"),
    ("D", "measurable outcomes in physiotherapy", "not-refuted"),
    ("D", "how to measure blood pressure", "not-refuted"),
    ("D", "wakefield town england", "not-refuted"),
    ("D", "lancet medical journal history", "not-refuted"),
    # ---- E: archive layer (15)
    ("E", "Wer war Albert Einstein?", "archive-or-unsourced"),
    ("E", "Doppelspaltexperiment", "archive-or-unsourced"),
    ("E", "Hauptstadt der Schweiz", "archive-or-unsourced"),
    ("E", "Was ist Quantenmechanik?", "archive-or-unsourced"),
    ("E", "Geschichte der Bibliothek von Alexandria", "archive-or-unsourced"),
    ("E", "Jorge Luis Borges Schriftsteller", "archive-or-unsourced"),
    ("E", "Was ist Hypnose?", "archive-or-unsourced"),
    ("E", "Poincare Wiederkehrsatz", "archive-or-unsourced"),
    ("E", "Conway Game of Life", "archive-or-unsourced"),
    ("E", "Georg Cantor Unendlichkeit", "archive-or-unsourced"),
    ("E", "EUV Lithographie ASML", "archive-or-unsourced"),
    ("E", "Karl Popper Falsifikation", "archive-or-unsourced"),
    ("E", "Retraction wissenschaftliche Publikation", "archive-or-unsourced"),
    ("E", "Placebo Effekt Studien", "archive-or-unsourced"),
    ("E", "Intuition Entscheidungsforschung", "archive-or-unsourced"),
    # ---- F: nonsense / underspecified (10)
    ("F", "blorp fizzle quantum banana", "not-refuted-not-compiled"),
    ("F", "xyzzy plugh", "not-refuted-not-compiled"),
    ("F", "asdf qwer zxcv", "not-refuted-not-compiled"),
    ("F", "purple monday sings loudly", "not-refuted-not-compiled"),
    ("F", "?", "not-refuted-not-compiled"),
    ("F", "hmm", "not-refuted-not-compiled"),
    ("F", "tell me something", "not-refuted-not-compiled"),
    ("F", "wibble wobble wubble", "not-refuted-not-compiled"),
    ("F", "gleep glorp", "not-refuted-not-compiled"),
    ("F", "zzz zzz zzz", "not-refuted-not-compiled"),
]


def check(rule: str, status: str, citation: str) -> bool:
    if rule.startswith("refuted:"):
        return status == "refuted" and rule.split(":", 1)[1] in citation
    if rule.startswith("compiled:"):
        return status == "compiled" and rule.split(":", 1)[1] in citation
    if rule == "not-refuted":
        return status != "refuted"
    if rule == "not-refuted-not-compiled":
        return status not in ("refuted", "compiled")
    if rule == "archive-or-unsourced":
        return status in ("archive", "unsourced")
    raise ValueError(rule)


def main() -> None:
    per_cat: dict[str, list[tuple[bool, str, str, str]]] = {}
    for cat, q, rule in CASES:
        ans = ask(q)
        ok = check(rule, ans.status, ans.citation)
        per_cat.setdefault(cat, []).append((ok, q, rule, ans.status + " | " + ans.citation[:70]))

    total = passed = 0
    names = {"A": "refuted-hit", "B": "compiled-hit", "C": "pair-split",
             "D": "false-positive probes", "E": "archive layer", "F": "nonsense"}
    print(f"{'cat':<4}{'name':<24}{'pass':>6}{'total':>7}")
    for cat in sorted(per_cat):
        rows = per_cat[cat]
        p = sum(1 for ok, *_ in rows if ok)
        total += len(rows); passed += p
        print(f"{cat:<4}{names[cat]:<24}{p:>6}{len(rows):>7}")
    print(f"{'':<4}{'TOTAL':<24}{passed:>6}{total:>7}   ({passed/total:.1%})")

    fails = [(c, q, r, got) for c, rows in per_cat.items() for ok, q, r, got in rows if not ok]
    if fails:
        print("\nFAILURES:")
        for c, q, r, got in fails:
            print(f"  [{c}] {q!r}\n      expected {r} — got {got}")


if __name__ == "__main__":
    main()
