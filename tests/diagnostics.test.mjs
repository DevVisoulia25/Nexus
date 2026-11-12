import test from "node:test";
import assert from "node:assert/strict";
import {Attempt, MAX_FRAMES, makePlan, exportReport} from "../web/diagnostics.mjs";

function attempt(label = "BOOK") {
  return new Attempt({id: "test", item: {label, task: label}, purpose: "evaluation", protocol: "single-v1",
    model: {sha256: "example"}, sessionOptions: {}, startedAt: "2026-11-10T00:00:00Z", startMs: 1000, videoRequested: false});
}
function frame(seq, decisions = [], event = null) {
  return {seq, capture_ms: 1000 + seq * 100, processing_ms: 20, quality: {body: true, hands: 1, face: true},
    points: [[.1, .2, 1]], jpeg: "must not persist", result: {state: "unknown", label: null, event}, diagnostics: decisions};
}
const decision = (accepted, candidate = "BOOK") => ({candidate, accepted, score: 1.2, evidence_frames: 6, evidence_start_s: 1, evidence_end_s: 2});

test("distinguishes rejection from event finalization", () => {
  const rejected = attempt(); rejected.add(frame(0, [decision(false)]), 1040);
  assert.equal(rejected.finish(2000).outcome, "matching_candidate_rejected");
  const accepted = attempt(); accepted.add(frame(0, [decision(true)]), 1040);
  assert.equal(accepted.finish(2000).outcome, "matching_candidate_not_finalized");
});
test("interruption never becomes a successful completed attempt", () => {
  const a = attempt(); a.add(frame(0, [decision(true)], {id: 1, label: "BOOK"}), 1040);
  assert.equal(a.finish(2000, "Camera disconnected").outcome, "interrupted");
  assert.equal(a.add(frame(1), 1200), false);
  assert.throws(() => a.finish(2100));
});
test("reports false events on movements and mixed sign events", () => {
  const a = attempt("__OTHER__"); a.add(frame(0, [decision(true)], {id: 1, label: "BOOK"}), 1040);
  assert.equal(a.finish(2000).outcome, "false_event");
  const b = attempt(); b.add(frame(0, [], {id: 1, label: "BOOK"}), 1040);
  b.add(frame(1, [decision(true, "YES")], {id: 2, label: "YES"}), 1140);
  assert.equal(b.finish(2000).outcome, "mixed_events");
});
test("reports contain no images or landmark arrays and have bounded memory", () => {
  const a = attempt();
  for (let i = 0; i < MAX_FRAMES; i++) a.add(frame(i), 1040 + i * 100);
  assert.throws(() => a.add(frame(MAX_FRAMES), 1040 + MAX_FRAMES * 100), /limit/);
  const exported = JSON.stringify(exportReport([a.finish(30000)], []));
  assert.equal(exported.includes("must not persist"), false);
  assert.equal(exported.includes('"points"'), false);
});
test("rejects stale result ordering and excludes pre-attempt capture", () => {
  const a = attempt(); assert.equal(a.add({...frame(0), capture_ms: 900}, 1040), false);
  a.add(frame(1), 1140);
  assert.throws(() => a.add(frame(0), 1200));
  assert.throws(() => a.add({...frame(2), capture_ms: 1099}, 1200));
});
test("fixed plan has three rounds with each sign and movement exactly once", () => {
  const labels = Object.fromEntries(Array.from({length: 10}, (_, i) => [`SIGN${i}`, `Sign ${i}`]));
  const plan = makePlan(labels); assert.equal(plan.length, 39);
  for (const round of [1, 2, 3]) {
    const items = plan.filter(item => item.round === round);
    assert.equal(new Set(items.map(i => i.task)).size, 13);
    assert.equal(items.filter(i => i.label === "__OTHER__").length, 3);
  }
});
