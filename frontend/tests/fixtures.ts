import type { Grounding } from "../src/types/copilot.ts";

export function supported(text = "Synthetic recovery requires two independent operators."): Grounding {
  return {
    status: "supported_quotes", answer: "Backend display text.", abstained: false, reason: "complete_section_quotations_only",
    verification_scope: "quotation_attribution_only", answer_completeness: "not_verified",
    claims: [{ claim_id: "claim-1", text, citation_ids: ["E-aaaaaaaaaaaaaaaaaaaa"], section_hash: "a".repeat(64),
      kind: "complete_section_quote", verification: "exact_excerpt", verification_scope: "quotation_attribution_only" }],
    evidence: [{ citation_id: "E-aaaaaaaaaaaaaaaaaaaa", chunk_id: "chunk-" + "a".repeat(64),
      document_id: "doc-" + "b".repeat(64), source_id: "fixture-reference", record_id: "SYNTHETIC-1",
      title: "Synthetic recovery reference", canonical_url: "https://example.com/reference",
      section: "Recovery", excerpt: text, published_at: "2026-01-02T00:00:00Z", modified_at: null,
      retrieved_at: "2026-11-10T00:00:00Z", source_version: "v-" + "c".repeat(64),
      content_hash: "d".repeat(64), trust: "synthetic_fixture", scope: "public" }],
  };
}
