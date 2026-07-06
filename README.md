# NVIDIA CKG Plugin

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills Spec](https://img.shields.io/badge/Agent%20Skills-Specification-blue?style=flat)](https://agentskills.io)
[![ckg-mcp](https://img.shields.io/badge/ckg--mcp-v0.7.6-76B900?style=flat)](https://pypi.org/project/ckg-mcp/)
[![Benchmark](https://img.shields.io/badge/F1-0.471_vs_RAG_0.123-76B900?style=flat)](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)
[![Dataset](https://img.shields.io/badge/HuggingFace-danyarm%2Fckg--benchmark-orange?style=flat)](https://huggingface.co/datasets/danyarm/ckg-benchmark)

Structured knowledge retrieval for NVIDIA's AI developer stack. `nvidia-ckg-skill` gives agents a typed, traversable graph of NVIDIA's documentation — list domains, search concepts, query dependency subgraphs, and multi-hop traverse. Every result is a declared relationship, not a probabilistic inference.

---

## Benchmark

Evaluated on [ckg-benchmark v0.6.2](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf) — 7,758 queries across 51 domains.

| Rank | System | F1 | Tokens/Query | Cost/1M Queries | 5-Hop F1 | Queries |
|:---:|---|---:|---:|---:|---:|---:|
| **1** | **CKG (ckg-mcp v0.7.6)** | **0.471** | **269** | **$7.81** | **0.771** | 7,758 |
| 2 | RAG (text-embedding-3-small) | 0.123 | 2,982 | $76.23 | 0.170 | 7,191 |
| 3 | GraphRAG (MS global mode) | 0.120 | 3,450 | $44.43 | — | 2,683 |

**CKG F1 improves with hop depth — 0.37 → 0.77 from hop 0 to hop 5. RAG stays flat at ~0.13 regardless of depth.** Retrieval has no mechanism for traversing a chain. This is the architectural gap the benchmark was designed to surface.

→ [Full leaderboard](https://huggingface.co/datasets/danyarm/ckg-benchmark) · [Paper](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)

### Reproduce

```bash
git clone https://github.com/Yarmoluk/ckg-benchmark
cd ckg-benchmark
pip install ckg-mcp
python evaluate.py --system ckg --domains nvidia-developer-ecosystem nvidia-cuda-toolkit nvidia-tensorrt-triton
```

Dataset: [huggingface.co/datasets/danyarm/ckg-benchmark](https://huggingface.co/datasets/danyarm/ckg-benchmark)

---

## Usage

### Claude Desktop (MCP — recommended)

Once the MCP server is installed and Claude Desktop is restarted, open a new chat and ask:

```
Use your ckg-nvidia-nim tools to find what an enterprise needs to deploy NIM on-prem.

Use your ckg-nvidia-cuda-toolkit tools to explain what TMA memory access requires and enables.

Use your ckg-nvidia-tensorrt-triton tools to trace the full inference optimization pipeline.
```

The phrase **"Use your ckg-[domain] tools to..."** tells Claude to call the graph rather than answer from training data. Claude will call `search_concepts` to find concept IDs, then `query_ckg` to traverse the subgraph. Every answer traces to a declared relationship — not inference.

**Tool call flow:**
1. `search_concepts(query)` — finds matching concept IDs by keyword
2. `query_ckg(concept, depth)` — BFS traversal returning the typed subgraph
3. Claude answers grounded in declared edges only

### Claude Code / CLI (with NIM)

```bash
export NIM_API_KEY="nvapi-..."
python demos/ckg_nim_demo.py \
  --domain nvidia-nim \
  --question "What does an enterprise need to deploy a NIM on-prem?" \
  --depth 2
```

See `demos/ckg_nim_demo.py` — traverses the CKG, formats the subgraph as structured context, calls NIM, returns a grounded answer with token comparison vs RAG baseline.

---

## Install

**Claude Code**
```bash
claude plugin marketplace add https://github.com/Yarmoluk/nvidia-ckg.git
claude plugin install nvidia-ckg@nvidia-ckg --scope user
```

**Codex**
```bash
codex plugin marketplace add https://github.com/Yarmoluk/nvidia-ckg.git
```

**Local / other harnesses**
```bash
git clone https://github.com/Yarmoluk/nvidia-ckg.git
cp -R nvidia-ckg/skills/nvidia-ckg-skill <your-skills-directory>/
```

---

## Workflows

| Workflow | Command |
|---|---|
| List all NVIDIA CKG domains | `python ./scripts/list_domains.py --filter nvidia` |
| Load a domain (full or summary) | `python ./scripts/load_domain.py nvidia-cuda-toolkit` |
| Search concepts by keyword | `python ./scripts/search_concepts.py nvidia-tensorrt-triton quantization` |
| Query a concept's subgraph | `python ./scripts/query_ckg.py nvidia-tensorrt-triton tensorrt_sdk --depth 2` |
| Full upstream dependency chain | `python ./scripts/query_ckg.py nvidia-cuda-toolkit tma_memory_access --depth 3` |

---

## NVIDIA Domains

19 CKGs covering NVIDIA's full stack — developer documentation, inference platform, training framework, enterprise layer, and physical AI. Each is a typed dependency graph — nodes are concepts, edges are named relations (ENABLES, REQUIRES, EXTENDS, OPTIMIZES, …).

### Platform & Enterprise

| Domain | Nodes | Edges | Coverage |
|---|---:|---:|---|
| `nvidia-developer-ecosystem` | 73 | 142 | Full ecosystem map — parent of all below |
| `nvidia-nim` | 50 | 74 | NIM microservices: LLM, VLM, speech, biology, RAG, Kubernetes |
| `nvidia-nemo` | 50 | 72 | NeMo: pretraining, SFT, LoRA, RLHF, DPO, GRPO, guardrails |
| `nvidia-ai-enterprise` | 50 | 71 | NVAIE: licensing, ISV program, Kubernetes operators, cloud |
| `nvidia-cosmos` | 46 | 66 | Cosmos WFM: world prediction, sim-to-real, synthetic data, robotics |

### Developer Documentation

| Domain | Nodes | Edges | Coverage |
|---|---:|---:|---|
| `nvidia-cuda-toolkit` | 50 | 76 | Runtime, compiler, PTX, Hopper/Blackwell features |
| `nvidia-tensorrt-triton` | 51 | 71 | TensorRT v11.1 optimizer + Triton serving |
| `nvidia-cuda-x-libraries` | 50 | 70 | cuDNN, cuBLAS, cuFFT, NCCL, cuSPARSE |
| `nvidia-hpc-sdk` | 50 | 72 | C/C++/Fortran compilers, OpenACC, NVSHMEM |
| `nvidia-developer-tools` | 48 | 72 | Nsight Systems, Nsight Compute, sanitizers |
| `nvidia-omniverse` | 50 | 72 | OpenUSD, digital twins, PhysX simulation |
| `nvidia-gameworks` | 49 | 72 | RTX, DLSS 4, ray tracing, PhysX, Reflex |
| `nvidia-graphics-research` | 46 | 71 | nvdiffrast, instant-ngp, 3DGS, Kaolin, tiny-cuda-nn, NVLabs |

### Edge, Robotics & Verticals

| Domain | Nodes | Edges | Coverage |
|---|---:|---:|---|
| `nvidia-jetson` | 49 | 73 | Edge AI, JetPack, embedded compute |
| `nvidia-isaac-robotics` | 48 | 68 | GR00T, Isaac Lab, Sim, robot learning |
| `nvidia-drive-av` | 45 | 68 | DRIVE OS, DriveWorks, DRIVE Sim |
| `nvidia-metropolis` | 50 | 76 | Smart cities, DeepStream, IVA pipelines |
| `nvidia-clara` | 45 | 67 | Medical imaging, genomics, MONAI |
| `nvidia-riva` | 48 | 72 | ASR, TTS, NLP, streaming speech AI |

---

## Demo: CKG + NIM

Traverse a CKG domain and answer a question using NIM as the inference engine. The subgraph becomes the context — structured, typed, and compact.

```bash
export NIM_API_KEY="nvapi-..."

# Enterprise NIM deployment
python demos/ckg_nim_demo.py \
  --domain nvidia-nim \
  --question "What does an enterprise need to deploy a NIM on-prem?" \
  --depth 2

# TensorRT quantization chain
python demos/ckg_nim_demo.py \
  --domain nvidia-tensorrt-triton \
  --question "How does TensorRT quantization reduce inference latency?" \
  --depth 3

# Cosmos robot training pipeline
python demos/ckg_nim_demo.py \
  --domain nvidia-cosmos \
  --question "How does Cosmos generate synthetic training data for robots?" \
  --depth 2
```

**What you see:** CKG loads → entry concept found → subgraph extracted → token count (CKG vs RAG baseline) → NIM answer grounded in declared graph relationships.

Default model: `meta/llama-3.1-70b-instruct`. Any model on [build.nvidia.com](https://build.nvidia.com) with a Free Endpoint badge works via `--model <model-id>`.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `CKG_PATH` | `~/Desktop/Knowledge_Graph_Graphify` | Directory containing CKG `.md` files |
| `CKG_API_KEY` | — | Required for Pro-gated domains. Get at [graphifymd.com/caas](https://graphifymd.com/caas) |

---

## Custom Domains

The 14 NVIDIA domains are free. **Need a CKG for your own codebase, internal documentation, or a domain not covered here?**

→ [graphifymd.com/caas](https://graphifymd.com/caas) — CKG-as-a-Service, $99/mo. Submit a domain, get back a typed knowledge graph your agents can traverse.

65+ domains available across science, engineering, policy, and AI research. [Full catalog](https://graphifymd.com).

---

## Requirements

- Python 3.10+
- Agent runtime with plugin or Agent Skills support (Claude Code, Codex, or compatible harness)
- CKG `.md` files on disk, or `CKG_API_KEY` for Pro domains

## Development

```bash
uv sync
uv run pytest
claude plugin validate .
```

## Evaluation

See [BENCHMARK.md](BENCHMARK.md) for the full evaluation report including per-metric scores and eval task breakdown.

## License

MIT
