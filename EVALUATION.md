# Evaluation contract — draft v0

## Measured development results — 2026-11-08

These are development results, not final acceptance. Final test remains untouched.

| Experiment | Forced-choice full-clip correct | Correct first event in causal cached replay | Unknown clips with event |
|---|---|---|---|
| R003 deployed R002 model, original engine | 29/39 | 0/39 | 0/20 |
| R004 aligned training, original engine | 34/39 | 0/39 | 0/20 |
| R004 aligned training, short engine, rejection disabled (diagnostic) | 34/39 | 25/39 | Not an unknown-rejection system |
| R004 aligned training, short engine, rejection enabled | 34/39 | 0/39 | 1/20 |
| R005 temporal convolution, short engine, rejection enabled | 32/39 | 0/39 | 1/20 |
| R006 background class, zero threshold | 33/39 (forced known) | 23/39 | 13/20 |
| R006 background class, dev-calibrated threshold | 33/39 (forced known) | 0/39 | 2/20 |
| R007 hand geometry, zero threshold | 36/39 (forced known) | 24/39 | 12/20 |
| R007 hand geometry, dev-calibrated threshold | 36/39 (forced known) | 0/39 | 1/20 |

Original engine never decoded 23/39 known clips. Short-sign policy reduced that
to 0/39. Policy: minimum 3 frames/0.25 s; optional final prediction after 0.5 s
of observed no-hands, with body framing still valid. It never fabricates trailing
frames to finish an attempt. This candidate policy is not deployed by default.

The improvement in forced-choice accuracy does not establish useful recognition.
Rejection is unresolved. Ordinary movement false activations/minute and
independent webcam accuracy remain unmeasured. Cached replay is causal but does
not sleep at source timing and cannot measure camera throughput or semantic
latency. Quality flags are reconstructed from cached landmark masks.

Transport-only check: two reconnecting loopback sessions, ten generated blank
frames, zero emitted events. Timings in artifacts/recognition/transport.json
exclude real signing and cannot be presented as sign response delay.

## Current deliverable: individual-sign recognition

Scope update 2026-11-07. Use the following draft for the first deliverable; retain the continuous-translation contract below for the later phase. No numerical performance thresholds have been agreed. Set them from development measurements before the final test; do not choose test examples by prediction quality.

| Requirement | Measurement method | Baseline | Target | Final result |
|---|---|---|---|---|
| Limited-vocabulary recognition | Fixed signer/source-separated test; macro F1, balanced accuracy, per-class precision/recall and confusion matrix | NM | Proposed 10 signs; quality threshold after pilot | Not evaluated |
| Unknown/no-sign behavior | Separate out-of-vocabulary signs and ordinary movements; false activations/minute, known-sign recall and rejection coverage | NM | Calibrate on development only; freeze threshold before test | Not evaluated |
| Motion and boundaries | Static versus moving signs, repeated signs, held signs and transitions; misses and duplicate events | NM | No framewise-label concatenation; event thresholds after pilot | Not evaluated |
| Local responsiveness | End-to-end p50/p95 detection delay, processed fps, CPU and peak RAM on this laptop; declare temporal window | NM | CPU deployment preferred; latency target after measurement | Not evaluated |
| Robustness and controls | Predetermined lighting/framing/speed variations and start/stop/reset/camera-loss scenarios | NM | Freeze supported conditions and recovery criteria before final evaluation | Not evaluated |

Report untrimmed webcam behavior separately from pre-segmented clip accuracy. Verify signer identities where possible; if unknown, use source grouping and avoid unseen-signer claims. No competent ASL reviewer is currently available, so dataset-label correctness and independent user signing remain limitations. Classification probability alone is not calibrated confidence.

## Later phase: continuous translation

2026-11-07. No translation baseline, latency result or final target has been measured or agreed. E000 measured metadata/access only. `NM` means not measured; `N/A` means not applicable, never zero. Targets below marked **proposed** require review after baseline measurements. Record agreement and freeze this file before final evaluation. A failed target remains a failure unless a prospective change is explicitly agreed and documented.

## Acceptance matrix

