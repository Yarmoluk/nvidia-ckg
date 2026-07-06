#!/usr/bin/env python3
"""
CKG + NIM Demo — structured knowledge graph context → NIM inference.

Traverses a CKG domain, extracts a typed subgraph around a concept,
and sends it as structured context to a NIM endpoint. Shows token
compression vs RAG baseline (ckg-benchmark v0.6.2: 269 vs 2,982 avg).

Usage:
  export NIM_API_KEY="nvapi-..."
  python demos/ckg_nim_demo.py \\
    --domain nvidia-cuda-toolkit \\
    --question "What does TMA memory access require and what does it enable?"

  python demos/ckg_nim_demo.py \\
    --domain nvidia-tensorrt-triton \\
    --question "How does TensorRT quantization reduce inference latency?" \\
    --depth 3

  python demos/ckg_nim_demo.py --domain nvidia-nim \\
    --question "What does an enterprise need to deploy a NIM on-prem?" \\
    --no-nim   # print context only, skip API call
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.table import Table
    RICH = True
except ImportError:
    RICH = False

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "nvidia-ckg-skill" / "scripts"))
from _parse import find_domain_file, parse_nodes, parse_edges

DEFAULT_PATH = os.environ.get("CKG_PATH", "~/Desktop/Knowledge_Graph_Graphify")
DEFAULT_MODEL = "meta/llama-3.1-70b-instruct"
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
RAG_TOKEN_BASELINE = 2982      # ckg-benchmark v0.6.2 corpus-wide average
CKG_TOKEN_BENCHMARK = 269      # ckg-benchmark v0.6.2 corpus-wide average


def find_entry_concept(nodes: dict, question: str) -> str | None:
    words = [w.lower().strip("?.,!") for w in question.split() if len(w) > 3]
    best_id, best_score = None, 0
    for nid, node in nodes.items():
        score = sum(
            (3 if w in nid.lower() else 0) +
            (2 if w in node.get("display", "").lower() else 0) +
            (1 if w in node.get("desc", "").lower() else 0)
            for w in words
        )
        if score > best_score:
            best_score, best_id = score, nid
    return best_id


def bfs_subgraph(concept_id: str, nodes: dict, edges: list, depth: int):
    from collections import deque
    adj = {nid: [] for nid in nodes}
    for src, rel, tgt in edges:
        if src in adj:
            adj[src].append((rel, tgt))
        if tgt in adj:
            adj[tgt].append((rel, src))

    visited = {concept_id: 0}
    queue = deque([concept_id])
    sub_edges = []

    while queue:
        cur = queue.popleft()
        if visited[cur] >= depth:
            continue
        for rel, nbr in adj.get(cur, []):
            if nbr not in nodes:
                continue
            edge = (cur, rel, nbr)
            if edge not in sub_edges:
                sub_edges.append(edge)
            if nbr not in visited:
                visited[nbr] = visited[cur] + 1
                queue.append(nbr)

    return {nid: nodes[nid] for nid in visited}, sub_edges


def format_context(root_id: str, sub_nodes: dict, sub_edges: list, domain: str) -> str:
    root = sub_nodes.get(root_id, {})
    lines = [
        f"# Knowledge Graph: {domain}",
        f"## Root: {root.get('display', root_id)} [{root.get('type', '')}]",
        root.get("desc", ""),
        "",
        "## Related Concepts",
    ]
    for nid, node in sub_nodes.items():
        if nid == root_id:
            continue
        desc = node.get("desc", "")[:110]
        lines.append(f"- **{node.get('display', nid)}** [{node.get('type', '')}]: {desc}")

    lines += ["", "## Declared Relationships"]
    for src, rel, tgt in sub_edges:
        s = sub_nodes.get(src, {}).get("display", src)
        t = sub_nodes.get(tgt, {}).get("display", tgt)
        lines.append(f"- {s} --[{rel}]--> {t}")

    return "\n".join(lines)


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def call_nim(question: str, context: str, model: str, api_key: str) -> dict:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a precise technical expert. Answer using ONLY the knowledge graph "
                    "context provided. Cite specific concepts and relationships from the graph. "
                    "Be concise and accurate."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
        "max_tokens": 512,
        "temperature": 0.1,
    }

    req = urllib.request.Request(
        f"{NIM_BASE_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(
        description="CKG + NIM Demo: traverse a knowledge graph, call NIM with structured context.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--domain", "-d", required=True,
                        help="CKG domain slug (e.g. nvidia-cuda-toolkit, nvidia-nim)")
    parser.add_argument("--question", "-q", required=True,
                        help="Question to answer from the knowledge graph")
    parser.add_argument("--concept", "-c",
                        help="Seed concept node ID (auto-detected from question if omitted)")
    parser.add_argument("--depth", type=int, default=2, choices=[1, 2, 3],
                        help="BFS traversal depth (default: 2)")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL,
                        help=f"NIM model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--path", "-p", default=DEFAULT_PATH,
                        help="Directory containing CKG .md files")
    parser.add_argument("--no-nim", action="store_true",
                        help="Print CKG context only; skip the NIM API call")
    args = parser.parse_args()

    api_key = os.environ.get("NIM_API_KEY") or os.environ.get("NVIDIA_API_KEY")
    if not api_key and not args.no_nim:
        print("ERROR: NIM_API_KEY or NVIDIA_API_KEY not set.", file=sys.stderr)
        print("  export NIM_API_KEY='nvapi-...'", file=sys.stderr)
        sys.exit(1)

    console = Console() if RICH else None

    # ── Load CKG ──────────────────────────────────────────────────────────────
    ckg_dir = Path(args.path).expanduser()
    ckg_file = find_domain_file(ckg_dir, args.domain)
    if not ckg_file:
        print(f"ERROR: Domain '{args.domain}' not found in {ckg_dir}", file=sys.stderr)
        sys.exit(1)

    text = ckg_file.read_text(errors="replace")
    nodes = parse_nodes(text)
    edges = parse_edges(text)

    if console:
        console.print(f"\n[bold green]✓[/bold green] {args.domain} — {len(nodes)} nodes, {len(edges)} edges")

    # ── Find entry concept ────────────────────────────────────────────────────
    concept_id = args.concept
    if concept_id and concept_id not in nodes:
        candidates = [n for n in nodes if concept_id.lower() in n.lower()]
        if candidates:
            concept_id = candidates[0]
            if console:
                console.print(f"[yellow]⚠[/yellow]  Fuzzy match: using '{concept_id}'")
        else:
            print(f"ERROR: Concept '{concept_id}' not found. Run search_concepts.py to find valid IDs.", file=sys.stderr)
            sys.exit(1)

    if not concept_id:
        concept_id = find_entry_concept(nodes, args.question)

    if not concept_id:
        print("ERROR: Could not auto-detect a concept. Use --concept to specify one.", file=sys.stderr)
        sys.exit(1)

    root_node = nodes[concept_id]
    if console:
        console.print(f"[bold green]✓[/bold green] Entry concept: [cyan]{concept_id}[/cyan] — {root_node.get('display', '')}")

    # ── BFS traversal ─────────────────────────────────────────────────────────
    sub_nodes, sub_edges = bfs_subgraph(concept_id, nodes, edges, args.depth)
    if console:
        console.print(f"[bold green]✓[/bold green] Subgraph: {len(sub_nodes)} nodes, {len(sub_edges)} edges at depth={args.depth}\n")

    # ── Format context ────────────────────────────────────────────────────────
    context = format_context(concept_id, sub_nodes, sub_edges, args.domain)
    ckg_tokens = approx_tokens(context)
    compression = RAG_TOKEN_BASELINE / ckg_tokens

    if console:
        console.rule("[bold dim]CKG Context (sent to NIM)")
        console.print(context)
        console.rule()

        t = Table(show_header=False, box=None, padding=(0, 2))
        t.add_column(style="dim")
        t.add_column(justify="right")
        t.add_row("CKG context tokens:", f"[green]{ckg_tokens:,}[/green]")
        t.add_row("RAG baseline (benchmark avg):", f"[red]{RAG_TOKEN_BASELINE:,}[/red]")
        t.add_row("Compression:", f"[bold green]{compression:.1f}×[/bold green] fewer tokens")
        console.print(t)
        console.print()
    else:
        print(f"\n--- CKG Context ---\n{context}")
        print(f"\nTokens: CKG {ckg_tokens} | RAG baseline {RAG_TOKEN_BASELINE} | {compression:.1f}× compression\n")

    if args.no_nim:
        return

    # ── Call NIM ──────────────────────────────────────────────────────────────
    if console:
        console.rule(f"[bold]NIM Response[/bold]  [dim]{args.model}[/dim]")

    try:
        result = call_nim(args.question, context, args.model, api_key)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"ERROR {e.code} from NIM: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR calling NIM: {e}", file=sys.stderr)
        sys.exit(1)

    answer = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    prompt_tok = usage.get("prompt_tokens", "?")
    completion_tok = usage.get("completion_tokens", "?")

    if console:
        console.print(Panel(answer, border_style="green", title="Answer"))
        console.print(
            f"\n[dim]NIM usage — prompt: {prompt_tok} tokens  |  "
            f"completion: {completion_tok} tokens  |  model: {args.model}[/dim]\n"
        )
    else:
        print(f"Answer:\n{answer}")
        print(f"\nNIM usage — prompt: {prompt_tok}, completion: {completion_tok}")


if __name__ == "__main__":
    main()
