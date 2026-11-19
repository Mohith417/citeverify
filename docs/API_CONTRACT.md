# CiteVerify API Contract (v1.0)

Base URL: `http://127.0.0.1:8000`. JSON bodies unless noted. Schemas live in
`backend/app/schemas/`. Errors: `{ "detail": "human readable message" }` with a proper status
(400, 404, 413, 422, 500).

## Status values (`ProcessingStatus`)

`uploaded`, `extracting`, `searching_references`, `retrieving_evidence`,
`comparing_claims`, `generating_report`, `completed`, `failed`, `needs_review`

## Verdicts

`supported`, `partially_supported`, `unsupported`, `contradictory`,
`potentially_outdated`, `insufficient_evidence`

`needs_human_review` is a separate boolean. It is always true for non-supported verdicts.

## Endpoints

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/api/health` | — | `{status, version, ai_provider, ai_configured, providers{}}` |
| GET | `/api/documents` | — | `DocumentOut[]` (latest 25) |
| POST | `/api/documents/upload` | multipart `file` | `DocumentOut` |
| POST | `/api/documents/{id}/analyze` | — | `StatusOut` (starts a background thread) |
| GET | `/api/documents/{id}/status` | — | `StatusOut` |
| GET | `/api/documents/{id}/results` | — | `DocumentResults` |
| DELETE | `/api/documents/{id}` | — | `{deleted}` |
| POST | `/api/documents/{id}/extract-citations` | — | citation inspection payload (debug/tests) |
| GET | `/api/claims/{claim_id}` | — | `ClaimDetail` |
| POST | `/api/claims/{claim_id}/review` | `ReviewUpdate` | `VerificationOut` |
| GET | `/api/references/{reference_id}` | — | `ReferenceOut` |
| POST | `/api/references/{reference_id}/upload-source` | multipart `file` | `ReferenceOut` (fallback hook) |
| GET | `/api/documents/{id}/report` | — | `application/pdf` |

## `DocumentResults`

```jsonc
{
  "document": { "id", "filename", "uploaded_at", "processing_status", "page_count", "needs_ocr" },
  "summary": {
    "total_claims", "total_citations", "references_matched", "papers_retrieved",
    "supported", "partially_supported", "unsupported", "contradictory",
    "potentially_outdated", "insufficient_evidence", "needs_human_review"
  },
  "claims": [ { "claim_id", "claim_text", "page_number", "citation_markers",
                "source_title", "verdict", "confidence_level",
                "needs_human_review", "reviewed_status", "flags" } ],
  "references": [ /* ReferenceOut */ ]
}
```

`Summary` is computed from database rows on every request; nothing is hardcoded.

## `ClaimDetail`

```jsonc
{
  "claim_id", "claim_text", "page_number", "section", "citation_markers",
  "claim_category", "flags",
  "references": [ { "marker", "match_status", "reference": ReferenceOut } ],
  "evidence": [ { "passage", "paragraph_id", "source_section", "source_url",
                  "relevance_score", "is_abstract_only", "quote_verified" } ],
  "verification": {
    "verdict", "explanation", "key_supporting_facts", "limitations",
    "confidence_level", "confidence_reason", "evidence_basis",
    "needs_human_review", "review_reasons", "reviewed_status", "reviewer_note"
  }
}
```

## Rules the UI relies on

- The frontend polls `/status` every ~2s until `completed` or `failed`.
- `POST /analyze` is idempotent while a run is active; it returns the current status.
- Every displayed dashboard number comes from `summary`, never from the client.
- A passage is shown as a quote only when `quote_verified` is true. AI-returned quotations are
  checked against the retrieved source text and dropped if absent.
- `evidence_basis = abstract_only` must be labelled in the UI; `none` implies human review.
- `fulltext_availability` on a reference is only `full_text` after text was actually retrieved.
