# Experiment log

## R001 — individual-sign data and local feasibility

Status: **proposed, not implemented or executed**, following the 2026-11-07 scope discussion. This is the current priority; translation E001 below is deferred.

Hypothesis: a compact temporal classifier can recognize a small documented ASL vocabulary on the user's CPU with useful response time. First verify dataset terms, access, label quality and signer/source grouping; select a proposed 10-sign vocabulary from usable data, without choosing only successful predictions. Include ordinary movement and out-of-vocabulary inputs in a separate negative set. No architectural choice or CPU performance is established yet.

Next experiment after data verification: fixed training/development groups, a small reproducible baseline, per-class recognition results and end-to-end local runtime. Fit preprocessing only on training data, tune rejection on development data and keep final test untouched. Do not train on the user's improvised signing as authoritative ASL data without validation. Establish download/time/memory caps from the selected data before execution. Budget remains INR 0.

Outcome needed: evidence for which vocabulary is supportable, measured CPU resource use, failure examples and a justified next step. A successful isolated classifier is not evidence of continuous sentence translation.

## E000 — public artifact and validation alignment feasibility

Status: **implemented and executed**, 2026-11-07. Hypothesis: small public metadata downloads can establish a real ASL checkpoint route and reveal whether original clip boundaries are interchangeable with corrected timestamps.

Command: `python scripts/stage0_probe.py`. Standard library only, Python 3.14.3. Network required. Each metadata fetch capped at 2 MiB; checkpoint fetch capped at 64 KiB; no checkpoint deserialization, test access, GPU, model training or video downloads. Outputs and SHA256s: [probe_report.json](artifacts/stage0/probe_report.json). Code/source metadata: [source_audit.json](artifacts/stage0/source_audit.json).

Results:

- Official original and realigned validation annotations: 1,741 matching unique IDs; no unmatched IDs or invalid corrected intervals. Median absolute start shift 3.48 s; median end shift 4.77 s. Maxima 63.74/66.56 s. More than 0.5 s changes: 1,434 starts, 1,488 ends.
- Uni-Sign model catalog HTTP 200; ASL checkpoint range HTTP 206, 65,536 bytes, ZIP signature and total size 1,186,925,007 bytes. This proves partial byte access only, not full download, state-dict compatibility or translation quality.
- WiCV Dataverse API failed certificate-chain validation from Python; web access also failed. Do not disable TLS checking to claim access. Metadata and actual weight download remain unverified for that route.
- Local hardware was read separately and recorded in PROJECT_SPEC. Wi-Fi physical link rate is not measured internet throughput.

Conclusion: reject the assumption that original and corrected time intervals are interchangeable. Prioritize a provenance-aware loader and explicitly matched crops. Uni-Sign has a real accessible ASL artifact, but no execution evidence yet. This is an access/data diagnostic, not an ML translation experiment.

Failures and smallest next actions: Dataverse failure is supported by TLS error text, not evidence the deposit is deleted. Try a normally trusted OS HTTPS client for the small catalog or a publisher-provided alternate endpoint, without disabling certificate verification; budget under 2 MiB, no GPU. Do not begin a full dataset download.

## E001 — smallest useful translation feasibility experiment

Status: **proposed, not implemented or run**. No scores predicted.

Hypothesis: the released ASL checkpoint can produce visually conditioned sequence-to-text output on a fixed small development set within a free notebook's memory/time limits, and prefix-only evaluation can be instrumented without future leakage.

Prerequisites: pin code/model/tokenizer/pose extractor versions; clarify code-use terms and training/split/realignment provenance; establish a small input path. Port an explicit dev adapter because upstream rejects How2Sign dev. Verify every key, shape and normalization; fail on missing weights rather than using partial initialization. Avoid installing legacy research dependencies into the system Python.

Smallest data plan:

