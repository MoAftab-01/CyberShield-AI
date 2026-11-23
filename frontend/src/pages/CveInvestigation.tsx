import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import GroundedAnswer from "../components/copilot/GroundedAnswer";
import { readGrounding } from "../lib/grounding";
import { validCve, workflowNodes } from "../lib/investigation";
import type { InvestigationReport, WorkflowNode } from "../lib/investigation";
import { investigateCve } from "../services/investigationService";
import "./investigation.css";

const labels: Record<WorkflowNode, string> = {
  validate: "Validate CVE", nvd: "Retrieve NVD intelligence", kev: "Check CISA KEV",
  correlate: "Correlate evidence", assess: "Assess impact and uncertainty",
  verify: "Verify citations", report: "Produce report",
};
export default function CveInvestigation() {
  const [cve, setCve] = useState("CVE-2021-44228");
  const [progress, setProgress] = useState<WorkflowNode[]>([]);
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const active = useRef<AbortController | null>(null);
  useEffect(() => () => active.current?.abort(), []);
  const run = async (event: React.FormEvent) => {
    event.preventDefault();
    if (active.current || !validCve(cve)) return;
    const controller = new AbortController();
    active.current = controller;
    setProgress([]); setReport(null); setError(""); setRunning(true);
    const timeout = window.setTimeout(() => controller.abort(), 90_000);
    try {
      await investigateCve(cve, controller.signal, event => {
        if (active.current !== controller || controller.signal.aborted) return;
        if (event.type === "progress") setProgress(previous => [...previous, event.node]);
        else setReport(event.report);
      });
    } catch {
      if (active.current === controller) setError(controller.signal.aborted
        ? "Investigation cancelled or timed out. You can run it again."
        : "Investigation unavailable. Check authentication, server enablement, or try again later.");
    } finally {
      window.clearTimeout(timeout);
      if (active.current === controller) { active.current = null; setRunning(false); }
    }
  };
  const download = () => {
    if (!report) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url; link.download = report.cve + "-investigation.json";
    document.body.appendChild(link); link.click(); link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const grounding = report ? readGrounding(report.grounding) : null;
  return <div className="investigation-page">
    <header>
      <p className="investigation-eyebrow">CyberShield AI · LangGraph</p>
      <h1>CVE Investigation</h1>
      <p>A bounded, read-only workflow with source quotations and explicit uncertainty.</p>
      <Link to="/copilot">Return to CyberGPT chat</Link>
    </header>
    <form onSubmit={run} className="investigation-form">
      <label htmlFor="investigation-cve">CVE identifier</label>
      <div><input id="investigation-cve" value={cve} disabled={running} autoComplete="off"
        spellCheck={false} maxLength={28} onChange={e => setCve(e.target.value)}
        aria-describedby="cve-help" aria-invalid={!validCve(cve)} />
        <button type="submit" disabled={running || !validCve(cve)}>Investigate CVE</button>
        {running && <button type="button" onClick={() => active.current?.abort()}>Cancel investigation</button>}
      </div>
      <p id="cve-help">Use uppercase CVE-YYYY-NNNN. The server operator selects fixture or approved live mode.</p>
    </form>
    <section aria-label="Investigation workflow" className="investigation-workflow">
      <h2>Workflow</h2>
      <ol>{workflowNodes.map(node => <li key={node}>
        <span aria-hidden="true">{progress.includes(node) ? "✓" : "○"}</span> {labels[node]}
        {progress.filter(value => value === node).length > 1 && " (retried)"}
      </li>)}</ol>
      <p role="status" aria-live="polite">{running ? "Investigation running. Completed " + progress.length + " steps."
        : report ? "Investigation finished: " + report.status.replaceAll("_", " ") : "Ready to investigate."}</p>
    </section>
    {error && <p role="alert">{error}</p>}
    {report && <article aria-label="Investigation findings">
      <header><h2>{report.cve} findings</h2>
        <p className="investigation-mode">{report.mode === "offline_fixture"
          ? "OFFLINE SYNTHETIC DEMO — not live threat intelligence" : "Read-only live source snapshots"}</p>
        <p>Status: {report.status.replaceAll("_", " ")}. This is workflow coverage, not a factual confidence score.</p>
      </header>
      <dl className="investigation-facts">
        <dt>NVD record</dt><dd>{report.findings.nvd_status ?? "Unavailable"}</dd>
        <dt>KEV observation</dt><dd>{report.findings.kev_status ?? "Unknown"}</dd>
        <dt>Elapsed</dt><dd>{report.metrics.latency_ms.toFixed(1)} ms</dd>
        <dt>Model usage</dt><dd>{report.metrics.llm_calls} calls; {report.metrics.input_tokens + report.metrics.output_tokens} tokens</dd>
      </dl>
      {grounding && grounding.kind !== "legacy" ? <GroundedAnswer view={grounding} />
        : <p>Insufficient source evidence. No citation verification is claimed.</p>}
      <section aria-label="Uncertainty and limitations"><h3>Uncertainty and limitations</h3>
        <ul>{report.uncertainty.map((warning, index) => <li key={index}>{warning}</li>)}</ul>
        <p>No assets were scanned. No exploitation or remediation was attempted. Absence from KEV does not establish safety.</p>
      </section>
      <button type="button" onClick={download}>Download investigation report (JSON)</button>
    </article>}
  </div>;
}
