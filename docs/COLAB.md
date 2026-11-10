# Free notebook experiment

The app is not complete. R003 reproduced zero emitted detections on the cached
development sequences. R004 improved forced-choice whole-clip classification
from 29/39 to 34/39, but rejection remained inadequate. Candidate artifacts are
kept separate from `models/signs.npz`.

Use `notebooks/train_temporal.ipynb` in Google Colab. Training is an experiment,
not hosting; webcam frames continue to stay on the laptop. Free GPU availability
is variable: https://research.google.com/colaboratory/faq.html.

1. Locally run `.venv/Scripts/python.exe -m nexus.cloud_bundle` after the existing
   data extraction and R001/R002 runs. This creates a small private ZIP in
   `artifacts/recognition/private/colab_features.zip`. It contains derived research
   data, never publish it or notebook outputs containing individual samples.
2. Open the notebook in Colab and run its cells in order. Select a free GPU
   runtime if available; CPU also works for this small experiment. Do not buy
   compute or run a public web server in the notebook.
3. Upload that ZIP only to your own runtime. No Google Drive mount is required.
   The notebook checks file names, sizes and SHA256 hashes before importing.
4. The notebook runs R004, then R005 (a 32-channel temporal convolution network,
   fixed 60 epochs, batch 32, seed 20261107). It saves dependencies, commit ID,
   metrics and candidate weights. No final-test examples are present.
5. Download the private result archive. Do not overwrite the app model: compare
   correct accepted signs, false activations and local CPU runtime first.

Envelope: feature bundle capped at 16 MiB, 206 clips, 100-epoch hard cap, two CPU
threads. Dependencies may need several GB in the notebook runtime; inspect the
runtime before installation. A failed compatibility check should be diagnosed,
not bypassed by silently changing versions. This is not a full-dataset job.

The notebook itself has not been executed in Colab. Local CPU execution results
are tracked separately. CUDA and CPU may differ numerically; runtime versions
and all configurations must accompany comparisons.

Current blockers: small training set, missing ordinary-movement negatives,
unvalidated rejection, independent webcam evaluation, and no ASL reviewer.
