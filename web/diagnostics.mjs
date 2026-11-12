// Pure bounded report logic, shared by the UI and Node tests. No persistence.
export const DURATION_MS = 10000;
export const MAX_FRAMES = 240;
export const MAX_ATTEMPTS = 120;

export function makePlan(labels) {
  const items = Object.keys(labels).map(label => ({label, task: label}));
  items.push(...["REST", "ADJUST_GLASSES", "REACH"].map(task => ({label: "__OTHER__", task})));
  return Array.from({length: 3}, (_, round) => items.map(item => ({...item, round: round + 1}))).flat();
}

function percentile(values, p) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.ceil(p * (sorted.length - 1))];
}

export class Attempt {
  constructor({id, item, purpose, protocol, model, sessionOptions, startedAt, startMs, videoRequested}) {
    this.id = id; this.item = {...item}; this.purpose = purpose; this.protocol = protocol;
    this.model = model; this.sessionOptions = sessionOptions;
    this.startedAt = startedAt; this.startMs = startMs; this.videoRequested = videoRequested;
    this.frames = []; this.lastSeq = -1; this.lastCapture = -Infinity; this.closed = false;
  }

  add(frame, displayMs) {
    if (this.closed || frame.capture_ms < this.startMs) return false;
    if (this.frames.length >= MAX_FRAMES) throw new Error("Diagnostic frame limit reached");
    if (frame.seq <= this.lastSeq || frame.capture_ms <= this.lastCapture || !Number.isFinite(frame.capture_ms) || !Number.isFinite(displayMs)
        || displayMs < frame.capture_ms) throw new Error("Invalid diagnostic frame timing");
    this.lastSeq = frame.seq;
    this.lastCapture = frame.capture_ms;
    // Explicit allowlist: omit image bytes and landmark coordinates.
    this.frames.push({seq: frame.seq, capture_elapsed_ms: frame.capture_ms - this.startMs,
      result_elapsed_ms: displayMs - this.startMs, frame_result_age_ms: displayMs - frame.capture_ms,
      processing_ms: frame.processing_ms, body: !!frame.quality.body, hands: frame.quality.hands,
      face: !!frame.quality.face, state: frame.result.state, gap: !!frame.result.gap,
      label: frame.result.label, event: frame.result.event ? {...frame.result.event} : null,
      decisions: (frame.diagnostics || []).map(d => ({candidate: d.candidate, accepted: !!d.accepted,
        score: d.score, evidence_frames: d.evidence_frames,
        evidence_span_ms: (d.evidence_end_s - d.evidence_start_s) * 1000}))});
    return true;
  }

  finish(endMs, reason = "completed") {
    if (this.closed) throw new Error("Attempt already closed");
    this.closed = true;
    const frames = this.frames, decisions = frames.flatMap(f => f.decisions);
    const events = frames.filter(f => f.event).map(f => ({...f.event, elapsed_ms: f.result_elapsed_ms}));
    const known = this.item.label !== "__OTHER__";
    let outcome;
    if (reason !== "completed") outcome = "interrupted";
    else if (!frames.length) outcome = "no_frames";
    else if (!decisions.length) outcome = "no_model_decision";
    else if (!known) outcome = events.length ? "false_event" : "no_event_during_movement";
    else if (events.some(e => e.label === this.item.label)) outcome = events.some(e => e.label !== this.item.label) ? "mixed_events" : "matched_intent";
    else if (events.length) outcome = "different_event";
    else if (decisions.some(d => d.accepted && d.candidate === this.item.label)) outcome = "matching_candidate_not_finalized";
    else if (decisions.some(d => d.candidate === this.item.label)) outcome = "matching_candidate_rejected";
    else outcome = "no_matching_candidate";
    return {schema_version: 1, id: this.id, intended: this.item, purpose: this.purpose, protocol: this.protocol,
      label_verification: "user_intent_only_not_ASL_verified", model: this.model, session_options: this.sessionOptions,
      started_at: this.startedAt, duration_ms: Math.max(0, endMs - this.startMs), end_reason: reason,
      outcome, video_requested: this.videoRequested, frames, events,
      summary: {processed_frames: frames.length, model_decisions: decisions.length,
        accepted_decisions: decisions.filter(d => d.accepted).length,
        matching_candidate_decisions: decisions.filter(d => d.candidate === this.item.label).length,
        body_visible_fraction: frames.length ? frames.filter(f => f.body).length / frames.length : null,
        hands_visible_fraction: frames.length ? frames.filter(f => f.hands > 0).length / frames.length : null,
        capture_gaps: frames.filter(f => f.gap).length,
        processing_ms_p50: percentile(frames.map(f => f.processing_ms), .5),
        frame_result_age_ms_p95: percentile(frames.map(f => f.frame_result_age_ms), .95)},
      limitations: ["Intended labels are unverified", "Frame-result age is not semantic sign latency",
        "Outcome describes observed decisions, not proven cause", "No automatic training or calibration"]};
  }
}

export function exportReport(attempts, plan) {
  return {schema_version: 1, application: "Nexus guided diagnostics", protocol_version: "guided-v1",
    exported_at: new Date().toISOString(), plan, attempts,
    retention: "Explicit local download; no automatic upload, training, or browser persistence"};
}
