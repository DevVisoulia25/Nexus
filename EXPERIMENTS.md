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
