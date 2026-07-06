# The Librarian: A Specification for Sovereign, Auditable, Navigation-First AI

**Sadu Pamdir** — Independent Researcher, Switzerland · Draft v0.1 · License: MIT (spec) / CC BY 4.0 (text)

## Abstract

Large language models answer by predicting plausible text, which makes them eloquent and unreliable in the same breath. This paper specifies an alternative operating mode we call *the Librarian*: the model never serves as the source of facts, only as the interface to a locally held, versioned, auditable library. The specification integrates five existing, individually proven components — offline knowledge archives (ZIM/Kiwix), the Model Context Protocol (MCP), a compile-step that turns raw sources into a cross-referenced Markdown wiki with a single index layer, machine-readable vendor contracts (OpenAPI), and a two-tenant quarantine that separates a volatile online sandbox from an immutable offline master. None of these components is novel. The contribution is the integration contract between them, and a design philosophy: navigation instead of generation, sources instead of confidence, local sovereignty instead of cloud dependency. We describe the architecture, its auditability and privacy properties, its limitations, and a reference-implementation roadmap.

## 1. Problem

Two failure modes dominate practical LLM deployment:

1. **Hallucination as an architectural property.** A model asked for a Cisco configuration or a legal deadline produces *likely* text. Retrieval-augmented generation reduces this but typically still lets the model paraphrase sources it fetched from a live, mutable web.
2. **Sovereignty loss as a default.** The knowledge, the retrieval index, and the interaction logs usually live with a cloud provider. For European SMEs under GDPR/revDSG this is not a detail; it decides whether a system may process client data at all. The February 2025 shutdown of the Humane AI Pin — devices rendered inoperable when the vendor's cloud disappeared — is the canonical warning: an assistant whose knowledge lives elsewhere dies with its vendor.

## 2. Related work (what already exists)

This spec builds on, and must be honest about, substantial prior art:

- **Grounded chat over Wikipedia.** WikiChat (Semnani et al., EMNLP 2023) demonstrated few-shot grounding on Wikipedia with 97.3 % factual accuracy on tail topics — evidence that navigation-first beats generation-first for factuality.
- **Retrieval-augmented generation** as a family of methods (Lewis et al., 2020) is standard practice.
- **Offline knowledge archives.** The Kiwix/openZIM ecosystem ships the full text of Wikipedia in the tens of gigabytes; MCP servers for ZIM archives already exist (kiwix-wiki-mcp-server, openzim-mcp).
- **Compiled knowledge.** Andrej Karpathy's "LLM wiki" pattern — pre-compiling sources into interlinked, LLM-friendly Markdown — has multiple community implementations.
- **In-memory and single-level-store research.** TreeSLS (SOSP 2023) demonstrates whole-system persistence on a single-level store; processing-in-memory is a mature research field motivated by data-movement energy: Boroumand et al. (ASPLOS 2018) measured that data movement accounts for 62.7 % of total system energy across Google *consumer-device* workloads.

**Novelty claim, stated precisely:** not the components, but (a) the *integration contract* — offline ZIM + MCP + compiled wiki + two-tenant quarantine + OpenAPI grounding specified as one coherent, self-hostable system with end-to-end source attribution; and (b) the design philosophy that the model is *never* the source of record.

## 3. Design principles

1. **Navigate, don't generate.** For factual queries the model's job is routing: question → index → source passage → cited answer. Free generation is reserved for synthesis and explicitly labeled.
2. **The source of record is a file you own.** Every answer must be traceable to an immutable local artifact (ZIM archive, OpenAPI spec, compiled wiki page) — byte-addressable, versioned, diffable.
3. **Quarantine before trust.** Nothing enters the master tenant unreviewed. Online material lands in a sandbox tenant; promotion to the offline master is an explicit, logged act.
4. **Compile once, answer cheaply.** Ingestion is a deliberate compile step, not per-query scraping. Answering reads an index file and one page — no vector database required for the core loop.
5. **Degrade gracefully offline.** The system's full factual competence must be available with zero network.

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

### 4.2 The answer path

```
User intent
   → C4 knowledge-map (route)
   → C3 compiled page  ─ if missing ─→ C2/C1 archive lookup ─ if missing ─→ C6 sandbox (online, quarantined)
   → answer with citation (file + section)
   → optional: promotion proposal sandbox → master (human-approved, logged)
```

Every hop is logged. An answer without a resolvable citation is delivered as *unsourced synthesis* — visibly labeled.

### 4.3 Integrity

Promoted artifacts are hashed (SHA-256) and chained; the promotion log is append-only. (This mirrors requirements the Swiss GeBüV places on business records and reuses a pattern already implemented in our accounting pipeline.)

## 5. Properties

- **Auditability:** every factual sentence resolves to file + section in an immutable local artifact.
- **Sovereignty:** the full loop — archive, index, model, logs — runs on hardware the operator owns; compliant-by-design for GDPR/revDSG contexts.
- **Energy/cost:** the core loop is two file reads; no per-query embedding search is required. (Vector search may be added as an *optional* recall layer, never as the source of record.)
- **Longevity:** knowledge survives vendor death; ZIM archives from a decade ago still open today.

## 6. Outlook (position, not claim)

Two convergence theses motivate where this spec wants to run eventually. We state them as positions:

1. **Memory-centric hardware.** Single-level stores (TreeSLS), processing-in-memory, and unified memory are converging toward machines where the historical RAM/storage split disappears. Uncompressed weights of a 1.2-trillion-parameter model occupy ≈ 2.4 TB in BF16 — feasible on today's high-capacity portable storage, though a true PIM "stick" does not exist yet; current memristor arrays are lab-scale.
2. **Ambient form factor.** Retinal-projection wearables are real (TDK's 0.35 g full-color laser modules; QD Laser's RETISSA line) but honest numbers matter: microwatts describes optical power at the eye, while shipping DRP systems draw on the order of 6 W of system power. On-device visual-memory wearables (Project LUCI, CES 2026) show the direction. The Librarian is the software such a device needs: local, sourced, quiet.

## 7. Limitations

- The compile step (C3) needs curation; garbage compiled is garbage cited.
- ZIM snapshots lag live Wikipedia; the two-tenant design makes this explicit rather than hiding it.
- OpenAPI coverage is limited to what vendors publish; CLI handbooks remain semi-structured.
- The spec does not solve alignment or reasoning quality; it constrains *where facts come from*, not *how well the model thinks*.
- No implementation is benchmarked yet — this document is a specification with a reference implementation in progress. *(TODO: replace with repo link + first measurements before publishing.)*

## References

*(Full list with links in the Rex audit file; to be formatted for publication.)* Semnani et al. 2023 (WikiChat, arXiv:2305.14292) · Lewis et al. 2020 (RAG) · Boroumand et al. 2018 (ASPLOS, consumer-workload energy) · TreeSLS, SOSP 2023 · Kantamneni & Tegmark 2025 (arXiv:2502.00873) · Kiwix/openZIM project · Cisco DevNet Catalyst Center API · TDK press 2022/2024 · QD Laser RETISSA · Moravec 1988 · von der Malsburg (binding-by-synchrony).

