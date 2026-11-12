# Local ASL sign recognition and future live translation

Current priority: a limited-vocabulary individual-sign webcam recognizer running on the existing laptop. **A prototype is implemented, but recognition is not reliable yet.** Continuous live ASL-to-English translation remains a later research phase. Earlier translation feasibility work is retained; the audit below is a translation-data diagnostic, not the current classifier experiment.

## Run the local prototype (Windows PowerShell)

Read [dataset terms and provenance](docs/DATA_MODEL.md) before preparation.

```powershell
.\setup.ps1
.venv/Scripts/python.exe -m nexus.data.prepare
.venv/Scripts/python.exe -m nexus.extract --workers 2
.venv/Scripts/python.exe -m nexus.train
.venv/Scripts/python.exe -m nexus.rejection_experiment
.\start.ps1
```

Open http://127.0.0.1:8765. Allow the camera, keep hands/face/shoulders visible,
and try one sign at a time. Start, Stop and Reset control the session. Frames
stay in memory on the loopback server; video recording is off by default. Guided
testing offers explicitly enabled local recording and report export. Closing or hiding
the tab releases the camera. A detected label is not evidence of correct ASL.

**Next practical step:** use [Guided camera checks](docs/GUIDED_TESTING.md) to
compare Book, Yes, a failing sign you know, and ordinary movements. Reports
distinguish missing model decisions, rejection and event finalization. Export
them locally for diagnosis; no automatic training occurs.

Preparation retrieves only the bounded subset, not the 45.9 GB archive. Research
videos, features and weights are excluded from Git. Do not redistribute them.
The first experiment uses 147 train, 39 known dev and 20 unknown dev clips.

## Reproduce recognition diagnostics

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m nexus.replay
.venv/Scripts/python.exe -m nexus.window_experiment
```

These diagnostics preserve the app model. Cached replay feeds frames in timestamp
order without future context, but does not sleep at source timing: it is not a
real-time video or latency benchmark. Candidate models remain separate.

## Optional temporal-model experiment

See [Colab instructions](docs/COLAB.md) and [notebook](notebooks/train_temporal.ipynb).
The notebook has not been executed in Colab. Colab is for training, while the app
stays local. For the same small experiment on local CPU after R004:

```powershell
.venv/Scripts/python.exe -m ensurepip
.venv/Scripts/python.exe -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
.venv/Scripts/python.exe -m nexus.temporal --epochs 60 --device cpu
```

PyTorch is optional; the webcam baseline does not require it. No candidate is
automatically promoted. See [experiment results](EXPERIMENTS.md), including
failures. Final test stays untouched.

Additional reproducible diagnostics:

```powershell
.venv/Scripts/python.exe -m nexus.timed_replay
.venv/Scripts/python.exe -m nexus.background_data
.venv/Scripts/python.exe -m nexus.background_experiment
```

Timed replay processes three predetermined development videos at their original
timing, including landmark extraction and stale-frame dropping. It excludes the
browser and camera; frame-result age is not semantic recognition latency.
Background preparation adds 60 training-only other-sign clips with a 96 MiB
transfer cap. R006 did not pass the recognition gate and is not deployed.

Hand-geometry ablation and explicit candidate inspection:

```powershell
.venv/Scripts/python.exe -m nexus.rejection_audit
.venv/Scripts/python.exe -m nexus.background_experiment --handshape
.venv/Scripts/python.exe -m nexus.app --model models/signs-handshape-candidate.npz --short-signs --port 8766
```

This candidate gets 36/39 complete development clips correct when forced to choose
a known sign, but still fails useful rejection. It is for research inspection,
not a reliable upgrade. The normal app model is preserved. The candidate UI names
its artifact and does not show baseline metrics as candidate results.

Start with [STATUS.md](STATUS.md), then [FEASIBILITY.md](FEASIBILITY.md) and [PROJECT_SPEC.md](PROJECT_SPEC.md). Evaluation requirements are in [EVALUATION.md](EVALUATION.md); experiments, decisions and risks have separate logs.

## Run the small Stage 0 audit

From this directory, with Python 3 and internet access:

```powershell
python scripts/stage0_probe.py
```

This dependency-free script downloads small public metadata and two validation annotation TSVs, checks IDs/timing changes, and reads at most 64 KiB of an author-hosted ASL checkpoint. It writes `artifacts/stage0/probe_report.json`; each check explicitly records success or failure. Exit success means the audit completed, not that every remote endpoint worked. It never loads model weights, downloads videos, trains or reads the final test set. A rerun replaces the current audit report; archive that report before a new dated study.

Research downloads retain their own licenses. Dataset text and model weights are not part of a redistributable application release. See [source audit](artifacts/stage0/source_audit.json) and [experiment log](EXPERIMENTS.md) for exact scope and limitations.
