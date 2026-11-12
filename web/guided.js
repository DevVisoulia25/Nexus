import {Attempt, DURATION_MS, MAX_ATTEMPTS, makePlan, exportReport} from "./diagnostics.mjs";

const $ = id => document.getElementById(id);
const tasks = {REST: "Rest without signing", ADJUST_GLASSES: "Adjust glasses or touch your forehead", REACH: "Reach for an object"};
const outcomes = {interrupted: "Interrupted — excluded from completed results", no_frames: "No processed frames",
  no_model_decision: "No model decision — inspect tracking and window timing", false_event: "A sign was emitted during ordinary movement",
  no_event_during_movement: "No sign event during this movement", matched_intent: "Event matched your intended label (unverified)",
  mixed_events: "Both matching and different events", different_event: "Emitted a different label",
  matching_candidate_not_finalized: "Matching candidate accepted, but no stable event",
  matching_candidate_rejected: "Matching candidate was rejected", no_matching_candidate: "No candidate matched your intended label"};

export function createGuided({startCamera, stopCamera, getStream}) {
  let labels = {}, plan = [], attempt = null, reports = [], tick, recorder = null;
  let videoBlob = null, videoName = "", recordingPending = false, modelReady = false;
  const protocol = () => $("testProtocol").value;
  const completed = () => reports.filter(r => r.end_reason === "completed" && r.protocol === "fixed-39-v1").length;
  const say = text => { $("testStatus").textContent = text; };
  const itemName = item => tasks[item.task] || labels[item.label] || item.label;
  function render() {
    const busy = !!attempt || recordingPending;
    for (const id of ["testProtocol", "testPurpose", "testIntent"]) $(id).disabled = busy || (id !== "testIntent" && reports.length > 0);
    $("testIntent").hidden = protocol() === "fixed-39-v1";
    $("testIntentLabel").hidden = protocol() === "fixed-39-v1";
    $("recordVideo").disabled = busy || typeof MediaRecorder === "undefined";
    $("beginTest").disabled = busy || !modelReady || reports.length >= MAX_ATTEMPTS || (protocol() === "fixed-39-v1" && completed() >= plan.length);
    $("cancelTest").disabled = !attempt;
    $("exportTests").disabled = busy || !reports.length;
    $("viewReport").disabled = busy || !reports.length;
    $("clearTests").disabled = busy || !reports.length;
    $("downloadVideo").disabled = busy || !videoBlob;
    $("testProgress").textContent = protocol() === "fixed-39-v1" ? `${completed()} / ${plan.length} completed` : `${reports.length} attempts`;
    const next = plan[completed()];
    $("testPrompt").textContent = protocol() === "fixed-39-v1" ? (next ? `Next: ${itemName(next)} · round ${next.round} of 3` : "Fixed set complete. Download the report.") : "Choose an intended sign or ordinary movement.";
  }
  function download(blob, filename) {
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url; link.download = filename; link.hidden = true;
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  function recordVideo(current) {
    for (const report of reports) if (report.video) report.video.available_in_browser = false;
    videoBlob = null; videoName = "";
    if (!current.videoRequested) return;
    if (typeof MediaRecorder === "undefined") { current.videoError = "Recording unsupported"; return; }
    let chunks = [], bytes = 0, failed = false;
    try {
      const mimeType = ["video/webm;codecs=vp8", "video/webm", "video/mp4"].find(type => MediaRecorder.isTypeSupported(type));
      if (!mimeType) throw new Error("No supported recording format");
      const local = new MediaRecorder(getStream(), {mimeType, videoBitsPerSecond: 1000000});
      recorder = local; recordingPending = true;
      local.ondataavailable = event => {
        if (failed) return;
        bytes += event.data.size;
        if (bytes > 16 * 1024 * 1024) {
          failed = true; chunks = []; current.videoError = "Recording exceeded 16 MiB cap";
          if (local.state !== "inactive") local.stop();
        } else if (event.data.size) chunks.push(event.data);
      };
      local.onerror = () => {
        failed = true; chunks = []; current.videoError = "Browser recording failed";
        if (local.state !== "inactive") local.stop();
      };
      local.onstop = () => {
        if (!failed && chunks.length) {
          videoBlob = new Blob(chunks, {type: local.mimeType});
          videoName = `nexus-${current.id}.${local.mimeType.includes("mp4") ? "mp4" : "webm"}`;
        }
        chunks = []; recordingPending = false; recorder = null;
        const report = reports.find(r => r.id === current.id);
        if (report) report.video = {available_in_browser: !!videoBlob, filename: videoName || null,
          bytes: videoBlob?.size || 0, error: current.videoError || null, audio: false};
        if (current.videoError) say(`Attempt finished. Video unavailable: ${current.videoError}. Diagnostic report is still available.`);
        render();
      };
      local.start(250);
    } catch (error) { current.videoError = error.message; recordingPending = false; recorder = null; }
  }
  function finish(reason) {
    if (!attempt) return;
    clearInterval(tick);
    const current = attempt; attempt = null;
    const report = current.finish(performance.now(), reason);
    report.video = {available_in_browser: false, filename: null, error: current.videoError || null, audio: false};
    reports.push(report);
    $("reportPanel").hidden = true; $("reportText").value = "";
    if (recorder?.state !== "inactive" && recorder) recorder.stop();
    const li = document.createElement("li"), title = document.createElement("strong"), text = document.createElement("span");
    title.textContent = itemName(current.item);
    text.textContent = `${outcomes[report.outcome]} · ${report.summary.processed_frames} frames · ${report.summary.model_decisions} decisions`;
    li.append(title, text); $("testResults").prepend(li);
    say(`${outcomes[report.outcome]}. Results are diagnostic observations, not verified ASL accuracy.`);
    render();
  }
  $("beginTest").onclick = () => {
    if (attempt || recordingPending || reports.length >= MAX_ATTEMPTS) return;
    stopCamera("Starting a fresh guided attempt…");
    let item;
    if (protocol() === "fixed-39-v1") item = plan[completed()];
    else { const value = $("testIntent").value; item = {label: tasks[value] ? "__OTHER__" : value, task: value, round: null}; }
    if (!item) return;
    for (const report of reports) if (report.video) report.video.available_in_browser = false;
    attempt = new Attempt({id: crypto.randomUUID(), item, purpose: $("testPurpose").value,
      protocol: protocol(), model: null, sessionOptions: null, startedAt: new Date().toISOString(),
      startMs: performance.now(), videoRequested: $("recordVideo").checked});
    videoBlob = null; videoName = "";
    say(`Preparing camera for ${itemName(item)}. Wait for “Begin”.`); render();
    startCamera();
  };
  $("cancelTest").onclick = () => stopCamera("Guided attempt cancelled");
  function showReport() {
    const text = JSON.stringify(exportReport(reports, plan), null, 2);
    $("reportText").value = text; $("reportPanel").hidden = false;
    return text;
  }
  $("viewReport").onclick = showReport;
  $("exportTests").onclick = () => {
    download(new Blob([showReport()], {type: "application/json"}), "nexus-diagnostics.json");
    say("Report prepared. If your browser does not download it, select and copy the report below. Nothing is uploaded.");
  };
  $("downloadVideo").onclick = () => { if (videoBlob) download(videoBlob, videoName); };
  $("clearTests").onclick = () => {
    if (attempt || recordingPending) return;
    reports = []; videoBlob = null; videoName = ""; $("testResults").replaceChildren();
    $("reportPanel").hidden = true; $("reportText").value = "";
    say("Diagnostic memory cleared. Previously downloaded files are unchanged."); render();
  };
  $("testProtocol").onchange = () => {
    if (protocol() === "single-v1" && $("testPurpose").value === "evaluation") $("testPurpose").value = "debug";
    render();
  };
  $("testPurpose").onchange = () => {
    if ($("testPurpose").value === "evaluation") $("testProtocol").value = "fixed-39-v1";
    render();
  };
  return {
    init(knownLabels, ready) {
      labels = knownLabels; modelReady = ready; plan = makePlan(labels);
      for (const [value, name] of [...Object.entries(labels), ...Object.entries(tasks)]) {
        const option = document.createElement("option"); option.value = value; option.textContent = name; $("testIntent").append(option);
      }
      render();
    },
    onReady(ready) {
      if (!attempt) return;
      attempt.model = ready.model; attempt.sessionOptions = ready.session_options;
      attempt.startMs = performance.now(); attempt.startedAt = new Date().toISOString();
      recordVideo(attempt);
      const item = attempt.item;
      const update = () => {
        if (!attempt) return;
        const left = Math.max(0, Math.ceil((DURATION_MS - (performance.now() - attempt.startMs)) / 1000));
        if (!left) { finish("completed"); stopCamera("Guided attempt complete. Camera released."); return; }
        say(`Begin: ${itemName(item)} · ${left} seconds remaining. ${attempt.videoRequested ? "Local video recording requested." : "No video recording."}`);
      };
      update(); tick = setInterval(update, 200);
    },
    onFrame(frame, now) {
      if (!attempt) return;
      try { attempt.add(frame, now); } catch (error) { stopCamera(error.message); }
    },
    onStop(reason) { finish(reason); },
    get active() { return !!attempt; },
    get hidePredictions() { return !!attempt && attempt.purpose === "evaluation"; },
  };
}
