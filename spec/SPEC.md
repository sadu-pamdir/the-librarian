# The Librarian: A Specification for Sovereign, Auditable, Navigation-First AI

**Sadu Pamdir** · Independent Researcher, Switzerland · Draft v0.2 · License: MIT (spec) / CC BY 4.0 (text)

## Abstract

Large language models answer by predicting plausible text, which makes them eloquent and unreliable in the same breath. This paper specifies an alternative operating mode we call *the Librarian*: the model never serves as the source of facts, only as the interface to a locally held, versioned, auditable library. The specification integrates five existing, individually proven components: offline knowledge archives (ZIM/Kiwix), the Model Context Protocol (MCP), a compile-step that turns raw sources into a cross-referenced Markdown wiki with a single index layer, machine-readable vendor contracts (OpenAPI), and a two-tenant quarantine that separates a volatile online sandbox from an immutable offline master. None of these components is novel. The contribution is the integration contract between them, and a design philosophy: navigation instead of generation, sources instead of confidence, local sovereignty instead of cloud dependency. We describe the architecture, its auditability and privacy properties, its limitations, and a reference-implementation roadmap.

Version 0.2 extends the library in one direction the literature mostly ignores: **the known-false**. A library that only holds the true loses the refutation with every refuted claim. We add a claim catalog with typed claims (formal, empirical, experiential, interpretive), a *refuted wing* that makes documented falsehoods first-class, citable answers, and a clarifying-interview step in which the librarian asks before it routes.

## 1. Problem

Two failure modes dominate practical LLM deployment:

