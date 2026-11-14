import test from "node:test";
import assert from "node:assert/strict";
import { readGrounding, safeCitationUrl, sourceOrganization, displayDate, readCopilotResponse, groundingStatuses } from "../src/lib/grounding.ts";
import { supported } from "./fixtures.ts";

test("legacy responses remain legacy without an invented verification claim", () => {
  assert.deepEqual(readGrounding(null), { kind: "legacy" });
  assert.deepEqual(readGrounding(undefined), { kind: "legacy" });
});
test("exact attributed quotation is accepted and distinguished from factual verification", () => {
  const view = readGrounding(supported());
  assert.equal(view.kind, "valid");
  assert.match(groundingStatuses.supported_quotes[1], /truth.*not verified/);
});
test("multiple distinct citations resolve to their exact source passages", () => {
  const data = supported();
  data.evidence.push({ ...data.evidence[0], citation_id: "E-bbbbbbbbbbbbbbbbbbbb" });
  data.claims[0].citation_ids.push("E-bbbbbbbbbbbbbbbbbbbb");
  assert.equal(readGrounding(data).kind, "valid");
});
const malformed: [string, (data: ReturnType<typeof supported>) => void][] = [
  ["missing evidence", d => { d.evidence = []; }],
  ["fabricated citation", d => { d.claims[0].citation_ids = ["E-ffffffffffffffffffff"]; }],
  ["incorrect attribution", d => { d.claims[0].text = "Unsupported synthetic claim."; }],
  ["missing qualifier", d => { d.claims[0].text = d.claims[0].text.replace("two independent", "one"); }],
  ["duplicate evidence", d => { d.evidence.push(d.evidence[0]); }],
  ["duplicate claims", d => { d.claims.push(d.claims[0]); }],
  ["duplicate citation", d => { d.claims[0].citation_ids.push(d.claims[0].citation_ids[0]); }],
  ["unreferenced passage", d => { d.evidence.push({ ...d.evidence[0], citation_id: "E-bbbbbbbbbbbbbbbbbbbb" }); }],
  ["unknown verification", d => { (d as unknown as Record<string, unknown>).verification_scope = "factual_truth"; }],
  ["private public trust mismatch", d => { d.evidence[0].scope = "private"; }],
  ["missing retrieval date", d => { d.evidence[0].retrieved_at = ""; }],
  ["invalid date", d => { d.evidence[0].published_at = "not-a-date"; }],
  ["oversized excerpt", d => { d.evidence[0].excerpt = "x".repeat(2001); }],
  ["oversized evidence list", d => { d.evidence = Array(6).fill(d.evidence[0]); }],
];
for (const [name, mutate] of malformed) test("fail closed: " + name, () => {
  const data = supported(); mutate(data);
  assert.equal(readGrounding(data).kind, "invalid");
});
for (const status of Object.keys(groundingStatuses).filter(s => s !== "supported_quotes")) {
  test("controlled abstention: " + status, () => {
    const data = { ...supported(), status, abstained: true, claims: [], evidence: [] };
    assert.equal(readGrounding(data).kind, "valid");
    assert.equal(readGrounding({ ...data, evidence: supported().evidence }).kind, "invalid");
  });
}
for (const [index, url] of [
  "javascript:alert(1)", "JaVaScRiPt:alert(1)", "data:text/html,synthetic", "vbscript:synthetic",
  "file:///synthetic", "mailto:test@example.com", "http://example.com", "//example.com",
  "/relative", " https://example.com", "https://example.com/\n", "https:\\example.com",
  "https://user:synthetic@example.com", "https:example.com", "https://", "about:blank",
].entries()) test("unsafe URL rejected, case " + index, () => assert.equal(safeCitationUrl(url), null));
test("canonical HTTPS URL is retained without unsafe credentials", () => {
  assert.equal(safeCitationUrl("https://example.com/reference#section"), "https://example.com/reference#section");
});
test("unsafe canonical URL never invalidates textual evidence but remains non-clickable", () => {
  const data = supported(); data.evidence[0].canonical_url = "javascript:alert(1)";
  assert.equal(readGrounding(data).kind, "valid");
  assert.equal(safeCitationUrl(data.evidence[0].canonical_url), null);
});
test("private source needs private provenance and cannot claim an external URL", () => {
  const data = supported();
  Object.assign(data.evidence[0], { source_id: "private-upload", scope: "private", trust: "private_upload", canonical_url: null });
  assert.equal(readGrounding(data).kind, "valid");
  data.evidence[0].canonical_url = "https://example.com";
  assert.equal(readGrounding(data).kind, "invalid");
});
test("organization labels use only known source IDs", () => {
  assert.equal(sourceOrganization("nvd"), "NIST National Vulnerability Database");
  assert.equal(sourceOrganization("__proto__"), null);
  assert.equal(sourceOrganization("unregistered"), null);
});
test("dates are labelled in UTC with safe missing-date fallback", () => {
  assert.equal(displayDate(null), null);
  assert.equal(displayDate("invalid"), null);
  assert.equal(displayDate("2026-01-02T00:00:00Z"), "Jan 2, 2026");
});
test("malformed metadata is retained for an invalid-state UI instead of silently becoming legacy", () => {
  const response = readCopilotResponse({ answer: "Unverified synthetic display text", grounding: { status: "supported_quotes" }, sources: null });
  assert.equal(readGrounding(response.grounding).kind, "invalid");
  assert.deepEqual(response.sources, []);
});
test("missing conversation identity and malformed legacy source entries are controlled", () => {
  const response = readCopilotResponse({ answer: "Legacy answer", sources: [{ filename: "fixture.txt", page: 1 }, null, { filename: "bad" }] });
  assert.equal(response.conversation_id, null);
  assert.equal(response.sources.length, 1);
});
test("invalid API contracts raise only a fixed diagnostic", () => {
  assert.throws(() => readCopilotResponse({ diagnostic: "SYNTHETIC_PRIVATE_DETAIL" }), { message: "Invalid chat response." });
});


test("empty-looking quotations are not treated as usable evidence", () => {
  const data = supported("   ");
  assert.equal(readGrounding(data).kind, "invalid");
});
test("a private-upload source cannot be presented as public authority", () => {
  const data = supported(); data.evidence[0].source_id = "private-upload";
  assert.equal(readGrounding(data).kind, "invalid");
});
