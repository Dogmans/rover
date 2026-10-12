# Model research and evaluation

Research snapshot: 2026-10-05. Scope reconciled: 2026-10-12. This document owns
candidate comparison and evaluation rationale, not the runtime architecture or
implementation status. Upstream availability, licensing and benchmarks need
rechecking before deployment. No new model benchmark is claimed by this revision.

The [architecture](../architecture/ROS_ARCHITECTURE.md) owns execution and command
boundaries; [perception design](../architecture/PERCEPTION_AND_SEMANTIC_MAP.md)
owns object memory and enrichment. The [feature checklist](../project/FEATURE_STATUS.md)
and [PC viewer guide](../../tools/pc/README.md) identify the running prototype.

## Recommendation

Use a small detector plus **one local multimodal model on the PC**. The detector
produces boxes and initial labels; the multimodal model adds richer meaning to
selected images/saved sightings and can propose bounded task tools. A second,
separate language-model decision service is not the v1 baseline. The two-stage
visual pipeline does not require two large models.

Qwen3-VL Instruct 4B with a supported 4-bit runtime is a candidate to benchmark,
not a fixed dependency or a deployed replacement for the prototype's
`qwen2.5vl:7b`. Compare smaller checkpoints if latency/memory is inadequate.
Select on measured task accuracy and combined detector/model load on the actual
[development PC](../hardware/DEVELOPMENT_PC_PROFILE.md), not nominal GPU capacity.

The model can interpret selected frames and structured map records. It does not
supply a geometric map, reliable depth or a motion controller. The selected LD06
and onboard encoder/IMU integration are described by the hardware documents;
their quality remains commissioning work rather than a model capability.

## Proposed action boundary

