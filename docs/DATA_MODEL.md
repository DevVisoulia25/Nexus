# Data and baseline provenance

## 2026-11-08 diagnostic updates

R007 (2026-11-10) adds hand-relative geometry as a separate representation.
Finger XY positions are centered on each wrist and scaled by distance between
index and little-finger MCP landmarks. Rotation is preserved. Missing/degenerate
palms stay masked. Original body-relative coordinates and motion remain in the
vector. The original extraction cache is reused; representation choice is stored
in model metadata. This retains only 2D evidence, not depth or RGB texture.

R002's distance gate replaced the initial margin gate in the experimental app
artifact, accepting only 2/39 genuine development clips at 19/20 unknown
rejection. R003 causal cached replay produced no stable known events. R004 is a
separate active-hand window candidate: 34/39 forced-choice accuracy, but failed
rejection. It is not deployed. Optional short-sign boundary handling is ablated
separately and is disabled in the default app. Current code is a prototype;
neither clip accuracy nor blank-frame transport checks validate webcam accuracy.

The temporal candidate uses a small two-layer convolution network and retains
the R004 training-only standardization. Parameters, seeds, runtime version and
export/reload checks are saved by its runner. Models stay local; the private
Colab bundle is for the same user's research runtime and must not be published.

This milestone recognizes individual ASL signs. It does not translate sentences.

## Source choice

Use [ASL Citizen](https://www.microsoft.com/en-us/research/project/asl-citizen/), a consented dataset with video labels and signer IDs. Its [datasheet](https://www.microsoft.com/en-us/research/project/asl-citizen/datasheet/) specifies signer-separated train/validation/test splits and discusses label variation and recording noise. Our metadata check verifies no train/validation signer overlap before downloading any videos. We do not load final test labels or videos.

The [dataset terms](https://www.microsoft.com/en-us/research/project/asl-citizen/dataset-license/) restrict use to noncommercial, non-revenue-generating research and prohibit redistributing the supplied data or modifications. Videos, individual pose features, manifests and model artifacts stay local and ignored by Git. This repository publishes our own implementation and aggregate research results, not the dataset. Do not add data or derived files to a release. This experiment does not authorize commercial deployment.

WLASL was considered through its [official repository](https://github.com/dxli94/WLASL), but source-video disappearance and the missing-video request workflow make a small reproducible first run harder. We do not treat its available weights as interchangeable with the current feature pipeline.

## Fixed first experiment

- Known labels: HELLO, THANKYOU, PLEASE, SORRY, YES, NO, HELP, WATER, BOOK, MILK1. MILK1 is the dataset's particular variant, not a promise to cover all ways of signing milk.
- All available official training/development clips for those labels: 147 train, 39 validation.
- Unknown-sign diagnostic: 20 validation clips, two each from the ten out-of-vocabulary labels recorded in `configs/recognition.json`, selected with seed 20261107 before predictions.
- Archive size observed: 45,924,134,223 bytes. Selected compressed videos: approximately 112.6 MB. A bounded HTTP Range reader retrieves the ZIP directory and selected members only; it refuses servers that ignore ranges. Budget 256 MiB, per-member size limit, ZIP CRC and local SHA256 checks.
- Official test is untouched. The archive directory contains file metadata, but no test CSV or video is opened.

## Representation and model

MediaPipe Holistic 0.10.21 runs on CPU, extracting a per-frame pose, hands and face. The classifier retains 9 upper-body, 42 hand and 20 selected facial points, with xy coordinates and explicit presence masks. Shoulder-center/width normalization is frame-local, not fitted to a whole recording. The full face mesh is detected but only the declared subset is used by this baseline; omitted cues remain a limitation. MediaPipe's legacy solution is deliberately pinned for a reproducible first experiment and is no longer maintained upstream: [upstream documentation](https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/holistic.md). It is a landmark extractor, not an ASL recognizer by itself.

Source clips are sampled at up to 6 fps, with source timestamps and decoder-FPS fallback documented in code. The first one-clip 12 fps feasibility check was slow on CPU; 6 fps was selected before training. A 15-second initial extraction cap rejected one 22.13-second training clip. The cap was raised to 30 seconds, retaining that clip instead of excluding it. The live context remains bounded to 4 seconds; this offline/live duration mismatch must be evaluated.

The baseline resamples each supplied sequence to 24 temporal steps, appends mean/std features, and learns a regularized multiclass logistic-regression classifier (C=0.1). Feature mean and scale are fitted on training data only. This is a compact sequence classifier, not a language model or single-frame hand-pose rule system. Its training examples—not hand-written gesture rules—define the labels.

An internal score-margin cutoff is calibrated to reject at least 90% of the 20 negative development clips. The resulting rejection rate on those same clips is a calibration result, not independent validation. We report known-sign coverage and correct-and-accepted rate as well, because rejecting everything would otherwise look good. No probability or margin is shown as translation confidence. Ordinary movements and independent webcam signing are still missing from evaluation.

## Live processing and limits

Guided testing adds opt-in browser video capture and explicit local report export.
Default operation still records no video. The backend never persists frames or
landmarks; browser reports omit coordinate arrays. See docs/GUIDED_TESTING.md for
retention limits, intended-label caveats and separate calibration/evaluation use.

The browser sends JPEG frames only to the loopback server, one request in flight. The backend processes with one worker per session and accepts one active session. It stores at most 60 feature frames / 4 seconds of context; no camera frames or landmarks are written to disk. UI history contains at most 30 sign events and is cleared on Reset. Tab hiding, Stop, disconnection and watchdog failure release the camera. Captured timestamps and sequence IDs reject stale/out-of-order input; gaps clear context.

The candidate classifier runs at most every 0.4 seconds after at least 0.8 seconds / six usable frames. Three matching accepted candidates emit one event; holding the same sign does not repeatedly append it. Lowering hands out of view briefly or resetting begins another attempt. This rule is a provisional engineering policy, not a validated linguistic boundary detector. Stability is not correctness. The display delay is capture-to-result age, not semantic sign latency.

## Reproduction and storage

`requirements-lock.txt` records the resolved Windows/Python 3.11 environment. Preparation records source hashes, archive ETag, selection seed and source metadata hashes locally. Feature caches verify source hash, feature version and sample rate; changes must invalidate caches. Model NPZ contains fitted parameters and provenance without Python pickle. Dataset and training paths are explicit; scripts fail on missing files or invalid splits rather than silently substituting examples.

Initial resource envelope: 3 GB for environment/runtime/caches, 256 MiB transfer budget for data, 1 GB for clips/features/artifacts, two CPU extraction workers maximum, no dedicated GPU, INR 0. First complete extraction is bounded to this 206-clip manifest; stop and diagnose errors before expanding data. Do not train full-dataset models or start paid services.
