"""Module 8: Misleading Reference Detection.

Flags references and claims that are suspicious: missing citations, incorrect DOIs,
mismatched titles/authors, unrelated research, exaggerated results, weak evidence.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..models import Claim, Reference, Verification

logger = logging.getLogger(__name__)


def detect_issues(
    *,
    claim: Claim,
    reference: Optional[Reference],
    verification: Optional[Verification],
) -> list[str]:
    """Return a list of human-readable issue flags for a claim-reference-verification triple."""
    flags: list[str] = []

    # Missing citation
    if not claim.citation_markers:
        flags.append("missing_citation")

    # No reference matched
    if reference is None:
        if claim.citation_markers:
            flags.append("unmatched_citation")
        return flags

    # Reference-level flags carried over
    for flag in (reference.flags or []):
        if flag in (
            "incomplete_reference",
            "duplicate_reference",
            "doi_not_found",
            "doi_mismatch",
            "title_mismatch",
            "author_mismatch",
            "year_mismatch",
            "ambiguous",
        ):
            flags.append(f"reference_{flag}")

    # No original paper found
    if reference.matching_status in ("not_found", "ambiguous", "incomplete"):
        flags.append("original_paper_not_found")

    # No full text available
    if reference.fulltext_availability == "none":
        flags.append("no_full_text_available")
    elif reference.fulltext_availability == "abstract_only":
        flags.append("abstract_only_evidence")

    # Verification-level flags
    if verification is None:
        flags.append("not_yet_verified")
    else:
        if verification.needs_human_review:
            flags.append("needs_human_review")
        if verification.verdict in ("unsupported", "contradictory"):
            flags.append(f"verdict_{verification.verdict}")
        if verification.confidence_level == "low":
            flags.append("low_confidence")
        if verification.evidence_basis == "abstract_only":
            flags.append("abstract_only_verdict")
        if verification.evidence_basis == "none":
            flags.append("no_evidence_accessible")

    # Deduplicate while preserving order
    seen = set()
    unique_flags: list[str] = []
    for f in flags:
        if f not in seen:
            seen.add(f)
            unique_flags.append(f)
    return unique_flags


def summarize_flags(document_claims: list[Claim], document_refs: list[Reference], verifications: dict[str, Verification]) -> dict[str, int]:
    """Count issue categories across all claims."""
    counts: dict[str, int] = {}
    for claim in document_claims:
        ref = None
        if claim.reference_links:
            # take first linked reference
            link = claim.reference_links[0]
            ref = link.reference
        ver = verifications.get(claim.id)
        for flag in detect_issues(claim=claim, reference=ref, verification=ver):
            counts[flag] = counts.get(flag, 0) + 1
    return counts