The canonical proposed skills and their execution owners are in
[bounded robot actions](../architecture/ROS_ARCHITECTURE.md#command-authority-and-bounded-robot-actions).
Task state, cancellation and navigation stay under deterministic software.
Do not maintain a second action vocabulary or semantic-discovery procedure here.

## Options assessed

| Option | Local PC use | Fit for this rover | Assessment |
|---|---|---|---|
| Qwen3-VL Instruct (2B/4B/8B) | Yes; public checkpoints and inference code | Language + image interpretation, object grounding, and proposing tools | Recommended multimodal family to benchmark alongside the small detector. Start with 4B at supported 4-bit quantization only if it fits the target PC; compare 2B if memory or latency is inadequate. The current development PC profile is recorded separately. It is not a trained rover controller; validate all proposed skills in mission software. Exact VRAM and throughput depend on precision, image resolution, context, and serving runtime. |
| Clef / Clef-Flash (27B / 9B) | Yes; Apache-2.0 open weights and local inference code; also hosted on Workers AI | Multimodal, schema-constrained decisions with probabilities over allowed choices | Not selected for v1: it would introduce a second model beside the conversational VLM, and its local hardware requirements are high. Keep as a future alternative if typed action selection proves inadequate; Cloudflare benchmark claims are not yet independently reproduced. |
| Jev (TypeSafe System One) | No; hosted API, proprietary weights | Fast typed choices/scores over supplied text or structured state | Sensible optional decision/classification service after perception has converted images to structured state. Text-only, no local/offline inference, and no conversational generation. Treat confidence as a routing signal, not a safety guarantee. |
| Cloud multimodal model | No local weights required | Potentially strong reasoning for ambiguous images and tasks | Optional provider. Adds internet dependency, latency, recurring cost, and image privacy concerns. It cannot be required in the stop/control loop. |
| Text-only LLM + detector | Yes | Good when object classes and task patterns are known | Modular and potentially faster. A closed-set detector may miss a user-specified uncommon object; open-vocabulary detection or a VLM may be needed. Localization still needs geometry and robot pose. |
| OpenVLA (7B) | Yes, with suitable NVIDIA GPU; upstream supports local and server inference | Pretrained action space/evaluations target robot-arm manipulation | Not a ready rover action model. Adapting it requires mapping/fine-tuning a new embodiment and action space; upstream notes target-domain fine-tuning is normally needed. Consider only as a later learning experiment. |
| π0 / π0.5 (`openpi`) | Yes; upstream documents GPU inference and remote policy serving | VLA policies, but public examples/checkpoints are arm manipulation tasks | Not a direct differential-drive navigation policy. The upstream project explicitly warns transfer to other robots may not work. Fine-tuning, action mapping, and substantial GPU capacity are likely. |
| SmolVLA (450M) | Yes; comparatively lightweight inference | Small manipulation policy intended to be fine-tuned on the target setup | Low-resource research option, not a semantic mission planner. The official guide recommends collecting task-specific demonstrations (about 50 episodes as a starting point); its shown tasks are manipulation. |
| V-JEPA 2 / V-JEPA 2-AC | Yes; open research code/checkpoints, GPU-oriented | World-model video prediction; V-JEPA 2-AC has demonstrated image-goal manipulation planning on a Franka arm | JEPA is a predictive representation/world-model approach, not a ready chat/task decision model. The demonstrated action-conditioned setup is arm manipulation, not household rover navigation. Interesting future research, poor v1 dependency. |
| VLA-JEPA (LeRobot) | Yes, with supported ML hardware/runtime | Combines Qwen3-VL, a V-JEPA2-trained video predictor, and an action head | A real research option, but published checkpoints use 7D manipulation actions and LIBERO/DROID/Bridge-style data. Adapting to the rover requires rover data and new action/state mappings. The world model is used for training; documented inference uses Qwen plus the action head. Not the recommended initial rover controller. |

LeRobot is useful infrastructure for datasets, evaluation, and training policies. It is not itself the choice of task decision model or a substitute for ROS navigation and safety layers.

## Why Jev is not the whole solution

Jev's interface is well matched to bounded questions such as “which available skill best advances this search?” when the state has already been represented as text/JSON and the answer choices are defined by application code. Its fast typed response could be useful in that narrow role, and its confidence could support “ask the operator” branches. But the rover still needs a separate conversational interface and vision system; Jev currently accepts no images/video. It is an early-access hosted service, so service availability, rate limits, network latency, and model-version changes also need to be evaluated. Pin a version and log it if confidence thresholds are tuned.

Clef-Flash remains a local alternative in this research snapshot: it accepts image/video inputs and returns typed schema-bounded probabilities through a Jev-compatible interface. It is not part of the v1 recommendation because the project uses one multimodal model for interpretation and tool proposals; running a separate decision model beside it would add cost and complexity. Reconsider it if measured tasks demonstrate a need for specialized typed decisions and suitable GPU hardware is available.

JEPA and Jev are different research directions. V-JEPA 2 predicts video representations; V-JEPA 2-AC adds action-conditioned prediction and reports image-goal manipulation results. Neither supplies semantic room-level rover navigation. These options remain candidate research, distinct from the conventional navigation and mission execution defined by the architecture.

## Evaluation plan

1. Benchmark candidates with representative clean rover frames, object crops,
   scene context and structured evidence. Include low light, blur and unfamiliar
   viewpoints, plus tasks beyond the current detector's fixed class vocabulary.
2. Measure warm/cold latency, peak GPU memory, correctness of referenced object
   IDs and attributes, disagreement with detector evidence and invalid tool calls.
3. Check behavior under omitted/stale geometry, moved objects and delayed results;
   richer descriptions must remain bound to their source sighting.
4. Compare smaller candidates if the chosen runtime cannot meet the task budget.
   Record model/provider/version, prompts, source evidence, validation results
   and resource measurements alongside each trial.
5. Connect task proposals only after the conventional navigation and mission
   interfaces pass the [project milestones](../project/FEATURE_STATUS.md#suggested-next-sequence).

The model-serving runtime, quantization and task vocabulary remain choices to
validate. Inspection/enrichment scheduling and model-facing tools are specified
in the perception design rather than repeated in this research assessment.

## Research references

- Jev model documentation and modalities: https://docs.typesafe.ai/models
- TypeSafe System One model concepts and primitives: https://docs.typesafe.ai/concepts/system-one
- TypeSafe introduction to Jev: https://typesafe.ai/blog/introducing-system-one-models-and-jev
- Independent overview of Jev's design and early use cases: https://techcrunch.com/2026/09/18/a-new-kind-of-ai-model-from-a-chatgpt-inventor-is-thrilling-developers/
- Cloudflare Clef/Clef-Flash announcement and author-reported evaluations: https://blog.cloudflare.com/clef-decision-models/
- Clef 27B model card: https://huggingface.co/Cloudflare/clef
- Clef-Flash 9B model card: https://huggingface.co/Cloudflare/clef-flash
- Independent report on Clef hardware requirements and benchmark caveats: https://www.theregister.com/2026/10/01/cloudflare-tries-to-outplay-jev-with-open-weight-clef-models/5300649
- Community Decision Index leaderboard and its self-reported-result caveat: https://clef-evals.workers-ai-mle.workers.dev/
- Qwen3-VL project, model sizes, visual grounding, local inference, and serving: https://github.com/QwenLM/Qwen3-VL
- VLA-JEPA architecture, checkpoints, action dimensions, and training guidance: https://huggingface.co/docs/lerobot/main/vla_jepa
- SmolVLA model and task-specific fine-tuning guidance: https://huggingface.co/docs/lerobot/main/smolvla
- OpenVLA model, evaluations, and fine-tuning guidance: https://github.com/openvla/openvla
- Open π model checkpoints, hardware notes, and remote inference: https://github.com/Physical-Intelligence/openpi
- V-JEPA 2 / V-JEPA 2-AC research, checkpoints, and manipulation experiments: https://github.com/facebookresearch/vjepa2
- LeRobot policy, robot, and dataset framework: https://github.com/huggingface/lerobot
- ROS 2 Navigation (Nav2) implementation: https://github.com/ros-navigation/navigation2