| Requirement | Measurement method | Baseline | Target | Final result |
|---|---|---|---|---|
| Genuine continuous ASL-to-English translation | Paired unseen-in-project dev clips, raw hypotheses, references, visual negative controls; verify trained sequence-to-text path | NM | Visual conditioning and useful semantic content; threshold after Stage 2; competent review needed | Not evaluated |
| Benchmark quality | Corpus SacreBLEU BLEU-4, chrF; optionally ROUGE-L/BLEURT to match selected paper; record every metric version/signature and reference normalization | NM; published WiCV 8.03 is context, not our baseline | Reproduction tolerance and quality floor after compatible baseline run; agree before final test | Not evaluated |
| Semantic fidelity | ASL/English reviewer examines signed input, reference and outputs; score meaning, negation, quantities, entities, omissions and unsupported additions separately | Unavailable: no reviewer | Reviewer availability and rubric unresolved; no human-fidelity pass can be claimed without review | Not evaluated |
| Pre-end useful captions | On fixed timed replay and independent live sessions, reviewer marks first supported useful phrase and utterance end | NM | Fraction of utterances with useful text before end: set after pilot; must be demonstrably greater than zero for Stage 5 | Not evaluated |
| Time to first displayed caption | First nonempty provisional display minus first signing-frame timestamp | NM | p50/p95 targets after Stage 5 pilot; distinguish from usefulness | Not evaluated |
| Caption latency | Display time minus annotated availability of the evidence supporting a phrase; otherwise explicit proxies below | NM | p50/p95 quality-latency tradeoff agreed after baseline | Not evaluated |
| Finalization delay | Commit time minus supported phrase evidence time, or utterance-end proxy when evidence alignment absent | NM | p50/p95 threshold after boundary pilot | Not evaluated |
| Offline versus streaming quality | Same clips and references; full-input offline decoding versus timestamped prefix-only replay; paired metric differences and grouped bootstrap intervals | NM | Permitted quality loss agreed after sweep; no independent cherry-picked sets | Not evaluated |
| Revision frequency and stability | Token edits per minute, erased tokens per emitted token, time to last edit; visible post-commit amendments separately | NM | Threshold after measured quality/stability frontier | Not evaluated |
| No future frames | Input provenance and timestamps at every stage; mutate unavailable video suffix and check prefix outputs unchanged | Not implemented | **Required: 0 future-frame dependencies**, including normalization/cropping/interpolation | Not evaluated |
| Bounded processing | Queue length, oldest-frame age, inflight requests, bytes, context duration, drops/gaps every second under overload | Not implemented | **Required: no unbounded growth**; initial queue caps 2 raw, 1 active decode, 1 pending; caps are provisional design values | Not evaluated |
| Throughput and resources | Effective processed fps; real-time factor; CPU/RAM/GPU/network; cold/warm runs, concurrency and thermal effects | Hardware known; runtime NM | Fit available machine/free experiment resources; practical cadence agreed after profiling | Not evaluated |
| Pause/boundary handling | Short internal pauses, long pauses, slow signing, continuous multi-sentence input; false splits/merges and timeouts | NM | Thresholds after annotated development pilot; pause alone must not force finalization | Not evaluated |
| Overlap and committed captions | Segment ownership/revision event audit; scripted repeated phrases and overlapping windows | Not implemented | **Required: 0 system-caused duplicate segment commits; 0 silent changes to committed text** | Not evaluated |
| Controls and recovery | Start/stop/reset cycles, permission denial, camera loss, network loss, delayed/out-of-order replies and process restart | Not implemented | Proposed: 20/20 scripted control/recovery scenarios; old-session results never displayed | Not evaluated |
| Session reliability | Three predetermined 10-minute live sessions on actual computer; log faults, context caps, drop rate and restart requirements | NM | Proposed: no crash or uncontrolled backlog in all three; this is a demo-level check, not an availability guarantee | Not evaluated |
| Input robustness | Fixed framing, lighting, background and signing-speed variations; report each condition and missingness | NM | Support envelope chosen from measurements; never relabel failed supported conditions after final testing | Not evaluated |
| Unseen signer generalization | Verified signer/source-disjoint subset or independent consented recordings | NM; default How2Sign split insufficient | Claim only if actual checkpoint training and evaluation signer identities support it | Not evaluated |
| Retention/network behavior | Inspect actual files, logs, packet destinations and session teardown in chosen deployment | Not implemented | Stated policy matches implementation; no unapproved persistent camera recording | Not evaluated |
| Reproducibility | Clean isolated install, manifest validation, deterministic subset and command execution on a second environment | Not implemented | All documented stages run with pinned assets/configs; explicit hardware exceptions | Not evaluated |

## Timing definitions

Use a monotonic client clock. Every frame has source PTS (for replay), mapped capture/arrival time, and frame ID. Every result has session ID, segment ID, hypothesis revision, latest observed frame timestamp, input cutoff timestamp, enqueue time, compute start/end and display acknowledgment. Never subtract unsynchronized server and client clocks. Report server compute duration on its own clock and client round-trip/display times on the client clock.

