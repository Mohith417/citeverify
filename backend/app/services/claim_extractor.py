"""Module 2: Scientific claim extraction.

Uses the configured LLM for high-quality extraction, and falls back to a
deterministic sentence heuristic when no AI provider is reachable, so the rest of
the pipeline still produces real output. The fallback never invents wording.
"""

from __future__ import annotations

import logging
import re

from ..config import settings
from ..schemas.claim_schema import ExtractedClaim
from . import llm

logger = logging.getLogger(__name__)

CITATION_HINT = re.compile(
    r"\[\s*\d+[\s,\u2013\u2014-]*\]|\(\s*[A-Z][A-Za-z'’\-]+[^()]{0,60}(?:19|20)\d{2}[^()]{0,20}\)"
)
NUMERIC = re.compile(r"\d+(?:\.\d+)?\s*%|\bp\s*[<=>]\s*0?\.\d+|\bn\s*=\s*\d+|\b\d{2,}\b")
FINDING_VERB = re.compile(
    r"\b(found|shows?|shown|demonstrat\w+|report\w*|suggest\w*|indicat\w+|reveal\w+|"
    r"conclude\w*|evidence|associated|increas\w+|decreas\w+|improv\w+|significant\w*)\b",
    re.IGNORECASE,
)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\[])")


def is_available() -> bool:
    return llm.is_available()


def _chunks(text_by_page: list[tuple[int, str]], size: int = 11000):
    buf, length = [], 0
    for page, text in text_by_page:
        if not text.strip():
            continue
        buf.append(f"=== PAGE {page} ===\n{text}")
        length += len(text)
        if length >= size:
            yield "\n\n".join(buf)
            buf, length = [], 0
    if buf:
        yield "\n\n".join(buf)


def _dedupe(claims: list[ExtractedClaim]) -> list[ExtractedClaim]:
    seen, out = set(), []
    for c in claims:
        key = re.sub(r"\W+", "", c.claim_text.lower())[:160]
        if key and key not in seen:
            seen.add(key)
            out.append(c)
    return out


def heuristic_claims(text_by_page: list[tuple[int, str]]) -> list[ExtractedClaim]:
    """Deterministic fallback: sentences asserting findings, numbers or citations."""
    out: list[ExtractedClaim] = []
    for page, text in text_by_page:
        flat = re.sub(r"\s+", " ", text)
        for sentence in SENTENCE_SPLIT.split(flat):
            s = sentence.strip()
            if len(s) < 60 or len(s) > 450:
                continue
            markers = [m.group(0) for m in CITATION_HINT.finditer(s)]
            if not (markers or NUMERIC.search(s) or FINDING_VERB.search(s)):
                continue
            if s.lower().startswith(("figure ", "table ", "copyright", "http")):
                continue
            if NUMERIC.search(s):
                category = "numerical"
            elif FINDING_VERB.search(s):
                category = "finding"
            elif markers:
                category = "assertion"
            else:
                category = "factual"
            out.append(
                ExtractedClaim(
                    claim_text=s,
                    page_number=page,
                    section=None,
                    citation_markers=markers[:5],
                    claim_category=category,
                )
            )
            if len(out) >= 40:
                return out
    return out


class ClaimExtractor:
    def is_available(self) -> bool:
        return is_available()

    def extract_claims(self, text_by_page: list[tuple[int, str]]) -> list[ExtractedClaim]:
        if not self.is_available():
            logger.warning("No AI provider configured; using heuristic claim extraction.")
            return heuristic_claims(text_by_page)[: settings.max_claims]

        claims: list[ExtractedClaim] = []
        for chunk in _chunks(text_by_page):
            try:
                data = llm.generate_json(
                    system=(
                        "You extract scientific claims from academic documents. "
                        "You always copy claim wording verbatim and answer with JSON only."
                    ),
                    prompt=self._build_prompt(chunk),
                )
                for raw in data.get("claims", []):
                    try:
                        claims.append(ExtractedClaim.model_validate(raw))
                    except Exception:
                        continue  # skip malformed entries, never fabricate
            except llm.LLMError as exc:
                logger.warning("Claim extraction chunk failed: %s", exc)
            if len(claims) >= settings.max_claims * 2:
                break

        claims = _dedupe(claims)
        if not claims:
            logger.warning("LLM returned no claims; falling back to heuristics.")
            return heuristic_claims(text_by_page)[: settings.max_claims]
        return claims[: settings.max_claims]

    @staticmethod
    def _build_prompt(combined_text: str) -> str:
        return f"""Read this academic document text. Page markers look like "=== PAGE N ===".

Identify up to 12 statements that REQUIRE empirical evidence or citation support:
factual statements, numerical/statistical claims, scientific findings and conclusions.

Rules:
- claim_text: the EXACT sentence(s) copied word-for-word from the document. Never paraphrase.
- page_number: integer page where it appears.
- section: section name if obvious (e.g. "Introduction", "Results"), else null.
- citation_markers: in-text markers attached, e.g. ["[1]", "(Smith, 2023)"].
- claim_category: one of "factual", "numerical", "finding", "statistical", "conclusion", "assertion".

Skip headings, boilerplate, author affiliations and method descriptions without a result.

Return ONLY this JSON object:
{{"claims": [{{"claim_text": "...", "page_number": 1, "section": "Introduction", "citation_markers": ["[1]"], "claim_category": "finding"}}]}}

Document text:
{combined_text}"""


claim_extractor = ClaimExtractor()
