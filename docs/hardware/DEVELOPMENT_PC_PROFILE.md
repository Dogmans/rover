# Development PC Hardware Profile

This file records the local PC used for early model experiments. It is an environment snapshot, not a minimum requirement or a fixed deployment target for the rover. Update it when the development machine changes; deployments on other PCs should use their own measured hardware and runtime capabilities.

## Confirmed Snapshot

- GPU: NVIDIA GeForce RTX 2080 Ti
- GPU memory: 11,264 MiB (reported by `nvidia-smi`)
- Checked: 2026-10-05

## Not Yet Recorded

- Operating system and version
- CPU model and system memory
- NVIDIA driver, CUDA/runtime, and inference framework versions
- Measured inference latency, peak GPU memory, and task quality on rover camera images

Collect these values on the actual target PC before choosing installation instructions or fixing a model deployment. For an NVIDIA system, `nvidia-smi` reports the GPU and driver; record the inference runtime and benchmark results separately.

## Model Evaluation Context

Qwen3-VL Instruct 4B with supported 4-bit quantization is a candidate to benchmark on this machine. That recommendation is only a starting hypothesis based on this GPU's reported memory, not a benchmark result. Compare a smaller model if the candidate exceeds available memory or latency targets.

For another PC, do not assume this GPU, memory size, operating system, or model choice. Benchmark the candidate models using representative rover images and prompts on that machine, and record the resulting model/runtime choice in its deployment configuration.
