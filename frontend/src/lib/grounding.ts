import type { Grounding, GroundingEvidence, Source, CopilotResponse } from "../types/copilot.ts";

export const groundingStatuses = {
  supported_quotes: ["Quotation attribution checked", "The backend linked these quotations to retrieved passages. Factual truth and answer completeness are not verified."],
  insufficient_evidence: ["Insufficient evidence", "The retrieved passages do not provide enough evidence. Try a narrower question or provide an appropriate source."],
  conflicting_evidence: ["Conflicting sources", "The retrieved sources disagree for the same scope. No supported resolution is available."],
  retrieval_failure: ["Retrieval unavailable", "Retrieval did not complete. This does not establish that relevant evidence is absent."],
  unsupported_claims: ["Claims not supported", "The proposed answer did not pass the citation and quotation checks."],
  unverified_evidence: ["Evidence could not be checked", "The retrieved evidence could not be authorized or validated."],
  unsafe_evidence: ["Source content withheld", "Instruction-like or sensitive content was excluded from the evidence."],
  generation_failure: ["Answer generation unavailable", "The provider did not produce a usable verified answer. You may try again later."],
} as const;
export type GroundingView =
  | { kind: "legacy" }
  | { kind: "invalid" }
  | { kind: "valid"; value: Grounding };
type RecordValue = Record<string, unknown>;
function object(value: unknown): value is RecordValue {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function text(value: unknown, maximum = 2000): value is string {
  return typeof value === "string" && value.trim().length > 0 && value.length <= maximum;
}
function nullableText(value: unknown, maximum = 2000): boolean {
  return value === null || text(value, maximum);
}
function date(value: unknown): boolean {
  return text(value, 64) && /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) && Number.isFinite(Date.parse(value));
}
export function safeCitationUrl(value: unknown): string | null {
  if (typeof value !== "string" || value.length > 2048 ||
      !/^https:\/\//i.test(value) || Array.from(value).some(character => { const code = character.charCodeAt(0); return code <= 32 || (code >= 127 && code <= 159) || character === "\\"; })) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && url.hostname && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}
export function sourceOrganization(sourceId: string): string | null {
  const organizations: Record<string, string> = {
    nvd: "NIST National Vulnerability Database", "cisa-kev": "CISA",
    "mitre-attack": "MITRE ATT&CK", "mitre-cwe": "MITRE CWE",
    "nist-csrc": "NIST CSRC", owasp: "OWASP",
    "fixture-reference": "CyberShield synthetic fixtures", "private-upload": "Private user material",
  };
  return Object.hasOwn(organizations, sourceId) ? organizations[sourceId] : null;
}
export function displayDate(value: string | null): string | null {
  if (!date(value)) return null;
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(value!));
}
function evidence(value: unknown): value is GroundingEvidence {
  if (!object(value) || !text(value.citation_id, 22) || !/^E-[a-f0-9]{20}$/.test(value.citation_id)) return false;
  if (!["chunk_id", "document_id", "source_id", "source_version", "content_hash", "record_id", "title", "section", "excerpt"]
    .every(key => text(value[key], key === "excerpt" ? 2000 : 500))) return false;
  if (!nullableText(value.canonical_url, 2048) || !date(value.retrieved_at) ||
      !(value.published_at === null || date(value.published_at)) ||
      !(value.modified_at === null || date(value.modified_at))) return false;
  return (value.scope === "private" && value.source_id === "private-upload" && value.trust === "private_upload" && value.canonical_url === null) ||
    (value.scope === "public" && value.source_id !== "private-upload" && ["official_snapshot", "synthetic_fixture"].includes(String(value.trust)));
}
/** Display validation only: the server remains the authorization/verifier boundary. */
export function readGrounding(raw: unknown): GroundingView {
  if (raw === undefined || raw === null) return { kind: "legacy" };
  const invalid: GroundingView = { kind: "invalid" };
  if (!object(raw) || typeof raw.status !== "string" || !Object.hasOwn(groundingStatuses, raw.status) ||
      raw.verification_scope !== "quotation_attribution_only" || raw.answer_completeness !== "not_verified" ||
      !Array.isArray(raw.claims) || !Array.isArray(raw.evidence)) return invalid;
  if (raw.status !== "supported_quotes") {
    return raw.abstained === true && raw.claims.length === 0 && raw.evidence.length === 0
      ? { kind: "valid", value: raw as unknown as Grounding } : invalid;
  }
  if (raw.abstained !== false || raw.claims.length < 1 || raw.claims.length > 5 ||
      raw.evidence.length < 1 || raw.evidence.length > 5 || !raw.evidence.every(evidence)) return invalid;
  const known = new Map(raw.evidence.map(item => [item.citation_id, item]));
  if (known.size !== raw.evidence.length) return invalid;
  const used = new Set<string>();
  const claimIds = new Set<string>();
  for (const claim of raw.claims) {
    if (!object(claim) || !text(claim.claim_id, 100) || claimIds.has(claim.claim_id) ||
        !text(claim.text) || claim.kind !== "complete_section_quote" ||
        claim.verification !== "exact_excerpt" || claim.verification_scope !== "quotation_attribution_only" ||
        !text(claim.section_hash, 128) || !Array.isArray(claim.citation_ids) ||
        claim.citation_ids.length < 1 || claim.citation_ids.length > 5 ||
        new Set(claim.citation_ids).size !== claim.citation_ids.length) return invalid;
    claimIds.add(claim.claim_id);
    for (const id of claim.citation_ids) {
      if (typeof id !== "string" || known.get(id)?.excerpt !== claim.text) return invalid;
      used.add(id);
    }
  }
  return used.size === known.size ? { kind: "valid", value: raw as unknown as Grounding } : invalid;
}
export function sourceList(raw: unknown): Source[] {
  return Array.isArray(raw) ? raw.filter((s): s is Source => object(s) &&
    text(s.filename, 500) && typeof s.page === "number" && Number.isInteger(s.page) && s.page > 0 &&
    (s.folder === undefined || s.folder === null || text(s.folder, 500))).slice(0, 20) : [];
}

export function readCopilotResponse(raw: unknown): CopilotResponse {
  if (!object(raw) || !text(raw.answer, 100000)) throw new Error("Invalid chat response.");
  return {
    answer: raw.answer,
    conversation_id: typeof raw.conversation_id === "number" && Number.isInteger(raw.conversation_id) && raw.conversation_id > 0 ? raw.conversation_id : null,
    sources: sourceList(raw.sources), related_sources: sourceList(raw.related_sources),
    // Preserve malformed metadata so display fails closed instead of becoming legacy.
    grounding: raw.grounding as Grounding | null | undefined,
  };
}
