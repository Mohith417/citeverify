"""Module 7: Claim-to-evidence comparison.

Sends the exact claim, publication metadata and retrieved source passages to the
configured LLM and validates the structured verdict. Every quotation the model
returns is checked against the retrieved source text; quotes that cannot be found
are discarded, so a fabricated quotation can never reach the report.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from ..schemas.verification_schema import AIVerdictOutput
from . import llm

logger = logging.getLogger(__name__)

VERDICTS = {
    "supported",
    "partially_supported",
    "unsupported",
    "contradictory",
    "potentially_outdated",
    "insufficient_evidence",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def quote_in_source(quote: str, source_text: str) -> bool:
    q = _norm(quote)
    if len(q) < 20:
        return False
    if q in _norm(source_text):
        return True
    # tolerate hyphenation/line-break artefacts from PDF extraction
    return _norm(re.sub(r"-\s+", "", quote)) in _norm(re.sub(r"-\s+", "", source_text or ""))


def _fallback(claim_id: str, reason: str, **kw) -> AIVerdictOutput:
    return AIVerdictOutput(
        claim_id=claim_id,
        verdict="insufficient_evidence",
        explanation=reason,
        evidence_passages=[],
        source_title=kw.get("source_title"),
        source_doi=kw.get("source_doi"),
        source_url=kw.get("source_url"),
        source_page_or_section=kw.get("source_page_or_section"),
        key_supporting_facts=[],
        limitations=["Automated comparison unavailable"],
        confidence_level="low",
        confidence_reason=reason,
        needs_human_review=True,
    )


class AIVerifier:
    def is_available(self) -> bool:
        return llm.is_available()

    def verify_claim(
        self,
        *,
        claim_id: str,
        claim_text: str,
        citation_markers: list[str],
        source_title: Optional[str],
        source_doi: Optional[str],
        source_url: Optional[str],
        evidence_passages: list[str],
        source_page_or_section: Optional[str],
        study_context: Optional[str] = None,
        abstract_only: bool = False,
    ) -> AIVerdictOutput:
        if not self.is_available():
            return _fallback(
                claim_id,
                "No AI provider configured, so the claim was not compared against the source. "
                "Evidence passages are still shown for manual review.",
                source_title=source_title,
                source_doi=source_doi,
                source_url=source_url,
                source_page_or_section=source_page_or_section,
            )
        if not evidence_passages:
            return _fallback(
                claim_id,
                "No usable evidence passage could be retrieved from the cited paper, so the "
                "statement could not be compared against the original research.",
                source_title=source_title,
                source_doi=source_doi,
                source_url=source_url,
                source_page_or_section=source_page_or_section,
            )

        evidence_block = "\n\n".join(
            f"[Passage {i + 1}] {p}" for i, p in enumerate(evidence_passages)
        )
        prompt = self._build_prompt(
            claim_text=claim_text,
            citation_markers=citation_markers,
            source_title=source_title,
            source_doi=source_doi,
            source_url=source_url,
            evidence_block=evidence_block,
            source_page_or_section=source_page_or_section,
            study_context=study_context,
            abstract_only=abstract_only,
        )
        try:
            data = llm.generate_json(
                system=(
                    "You are a rigorous scientific claim verifier. You use only the supplied "
                    "evidence passages, never outside knowledge, and answer with JSON only."
                ),
                prompt=prompt,
                response_schema=AIVerdictOutput,
            )
        except llm.LLMError as exc:
            logger.warning("AI verification failed: %s", exc)
            return _fallback(
                claim_id,
                f"Automated comparison failed: {exc}",
                source_title=source_title,
                source_doi=source_doi,
                source_url=source_url,
                source_page_or_section=source_page_or_section,
            )

        result = self._coerce(data, claim_id, source_title, source_doi, source_url,
                              source_page_or_section)
        # Hard guard: quotations must exist in the retrieved source text.
        joined = "\n".join(evidence_passages)
        verified = [p for p in result.evidence_passages if quote_in_source(p.quote, joined)]
        if result.evidence_passages and not verified:
            logger.warning("Dropped unverifiable quotations for claim %s", claim_id)
            result.limitations = (result.limitations or []) + [
                "Model quotation was removed because it did not appear in the retrieved source text."
            ]
            result.needs_human_review = True
        result.evidence_passages = verified
        return result

    @staticmethod
    def _coerce(data: dict, claim_id, source_title, source_doi, source_url, section) -> AIVerdictOutput:
        verdict = str(data.get("verdict", "")).strip().lower().replace(" ", "_")
        if verdict not in VERDICTS:
            verdict = "insufficient_evidence"
        confidence = str(data.get("confidence_level", "low")).strip().lower()
        if confidence not in ("low", "medium", "high"):
            confidence = "low"
        passages = []
        for p in data.get("evidence_passages") or []:
            if isinstance(p, str) and p.strip():
                passages.append({"quote": p, "source_page_or_section": section})
            elif isinstance(p, dict) and p.get("quote"):
                passages.append({
                    "quote": str(p["quote"]),
                    "source_page_or_section": p.get("source_page_or_section") or section,
                })
        payload = {
            "claim_id": claim_id,
            "verdict": verdict,
            "explanation": str(data.get("explanation") or "No explanation returned.")[:4000],
            "evidence_passages": passages,
            "source_title": data.get("source_title") or source_title,
            "source_doi": data.get("source_doi") or source_doi,
            "source_url": data.get("source_url") or source_url,
            "source_page_or_section": data.get("source_page_or_section") or section,
            "key_supporting_facts": [str(x) for x in (data.get("key_supporting_facts") or [])][:8],
            "limitations": [str(x) for x in (data.get("limitations") or [])][:8],
            "confidence_level": confidence,
            "confidence_reason": str(data.get("confidence_reason") or "")[:1000],
            "needs_human_review": bool(data.get("needs_human_review", True)),
        }
        if payload["verdict"] != "supported":
            payload["needs_human_review"] = True
        return AIVerdictOutput.model_validate(payload)

    @staticmethod
    def _build_prompt(
        *,
        claim_text: str,
        citation_markers: list[str],
        source_title: Optional[str],
        source_doi: Optional[str],
        source_url: Optional[str],
        evidence_block: str,
        source_page_or_section: Optional[str],
        study_context: Optional[str],
        abstract_only: bool,
    ) -> str:
        scope = "ABSTRACT ONLY - do not treat as full-text confirmation" if abstract_only else "full-text passages"
        return f"""Compare the CLAIM from an uploaded document against the EVIDENCE PASSAGES
