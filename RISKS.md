# Risk register

Current priority update, 2026-11-07: for individual-sign recognition, first investigate labeled-data access/licensing, signer/source leakage, unknown/no-sign false activations, temporal-boundary errors, lost hand/face information and CPU runtime. No classifier experiment has run. The detailed register below remains relevant to the deferred continuous-translation phase; its blockers do not automatically block a small recognizer.

Updated 2026-11-07. High/medium describe project impact, not measured probabilities. Owner: implementation partner for experiments; user for budget and access preferences. No third parties have been contacted.

| Risk | Impact and current evidence | Mitigation / smallest next action | Escalation condition |
|---|---|---|---|
| Access and alignment | High: original versus corrected validation timings differ; corrected raw source archives are large | Establish eight paired clips with exact interval provenance; range/individual access before full archives | No verified valid input/target path within resource cap |
| Checkpoint compatibility | High: Uni-Sign byte access verified, full load not run; How2Sign dev loader unsupported | Pin weights/code/tokenizer/extractor; strict state-dict load; explicit dev adapter; log key/shape errors | Missing critical weights or unavailable matching preprocessing |
| Artifact licensing/provenance | High: Uni-Sign model card CC BY-NC; code license unidentified; checkpoint training history incomplete; WiCV deposit access failed | Inventory each component; clarify terms and training split before redistribution/final claims; consider licensed fallback | Cannot establish appropriate project use or provenance |
| Compute limits | High: CPU-only laptop, 16 GB RAM; free GPU uncertain | Batch-one no-training smoke with time/RAM/disk caps; measure CPU and cache eligible features | No affordable configuration meets quality/latency needs |
| Domain/signer generalization | High: instructional studio data, shared signers/narratives; no independent ASL recordings | Separate benchmark and camera results; group manifests; recruit reviewer/signer when feasible | Webcam errors overwhelm usable content |
| Streaming conversion | High: current demo reads whole video; normalization uses complete supplied sequence | Causal prefix recomputation and suffix-invariance checks; later timed contiguous replay | No useful pre-end output across predetermined set |
| Lost visual information | High: pose face subset omits detail; hand tracking may fail | Retain whole-body extraction; audit missingness; evaluate RGB alternative based on failures | Critical expression/handshape errors dominate |
| Unsupported language output | High: generative decoder can emit fluent common phrases | Preserve raw hypotheses; negative visual controls; no fluency rewrite; semantic review when available | Visual perturbations barely affect generic output or severe additions persist |
| Latency/queues | High: repeated prefix decoding cost and unknown network speed | Timestamp every stage; one pending decode; age limits; bounded context; measure tails | Unbounded growth, stale captions or frequent lost context |
| Deployment reliability | High: no selected always-available free host | Local inference profiling; separate notebook and host; scripted interruptions/restarts | CPU insufficient and reliable remote deployment exceeds INR 0 |
| Evaluation validity | High: no ASL reviewer; imperfect sentence references and no exact evidence alignment | Explicit unavailable semantic measures and latency proxies; lock test protocol | Cannot support a useful-caption claim honestly |
| Reproducibility | Medium: older Fairseq environment and upstream path/validation issues | Isolated pinned environment and reusable modules, raw manifests and hashes; fail instead of silent sample replacement | Clean run differs materially from experiment environment |

If live translation is infeasible at INR 0, report the evidence and discuss options: slower provisional updates if still useful before end, an authorized hosted inference budget, a focused model-efficiency experiment, or continued research with the final objective explicitly unresolved. Offline translation is not renamed live.
