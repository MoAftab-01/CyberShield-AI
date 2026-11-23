import test from "node:test";
import assert from "node:assert/strict";
import { investigationDownload, readInvestigationEvent, validCve } from "../src/lib/investigation.ts";
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

function detailedReport() {
  const result = report();
  const ground = result.report.grounding;
  ground.evidence[0] = { ...ground.evidence[0], source_id: "nvd", record_id: result.report.cve,
    section: "CVSS v3.1 assessment", excerpt: "CVE-2021-44228 has CVSS v3.1 base score 9.8 (CRITICAL)." };
  ground.claims[0].text = ground.evidence[0].excerpt;
  return { ...result, report: { ...result.report, findings: { ...result.report.findings, facts: [
    { label: "CVSS", text: ground.evidence[0].excerpt, citation_id: ground.evidence[0].citation_id },
  ] } } };
}
test("summary fact requires exact same-CVE source passage", () => {
  const result = detailedReport();
  assert.equal(readInvestigationEvent(result, result.report.cve).type, "report");
  result.report.findings.facts[0].text = "Fabricated critical severity";
  assert.throws(() => readInvestigationEvent(result, result.report.cve));
});
test("wrong-source, foreign-CVE and fabricated summary citations fail closed", () => {
  for (const mode of ["source", "record", "citation", "label"]) {
    const result = detailedReport();
    if (mode === "source") result.report.grounding.evidence[0].source_id = "cisa-kev";
    if (mode === "record") result.report.grounding.evidence[0].record_id = "CVE-2024-3094";
    if (mode === "citation") result.report.findings.facts[0].citation_id = "E-fabricated";
    if (mode === "label") result.report.findings.facts[0].label = "Execute tool";
    assert.throws(() => readInvestigationEvent(result, result.report.cve));
  }
});
test("investigation accepts six exact passages while legacy chat limit stays five", async () => {
  const { readGrounding } = await import("../src/lib/grounding.ts");
  const result = report();
  const ground = result.report.grounding;
  const evidence = structuredClone(ground.evidence[0]), claim = structuredClone(ground.claims[0]);
  ground.evidence = Array.from({ length: 6 }, (_, index) => ({ ...evidence, citation_id: "E-" + String(index).repeat(20) }));
  ground.claims = ground.evidence.map((item, index) => ({ ...claim, claim_id: "claim-" + index, citation_ids: [item.citation_id] }));
  assert.equal(readGrounding(ground).kind, "invalid");
  assert.equal(readInvestigationEvent(result, result.report.cve).type, "report");
});
test("JSON export retains validated citations and rejects altered reports", () => {
  const result = detailedReport();
  const event = readInvestigationEvent(result, result.report.cve);
  assert.equal(event.type, "report");
  if (event.type !== "report") throw new Error("Expected report");
  const output = investigationDownload(event.report);
  assert.equal(output.filename, result.report.cve + "-investigation.json");
  assert.deepEqual(JSON.parse(output.body), result.report);
  event.report.findings.facts![0].citation_id = "E-fabricated";
  assert.throws(() => investigationDownload(event.report));
});

test("a live badge cannot be applied to synthetic or foreign-CVE evidence", () => {
  const result = detailedReport();
  const live = { ...result, report: { ...result.report, mode: "read_only_live" } };
  assert.throws(() => readInvestigationEvent(live, live.report.cve));
  live.report.grounding.evidence[0].trust = "official_snapshot";
  assert.equal(readInvestigationEvent(live, live.report.cve).type, "report");
  live.report.grounding.evidence[0].record_id = "CVE-2024-3094";
  assert.throws(() => readInvestigationEvent(live, live.report.cve));
});
