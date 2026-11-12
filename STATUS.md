# Project status

Updated: 2026-11-13 (Asia/Calcutta).

Guided testing is implemented: ten-second attempts, optional local video (off by
default), fixed 39-attempt plan, explicit debug/calibration/evaluation purposes,
model hashes and per-frame decision traces. Reports have a visible copy fallback
and a summary CLI. No automatic training, upload or evaluation-data reuse.

Verification: 27 Python tests and 6 JavaScript tests passed. Synthetic browser
completion, cancellation, fixed-plan cancellation behavior, visible JSON parsing,
and optional video-blob creation passed. Native download completion is unverified
in the in-app browser. No independent user webcam accuracy was collected.

Next action requires real observations: run debugging attempts for Book, Yes,
one failing sign the user knows, and the three ordinary movements; export the
report. Inspect failures before changing thresholds or launching Colab training.
Detailed steps: docs/GUIDED_TESTING.md. Recognition quality gate remains unmet.

User feedback: mainly BOOK, YES and one unidentified sign appeared to work in
their webcam test. Framing conditions and counts were not provided, so this is
qualitative evidence only. Continue the rejection audit before model escalation.

Repository update: the earlier approval-review spend-cap failure cleared on the
user-authorized retry. Prototype commit 20a1a1d was pushed successfully; the guided
testing follow-up is being prepared. Private data and weights remain excluded.

## Current assessment — recognition quality gate NOT met

2026-11-10: R007 adds wrist-relative finger geometry while preserving global
body/hand position and motion. On the same development set, forced-known
full-clip classification improved from R006's 33/39 to 36/39. At zero background
threshold, correct first events improved 23/39 to 24/39 and unknown false-event
clips fell 13/20 to 12/20. Strict rejection still accepted zero correct known
events. Candidate retained for research comparison only, not promoted.

The score audit found unknown gate scores up to 11.90 versus a maximum 7.71
for known development signs; feature magnitudes largely overlap. This does not
support simple clipping as a fix. Next work must address unknown-sign separation
and fresh calibration examples, rather than more threshold tuning on these 59
observed clips. Handshape alone does not solve open-set recognition.

Engineering updates: JPEGs decode once in the worker, candidate model/short-sign
policy can be selected explicitly by CLI, and the UI identifies the experimental
artifact. Candidate status never reuses baseline evaluation. 24 tests passed;
two live transport sessions with ten blank frames passed, and browser status was
verified without activating the camera. These are not webcam accuracy results.

The individual-sign prototype is implemented and has been trained locally. The historical feasibility snapshot below predates this implementation. The user reports intermittent recognition during webcam testing; this is qualitative feedback, not a measured webcam benchmark.

- ASL Citizen subset: 147 training clips, 39 known development clips and 20 unknown development clips; 10 known classes. Final test untouched.
- R001 forced-choice development accuracy: 29/39 (74.4%). With its rejection gate, only 1/39 known examples was accepted.
- R002 changed only rejection: 2/39 known examples accepted, with 19/20 unknown examples rejected on the same development calibration set. This remains inadequate; retaining this experimental artifact does not establish success.
- Camera UI, local inference and bounded session handling exist. Recognition reliability and useful live performance are not validated.
- Code inspection identified a training/live discrepancy: whole-clip training included missing-hand frames, while live windows retained only frames with detected hands/body. R004 measures an aligned-window candidate below.

R003/R004 now executed: original replay emitted no events and skipped decoding on 23/39 known clips. Shared visible-hand training improved forced-choice classification from 29/39 to 34/39. Short-sign policy decoded all 39; rejection still failed (zero correct first known events, one unknown false event). Candidates are not promoted. See artifacts/recognition/replay.json and window_experiment.json.

Implemented: causal cached replay, separate short-sign boundary policy, aligned training candidate, temporal-convolution experiment runner, private hash-checked feature bundle and Colab notebook. Notebook code cells parse; private feature export/import round-trip executed (1.56 MB). Colab itself has not been run. Transport check passed two sessions/ten blank frames, not webcam sign validation.

R005 and the bounded training-negative experiment are complete below. Do not merely lower thresholds, increase vocabulary or claim completion. Ordinary movements and independent webcam behavior still need evaluation.

R005 now executed on local CPU: 32/39 forced-choice, zero correct accepted replay
events. Not promoted. Export/reload parity passed. Colab code is available but a
GPU was unnecessary for this small experiment. R006 adds a bounded training-only
negative subset to test explicit background rejection; results follow below.

