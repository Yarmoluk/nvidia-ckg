# CKG Research Brief

## What Is a CKG

A Compact Knowledge Graph (CKG) is a typed, directed knowledge graph stored as a structured markdown file. Unlike RAG, which retrieves text chunks and hopes the model reasons correctly over them, a CKG traversal follows declared edges — every result is an explicit relationship, not a probabilistic inference.

## Benchmark Results (v0.6.2, locked)

| Metric | CKG | RAG | GraphRAG |
|---|---|---|---|
| F1 score | **0.471** | 0.123 | 0.120 |
| Tokens per query | **269** | 2,982 | ~3,200 |
| 5-hop F1 | **0.772** | 0.170 | 0.160 |
| Cost per 1M queries | **$7.81** | $76.23 | ~$80 |

~4× F1 improvement over RAG · 11× token compression · ~10× cost reduction

Source: [ckg-benchmark v0.6.2](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)
Dataset: [huggingface.co/datasets/danyarm/ckg-benchmark](https://huggingface.co/datasets/danyarm/ckg-benchmark)

## Why Graph-RAG Fails

Per arXiv:2603.14045 (Reasoning Bottleneck in Graph-RAG): 73–84% of Graph-RAG errors are reasoning failures, not retrieval failures. The retrieved text is present but the model infers incorrectly. CKG eliminates this by traversing declared relationships rather than inferring them.

## Available Domains (65+ free, 24+ Pro)

Free domains include: CUDA Toolkit, TensorRT/Triton, NVIDIA Developer Ecosystem, Isaac Robotics, Omniverse, Jetson Edge AI, Clara Healthcare, Metropolis, DRIVE AV, Riva, HPC SDK, CUDA-X Libraries, Developer Tools, plus 50+ science/engineering/policy domains.

Pro domains (CKG_API_KEY required): see graphifymd.com/caas

## Citation

```
@misc{ckg2026,
  title={Compact Knowledge Graphs: 11x Token Compression for Agentic AI},
  author={Yarmoluk, Daniel},
  year={2026},
  url={https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf}
}
```
