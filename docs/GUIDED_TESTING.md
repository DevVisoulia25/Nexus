# Guided webcam diagnosis

This measures what the application did during your attempt. It does not verify
that you performed the intended ASL sign correctly, and it does not train a model.

## First practical check

1. Start the current server with `./start.ps1`, open http://127.0.0.1:8765 and
   refresh the page. Scroll to **Guided camera checks**.
2. Choose **One diagnostic attempt** and **Debugging**. Start with Book and Yes,
   which previously appeared to work, then a sign you know that failed. Do not
   guess unfamiliar signs merely to fill the set.
3. Keep recording unchecked initially. Click **Start guided attempt**. Wait for
   **Begin**, perform the sign once, then lower your hands. The ten-second attempt
   ends automatically and releases the camera. Each attempt starts fresh context.
4. Also try **Rest without signing**, **Adjust glasses or touch your forehead**,
   and **Reach for an object**. These measure false activations during ordinary
   movement; they are not unfamiliar-sign examples.
5. Download the diagnostic report. If the browser blocks a download, use
   **View / copy report**, copy the JSON, and save it as `nexus-diagnostics.json`.
   Keep files under `recordings/` or outside the repository; default export names
   are also ignored by Git. No report is automatically uploaded or used to train.

The labels mean:

| Observation | What it establishes |
|---|---|
| No processed frames | No usable responses arrived during the attempt |
| No model decision | The engine did not invoke the classifier; inspect tracking and window timing |
| Matching candidate rejected | The classifier proposed your intended label, but its gate rejected it |
| Matching candidate not finalized | An accepted matching candidate did not become a stable event |
| Different / mixed events | Some emitted labels differ from your intent |
| Interrupted | Cancellation, reset or failure; excluded from completed results |

These are observations, not definitive root-cause or linguistic diagnoses.
Frame-result delay is not semantic sign latency. Raw scores in the JSON are
internal diagnostics, never calibrated translation confidence.

## Separate calibration and evaluation

The fixed set contains the ten supported signs and three ordinary movements,
repeated in the same order for three rounds: 39 ten-second attempts. Each start is
manual. Cancelled attempts stay in the report but do not advance the plan. This
protocol is meaningful only for someone who knows the requested signs.

Choose **Future calibration** for examples we may later use to select thresholds.
Choose **Evaluation** for a separate session; it enforces fixed order and hides
live predictions. Purpose and protocol lock once results exist. Never reuse an
evaluation recording for training or tuning. Clear diagnostics to begin a new
purpose after exporting; label intentions still require qualified ASL review.

Summarize locally:

```powershell
.venv/Scripts/python.exe -m nexus.report recordings/nexus-diagnostics.json
```

The command separates purpose, protocol and model hash; counts interruptions
separately; and reports ordinary-movement false events per minute. It does not
change weights or thresholds or present intended-label matches as ASL accuracy.

## Optional video and privacy

Recording is off by default. Checking the video option explicitly enables browser
MediaRecorder for that attempt, without audio. Only the latest recording is kept
for download, capped at 16 MiB. Download it before starting another attempt.
Diagnostic reports contain timing, tracking flags, decisions and model provenance,
not images or landmark coordinate arrays. The server never saves camera data.
No cloud upload or automatic browser persistence is implemented. Reloading loses
undownloaded data. Clear diagnostics removes in-memory results, not downloaded files.

Reports are capped at 120 attempts and 240 responses per attempt. Reaching the
limit requires exporting/clearing. Camera loss, hidden tabs and connection failures
interrupt rather than silently complete an attempt. A frame still in flight when
the attempt ends is not included; do not interpret this protocol as full-video
ground-truth alignment.

## Verification limits

The shared UI was exercised with an explicitly synthetic canvas stream, scripted
decisions and a real browser MediaRecorder. Completion, cancellation, fixed-set
non-advancement on cancel, visible JSON and a 16,020-byte video blob were observed.
The visible JSON was parsed and passed through the summary CLI. Native download
completion could not be verified in the in-app browser; the visible report is a
tested fallback. No person signed and no real webcam accuracy result was collected.

Reproduce the test-only fixture with `python scripts/serve_browser_checks.py` and
http://127.0.0.1:8767/__guided_check. This route is absent from the production app.
Recorder API references: https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder
and https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static.