1. Select 8 development utterances before viewing predictions, spanning duration quartiles and at least 4 source videos where possible. Use seed 20261107; exclude the final test set. Persist ordered IDs and source groups. Report exclusions and never replace failed clips with attractive examples.
2. For a pipeline smoke only, the official 1.7 GB validation sentence archive is a bounded fallback. Use original timestamps and label results as original-clip diagnostics, not corrected-alignment benchmark reproduction.
3. For quality conclusions, obtain exact realigned crops from long validation sources, or prove the checkpoint's released features correspond to its declared intervals. Investigate individual/range retrieval first. If this needs the full 16 GB raw validation archive, stop the small experiment and revise the resource plan explicitly; do not quietly download it. Upstream Uni-Sign pose parts total 8.47 GB and are not a small-subset download.

Procedure after those prerequisites:

- Load batch one on a free notebook GPU if available. Measure load time, peak host/GPU memory, preprocessing, decoding and wall time separately; synchronize GPU timing. Use eval mode, fixed seed, original decoding configuration and record precision. Do not presume every free GPU supports BF16; report any necessary precision change as an experiment difference.
- Save raw English generations for all eight clips and compute descriptive corpus SacreBLEU and chrF with complete signatures. Eight clips cannot establish benchmark performance. Inspect omissions, additions and repetition; semantic judgments remain unavailable without an ASL reviewer.
- For each clip compare real input against blank/zero pose, temporal shuffle (fixed permutation) and a mismatched clip. Record output similarity, metric changes and unsupported generic text. These controls detect some language-prior failures; passing them does not prove comprehension.
- If offline behavior warrants it, compare prefixes at 25%, 50%, 75%, 100% of elapsed clip time. Re-extract/recompute all sequence-dependent preprocessing using that prefix only. This is an offline prefix diagnostic, **not real-time replay or proof of pre-end useful captions**. Evaluate causal timed replay only at Stage 5.
- Stop after 30 GPU-minutes or 2 hours setup, 20 GB disk allocation, INR 0. Target batch-one peak RAM below 12 GiB and a 16 GB GPU as planning envelopes, not established minima. If no free GPU is available, finish static checks and profile eligible CPU components; no paid fallback.

Success for this experiment: compatible artifact chain, eight traceable paired inputs without silent failures, complete outputs/resource logs, and evidence outputs respond to the visual input. It does not pass Stage 2 by itself. Failure diagnosis order: alignment, preprocessing, model/tokenizer compatibility, domain shift, then capacity. Next experiment must isolate one cause and state expected cost.

## Later experiment template

ID; stage; status (planned/implemented/executed/validated); hypothesis; source commit; data/manifest hashes; seed; environment; configuration; resource cap; exact command; raw outputs; metrics with uncertainty; failures/exclusions; conclusions; smallest next experiment and cost. Register before running. Stage 3 changes exactly one factor with a paired baseline and ablation.
# Recognition update — 2026-11-08

## 2026-11-10 — R007 audit and hand geometry

User reports mainly BOOK, YES and one unspecified sign worked; no counts or
framing details supplied. Treat as qualitative evidence, not per-sign accuracy.

Audit of R006: known dev gate-score maximum 7.71, unknown maximum 11.90; known
dev standardized RMS median 0.83 vs unknown 1.04, with overlapping ranges and no
unknown standardized coordinates above magnitude five. Simple clipping is not
supported as the cause/fix for overconfident unknown classifications.

R007 hypothesis: hand-relative finger geometry improves separation. Changed only
representation versus R006. Added wrist-centered, palm-width-scaled XY coordinates
with masks, preserving hand orientation and all original body-relative features.
Same 147 known/60 background training clips, split, C=.1, seed and calibration
rule. No new downloads. Run: `python -m nexus.background_experiment --handshape`.

Result: forced-known full-clip correct 36/39 (R006 33/39). Zero background threshold:
24/39 correct first events, 12/20 unknown clips with false events (R006 23/39 and
13/20). Strict calibrated threshold: zero correct first known events and 1/20
unknown false-event clips. Runtime 34.73 s on CPU. This improves forced-choice
classification but fails usable open-set recognition; not promoted. Test untouched.

Next smallest useful step: a fresh, predetermined calibration/evaluation protocol
with unknown and ordinary-movement examples, plus visual review of false-positive
windows. Repeated tuning on the current 59 dev clips cannot establish generalization.
Existing caches support further diagnostics at no download/GPU cost. An ASL-fluent
reviewer remains unavailable, limiting claims about independent signing examples.

