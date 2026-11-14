import test from "node:test";
import assert from "node:assert/strict";
import { readInvestigationEvent, validCve } from "../src/lib/investigation.ts";
import { supported } from "./fixtures.ts";

const report = () => ({ type: "report", report: {
  schema_version: 1, cve: "CVE-2021-44228", status: "complete", mode: "offline_fixture",
  generated_at: "2026-11-14T00:00:00Z", findings: { nvd_status: "active", kev_status: "listed", known_exploited: true },
  grounding: supported(), uncertainty: ["Synthetic uncertainty."],
  workflow: ["validate", "nvd", "kev", "correlate", "assess", "verify", "report"],
  tools: [{ name: "nvd", attempts: 1, status: "ok" }],
  metrics: { latency_ms: 12, llm_calls: 0, input_tokens: 0, output_tokens: 0, estimated_model_cost_usd: 0 },
} });
test("valid canonical CVE, bounded ASCII only", () => {
  assert(validCve("CVE-2021-44228"));
  for (const bad of ["cve-2021-44228", "CVE-2021-44228\n", "CVE-2021-123", "CVE-2021-44228;id"]) assert(!validCve(bad));
});
test("workflow progress is limited to real node names", () => {
  assert.equal(readInvestigationEvent({ type: "progress", node: "nvd" }, "CVE-2021-44228").type, "progress");
  assert.throws(() => readInvestigationEvent({ type: "progress", node: "execute_shell" }, "CVE-2021-44228"));
});
test("valid report retains exact citation contract", () => {
  assert.equal(readInvestigationEvent(report(), "CVE-2021-44228").type, "report");
});
for (const [name, mutate] of [
  ["different CVE", (r: ReturnType<typeof report>) => { r.report.cve = "CVE-2024-3094"; }],
  ["fabricated citation", (r: ReturnType<typeof report>) => { r.report.grounding.claims[0].citation_ids = ["E-fabricated"]; }],
  ["incorrect attribution", (r: ReturnType<typeof report>) => { r.report.grounding.claims[0].text = "Unsupported claim."; }],
  ["negative cost", (r: ReturnType<typeof report>) => { r.report.metrics.estimated_model_cost_usd = -1; }],
  ["unknown mode", (r: ReturnType<typeof report>) => { r.report.mode = "arbitrary"; }],
] as const) {
  test("fail closed: " + name, () => {
    const r = report(); mutate(r);
    assert.throws(() => readInvestigationEvent(r, "CVE-2021-44228"));
  });
}
