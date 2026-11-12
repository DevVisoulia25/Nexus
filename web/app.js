import {createGuided} from "./guided.js";
const $ = (id) => document.getElementById(id);
const video = $("video"), overlay = $("overlay"), canvas = document.createElement("canvas");
const ctx = overlay.getContext("2d"), capture = canvas.getContext("2d");
let stream, socket, generation = 0, running = false, seq = 0, labels = {}, timer, watchdog;
let lastSent = 0, lastResponse = 0, history = [], modelReady = false;
const guided = createGuided({startCamera: start, stopCamera: stop, getStream: () => stream});

function message(text) { $("status").textContent = text; }
function candidate(label, state) {
  $("prediction").textContent = label ? labels[label] || label : ({idle: "Ready for a sign.", collecting: "Watching…", unknown: "Not recognized.", framing: "Adjust your framing."}[state] || "Watching…");
  $("predictionHelp").textContent = label ? "A provisional match. Keep signing naturally; the model can be wrong." : "Try one sign at a time, then lower your hands briefly.";
  document.querySelectorAll(".chip").forEach(el => el.classList.toggle("active", el.dataset.label === label));
}
function renderHistory() {
  $("history").replaceChildren();
  if (!history.length) {
    const empty = document.createElement("li"); empty.className = "empty";
    empty.textContent = "Stable detections will appear here. This is a sign list, not a translated sentence.";
    $("history").append(empty);
  }
  for (const item of history) {
    const li = document.createElement("li"), span = document.createElement("span"), time = document.createElement("time");
    span.textContent = labels[item.label] || item.label; time.textContent = item.time;
    li.append(span, time); $("history").append(li);
  }
  $("count").textContent = `${history.length} signs`;
}
function stop(reason = "Camera stopped. Your session list stays here until you reset.") {
  guided.onStop(reason);
  generation++; running = false;
  clearTimeout(timer); clearTimeout(watchdog);
  if (socket) { socket.onclose = null; socket.close(); socket = null; }
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
  video.srcObject = null; ctx.clearRect(0, 0, overlay.width, overlay.height);
  $("placeholder").hidden = false; $("cameraState").textContent = "Camera off";
  $("liveDot").classList.add("muted"); $("start").disabled = !modelReady; $("stop").disabled = true;
  $("quality").textContent = "Waiting for camera"; $("frameRate").textContent = "— fps";
  $("processing").textContent = "—"; $("delay").textContent = "—";
  candidate(null, "idle"); message(reason);
}
function draw(points) {
  overlay.width = video.videoWidth; overlay.height = video.videoHeight;
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  points.forEach(([x, y, valid], i) => {
    if (!valid) return;
    ctx.fillStyle = i >= 9 && i < 51 ? "#9af0ca" : "#e9fff2";
    ctx.beginPath(); ctx.arc(x * overlay.width, y * overlay.height, i < 51 ? 2.5 : 1.3, 0, Math.PI * 2); ctx.fill();
  });
}
async function sendFrame(epoch) {
  if (!running || epoch !== generation || socket?.readyState !== WebSocket.OPEN) return;
  if (!video.videoWidth) { timer = setTimeout(() => sendFrame(epoch), 100); return; }
  canvas.width = 640; canvas.height = Math.round(640 * video.videoHeight / video.videoWidth);
  capture.drawImage(video, 0, 0, canvas.width, canvas.height);
  const captured = performance.now();
  const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.75));
  if (!blob) { stop("Could not read the camera frame. Please start again."); return; }
  const jpeg = await blob.arrayBuffer();
  if (!running || epoch !== generation || socket?.readyState !== WebSocket.OPEN) return;
  const packet = new Uint8Array(12 + jpeg.byteLength), view = new DataView(packet.buffer);
  view.setFloat64(0, captured, true); view.setUint32(8, seq++, true); packet.set(new Uint8Array(jpeg), 12);
  lastSent = captured; socket.send(packet);
  watchdog = setTimeout(() => stop("Processing stopped responding. Camera released; start again to recover."), 8000);
}
async function start() {
  if (running) return;
  const epoch = ++generation; running = true; $("start").disabled = true; $("stop").disabled = false;
  message("Requesting camera access…");
  try {
    const media = await navigator.mediaDevices.getUserMedia({video: {width: {ideal: 640}, height: {ideal: 480}, facingMode: "user"}, audio: false});
    if (epoch !== generation) { media.getTracks().forEach(t => t.stop()); return; }
    stream = media; video.srcObject = media; await video.play();
    if (epoch !== generation) return;
    media.getVideoTracks()[0].onended = () => stop("The camera disconnected. Reconnect it and start again.");
    $("placeholder").hidden = true; $("cameraState").textContent = "Camera live"; $("liveDot").classList.remove("muted");
    message("Starting local landmark tracking…");
    socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
    watchdog = setTimeout(() => stop("Local model startup timed out. Start again to retry."), 15000);
    socket.onmessage = ({data}) => {
      if (epoch !== generation) return;
      const result = JSON.parse(data); clearTimeout(watchdog);
      if (result.type === "ready") { seq = 0; lastResponse = 0; guided.onReady(result); sendFrame(epoch); return; }
      if (result.seq !== seq - 1) { stop("Received an out-of-order result. Start a fresh session."); return; }
      const now = performance.now(), age = now - result.capture_ms;
      guided.onFrame(result, now);
      if (epoch !== generation) return;
      if (age > 2000) { stop("Processing fell behind by over 2 seconds. Camera released; start again to recover."); return; }
      $("processing").textContent = `${Math.round(result.processing_ms)} ms`;
      $("delay").textContent = `${Math.round(age)} ms`;
      $("frameRate").textContent = lastResponse ? `${(1000 / (now - lastResponse)).toFixed(1)} fps` : "… fps";
      lastResponse = now;
      const q = result.quality;
      $("quality").textContent = !q.body ? "Move back so both shoulders are visible" : !q.hands ? "Bring a hand into view to begin" : `${q.hands} hand${q.hands > 1 ? "s" : ""} tracked · ${q.face ? "Face visible" : "Face not detected"}`;
      draw(result.points); candidate(guided.hidePredictions ? null : result.result.label, guided.hidePredictions ? "collecting" : result.result.state);
      if (result.result.event && !guided.hidePredictions) {
        history.unshift({label: result.result.event.label, time: new Date().toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})});
        history = history.slice(0, 30); renderHistory();
      }
      message(result.result.gap ? "A capture gap cleared the context. Begin a fresh sign." : guided.active ? "Guided check running · See the test instructions below" : "Processing locally · Candidate labels are experimental · No video saved");
      timer = setTimeout(() => sendFrame(epoch), Math.max(0, 1000 / 12 - (performance.now() - lastSent)));
    };
    socket.onclose = event => { if (epoch === generation) stop(event.reason || "Connection interrupted. Camera released; start again to reconnect."); };
    socket.onerror = () => { if (epoch === generation) stop("Cannot reach the local processor. Check the server and start again."); };
  } catch (error) {
    if (epoch === generation) stop(error.name === "NotAllowedError" ? "Camera permission was denied. Allow camera access in your browser, then start again." : `Camera unavailable: ${error.message}`);
  }
}
$("start").onclick = start;
$("stop").onclick = () => stop();
$("reset").onclick = () => { stop("Session reset. Start the camera for a fresh attempt."); history = []; renderHistory(); };
window.addEventListener("pagehide", () => stop());
document.addEventListener("visibilitychange", () => { if (document.hidden && running) stop("Camera stopped because this tab became hidden."); });
try {
  const response = await fetch("/api/status"); if (!response.ok) throw new Error("status unavailable");
  const status = await response.json(); labels = status.labels; modelReady = status.model_ready;
  guided.init(labels, modelReady);
  for (const [key, label] of Object.entries(labels)) { const chip = document.createElement("span"); chip.className = "chip"; chip.dataset.label = key; chip.textContent = label; $("vocabulary").append(chip); }
  $("start").disabled = !modelReady;
  message(modelReady ? `Experimental model: ${status.model_name}. Recognition quality is not validated. Start the camera to test.` : "No trained model found. Run the documented prepare, extract and train steps first.");
  if (status.evaluation) $("evaluation").textContent = `DEVELOPMENT ONLY · ${status.evaluation.known_dev_n} known clips · FINAL TEST UNTOUCHED`;
} catch { message("Cannot connect to Nexus. Start the local server, then reload this page."); }
