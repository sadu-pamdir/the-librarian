# The Librarian

**A specification for sovereign, auditable, navigation-first AI.**

The model never invents facts. It navigates to them — in a library you own, offline, with every answer citing file and section.

## Why

LLMs hallucinate because generating plausible text is their architecture, not their bug.
The fix isn't a bigger model. It's a different job description:
**the model is the interface to knowledge, never the source of record.**

## What this is

- 📜 A **specification** ([`spec/SPEC.md`](spec/SPEC.md)) for integrating five proven components:
  1. Offline knowledge archives (ZIM / kiwix-serve)
  2. Model Context Protocol (MCP) access
  3. A compiled, cross-linked Markdown wiki ("LLM wiki" pattern)
  4. A single deterministic index layer (`knowledge-map.md`)
  5. OpenAPI vendor contracts + a **two-tenant quarantine** (online sandbox → reviewed, hashed promotion → offline master)
- 🛠 A **reference implementation** (in progress) targeting a single machine — no cloud required.
- 📝 An **essay** on the design philosophy (linked).

## What this is not

- Not a new model, not a new RAG paper, not a product.
- Not a claim that the components are novel — see [Related Work](#related-work). The contribution is the integration contract and the sovereignty guarantees.

## Design principles

1. Navigate, don't generate.
2. The source of record is a file you own.
3. Quarantine before trust.
4. Compile once, answer cheaply (two file reads, no mandatory vector DB).
5. Fully functional offline.

## Related work

WikiChat (Stanford) · RAG (Lewis et al. 2020) · Kiwix/openZIM + existing ZIM MCP servers · Karpathy's LLM-wiki pattern · TreeSLS (SOSP '23). Standing on all of these shoulders, deliberately.

## Status

Spec: draft v0.1 — open for issues and tear-downs.
Reference implementation: C1–C4 loop, single-machine, coming first.

## License

MIT. Take it, build it, sell it, improve it — attribution appreciated, not required.
