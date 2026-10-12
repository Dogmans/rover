# Development PC Hardware Profile

This file records the local PC used for early model experiments. It is an environment snapshot, not a minimum requirement or a fixed deployment target for the rover. Update it when the development machine changes; deployments on other PCs should use their own measured hardware and runtime capabilities.

## Confirmed Snapshot

- GPU: NVIDIA GeForce RTX 2080 Ti
- GPU memory: 11,264 MiB (reported by `nvidia-smi`)
- Checked: 2026-10-05

## Deployment context

The current viewer/perception prototype runs on Windows, as documented in the
[PC operating guide](../../tools/pc/README.md). The exact OS release and other
machine details have not been recorded in this profile.

## Not Yet Recorded

- Windows version/build
- CPU model and system memory
- NVIDIA driver, CUDA/runtime, and inference framework versions
- Measured inference latency, peak GPU memory, and task quality on rover camera images

Collect these values on the actual target PC before choosing installation instructions or fixing a model deployment. For an NVIDIA system, `nvidia-smi` reports the GPU and driver; record the inference runtime and benchmark results separately.

## Model evaluation context

Use [model research](../research/ACTION_MODEL_RESEARCH.md) for candidate comparisons
and the evaluation plan, and [Feature status](../project/FEATURE_STATUS.md) for the
running prototype. This hardware snapshot does not establish model throughput
or sufficient free memory for a particular runtime. Benchmark representative
rover images and prompts on each deployment PC and record the actual choice.