taken from the paper it cites.

CLAIM (verbatim, do not modify):
"{claim_text}"

Citation markers used by the writer: {", ".join(citation_markers) or "none"}

CITED PAPER
Title: {source_title or "unknown"}
DOI: {source_doi or "none"}
URL: {source_url or "none"}
Section/page: {source_page_or_section or "unknown"}
Publication context: {study_context or "not available"}
Evidence scope: {scope}

EVIDENCE PASSAGES (verbatim from that paper):
{evidence_block}

Evaluate, using ONLY these passages:
1. Does the central idea match?
2. Are numerical values, percentages and sample sizes accurate?
3. Is the population/context the same?
4. Is the claim broader than what the study tested?
5. Are findings exaggerated or overstated?
6. Do study limitations weaken the claim?
7. Does the cited paper actually justify the conclusion drawn?

Choose exactly one verdict:
- "supported": the evidence directly establishes the statement.
- "partially_supported": part of it is supported; numbers/details/scope are not.
- "unsupported": the evidence does not establish the statement.
- "contradictory": the passages report findings that oppose the statement.
- "potentially_outdated": newer evidence is required to judge; do NOT pick this just because the paper is old.
- "insufficient_evidence": the passages cannot answer the question.

Use "unsupported" when the passages neither establish nor oppose the statement (for example, a
paper that simply does not study that question). Reserve "contradictory" for evidence that
actively reports the opposite result.

Return ONLY this JSON:
{{
  "claim_id": "ignored",
  "verdict": "supported|partially_supported|unsupported|contradictory|potentially_outdated|insufficient_evidence",
  "explanation": "2-4 sentences explaining why, referencing the passages",
  "evidence_passages": [{{"quote": "exact substring copied from a passage above", "source_page_or_section": "section or page"}}],
  "source_title": "original paper title",
  "source_doi": "doi if known",
  "source_url": "url if known",
  "source_page_or_section": "section or page",
  "key_supporting_facts": ["fact drawn from the passages"],
  "limitations": ["limitation of the cited study"],
  "confidence_level": "low|medium|high",
  "confidence_reason": "why this confidence, based on evidence strength",
  "needs_human_review": true
}}

Quotes MUST be copied verbatim from the passages above. Never invent a quote, DOI, or finding."""


ai_verifier = AIVerifier()
