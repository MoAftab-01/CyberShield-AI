import api from "./api";
import { readInvestigationEvent, validCve } from "../lib/investigation";
import type { InvestigationEvent } from "../lib/investigation";

export async function investigateCve(cve: string, signal: AbortSignal,
  onEvent: (event: InvestigationEvent) => void): Promise<void> {
  if (!validCve(cve)) throw new Error("Enter a canonical CVE identifier.");
  const token = localStorage.getItem("access_token");
  const response = await fetch((api.defaults.baseURL || "").replace(/\/$/, "") + "/investigations/cve?stream=true", {
    method: "POST", headers: { "Content-Type": "application/json",
      ...(token ? { Authorization: "Bearer " + token } : {}) },
    body: JSON.stringify({ cve }), signal, cache: "no-store",
  });
  if (response.status === 401 || response.status === 403) {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
    throw new Error("Sign in again to investigate.");
  }
  if (!response.ok) throw new Error(response.status === 429 ? "Investigation rate limit reached. Try again later."
    : "Investigation unavailable. Check server enablement or try again later.");
  const reader = response.body?.getReader();
  if (!reader) throw new Error("Investigation stream unavailable.");
  let pending = "", size = 0, events = 0, complete = false;
  const decoder = new TextDecoder();
  const parse = (line: string) => {
    if (++events > 24 || complete) throw new Error("Invalid investigation stream.");
    const event = readInvestigationEvent(JSON.parse(line), cve);
    if (signal.aborted) return;
    if (event.type === "report") complete = true;
    onEvent(event);
  };
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      size += chunk.value.byteLength;
      if (size > 1_000_000) throw new Error("Investigation response too large.");
      pending += decoder.decode(chunk.value, { stream: true });
      let index;
      while ((index = pending.indexOf("\n")) >= 0) {
        const line = pending.slice(0, index); pending = pending.slice(index + 1);
        if (line.trim()) parse(line);
      }
    }
    pending += decoder.decode();
    if (pending.trim()) parse(pending);
    if (!complete && !signal.aborted) throw new Error("Investigation ended before a report was available.");
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
