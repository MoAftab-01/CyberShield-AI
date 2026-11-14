import { readGrounding } from "./grounding.ts";
import type { Grounding } from "../types/copilot.ts";

export const workflowNodes = ["validate", "nvd", "kev", "correlate", "assess", "verify", "report"] as const;
export type WorkflowNode = typeof workflowNodes[number];
export interface InvestigationReport {
  schema_version: 1; cve: string;
  status: "complete" | "partial" | "insufficient_evidence" | "invalid_input";
  mode: "offline_fixture" | "read_only_live"; generated_at: string;
  findings: { nvd_status?: string; kev_status?: string; known_exploited?: boolean | null };
  grounding: Grounding | null; uncertainty: string[]; workflow: WorkflowNode[];
  tools: { name: string; attempts: number; status: string }[];
  metrics: { latency_ms: number; llm_calls: number; input_tokens: number; output_tokens: number; estimated_model_cost_usd: number };
}
export type InvestigationEvent = { type: "progress"; node: WorkflowNode }
  | { type: "report"; report: InvestigationReport };
export function validCve(value: string): boolean {
  return /^CVE-[0-9]{4}-[0-9]{4,19}$/.test(value) && value.length <= 28;
}
function object(raw: unknown): raw is Record<string, unknown> {
  return typeof raw === "object" && raw !== null && !Array.isArray(raw);
}
export function readInvestigationEvent(raw: unknown, requestedCve: string): InvestigationEvent {
  const invalid = () => new Error("Invalid investigation response.");
  if (!object(raw)) throw invalid();
  if (raw.type === "progress" && workflowNodes.includes(raw.node as WorkflowNode)) {
    return { type: "progress", node: raw.node as WorkflowNode };
  }
  if (raw.type !== "report" || !object(raw.report)) throw invalid();
  const r = raw.report;
  const metrics = object(r.metrics) ? r.metrics : {};
  if (r.schema_version !== 1 || r.cve !== requestedCve ||
      !["complete", "partial", "insufficient_evidence", "invalid_input"].includes(String(r.status)) ||
      !["offline_fixture", "read_only_live"].includes(String(r.mode)) ||
      typeof r.generated_at !== "string" || !Number.isFinite(Date.parse(r.generated_at)) ||
      !object(r.findings) || !object(r.metrics) || !Array.isArray(r.tools) || r.tools.length > 2 ||
      !Array.isArray(r.uncertainty) || r.uncertainty.length > 30 ||
      !r.uncertainty.every(x => typeof x === "string" && x.length <= 500) ||
      !Array.isArray(r.workflow) || r.workflow.length > 16 ||
      !r.workflow.every(x => workflowNodes.includes(x as WorkflowNode)) ||
      !["latency_ms", "llm_calls", "input_tokens", "output_tokens", "estimated_model_cost_usd"]
        .every(k => typeof metrics[k] === "number" &&
          Number.isFinite(metrics[k]) &&
          Number(metrics[k]) >= 0)) throw invalid();
  if (![null, undefined, true, false].includes(r.findings.known_exploited as boolean | null | undefined) ||
      ![r.findings.nvd_status, r.findings.kev_status].every(x => x === undefined || typeof x === "string" && x.length <= 80) ||
      !r.tools.every(x => object(x) && ["nvd", "cisa-kev"].includes(String(x.name)) &&
        Number.isInteger(x.attempts) && Number(x.attempts) >= 1 && Number(x.attempts) <= 2 &&
        ["ok", "invalid", "unavailable"].includes(String(x.status)))) throw invalid();
  const grounding = readGrounding(r.grounding);
  if (grounding.kind === "invalid" || (r.grounding !== null && grounding.kind !== "valid")) throw invalid();
  if (grounding.kind === "valid" && grounding.value.evidence.some(e => e.scope !== "public")) throw invalid();
  if (r.status === "complete" && (grounding.kind !== "valid" || grounding.value.abstained)) throw invalid();
  return { type: "report", report: r as unknown as InvestigationReport };
}
