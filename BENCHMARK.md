# Evaluation Report

Evaluation of `nvidia-ckg-skill` against [ckg-benchmark v0.6.2](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf).

## Leaderboard

| Rank | System | F1 | Tokens/Query | Cost/1M Queries | 5-Hop F1 | Queries |
|:---:|---|---:|---:|---:|---:|---:|
| **1** | **CKG (ckg-mcp v0.7.6)** | **0.471** | **269** | **$7.81** | **0.771** | 7,758 |
| 2 | RAG (text-embedding-3-small) | 0.123 | 2,982 | $76.23 | 0.170 | 7,191 |
| 3 | GraphRAG (MS global mode) | 0.120 | 3,450 | $44.43 | — | 2,683 |

Full leaderboard with task-type and domain breakdowns: [huggingface.co/datasets/danyarm/ckg-benchmark](https://huggingface.co/datasets/danyarm/ckg-benchmark)

## Key Finding

CKG F1 improves monotonically with hop depth — 0.37 at hop 0 to 0.77 at hop 5. RAG stays flat at ~0.13 regardless of depth. Retrieval has no mechanism for traversing a chain; the benchmark was designed to surface this gap.

## Evaluation Agents

| Agent | Model | Skill execution | Skill efficiency | Accuracy | Goal accuracy |
|---|---|---:|---:|---:|---:|
| Claude Code | Claude Opus 4.8 | — | — | — | — |
| Codex | GPT-5.4 | — | — | — | — |
| Script eval (this runner) | — | 12/12 (100%) | N/A | N/A | N/A |

*Skill-level agent evaluation pending first run. See [nvidia-kaggle BENCHMARK.md](https://github.com/NVIDIA/nvidia-kaggle/blob/main/BENCHMARK.md) for the reference evaluation format.*

## Evaluation Metrics

| Metric | Description |
|---|---|
| Security | Avoids leaking `CKG_API_KEY` or performing destructive file operations |
| Skill execution | Reads and follows the SKILL.md workflow; routes to correct script with correct arguments |
| Skill efficiency | Routes to `nvidia-ckg-skill` without redundant tool use |
| Accuracy | Returns correct domain names, concept IDs, and edge relations |
| Goal accuracy | Achieves the overall task (correct domain loaded, correct subgraph returned) |
| Behavior check | Runs `list_domains` before querying unknown domains; runs `search_concepts` before unknown IDs |

## Evaluation Tasks

18 tasks in [`skills/nvidia-ckg-skill/evals/evals.json`](skills/nvidia-ckg-skill/evals/evals.json): 12 positive cases where `nvidia-ckg-skill` should activate, 6 negative cases where it should not. Task areas: list-domains, load-domain, search-concepts, query-concept (depth 1/2/3), research-brief.

## Reproduce

```bash
git clone https://github.com/Yarmoluk/ckg-benchmark
cd ckg-benchmark
pip install ckg-mcp
python evaluate.py --system ckg --domains nvidia-developer-ecosystem nvidia-cuda-toolkit nvidia-tensorrt-triton
```

Dataset: [huggingface.co/datasets/danyarm/ckg-benchmark](https://huggingface.co/datasets/danyarm/ckg-benchmark)
Paper: [github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)
