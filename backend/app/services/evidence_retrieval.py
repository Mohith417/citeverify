"""Module 6: Evidence extraction and passage retrieval.

Splits retrieved full text into section-aware paragraphs and ranks them against a
claim. Semantic ranking uses sentence-transformers + FAISS when those optional
packages are installed; otherwise a deterministic TF-IDF/BM25 style lexical
ranker is used, so retrieval always works without a large model download.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None
_semantic_unavailable = False

KNOWN_SECTIONS = {
    "abstract", "introduction", "background", "methods", "materials and methods",
    "method", "methodology", "participants", "results", "findings", "discussion",
    "conclusion", "conclusions", "limitations", "results and discussion",
}

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "were", "was", "are", "has",
    "have", "had", "not", "but", "they", "their", "there", "which", "these", "than",
    "into", "also", "such", "can", "may", "more", "most", "between", "among", "our",
    "using", "used", "its", "who", "all", "any", "each", "both", "other", "however",
    "study", "studies", "paper", "results", "findings", "based", "however",
}


@dataclass
class EvidenceParagraph:
    text: str
    source_title: str
    source_url: Optional[str] = None
    source_doi: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    paragraph_id: Optional[str] = None


def _get_model():
    global _model, _semantic_unavailable
    if _semantic_unavailable:
        return None
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            _model = SentenceTransformer(MODEL_NAME)
        except Exception as exc:  # optional dependency
            logger.info("Semantic embeddings unavailable (%s); using lexical ranking.", exc)
            _semantic_unavailable = True
            return None
    return _model


NUMBERED_HEADING = re.compile(r"^\d+(?:\.\d+)*[\.)]?\s+[A-Z]")
HEADING_BLOCKLIST = {
    "open access", "edited by", "reviewed by", "citation", "keywords", "copyright",
    "correspondence", "received", "revised", "accepted", "published",
    "frontiers in psychiatry", "original research", "article", "review article",
}


def _is_heading(line: str, source_title: str = "") -> bool:
    text = line.strip().rstrip(":")
    if not text or len(text) > 70 or len(text.split()) > 8:
        return False
    if text.endswith((".", ",", ";", "?", "!")):
        return False
    low = text.lower()
    if low in HEADING_BLOCKLIST or low.startswith(("figure", "table", "*", "citation", "keywords")):
        return False
    if source_title and low in source_title.lower():
        return False  # running head / repeated article title
    if low in KNOWN_SECTIONS:
        return True
    if NUMBERED_HEADING.match(text):
        return True
    if text.isupper() and 1 <= len(text.split()) <= 6:
        return True
    return False


def split_into_paragraphs(
    full_text: str,
    *,
    source_title: str,
    source_url: Optional[str] = None,
    source_doi: Optional[str] = None,
    source_page: Optional[int] = None,
    source_section: Optional[str] = None,
) -> list[EvidenceParagraph]:
    """Split full text into section-aware paragraphs.

    Handles line-oriented PDF text (few blank lines) as well as JATS XML where
    headings and paragraphs are separated by blank lines.
    """
    paragraphs: list[EvidenceParagraph] = []
    section = source_section
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        text = re.sub(r"\s+", " ", " ".join(buffer)).strip()
        buffer = []
        if len(text) < 60:
            return
        for piece in _split_long(text, 1400):
            paragraphs.append(
                EvidenceParagraph(
                    text=piece,
                    source_title=source_title,
                    source_url=source_url,
                    source_doi=source_doi,
                    source_page=source_page,
                    source_section=section,
                    paragraph_id=f"p{len(paragraphs)}",
                )
            )

    for raw_line in (full_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if _is_heading(line, source_title):
            flush()
            section = line.rstrip(":").title()
            continue
        buffer.append(line)
    flush()
    return paragraphs


def _split_long(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out, buf = [], ""
    for s in sentences:
        if len(buf) + len(s) + 1 > limit and buf:
            out.append(buf.strip())
            buf = s
        else:
            buf = f"{buf} {s}".strip()
    if buf:
        out.append(buf.strip())
    return out


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]{3,}", (text or "").lower()) if t not in STOPWORDS]


def _lexical_ranking(claim_text: str, paragraphs: list[EvidenceParagraph]) -> list[float]:
    docs = [_tokens(p.text) for p in paragraphs]
    query = set(_tokens(claim_text))
    if not query or not docs:
        return [0.0] * len(paragraphs)
    df = Counter()
    for doc in docs:
        for term in set(doc):
            df[term] += 1
    n = len(docs)
    scores = []
    for doc in docs:
        tf = Counter(doc)
        score = 0.0
        for term in query:
            if tf[term]:
                idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
                score += idf * (tf[term] / (tf[term] + 1.2))
        scores.append(score / (len(query) ** 0.5))
    return scores


def retrieve_relevant_passages(
    claim_text: str,
    paragraphs: list[EvidenceParagraph],
    *,
    top_k: int = 3,
    min_score: float = 0.05,
) -> list[tuple[EvidenceParagraph, float]]:
    """Return the highest-scoring evidence paragraphs for a claim."""
    if not paragraphs:
        return []

    model = _get_model()
    scored: list[float]
    if model is not None:
        try:
            import numpy as np  # type: ignore

            claim_vec = model.encode([claim_text], normalize_embeddings=True)[0]
            para_vecs = model.encode([p.text for p in paragraphs], normalize_embeddings=True)
            scored = [float(x) for x in (np.asarray(para_vecs) @ np.asarray(claim_vec))]
            threshold = 0.30
        except Exception as exc:  # pragma: no cover
            logger.info("Semantic scoring failed (%s); falling back to lexical.", exc)
            scored = _lexical_ranking(claim_text, paragraphs)
            threshold = min_score
    else:
        scored = _lexical_ranking(claim_text, paragraphs)
        threshold = min_score
        # Normalise BM25-style scores to a 0..1 relative relevance for display.
        peak = max(scored) if scored else 0.0
        if peak > 0:
            scored = [round(value / peak, 3) for value in scored]
            threshold = 0.15

    ranked = sorted(zip(paragraphs, scored), key=lambda x: -x[1])
    picked = [(p, s) for p, s in ranked if s >= threshold][:top_k]
    if not picked and ranked and ranked[0][1] > 0:
        picked = ranked[:1]
    return picked


def build_faiss_index(paragraphs: list[EvidenceParagraph]):
    """Optional helper retained for larger corpora (FAISS installed)."""
    model = _get_model()
    if model is None or not paragraphs:
        return None
    try:
        import faiss  # type: ignore

        embeddings = model.encode([p.text for p in paragraphs], normalize_embeddings=True).astype("float32")
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        return index
    except Exception:  # pragma: no cover
        return None


def search_faiss(claim_text: str, index, paragraphs, *, top_k: int = 3, min_score: float = 0.30):
    model = _get_model()
    if model is None or index is None:
        return retrieve_relevant_passages(claim_text, paragraphs, top_k=top_k)
    claim_vec = model.encode([claim_text], normalize_embeddings=True).astype("float32")
    scores, indices = index.search(claim_vec, min(top_k, len(paragraphs)))
    out = []
    for score, idx in zip(scores[0], indices[0]):
        if 0 <= idx < len(paragraphs) and float(score) >= min_score:
            out.append((paragraphs[idx], float(score)))
    return out