1. **Hallucination as an architectural property.** A model asked for a Cisco configuration or a legal deadline produces *likely* text. Retrieval-augmented generation reduces this but typically still lets the model paraphrase sources it fetched from a live, mutable web.
2. **Sovereignty loss as a default.** The knowledge, the retrieval index, and the interaction logs usually live with a cloud provider. For European SMEs under GDPR/revDSG this is not a detail; it decides whether a system may process client data at all. The February 2025 shutdown of the Humane AI Pin (devices rendered inoperable when the vendor's cloud disappeared) is the canonical warning: an assistant whose knowledge lives elsewhere dies with its vendor.

## 2. Related work (what already exists)

This spec builds on, and must be honest about, substantial prior art:

- **Grounded chat over Wikipedia.** WikiChat (Semnani et al., EMNLP 2023) demonstrated few-shot grounding on Wikipedia with 97.3 % factual accuracy on tail topics, evidence that navigation-first beats generation-first for factuality.
- **Retrieval-augmented generation** as a family of methods (Lewis et al., 2020) is standard practice.
- **Offline knowledge archives.** The Kiwix/openZIM ecosystem ships the full text of Wikipedia in the tens of gigabytes; MCP servers for ZIM archives already exist (kiwix-wiki-mcp-server, openzim-mcp).
- **Compiled knowledge.** Andrej Karpathy's "LLM wiki" pattern (pre-compiling sources into interlinked, LLM-friendly Markdown) has multiple community implementations.
- **In-memory and single-level-store research.** TreeSLS (SOSP 2023) demonstrates whole-system persistence on a single-level store; processing-in-memory is a mature research field motivated by data-movement energy: Boroumand et al. (ASPLOS 2018) measured that data movement accounts for 62.7 % of total system energy across Google *consumer-device* workloads.

**Novelty claim, stated precisely:** not the components, but (a) the *integration contract*: offline ZIM + MCP + compiled wiki + two-tenant quarantine + OpenAPI grounding, specified as one coherent, self-hostable system with end-to-end source attribution; and (b) the design philosophy that the model is *never* the source of record.

## 3. Design principles

1. **Navigate, don't generate.** For factual queries the model's job is routing: question → index → source passage → cited answer. Free generation is reserved for synthesis and explicitly labeled.
2. **The source of record is a file you own.** Every answer must be traceable to an immutable local artifact (ZIM archive, OpenAPI spec, compiled wiki page): byte-addressable, versioned, diffable.
3. **Quarantine before trust.** Nothing enters the master tenant unreviewed. Online material lands in a sandbox tenant; promotion to the offline master is an explicit, logged act.
4. **Compile once, answer cheaply.** Ingestion is a deliberate compile step, not per-query scraping. Answering reads an index file and one page; no vector database is required for the core loop.
5. **Degrade gracefully offline.** The system's full factual competence must be available with zero network.
6. **Honest in both directions** *(v0.2)*. Knowing that a claim is false is knowledge, often more expensively won than the true claim beside it. A documented falsehood is a first-class answer ("refuted, by this source"), never a silent miss.
7. **Ask before you route** *(v0.2)*. For ambiguous or consequential questions the librarian interviews the user first: one question at a time, with a recommendation, resolving only what the library itself cannot resolve. The same discipline applies at the promotion gate, where the *source* is interrogated.

## 4. Architecture

### 4.1 Components

| # | Component | Role | Existing building block |
|---|---|---|---|
| C1 | **Archive layer** | Immutable knowledge bodies | ZIM files served by `kiwix-serve` (full English Wikipedia text ≈ tens of GB) |
| C2 | **Protocol layer** | Tool access for the model | MCP servers over C1 (existing kiwix/openzim MCP implementations) |
| C3 | **Compiled wiki** | Curated, task-oriented knowledge | Karpathy-style LLM wiki: one topic per Markdown page, frontmatter summary, cross-links |
| C4 | **Index layer** | Deterministic routing | A single human-readable `knowledge-map.md`; the model reads the map, then exactly one page |
| C5 | **Contract layer** | Machine-precise vendor knowledge | OpenAPI specifications where vendors publish them (e.g., Cisco Catalyst Center Intent API); the model draws syntax from the spec, not from parametric memory |
| C6 | **Two-tenant boundary** | Trust management | Sandbox tenant (online, volatile, quarantined) → reviewed promotion → master tenant (offline, immutable, signed) |
| C7 | **Refuted wing** *(v0.2)* | Documented falsehoods as first-class results | A filtered view over the claim catalog (§4.4); implemented as `compiled-wiki/refuted/` pages routed by the same knowledge-map |

### 4.2 The answer path

```
User intent
   → (clarify: interview if ambiguous or consequential — v0.2)
   → C4 knowledge-map (routes against BOTH wings)
   → C3 compiled page ─ or ─ C7 refuted page ("documented falsehood, refuted by …")
        └ if missing ─→ C2/C1 archive lookup ─ if missing ─→ C6 sandbox (online, quarantined)
   → answer with citation (file + section)
   → optional: promotion proposal sandbox → master (human-approved, logged)
```

Every hop is logged. An answer without a resolvable citation is delivered as *unsourced synthesis*, visibly labeled. A hit in the refuted wing is a first-class result, not a failure mode.

### 4.3 Integrity

Promoted artifacts are hashed (SHA-256) and chained; the promotion log is append-only. (This mirrors requirements the Swiss GeBüV places on business records and reuses a pattern already implemented in our accounting pipeline.)

### 4.4 The claim catalog and the refuted wing (v0.2)

Libraries have always tried to hold the known-true; the known-false was left to scattered errata. Borges' total library fails precisely because its librarians cannot tell the two apart. We make the distinction a data structure.

**The catalog holds claims, not topics.** "Hypnosis" is not an entry; "hypnosis reduces surgical pain" is. Every claim page declares:

```yaml
claim: "The claim, verbatim"
type: formal | empirical | experiential | interpretive
status: proven | supported | effective-unexplained | attested | open |
        disputed | unsupported | refuted
refuted-by / evidence: source with date, file + section
paired-with: complement page, if any
last-checked: YYYY-MM-DD
```

**Claim types and their standards.** A *formal* claim is judged by proof (2 + 2 = 5: refuted — the hardest status). An *empirical* claim is judged by studies and reproduction ("the MMR vaccine causes autism": refuted — Lancet full retraction 2010, Taylor et al. 2014). An *experiential* claim is judged by documented practice under stated conditions (expert intuition: supported *within* domains that give fast, reliable feedback — Kahneman & Klein 2009). An *interpretive* claim is a map, not a territory, judged by coherence and usefulness ("attested", deliberately weaker than "supported").

**Type-relative judgment, with an anti-abuse rule.** A claim may only be refuted within its own type — but the moment a claim prescribes action in the physical world (healing, measurable effect, prediction), it *is* empirical, whatever its label; re-labeling after refutation is prohibited and logged. This single rule blocks the classic escape route of pseudoscience without letting the empirical standard colonize maps that never claimed to be territory.

**Complement pairs.** One word often carries two claims. "Chakras as measurable anatomy" (empirical: unsupported) and "chakras as an experiential map used across traditions" (interpretive: attested) are two honest entries that reference each other — a measurement waiting for a meaning, a meaning waiting for a measurement. Convergence across traditions is treated as a *prioritization signal* (worth looking here), never as proof: geocentrism converged for millennia. Where a claim carries both empirical support and convergent interpretation, the pair may be marked a *convergence point* — the catalog's strongest, and rarest, annotation.

**The refuted wing is a view, not a second store.** `refuted/` is the filtered set of claims whose status is refuted/unsupported/outdated, routed by the same knowledge-map. One catalog, one truth administration, honest in both directions.

## 5. Properties

- **Auditability:** every factual sentence resolves to file + section in an immutable local artifact.
- **Sovereignty:** the full loop (archive, index, model, logs) runs on hardware the operator owns; compliant-by-design for GDPR/revDSG contexts.
- **Energy/cost:** the core loop is two file reads; no per-query embedding search is required. (Vector search may be added as an *optional* recall layer, never as the source of record.)
- **Longevity:** knowledge survives vendor death; ZIM archives from a decade ago still open today.
- **Bidirectional honesty** *(v0.2)*: the system can say "this is documented as false, refuted by X" with the same auditability as any positive answer — a capability plain RAG over the known-true cannot express.

## 6. Outlook (position, not claim)

Two convergence theses motivate where this spec wants to run eventually. We state them as positions:

1. **Memory-centric hardware.** Single-level stores (TreeSLS), processing-in-memory, and unified memory are converging toward machines where the historical RAM/storage split disappears. Uncompressed weights of a 1.2-trillion-parameter model occupy ≈ 2.4 TB in BF16, feasible on today's high-capacity portable storage, though a true PIM "stick" does not exist yet; current memristor arrays are lab-scale.
2. **Ambient form factor.** Retinal-projection wearables are real (TDK's 0.35 g full-color laser modules; QD Laser's RETISSA line) but honest numbers matter: microwatts describes optical power at the eye, while shipping DRP systems draw on the order of 6 W of system power. On-device visual-memory wearables (Project LUCI, CES 2026) show the direction. The Librarian is the software such a device needs: local, sourced, quiet.

## 7. Limitations

- The compile step (C3) needs curation; garbage compiled is garbage cited.
- ZIM snapshots lag live Wikipedia; the two-tenant design makes this explicit rather than hiding it.
- OpenAPI coverage is limited to what vendors publish; CLI handbooks remain semi-structured.
- The spec does not solve alignment or reasoning quality; it constrains *where facts come from*, not *how well the model thinks*.
- **v0.2 limitations:** the refuted wing doubles the curation duty — an empty or stale negative wing is worse than none, because it implies exhaustiveness it does not have. `last-checked` makes status drift visible but does not prevent it; a review rhythm is an operational requirement, not a data structure. Assigning claim types can itself be contested; the anti-abuse rule covers the dangerous direction (physical-world claims escaping the empirical standard), while the remaining edge cases require the same human adjudication as promotion.
- **First measurements (reference implementation, Apple M4 Max, 07/2026):** with four live ZIM archives served by kiwix-serve, including the complete German Wikipedia (~14 GB, 2026-01) and the complete English Wikipedia (~49 GB, 2026-06) for ~63 GB total, the full answer path returns in **30-50 ms** on the compiled route (knowledge-map -> page) and **50-60 ms** on the archive route (search -> fetch -> extract), *including* Python interpreter startup, on a dependency-free stdlib implementation. Latency did not degrade when moving from ~2 GB test archives to the full 63 GB corpus. This substantiates the "two file reads" cost claim; broader benchmarks (recall quality, curation effort) remain open. **v0.2 addendum (07/2026):** the refuted wing is implemented and seeded (three claims, one complement pair). A 114-case routing evaluation (`tests/routing_eval.py`: 30 refuted paraphrases incl. German, 20 compiled, 14 pair-splits, 25 false-positive probes, 15 archive, 10 nonsense) passes **111/114 (97.4 %)** with zero false negatives; refuted rows require ≥ 2 overlapping keywords so a single generic word cannot trigger the falsehood label. The three residual failures are false positives on semantically adjacent questions ("what causes autism…", "what is 2 plus 2") — the documented limit of deterministic keyword routing, owned by the clarify step (principle 7) or an optional recall layer, not hidden by it.

## References

*(Full list with links in the Rex audit file; to be formatted for publication.)* Semnani et al. 2023 (WikiChat, arXiv:2305.14292) · Lewis et al. 2020 (RAG) · Boroumand et al. 2018 (ASPLOS, consumer-workload energy) · TreeSLS, SOSP 2023 · Kantamneni & Tegmark 2025 (arXiv:2502.00873) · Kiwix/openZIM project · Cisco DevNet Catalyst Center API · TDK press 2022/2024 · QD Laser RETISSA · Moravec 1988 · von der Malsburg (binding-by-synchrony). *v0.2:* Popper 1959 (falsification) · The Lancet 2010 (retraction of Wakefield et al. 1998) · Taylor, Swerdfeger & Eslick 2014 (Vaccine, meta-analysis) · Kahneman & Klein 2009 (Am. Psychologist, conditions for expert intuition) · Borges 1939/1941 (The Total Library / The Library of Babel) · Retraction Watch.

## Changelog

- **v0.2 (2026-07-16):** claim catalog with typed claims (§4.4), refuted wing as component C7 with first-class routing, complement pairs and convergence points, anti-abuse rule, clarifying-interview step (principles 6-7), reference implementation seeded and tested. Concept red-team-reviewed before drafting (10 findings incorporated, including the anti-abuse rule and the demotion of convergence from proof to prioritization signal).
- **v0.1 (2026-07-08):** initial specification, published (DOI 10.5281/zenodo.21269197).

## Acknowledgments

Written in collaboration with Claude (Fable 5, Anthropic) as a hands-on assistant. The direction, the decisions and the remaining errors are the author's.
