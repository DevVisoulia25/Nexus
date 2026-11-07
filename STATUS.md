# Project status

Updated: 2026-11-07 (Asia/Calcutta).

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