R003 executed: causal cached-feature replay of the deployed R002 model. No
events on 39 known clips; 23 never decoded. Even disabling rejection produced
zero stable events with the original timing policy. This isolates an engine
timing failure independently of rejection. It is not wall-clock real-time replay.

R004 executed: active-hand training window alignment improved forced-choice
accuracy 29/39 to 34/39. A separately ablated short-sign policy decoded all 39
clips; without rejection its first event was correct on 25/39. With rejection,
zero correct first known events and one unknown false event remained. Candidate
not promoted. Report: artifacts/recognition/window_experiment.json. CPU run
13.52 seconds; no new video download. Likely remaining causes: gate calibration
on full clips versus partial windows, too little background data, weak model
generalization. No causal attribution beyond the controlled comparisons.

R005 implementation: fixed 60-epoch small temporal convolution classifier with
the same active windows, split and training-only normalization. See the measured
report if present; Colab execution is not claimed. Candidate export/reload parity
and CPU classifier timings are included in its runner. It does not auto-promote.

R005 executed locally on CPU: 32/39 full-clip correct, 24/39 correct first forced
replay events, zero correct accepted replay events. This fails to improve on
R004; candidate not promoted. The 23,914-parameter model exports to 118,664 bytes
and reloads with identical class predictions. Final reproducible run: 25.03 s;
CPU classifier p50 5.18 ms/p95 6.53 ms, excluding landmark extraction. An earlier
run exposed float32 threshold rounding; calibration comparisons now use float64
and 19/20 unknown dev clips are rejected. Fixed-seed retraining reproduced 32/39.

R006 next experiment: add 60 training-only negative signs from 20 glosses,
excluding both known labels and the existing unknown-development glosses.
Compare an explicit background-class gate against zero-threshold background
classification, retaining the aligned linear architecture. Download capped at
96 MiB and two extraction workers. No ordinary-movement coverage is implied.

R006 executed: 46,189,016 downloaded bytes, 60/60 features valid. Training/evaluation
took 48.31 seconds. Forced-known accuracy 33/39. At background threshold zero,
23/39 first events were correct but 13/20 unknown clips emitted a false event.
Strict dev-calibrated threshold: zero correct known first events, 2/20 unknown
clips emitted an event. Rejected candidate; a larger model is not supported by
this result. An observed Windows process snapshot during R006 showed peak working
set 154,836,992 bytes; this is a process snapshot, not whole-application peak RAM.
Next smallest diagnostic: inspect false-positive windows and compare visual
features, with fresh calibration data before further model selection. Existing
features suffice for that diagnostic; no additional paid compute is needed.

Timed replay engineering check executed: first three known dev clips in fixed
manifest order, original CFR timing, real decoder/landmark/engine processing,
single in-flight frame and stale-frame dropping. Processed 17/7/4 frames with
1/58/29 stale drops; no events. Per-clip median computation 184/415/338 ms and
p95 frame-result age 429/976/1022 ms. See artifacts/recognition/timed_replay.json.
This is evidence of extraction throughput limitations, not a recognition latency
success. No browser/camera/network is included. Next efficiency comparison must
measure hand-tracking fidelity as well as speed before lowering image resolution.

R001 executed: 147 training clips; 39 known and 20 unknown development clips. Forced-choice accuracy 29/39; accepted known examples 1/39 after margin rejection. See artifacts/recognition/baseline.json.

R002 executed: change rejection gate only to nearest-training-feature distance. Accepted known examples 2/39; unknown rejection 19/20 on the same calibration set. See artifacts/recognition/rejection_experiment.json. This is not adequate recognition and does not establish generalization. The user reports inconsistent webcam recognition.

Next diagnostic (planned, not executed): compare full-clip inference with causal replay through RecognitionSession using cached landmarks. Hypothesis: different handling of missing hands and incomplete windows contributes to missed recognition. Resource cost: no new download or GPU; runtime to be measured. Fix and compare window preparation before training a larger model. Free Colab temporal-model training is proposed, not executed.
