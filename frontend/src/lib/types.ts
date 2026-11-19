export type Verdict =
  | "supported"
  | "partially_supported"
  | "unsupported"
  | "contradictory"
  | "potentially_outdated"
  | "insufficient_evidence";

export type Confidence = "low" | "medium" | "high";

export type ProcessingStatus =
  | "uploaded"
  | "extracting"
  | "searching_references"
  | "retrieving_evidence"
  | "comparing_claims"
  | "generating_report"
  | "completed"
  | "failed"
  | "needs_review";

export type FulltextAvailability = "none" | "abstract_only" | "full_text";
export type MatchingStatus = "pending" | "matched" | "ambiguous" | "not_found" | "incomplete";

export interface DocumentInfo {
  id: string;
  filename: string;
  uploaded_at: string;
  processing_status: ProcessingStatus;
  page_count: number;
  needs_ocr: boolean;
}

export interface DocumentStatus {
  id: string;
  processing_status: ProcessingStatus;
  stage_message: string;
  error: string | null;
}

export interface Summary {
  total_claims: number;
  total_citations: number;
  references_matched: number;
  references_cited: number;
  papers_retrieved: number;
  supported: number;
  partially_supported: number;
  unsupported: number;
  contradictory: number;
  potentially_outdated: number;
  insufficient_evidence: number;
  needs_human_review: number;
}

export interface ClaimRow {
  claim_id: string;
  claim_text: string;
  page_number: number | null;
  citation_markers: string[];
  source_title: string | null;
  verdict: Verdict | null;
  confidence_level: Confidence | null;
  needs_human_review: boolean;
  reviewed_status: string;
  flags: string[];
}

export interface Reference {
  id: string;
  ref_label: string;
  reference_text: string;
  title: string | null;
  authors: string[];
  year: number | null;
  doi: string | null;
  journal: string | null;
  matching_status: MatchingStatus;
  matching_confidence: number | null;
  matched_title: string | null;
  matched_authors: string[];
  matched_year: number | null;
  matched_doi: string | null;
  matched_source_url: string | null;
  publication_source: string | null;
  abstract: string | null;
  fulltext_availability: FulltextAvailability;
  fulltext_url: string | null;
  candidates: Array<Record<string, unknown>>;
  flags: string[];
}

export interface Evidence {
  id: string;
  reference_id: string;
  passage: string;
  paragraph_id: string | null;
  source_page: number | null;
  source_section: string | null;
  source_url: string | null;
  relevance_score: number | null;
  is_abstract_only: boolean;
  quote_verified: boolean;
}

export interface Verification {
  id: string;
  verdict: Verdict;
  explanation: string;
  key_supporting_facts: string[];
  limitations: string[];
  confidence_level: Confidence;
  confidence_reason: string;
  evidence_basis: "full_text" | "abstract_only" | "none" | string;
  needs_human_review: boolean;
  review_reasons: string[];
  reviewed_status: "pending" | "confirmed" | "overridden" | string;
  reviewer_note: string | null;
  created_at: string;
  history: Array<{
    id: string;
    action: string;
    previous_verdict: string | null;
    new_verdict: string | null;
    note: string | null;
    created_at: string;
  }>;
}

export interface DocumentResults {
  document: DocumentInfo;
  summary: Summary;
  claims: ClaimRow[];
  references: Reference[];
}

export interface ClaimDetail {
  claim_id: string;
  claim_text: string;
  page_number: number | null;
  section: string | null;
  citation_markers: string[];
  claim_category: string;
  flags: string[];
  references: Array<{ marker: string; match_status: string; reference: Reference }>;
  evidence: Evidence[];
  verification: Verification | null;
}

export interface Health {
  status: string;
  version: string;
  ai_provider: string;
  ai_configured: boolean;
  providers: Record<string, boolean>;
}