Verification: 21 automated tests passed using a workspace-local temporary
directory (the default system pytest temp directory was inaccessible). Notebook
cells parse, JS syntax check passed, private bundle round-trip passed. These
checks validate engineering behavior, not recognition quality.

R006 executed: all 60 training-negative clips extracted successfully (46,189,016
downloaded bytes); none excluded for tracking. Explicit background classifier:
33/39 forced-known full-clip correct. Default zero background threshold produced
23/39 correct first known events but 13/20 unknown clips with false events. The
calibrated strict threshold produced zero correct known events and 2/20 unknown
false events in replay. Not promoted. Current model/data cannot satisfy both
useful recall and rejection. Recognition gate remains failed.

Next focused work: audit high-scoring unknown windows against known examples,
then evaluate a stronger visual representation or more diverse training data
with a separate calibration set. Ordinary-movement and independently recorded
known-sign examples are still required for webcam validation. No further
architecture-size escalation is justified solely by GPU availability.

Original-timing video replay executed on the first three known dev clips:
processed 17/7/4 frames; stale drops 1/58/29; no emitted events. Per-clip median
processing 184/415/338 ms and p95 frame-result age 429/976/1022 ms. This exposes a
second deployment bottleneck in landmark extraction; it is not sign-semantic
latency, and three clips are not a full reliability benchmark.

User is willing to use Colab or Kaggle. Proposed next modelling experiment after the diagnostic: a compact temporal network on the same split, trained in free Colab if needed and benchmarked locally for inference. No cloud training has run, no paid services are authorized, and no improved quality is claimed. Colab resources are variable: https://research.google.com/colaboratory/faq.html.

## Historical feasibility snapshot (superseded for implementation status)

**Current work: individual-sign recognition — initial scope and data feasibility.** No classifier or camera app has been implemented or evaluated yet.

The user chose to pursue individual signs first on the existing laptop, then revisit continuous live translation. Initial proposal: 10 signs, unknown/no-sign behavior, motion-aware inputs where needed, and measured local webcam performance. Continuous translation remains a later objective; its Stage 0 gate is still unmet. Earlier research is retained below and is not evidence of sign-classifier performance.

## Completed

- Captured user scope and confirmed INR 0 / no ASL reviewer.
- Inspected hardware: i5-1235U, 15.71 GiB RAM, integrated graphics, ample initial C: disk; internet throughput remains unknown.
- Read primary dataset/paper/model sources; inspected actual inference/preprocessing code and model catalog.
- Implemented and ran a small bounded access/alignment probe. Downloaded only two validation annotation files and model metadata; tested 64 KiB checkpoint access. No video/full checkpoint downloads or test evaluation.
- Verified 1,741 paired validation rows and substantial original-versus-realigned timing changes.
- Recorded conditional model recommendation, source hashes, resource estimates, risk register, streaming design and acceptance draft.

## Implemented versus validated

| Work | State |
|---|---|
| Product specification and evidence review | Written; technical choices provisional |
| Stage 0 audit script | Implemented and executed; output/schema checks passed |
| Annotation ID/timing checks | Executed; do not validate semantic alignment or video decoding |
| ASL checkpoint access | Catalog and bounded byte access verified; full hash/load untested |
| Translation / preprocessing / training environment | Not implemented or executed |
| Offline quality, streaming quality, latency, deployment | Not measured or validated |
| Numerical acceptance targets | Draft method and some proposed engineering targets; no user agreement yet |

## Deferred translation dependencies

1. Confirm Uni-Sign code-use terms, checkpoint training/alignment provenance and compatible dependencies. Model-card license is not a substitute for a code license.
2. Establish a tiny valid video/pose subset without bulk raw-video download. Corrected labels cannot simply be attached to original clipped files.
3. Execute E001 within free available resources; no runtime compatibility or affordable latency has been established.
4. A competent ASL reviewer/signer is needed for semantic and useful-live-caption claims. Automatic metrics can proceed with this limitation explicit.
5. Internet throughput and final local/remote deployment remain unmeasured/undecided. No webcam video transmission is configured.

## Next action

Verify an isolated-ASL dataset's access, license, labels, motion coverage and signer/source split support. Select a proposed 10-sign vocabulary based on usable examples, then design the smallest CPU baseline and fixed evaluation protocol (R001 in EXPERIMENTS.md). Do not download translation checkpoints or run E001 as the immediate next step. Current risks are small-vocabulary data access, signer leakage, unknown-input false activations, pose information loss and unmeasured CPU speed.

Other project documents: [specification](PROJECT_SPEC.md), [feasibility](FEASIBILITY.md), [decisions](DECISIONS.md), [evaluation](EVALUATION.md), [risks](RISKS.md).
