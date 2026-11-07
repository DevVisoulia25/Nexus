# Stage 0 evidence and recommendation

Scope note, 2026-11-07: this report concerns the **later continuous-translation phase**. The user has since prioritized local individual-sign recognition; its dataset and model feasibility are not established by this report. See STATUS.md and experiment R001 for current work.

Checked 2026-11-07. **V** = verified source/access/code fact; **M** = measured locally; **A** = planning assumption; **H** = hypothesis to test. Published scores are not our results. Downloadable bytes do not establish checkpoint compatibility.

## Dataset choice

| Dataset | Primary-source evidence | Decision |
|---|---|---|
| How2Sign | Instructional ASL/English corpus, studio recordings, sentence timestamps and published translation baselines. Public page lists RGB and 2D body/face/hands downloads, CC BY-NC 4.0 and research use. | Tentative primary benchmark; record annotation version and investigate alignment first. |
| OpenASL | Authors provide a larger web-video ASL/English resource and collection instructions; independent research notes sentence-level splitting. [Repository](https://github.com/chevalierNoir/OpenASL), [split discussion](https://arxiv.org/html/2306.15162#S5). | Defer: web availability/provenance and source-video grouping add work; useful later for domain-shift comparison. Access/license details not fully audited here. |
| YouTube-ASL | Authors report about 1,000 hours and over 2,500 signers, with no supplied train/dev/test splits and evaluate on How2Sign. [Paper](https://arxiv.org/html/2306.15162). | Defer scaling and pretraining; unnecessary cost for the first feasibility test. |

**V — How2Sign caveats.** The original paper reports 31,128 / 1,741 / 2,322 green-screen clips and 8 / 5 / 6 signers for train/dev/test; validation has no signer absent from training. One test signer is absent from train, with a described 26-video subset. The overall test set is not signer-disjoint. English instructional source material was interpreted into signing, with some participants reporting contact signing alongside ASL. The paper describes additional depth/Panoptic modalities; that does not prove every advertised modality is currently downloadable. [Original paper](https://arxiv.org/pdf/2008.08143).

**V — alignment.** The public sentence RGB clips use original English timings. Manually realigned timings require cropping the long source videos. These are sentence-level intervals, not sign/word alignments. Listed frontal download sizes: long train/dev/test videos 290/16/23 GB; sentence clips 31/1.7/2.2 GB; 2D keypoints 21/1.2/1.6 GB. Download only necessary views. [Dataset and license statement](https://how2sign.github.io/).

**M — E000.** Both official validation TSVs downloaded and parsed: 1,741 matching unique sentence IDs, zero unmatched IDs and zero nonpositive/negative corrected intervals in the checked pairs. Median absolute start/end shifts: 3.48/4.77 seconds; maxima 63.74/66.56 seconds. 1,434 starts and 1,488 ends shift by over 0.5 seconds. These are metadata timing differences, not measured semantic misalignment; no videos were decoded. [Local evidence](artifacts/stage0/probe_report.json).

**V — leakage.** Later primary research reports shared How2Sign signers and some shared narratives across train/test. Audit original source ID, recording/take ID, signer, timestamp overlap, hashes and duplicate texts. Do not claim unseen-signer generalization from a standard aggregate score. [YouTube-ASL paper, section 5](https://arxiv.org/html/2306.15162#S5).

## Model evidence table

| Candidate | Verified capabilities | Data/checkpoint access | Compute requirements | Streaming limitations | Decision |
|---|---|---|---|---|---|
| [Uni-Sign How2Sign pose-only](https://github.com/ZechengLi19/Uni-Sign) | V: body/hand/selected-face pose to mT5 sequence-to-text; ASL-specific checkpoint; separate recognition tasks exist but are not our target | M: official checkpoint catalog and HTTP 206 byte access; 1,186,925,007 bytes, CC BY-NC 4.0 model card. Code license unverified: root has no license file; GitHub reports null. | V: default CUDA/BF16 demo; mT5-base dependency. A: batch-one 16 GB GPU trial, 8–12 GiB host RAM budget; no measured peak yet. | V: demo reads all video frames before inference; clip-wide normalization, temporal encoder and full-prefix text generation; no live-caption protocol. | **Conditional first feasibility candidate**, subject to compatibility, provenance and code-use clarity. CPU throughput is unknown. |
| [Tarrés et al., WiCV 2023](https://github.com/imatge-upc/slt_how2sign_wicv2023) | V: offline RGB I3D features to 6-layer encoder/3-layer decoder Transformer, 256-wide; published BLEU-4 8.03, not a project result | V: MIT code, linked tokenizer/features/weights in [Dataverse](https://dataverse.csuc.cat/dataset.xhtml?persistentId=doi%3A10.34810%2Fdata693). Indexed deposit says CC BY-NC-ND 4.0; live catalog/weights access not established here. | V: Python 3.8/PyTorch 1.11 environment; GPU training. A: cached-feature batch-one inference may be modest; RGB extraction must be measured separately. | Offline I3D temporal support and encoder attention require prefix-safe extraction and recomputation; a small decoder alone does not imply live video speed. | Fallback once deposit access, extractor/checkpoint chain and artifact terms are verified. |
| [SpaMo](https://github.com/eddie-euijun-hwang/SpaMo) | V: offline spatial CLIP + VideoMAE features to Flan-T5-XL; paper evaluates How2Sign | V: README links features and one generic checkpoint; inspected default config is PHOENIX, not How2Sign. ASL weight identity, bytes and code/checkpoint license not verified. | V: CUDA, BF16 config, two vision towers plus XL decoder. A: substantially heavier starting point; no VRAM claim made. | Motion windows and full-clip features; no verified causal prefix/revision implementation. | Defer; cannot treat a generic checkpoint as ASL-compatible. |
| [StreamSLST](https://github.com/streamsl/StreamSLST) | V: author code for pose-based joint temporal localization and translation using sliding windows and mBART; includes H2S settings | V: source tree accessible. README has no pretrained checkpoint download; no license identified in root or API metadata. H2S real-stream versus synthetic recipe needs reconciliation. | V: training recipes use 50 + 100 epochs, 1024-dimensional model and GPU evaluation. A: scratch training is outside first zero-cost experiment. | Sliding-window detection alone does not prove causal output before an event ends; must audit window support, aggregation and availability timestamps. | Research reference for Stage 5; no verified drop-in model. |
| [SSVP-SLT / SONAR ASL](https://github.com/facebookresearch/ssvp_slt) | V: RGB sign-video pretraining/translation; separate SONAR ASL complete-video demonstration | V: primarily CC BY-NC 4.0 code; demo documents model downloads but explicitly uses DailyMoth fine-tuning. We did not verify artifact bytes or a matching How2Sign translator. | V: documented feature extraction uses FP32 32 GB V100s, batch 2. This is a reported setup, not a minimum. | Complete-video pipeline, long feature windows and domain mismatch; streaming support unverified. | Secondary RGB alternative after small baseline; do not substitute its demo score for How2Sign reproduction. |

## Why the first recommendation is conditional

Uni-Sign is attractive because an ASL-specific model artifact is publicly accessible and its input can be compact. That is evidence for a low-cost experiment, not evidence for a working local live translator. In the [audited code](https://github.com/ZechengLi19/Uni-Sign/tree/eed438bcb49e30405cd6ccdfcccca330c134e830):

- `demo/online_inference.py` buffers the entire video before pose extraction and decoding, uses CUDA, and emits a final prediction. The title “online” does not meet this project's live requirement.
- `datasets.py` rejects How2Sign `dev`; `config.py` has an empty dev label path and placeholder WLASL pose paths for ASL. A small explicit validation adapter is needed; do not reuse test as development data.
- `crop_scale` finds extrema across the supplied sequence. Whole-video preprocessing followed by slicing would leak future information into replay. Prefix recomputation changes normalized older poses, so an incremental feature cache needs special care.
- The model consumes 9 body, 21+21 hand and 18 selected facial points. Preserve all extracted 133 points in transient buffers/opt-in caches; the baseline itself cannot be credited with using the omitted expression cues.
- Fixed checkpoint training provenance and preprocessing/alignment version remain to be established. A published checkpoint may already reflect its authors' test-driven decisions; we cannot promise an independent test history. Document that limitation and obtain independent camera evaluation later.

Record file blob hashes and code revisions in [source_audit.json](artifacts/stage0/source_audit.json). Weight SHA256 from the author catalog: `1bfd5f3312f04e4736f0a52f4ef9535916e6de9676a2a0d00c708748683fb00d`; catalog revision `eab251b7fe7e8521afc0e67be98add670ea40a0d`. Only the first 65,536 bytes were fetched, not the full hash verified.

## Resource envelope

| Work | Storage / memory estimate | Runtime/cost policy |
|---|---|---|
| E000 metadata audit (executed) | 695,405 response bytes read for successful checks, including discarded checkpoint prefix; small local logs/TSVs | Seconds of local work, INR 0; not an internet speed test |
| E001 checkpoint + 8-clip smoke (planned) | 1.19 GB translation weights; allow 3 GB more for mT5/tokenizer/pose assets, 4 GB for environment, up to 2 GB compressed input and 2 GB derived data; reserve 20 GB disk. Measure actual manifest before transfer. | No training; single free GPU only if available; stop after 30 GPU-minutes of inference/debugging or 2 hours setup. This is a cap, not a performance forecast. INR 0. |
| Full supplied Uni-Sign pose archive (not requested now) | M: catalog parts total 8,465,474,575 bytes, before extraction; their supplied merge command adds another compressed copy | Avoid full download for a smoke test; establish subset extraction or extract pose from selected videos |
| Future How2Sign experiments | Frontal original sentence archives alone about 34.9 GB; full long frontal set about 329 GB before extraction/caches | Do not bulk-download at Stage 0. Raw-video re-alignment can be the dominant storage cost. |
| Local streaming prototype | A: 30 s × 30 fps × 133 × 3 × 4 bytes ≈ 1.44 MB raw pose coordinates/scores; model/activations dominate; raw 720p RGB at the same duration would be about 2.49 GB | Keep raw-frame buffers short. End-to-end CPU speed, peak RAM and power/thermal behavior need measurement. |

mT5 is a generic text model, not an ASL translator without the trained visual path/checkpoint. Its [model card](https://huggingface.co/google/mt5-base) declares Apache-2.0; it does not resolve Uni-Sign code permissions. Do not blanket-license downloaded artifacts with our code. No weights/data will be republished by default.

Ideal transfer-time arithmetic only: `seconds = 8 × bytes / link_bits_per_second`; at a hypothetical 20 Mbps, 5 GB takes about 33 minutes before overhead. This is not this user's measured bandwidth. No paid hosting price is needed while spending remains zero; stable free GPU hosting is not assumed.

## Gate assessment

Stage 0 research and a small metadata/access experiment are delivered. **The gate is not fully met yet.** There is a technically plausible path, but an affordable compatible baseline runtime and deployable licensing/provenance chain remain unverified. First resolve the small subset/checkpoint issues and run E001, not large-scale training. Stage 1 has not begun. Streaming usefulness remains a research hypothesis even if E001 passes.
