---
name: nvidia-ckg-skill
description: "Use for structured knowledge retrieval: listing CKG domains, searching concepts, querying concept subgraphs, and multi-hop traversal. Not for general web search or unstructured document retrieval."
license: MIT
permissions:
  - "shell: run the bundled scripts/, basic file utilities (mkdir, cd, cp), and install runtime Python packages"
  - "network: HTTPS to graphifymd.com (CaaS API) and PyPI"
  - "env: read environment variables including CKG_API_KEY and load a project .env file"
  - "file_read: read CKG .md files from a local directory and user-specified paths"
  - "file_write: write traversal outputs and query results to user-specified paths"
metadata:
  short-description: "CKG domain traversal and concept search"
  author: "Graphify.md / Daniel Yarmoluk"
  tags:
    - ckg
    - knowledge-graph
    - retrieval
    - agents
    - nvidia
---

# NVIDIA CKG Skill

## Purpose

Use this skill when an agent needs to retrieve structured, declarative knowledge from a CKG (Compact Knowledge Graph): listing available domains, searching for a concept by name, querying a concept's neighbors and edges, or traversing multi-hop dependency chains.

Do not use it for general web search, unstructured document retrieval, or RAG over raw text. CKGs are traversed, not searched — each result is a declared relationship, not an inference.

## What Is a CKG

A CKG is a typed, directed knowledge graph stored as a structured markdown file. Each node is a named concept with a type (Concept, API, Tool, Platform, SDK, Algorithm, Standard, Workflow) and a precise description. Each edge is a named relation (ENABLES, REQUIRES, EXTENDS, IMPLEMENTS, OPTIMIZES, WRAPS, CONFIGURES, MONITORS, REPLACES, USED_IN, PART_OF, VALIDATES, GENERATES, CONSUMES). The graph doesn't guess — it traverses. Every result is a declared edge, not a probabilistic inference.

Key stats: 11× token compression vs RAG · F1 0.471 vs RAG 0.123 · 5-hop F1 0.772 vs 0.170 (ckg-benchmark v0.6.2).

## Inputs

| Input | Required | Description |
|---|---|---|
| Domain name | Yes for most workflows | Exact domain slug (e.g. `cuda-toolkit`, `nvidia-developer-ecosystem`). Run `list_domains` first if unsure. |
| Concept ID | For query/traverse | snake_case node ID within the domain (e.g. `tensorrt_sdk`, `cuda_toolkit`). |
| `CKG_PATH` env var | For local mode | Path to directory containing CKG .md files. Defaults to `~/Desktop/Knowledge_Graph_Graphify`. |
| `CKG_API_KEY` env var | For Pro domains | CaaS API key for Pro-gated domains. Get at graphifymd.com/caas. |

## Prerequisites

- Run commands from the skill directory unless a workflow specifies otherwise.
- Set `CKG_PATH` to the directory containing your local CKG .md files, or omit to use the default.
- For Pro-gated domains (24 premium domains), set `CKG_API_KEY` before querying.
- Never print or log `CKG_API_KEY`.

## Runtime Dependencies

```bash
if command -v uv >/dev/null 2>&1; then
  uv pip install rich python-dotenv requests
else
  python -m pip install rich python-dotenv requests
fi
```

## Workflows

### List Domains
```bash
python ./scripts/list_domains.py [--filter KEYWORD] [--path DIR]
```
Lists all CKG domains found in the configured path. Filter by keyword to narrow results.
Read `./domain-traversal.md` for domain naming conventions.

### Load Domain
```bash
python ./scripts/load_domain.py <domain-slug> [--path DIR] [--summary]
```
Loads a full CKG domain and prints its metadata, domain list, and node/edge counts. Use `--summary` for a compact overview without full node listing.

### Search Concepts
```bash
python ./scripts/search_concepts.py <domain-slug> <query> [--path DIR] [--limit N]
```
Searches concept names and descriptions within a domain for a keyword or phrase. Returns matching node IDs, types, and descriptions. Default limit: 10.

### Query Concept Subgraph
```bash
python ./scripts/query_ckg.py <domain-slug> <concept-id> [--depth 1|2|3] [--path DIR]
```
Returns a concept's immediate neighbors (depth=1), 2-hop neighborhood (depth=2), or full upstream chain (depth=3). Each result includes the edge relation and target node description.

### Research Brief
Read `./research-brief.md` for CKG benchmark data, positioning, and paper citation.

### Query Guide
Read `./query-guide.md` for how to form queries, interpret edge relations, and chain traversals.

## Outputs

- `list_domains` → terminal table of domain slugs, node counts, edge counts.
- `load_domain` → full or summary view of domain structure.
- `search_concepts` → matching nodes with type, ID, and description.
- `query_ckg` → subgraph centered on the queried concept, with edge labels and neighbor descriptions.

## Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| Domain not found | Slug misspelled or file not in CKG_PATH | Run `list_domains` to see available slugs. |
| Concept ID not found | ID doesn't exist in that domain | Run `search_concepts` first to find valid IDs. |
| `CKG_API_KEY` error | Pro domain queried without key | Set `CKG_API_KEY` or use a free domain. |
| Empty search results | Query too specific | Try a shorter keyword or partial ID. |
| File parse error | CKG file malformed | Check `## NODES` and `## EDGES` sections exist in the .md file. |

## Runtime Compatibility

Works with Claude Code (plugin installation), Codex (plugin installation), and any agent harness that supports the Agent Skills specification. Scripts are self-contained under `scripts/`.
