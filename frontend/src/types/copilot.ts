    export interface Source {

        filename: string;

        page: number;

        folder?: string | null;
    }

    export interface CopilotRequest {

        question: string;

        conversation_id?: number;
    }

    export interface CopilotResponse {

        conversation_id: number | null;

        answer: string;

        sources: Source[];

        related_sources?: Source[];
        grounding?: Grounding | null;
        answer_basis?: AnswerBasis;
    }
export type GroundingStatus = "supported_quotes" | "insufficient_evidence" | "retrieval_failure"
  | "conflicting_evidence" | "unsupported_claims" | "unverified_evidence" | "unsafe_evidence" | "generation_failure";
export interface GroundingEvidence {
  citation_id: string; chunk_id: string; document_id: string; source_id: string; record_id: string;
  title: string; canonical_url: string | null; section: string; excerpt: string;
  published_at: string | null; modified_at: string | null; retrieved_at: string;
  source_version: string; content_hash: string;
  trust: "official_snapshot" | "synthetic_fixture" | "private_upload"; scope: "public" | "private";
}
export interface GroundingClaim {
  claim_id: string; text: string; citation_ids: string[]; section_hash: string;
  kind: "complete_section_quote"; verification: "exact_excerpt"; verification_scope: "quotation_attribution_only";
}
export interface Grounding {
  status: GroundingStatus; answer: string; abstained: boolean; reason: string;
  claims: GroundingClaim[]; evidence: GroundingEvidence[];
  answer_completeness: "not_verified"; verification_scope: "quotation_attribution_only";
}

export type AnswerBasis = "document" | "general_knowledge" | "tool" | "conversation";
