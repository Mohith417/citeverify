# CiteVerify API Contract (v0.2)

Base URL: `http://localhost:8000`. All bodies are JSON unless noted. Schemas live in `backend/app/schemas/`.
Errors: `{ "detail": "human readable message" }` with a proper HTTP status (400, 404, 413, 422, 500).

## Status values (`ProcessingStatus`)
uploaded, extracting, searching_references, retrieving_evidence, comparing_claims,
generating_report, completed, failed, needs_review

## Verdicts
supported, partially_supported, unsupported, contradictory, potentially_outdated, insufficient_evidence
(`needs_human_review` is a separate boolean flag.)

## Endpoints
| Method | Path | Purpose | Response |
|---|---|---|---|
| POST | /api/documents/upload | multipart `file` (PDF, max MAX_UPLOAD_MB) | `DocumentOut` |
| POST | /api/documents/{id}/analyze | start background analysis | `StatusOut` |
| GET | /api/documents/{id}/status | poll progress | `StatusOut` |
| GET | /api/documents/{id}/results | dashboard data | `DocumentResults` |
| GET | /api/claims/{claim_id} | claim detail | `ClaimDetail` |
| POST | /api/claims/{claim_id}/review | body `ReviewUpdate` | `VerificationOut` |
| GET | /api/references/{reference_id} | reference + publication info | `ReferenceOut` |
| POST | /api/references/{reference_id}/upload-source | manual source PDF fallback | `ReferenceOut` |
| GET | /api/documents/{id}/report | PDF download (application/pdf) | file |

## Rules
- Frontend polls `/status` every 2s until `completed`, `failed` or `needs_review`.
- All dashboard numbers come from `Summary`, computed server-side from DB rows.
- Evidence `passage` is verbatim source text; `quote_verified` must be true before display as a quote.
- If `fulltext_availability` is `abstract_only`, UI must label the verdict as abstract-based.
