# Local ASL sign recognition and future live translation

Current priority: a limited-vocabulary individual-sign webcam recognizer running on the existing laptop. No model or app is implemented yet. Continuous live ASL-to-English translation remains a later research phase. Earlier translation feasibility work is retained; the audit below is a translation-data diagnostic, not the current classifier experiment.

Start with [STATUS.md](STATUS.md), then [FEASIBILITY.md](FEASIBILITY.md) and [PROJECT_SPEC.md](PROJECT_SPEC.md). Evaluation requirements are in [EVALUATION.md](EVALUATION.md); experiments, decisions and risks have separate logs.

## Run the small Stage 0 audit

From this directory, with Python 3 and internet access:

```powershell
python scripts/stage0_probe.py
```

This dependency-free script downloads small public metadata and two validation annotation TSVs, checks IDs/timing changes, and reads at most 64 KiB of an author-hosted ASL checkpoint. It writes `artifacts/stage0/probe_report.json`; each check explicitly records success or failure. Exit success means the audit completed, not that every remote endpoint worked. It never loads model weights, downloads videos, trains or reads the final test set. A rerun replaces the current audit report; archive that report before a new dated study.

Research downloads retain their own licenses. Dataset text and model weights are not part of a redistributable application release. See [source audit](artifacts/stage0/source_audit.json) and [experiment log](EXPERIMENTS.md) for exact scope and limitations.
