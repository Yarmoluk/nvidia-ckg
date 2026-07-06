#!/usr/bin/env python3
"""
NVIDIA CKG MCP Server

Serves typed knowledge graphs of NVIDIA's developer stack as MCP tools.
Reads CKG .md files from CKG_PATH (default: ~/Desktop/Knowledge_Graph_Graphify).

Single-domain mode (recommended):
  CKG_DOMAIN=nvidia-nim python mcp_server.py

Multi-domain mode:
  python mcp_server.py
"""
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).parent / "skills" / "nvidia-ckg-skill" / "scripts"))
from _parse import find_domain_file, parse_nodes, parse_edges

CKG_PATH = Path(os.environ.get("CKG_PATH", "~/Desktop/Knowledge_Graph_Graphify")).expanduser()
_DOMAIN = os.environ.get("CKG_DOMAIN", "").strip()
_SERVER_NAME = f"ckg-{_DOMAIN}" if _DOMAIN else "ckg-nvidia"

_INSTRUCTIONS = (
    f"NVIDIA CKG MCP server scoped to '{_DOMAIN}'. "
    f"Tools: search_concepts(query) to find concepts, "
    f"query_ckg(concept, depth) to traverse the subgraph. "
    f"Every result is a declared relationship — no inference."
) if _DOMAIN else (
    "NVIDIA CKG MCP server. Tools: list_domains() first, then "
    "search_concepts(domain, query) and query_ckg(domain, concept, depth). "
    "Every result is a declared relationship — no inference."
)

mcp = FastMCP(_SERVER_NAME, instructions=_INSTRUCTIONS)


def _all_nvidia_domains() -> list[str]:
    domains = []
    for f in sorted(CKG_PATH.glob("ckg-nvidia-*.md")):
        slug = f.stem.replace("ckg-", "").rsplit("-v0.", 1)[0]
        domains.append(slug)
    return domains


def _resolve(domain: str) -> str:
    resolved = domain.strip() or _DOMAIN
    if not resolved:
        raise ValueError("domain required — pass it or set CKG_DOMAIN env var")
    return resolved


def _load(domain: str):
    f = find_domain_file(CKG_PATH, domain)
    if not f:
        raise FileNotFoundError(f"Domain '{domain}' not found in {CKG_PATH}")
    text = f.read_text(errors="replace")
    return parse_nodes(text), parse_edges(text)


@mcp.tool()
def list_domains() -> str:
    """List available NVIDIA CKG domains on this server."""
    if _DOMAIN:
        return f"Single-domain mode — active domain: {_DOMAIN}"
    domains = _all_nvidia_domains()
    return f"Available NVIDIA domains ({len(domains)}): " + ", ".join(domains)


@mcp.tool()
def search_concepts(query: str, domain: str = "") -> str:
    """Find concepts in a domain by keyword. Returns matching concept IDs and descriptions.

    Args:
        query: Keyword to search (e.g. 'quantization', 'tma', 'helm').
        domain: Domain slug (omit in single-domain mode).
    """
    domain = _resolve(domain)
    try:
        nodes, _ = _load(domain)
    except FileNotFoundError as e:
        return str(e)

    q = query.lower()
    results = []
    for nid, node in nodes.items():
        score = (3 if q in nid.lower() else 0) + \
                (2 if q in node.get("display", "").lower() else 0) + \
                (1 if q in node.get("desc", "").lower() else 0)
        if score:
            results.append((score, nid, node))
    results.sort(key=lambda x: -x[0])

    if not results:
        return f"No concepts matching '{query}' in {domain}."

    lines = [f"Concepts matching '{query}' in {domain}:"]
    for _, nid, node in results[:15]:
        lines.append(f"  [{node.get('type','')}] {nid} — {node.get('desc','')[:100]}")
    return "\n".join(lines)


@mcp.tool()
def query_ckg(concept: str, depth: int = 2, domain: str = "") -> str:
    """Traverse the knowledge graph from a concept and return its subgraph.

    Args:
        concept: Concept node ID (use search_concepts to find exact IDs).
        depth: BFS traversal depth 1-3 (default 2).
        domain: Domain slug (omit in single-domain mode).
    """
    from collections import deque

    domain = _resolve(domain)
    try:
        nodes, edges = _load(domain)
    except FileNotFoundError as e:
        return str(e)

    depth = min(max(depth, 1), 3)

    if concept not in nodes:
        candidates = [n for n in nodes if concept.lower() in n.lower()][:5]
        if candidates:
            return f"'{concept}' not found. Did you mean: {', '.join(candidates)}"
        return f"'{concept}' not found in {domain}. Use search_concepts to find valid IDs."

    adj: dict[str, list] = {nid: [] for nid in nodes}
    for src, rel, tgt in edges:
        if src in adj:
            adj[src].append((rel, tgt))
        if tgt in adj:
            adj[tgt].append((rel, src))

    visited = {concept: 0}
    queue = deque([concept])
    sub_edges = []
    while queue:
        cur = queue.popleft()
        if visited[cur] >= depth:
            continue
        for rel, nbr in adj.get(cur, []):
            if nbr not in nodes:
                continue
            e = (cur, rel, nbr)
            if e not in sub_edges:
                sub_edges.append(e)
            if nbr not in visited:
                visited[nbr] = visited[cur] + 1
                queue.append(nbr)

    root = nodes[concept]
    lines = [
        f"## {root.get('display', concept)} [{root.get('type','')}] — {domain}",
        root.get("desc", ""),
        f"\nReachable: {len(visited)} nodes, {len(sub_edges)} edges (depth={depth})",
        "",
        "### Relationships",
    ]
    for src, rel, tgt in sub_edges:
        s = nodes.get(src, {}).get("display", src)
        t = nodes.get(tgt, {}).get("display", tgt)
        lines.append(f"- {s} --[{rel}]--> {t}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
