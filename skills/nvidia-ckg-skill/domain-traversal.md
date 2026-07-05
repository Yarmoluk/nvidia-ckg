# Domain Traversal Guide

## Domain Slug Conventions

Domain slugs are kebab-case strings matching the `domain:` field in each CKG's `## META` section.

NVIDIA documentation domains follow `nvidia-{product}`:

| Slug | Description |
|---|---|
| `nvidia-developer-ecosystem` | Full NVIDIA ecosystem map (73n/142e, parent of all nvidia- CKGs) |
| `nvidia-cuda-toolkit` | CUDA runtime, compiler, profiling tools (50n/76e) |
| `nvidia-cuda-x-libraries` | cuDNN, cuBLAS, cuFFT, NCCL, cuSPARSE |
| `nvidia-tensorrt-triton` | TensorRT optimizer + Triton serving (51n/71e) |
| `nvidia-jetson` | Edge AI, JetPack, embedded compute |
| `nvidia-isaac` | Robotics, GR00T, Isaac Lab, Sim |
| `nvidia-omniverse` | OpenUSD, digital twins, simulation |
| `nvidia-drive` | Autonomous vehicle stack, DRIVE OS, DriveWorks |
| `nvidia-metropolis` | Smart cities, IVA, DeepStream |
| `nvidia-clara` | Medical imaging, genomics, smart hospital sensors |
| `nvidia-riva` | ASR, TTS, NLP, conversational AI |
| `nvidia-hpc-sdk` | C/C++/Fortran compilers, HPC libraries |
| `nvidia-gameworks` | RTX, DLSS, ray tracing, PhysX |
| `nvidia-developer-tools` | Nsight profilers, debuggers |

## Relation Types

| Relation | Meaning |
|---|---|
| `ENABLES` | Source provides the capability that makes target possible |
| `REQUIRES` | Target cannot function without source |
| `EXTENDS` | Target adds functionality on top of source |
| `IMPLEMENTS` | Target is a concrete realization of source's specification |
| `OPTIMIZES` | Target improves performance characteristics of source |
| `WRAPS` | Target provides an abstraction layer around source |
| `CONFIGURES` | Source controls the behavior of target |
| `MONITORS` | Source observes and reports on target |
| `REPLACES` | Target supersedes source (deprecated → current) |
| `USED_IN` | Source is consumed by target workflow or system |
| `PART_OF` | Source is a component of the target system |
| `VALIDATES` | Source checks correctness of target |
| `GENERATES` | Source produces target as output |
| `CONSUMES` | Source takes target as input |

## Multi-hop Traversal Patterns

**Dependency chain (depth=3):** Find everything a concept transitively requires.
```bash
python ./scripts/query_ckg.py nvidia-cuda-toolkit tensorrt_sdk --depth 3
```

**Impact chain:** Find what a concept enables downstream.
```bash
python ./scripts/query_ckg.py nvidia-tensorrt-triton triton_inference_server --depth 2
```

**Cross-domain lookup:** Load the parent ecosystem CKG to see how products connect.
```bash
python ./scripts/load_domain.py nvidia-developer-ecosystem --summary
```