- **Inference time:** model computation from compute start to finish. Report visual encoder and text decoder separately when both run; GPU timing requires synchronization. Preprocessing, queueing, network and rendering are separate costs.
- **Caption latency:** for an expert-aligned unit whose meaning becomes available at time `e`, latency is `display_time - e`. ASL/English reordering means token offsets are not sign timings. This measurement is unavailable without appropriate annotation.
- **Finalization delay:** `commit_time - e` for that same supported unit. Also report `last_revision_time - e`, because a committed caption can receive a visible amendment later.
- **Evidence-age proxy:** `display_time - newest_used_frame_capture_time`. Measures pipeline freshness, not semantic delay: the relevant evidence may be much earlier.
- **Utterance completion proxy:** `commit_time - annotated_utterance_end`. Measures closure delay, not first-caption latency. Disclose boundary annotation uncertainty.
- **Time to first nonempty text:** `first_display - signing_onset`. A generic hallucination can score well here; report separately from first **useful** caption, which needs competent review.
- **Real-time factor:** total processing wall time divided by source duration; also measure scheduling deadline misses under actual periodic decoding. Offline RTF below one alone does not imply responsive streaming.

Report p50 and p95 across predetermined units, sample counts, empty-caption/failure fractions, and source-group bootstrap intervals where appropriate. Averages alone conceal stalled utterances. First-use model loading is a separate cold-start measurement.

## Data, split and test policy

1. Audit official split/source/signer metadata separately from opening final test content or translations. Preserve official split membership for comparable benchmark reproduction. Report known overlap; do not fix a contaminated pretrained checkpoint by merely moving evaluation rows.
2. Group additional training/development partitions by original source narrative and recording, not random sentence row. Check exact/perceptual duplicates and interval overlap; hash complete clips and source identifiers. All views/overlapping crops of one source stay together. Report any excluded cross-split groups and resulting benchmark differences.
3. Train tokenizers, normalizers, projection layers and learned preprocessing only on training data. Save fitting manifests. Do not mine test captions for lexicons, prompts or error-driven choices. Track author-pretrained data as a separate source of potential contamination.
4. E001's eight examples are diagnostics. Before Stage 2 comparisons, lock a larger development manifest (proposed 100 source-stratified clips with a documented seed) and retain failures. Use the full applicable held-out benchmark for the final report, or predeclare a resource-limited sample and restricted claims. Do not choose examples based on model outputs.
5. Maintain a second, independent webcam set when consented ASL signers become available. Include new signers only with verified independence from training. Benchmark results and camera results are separate tables; playing a benchmark video to the camera is only a pipeline diagnostic.
6. Freeze model, preprocessing, decoding, streaming/boundary settings, data exclusions, acceptance targets and hashes before opening the final test set. Log the first test evaluation. Subsequent development needs another untouched holdout or must be disclosed as test adaptation.

## Fidelity and visual controls

Preserve raw generations and display transformations. Score counts and severity of unsupported additions, missing content, negation reversals, wrong numbers/units/entities and repetition. With no ASL reviewer, automated text/reference mismatches are flags, not authoritative judgments of signed meaning. Reference translations can themselves be imperfect. No token probability will be displayed as translation confidence.

Blank input, temporally shuffled input and mismatched-video controls test reliance on visual evidence. A drop in BLEU is useful diagnostic evidence, not proof of faithfulness. If a refinement language model is later added, compare raw and refined outputs blind to reviewers and measure added unsupported content. Abstention thresholds require evaluated error/coverage curves and representative negative inputs before adoption.

## Streaming protocol

Replay original source timing; at wall time `t` only deliver frames whose mapped arrival is at most `t`. Never precompute whole-video normalization, temporal features, endpoint detection or sampling based on future frames. Offline preprocessing is permitted only when its output is provably per-frame and future-independent, with availability times preserved and compute costs separately measured. Real-time replay must include or account for actual preprocessing cost.

Use contiguous source recordings for long-stream evaluation. Concatenated sentence clips are explicitly synthetic stress tests; they cannot establish natural coarticulation or pause handling. Mutate withheld suffixes to catch hidden look-ahead. Test delays, dropouts and reordering with logged injection schedules and fixed seeds. Compare context lengths/cadences on development data, then freeze one policy.

Revision metrics: compare successive tokenized hypotheses per segment with a fixed edit-distance implementation. Count substitutions/deletions, avoid charging append-only growth as erased text, and report denominator conventions. Keep committed-caption amendments separate. Duplicate text is not automatically a duplicate event; repeated signs/phrases may be legitimate.

## Reporting and failure policy

Show all selected items, failed runs, omitted/dropped frames and boundary errors, plus representative successes and failures chosen by a fixed rubric. Record actual resource use and spending. No numerical baseline or final result can be populated from a paper, an estimate or a functioning UI. If competent review remains unavailable, semantic fidelity and useful-live-caption acceptance remain unresolved.
