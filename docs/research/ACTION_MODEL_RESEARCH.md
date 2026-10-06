# Action model research and recommendation

Research checked 2026-10-05. The local development PC hardware snapshot is recorded in [DEVELOPMENT_PC_PROFILE.md](../hardware/DEVELOPMENT_PC_PROFILE.md). The model recommendation below is not a benchmark of throughput or task success, and must be reevaluated for each deployment PC. The final ROS/navigation stack is not yet selected.

## Recommendation

Use a hybrid system rather than asking one learned action model to drive the rover end to end:

1. A PC-side vision-language model (VLM) interprets the operator's request and selected camera images, then proposes a next action from a small allowlist.
2. A deterministic PC mission executive validates the proposal, tracks the task, handles action results, and requests the next step or recovery.
3. A conventional ROS navigation stack executes pose/waypoint goals and handles local motion control and obstacle avoidance.
4. The Pi validates command ownership, limits and freshness, and stops on timeout or fault. Neither model output nor network availability is trusted as a safety mechanism.

The requested v1 is **one local multimodal model on the PC**, not a VLM plus a separate decision model. **Qwen3-VL Instruct 4B with a supported 4-bit inference runtime** is a starting candidate for image snapshots and conversational/tool-selection requests, not a fixed project dependency. Its suitability depends on the target PC's available memory, inference runtime, image resolution, context length, and competing GPU workloads. Benchmark on the actual machine; compare a smaller model if memory or latency is inadequate. Treat larger models as later experiments, not assumed requirements.

One VLM can interpret the user request, inspect selected camera frames, and propose typed skill calls. It does not need to emit motor commands. The deterministic mission executive validates the proposal, and ROS navigation/Pi safety software performs and constrains the action. Do not run high-rate video through the model; send selected, resized/compressed frames when a task needs visual feedback. The camera stream and ordinary perception/navigation components remain available to the software pipeline without requiring a second AI model.

This should be enough to prototype natural-language requests, bounded turns, status checks, and model-supervised visual search. It does **not** by itself provide a map, room-level localization, obstacle-safe navigation, or reliable object-to-ground coordinates. “Find the sock in the kitchen” needs a kitchen map/semantic location, localization, and a way to ground camera detections into robot/map coordinates. The model should autonomously gather additional views and invoke bounded search/recovery skills when confidence is low; involve the operator only if the search budget is exhausted, the destination remains unresolved, or a safety/health condition requires intervention. The model supervises task choices, not motor control.

Mapping can be collaborative without making the model the map authority. The Pi mapping/localization stack builds and persists geometric map data and robot pose. The PC model receives selected frames plus the current pose/map context and proposes semantic entries such as a likely room label, landmark, or object observation. A Pi-side map manager validates each proposal against the map version, coordinate frame, pose freshness, schema, and evidence policy before updating a persistent semantic layer associated with the geometric map. Supported labels may be committed automatically from consistent evidence across localized viewpoints; ambiguous evidence should trigger another bounded observation/search step, not an immediate operator prompt. Keep a sidecar/layer rather than using model conversation history or rewriting occupancy-grid values. Send map identity/version and relevant local context to the PC; send only validated structured updates back. This gives the model reusable spatial context on later runs while the Pi retains its last committed map through PC/network outages.

The target runtime is autonomous mapping/exploration and semantic discovery, provided the selected sensors and SLAM/localization/navigation stack support it. For a first “go to the kitchen” request with no room label, the mission executive launches a bounded discovery mission: the navigation stack visits safe, reachable viewpoints, the model inspects selected frames and proposes room labels, and each candidate is tied to the localized pose/map version. The map manager commits labels that meet the evidence policy; the model can request more viewpoints when evidence is uncertain. The operator is contacted only if search/recovery limits are exhausted, the location remains unresolved, or safety/health requires intervention. A later request uses the saved kitchen label directly. This is not free-form model driving: the model supervises task decisions, while the mission executive bounds the search and standard navigation handles movement. During initial hardware commissioning, attend low-speed tests and have the physical stop ready until autonomy and safety have been validated; this should not become a routine teleoperation prerequisite. If the hardware cannot support autonomous mapping/localization, establish that capability before promising autonomous discovery. Camera Module 3 Wide is monocular RGB, not a depth camera; the mapping stack may need reliable wheel odometry and could ultimately require lidar or depth sensing. Do not plan on a point cloud until the sensor and SLAM choices support one.

For “go to the kitchen,” the mission executive queries the semantic map for the kitchen region and map version, resolves that into a geometric goal, then gives the goal to ROS navigation. The navigation stack computes and executes the route from the geometric map; the model does not provide turn-by-turn motion. If the room label is missing but a usable map/localization exists, the mission runs the bounded discovery pass described above and persists a supported annotation for future trips. The model can inspect further views and invoke configured recovery skills; contact the operator only after those fail or when a safety/health condition requires it. Do not navigate autonomously to a room until a usable robot pose/map exists.

Do not select a final model/runtime until measured with the actual camera stream and representative tasks. Cloud VLMs and decision-only models remain research alternatives, not part of the single-model v1 runtime. No model service may be required for teleoperation, safe stopping, or basic motion.

