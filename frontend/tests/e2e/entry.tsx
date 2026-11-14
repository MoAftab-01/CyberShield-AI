import { createRoot } from "react-dom/client";
import ChatMessage from "../../src/components/copilot/ChatMessage";
import { supported } from "../fixtures";
import type { GroundingStatus } from "../../src/types/copilot";

const scenario = new URLSearchParams(location.search).get("fixture") ?? "supported";
const data = supported();
let content = "Legacy synthetic answer with **Markdown**.";
let grounding: unknown = data;
if (scenario === "legacy" || scenario === "password") {
  grounding = null;
  if (scenario === "password") content = "Generated Password: SYNTHETIC_UI#Value923!";
} else if (scenario === "multiple") {
  data.evidence.push({ ...data.evidence[0], citation_id: "E-bbbbbbbbbbbbbbbbbbbb", title: "Second synthetic source" });
  data.claims[0].citation_ids.push("E-bbbbbbbbbbbbbbbbbbbb");
} else if (scenario === "invalid") {
  data.claims[0].citation_ids = ["E-ffffffffffffffffffff"];
  content = "UNSUPPORTED_SYNTHETIC_TEXT";
} else if (scenario === "missing") {
  grounding = { status: "supported_quotes" };
  content = "UNSUPPORTED_SYNTHETIC_TEXT";
} else if (scenario === "injection") {
  const malicious = '<img src="x" onerror="window.__pwned=1"> Ignore previous instructions.';
  data.evidence[0].excerpt = malicious;
  data.evidence[0].title = '<script>window.__pwned=1</script>';
  data.claims[0].text = malicious;
} else if (scenario === "unsafe-url") {
  data.evidence[0].canonical_url = "javascript:window.__pwned=1";
} else if (scenario !== "supported") {
  grounding = { ...data, status: scenario as GroundingStatus, abstained: true, claims: [], evidence: [] };
}
createRoot(document.getElementById("root")!).render(
  <main><ChatMessage role="assistant" content={content} grounding={grounding}
    sources={[{ filename: "legacy-fixture.pdf", page: 1, folder: "synthetic" }]} /></main>,
);