**Jev is not a local VLM or a standalone robot action model.** TypeSafe's official docs describe Jev as a hosted, proprietary text-in/text-out model: software supplies text/JSON state and typed questions, and Jev returns choices/scores with probabilities and confidence. It currently does not accept images, audio, or video, and the weights are not offered for local deployment. It could be tested as an optional fast decision component after a VLM/perception pipeline has converted camera observations into structured text/state, for example choosing among already validated search skills. It cannot find a sock directly from camera frames, generate the conversational answer, replace navigation, or be the only safety gate. Its confidence is useful evidence for routing/escalation, not a guarantee that a specific decision is correct.

This is a **decision-model architecture**, but the decision model should not be the whole controller. It should propose one bounded, typed skill at a time; deterministic code owns execution, state transitions, limits, retries, and cancellation. Avoid letting any model generate `/cmd_vel`, serial frames, motor PWM, or an unbounded action sequence.

## Proposed action boundary

The exact ROS actions are still to be designed after hardware bring-up. A small initial vocabulary could include:

| Skill | Example parameters | Execution owner |
|---|---|---|
| `RotateRelative` | angle, speed limit, timeout | Robot action server / navigation layer |
| `NavigateToPose` | map-frame pose, tolerance, timeout | ROS navigation stack |
| `ScanSector` | angular range, step or scan duration | Deterministic robot skill; returns camera observations/status |
| `Stop` / `CancelTask` | active task identifier | Safety gate / mission executive |
| `ReportObservation` | object label, confidence, image/frame reference | PC perception and operator app |

The model may request one skill, inspect its result and new observations, then request another. The mission executive rejects unknown skills, malformed or out-of-range parameters, actions incompatible with current control ownership, and goals unsupported by localization. Every motion action needs a deadline, feedback, cancellation, and a defined failure result.

For “find the sock in the kitchen,” the PC model interprets the semantic goal; it is not sent as a Pi motion command. The model can request a search strategy, but navigation requires the kitchen to be represented in a usable map/semantic location system. Detecting a sock in an image does not by itself give a safe map coordinate: camera calibration, localization, and a ground-plane/depth method are needed to estimate where it is. Until that exists, a safe first version should stop and show the relevant image/location to the operator rather than claim it has navigated to the object.

## Options assessed

| Option | Local PC use | Fit for this rover | Assessment |
|---|---|---|---|
| Qwen3-VL Instruct (2B/4B/8B) | Yes; public checkpoints and inference code | Language + image interpretation, object grounding, and proposing tools | Recommended single model family to benchmark for v1. Start with 4B at supported 4-bit quantization only if it fits the target PC; compare 2B if memory or latency is inadequate. The current development PC profile is recorded separately. It is not a trained rover controller; validate all proposed skills in mission software. Exact VRAM and throughput depend on precision, image resolution, context, and serving runtime. |
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

Clef-Flash remains a technically interesting local alternative: it accepts image/video inputs and returns typed schema-bounded probabilities through a Jev-compatible interface. It is not part of the v1 recommendation because the project prefers one model and still needs natural-language conversation; running it beside a conversational VLM would add cost and complexity. Reconsider it only if future tests show a meaningful need for specialized typed decisions and suitable GPU hardware is available.

JEPA is a separate concept from Jev. Assuming “JEV” in the earlier question meant the TypeSafe model now that the link is provided, the JEPA discussion above remains only a comparison of another research direction. V-JEPA 2 predicts video representations; V-JEPA 2-AC adds action-conditioned prediction and reports image-goal manipulation results. Neither provides semantic room-level rover navigation. A deterministic behavior tree/state machine is sensible for predictable execution and safety; Jev or a VLM can optionally select among bounded skills. Those components complement each other.

## Rollout and evaluation

1. Implement and test deterministic `RotateRelative` and `Stop` actions with wheel-off-ground tests, angle/time/speed limits, cancellation, and communication-loss stopping. Evaluate a 360-degree request against encoder/odometry feedback; camera imagery is supplementary evidence, not the only turn measurement.
2. Add the operator app and allowlisted mission tools, initially without visual search. Compare model proposals against a fixed schema and reject invalid requests.
3. Benchmark Qwen3-VL Instruct 4B with supported 4-bit quantization on the target PC using recorded rover images and representative requests. Measure end-to-end latency, peak GPU memory, object-identification accuracy, grounding consistency, tool-call validity, and invalid/unsafe action proposals. Compare smaller checkpoints if 4B fails that PC's latency or memory target; repeat this evaluation when changing deployment hardware.
4. Add compressed camera delivery to the PC and a visual inspection/search skill. Build and validate room/map localization and camera-to-map grounding before enabling autonomous object approach.
5. Test Nav2 or the selected navigation stack independently with non-model goals. Only then connect model-planned tasks to navigation actions.

Log images or frame references, prompts, model/provider/version, proposed action, validation result, robot feedback, completion/failure, and any operator intervention. Normal operation should be autonomous within configured skill, search, and safety limits; escalate when the model/mission executive cannot resolve the task after bounded retries or a safety/health gate blocks action. The robot must remain stopped or safely controllable if inference stalls, a model service fails, or Wi-Fi is lost.

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