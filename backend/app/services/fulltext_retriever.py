"""Module 5: Original paper full-text retrieval.

Retrieval order:
1. Open-access PDF locations reported by OpenAlex / Unpaywall.
2. Europe PMC full-text XML for eligible biomedical papers.
3. Abstract-only fallback (explicitly labelled, never treated as full text).

Only publicly reachable http(s) URLs are fetched, private/loopback hosts are
refused (SSRF guard), downloads are size-capped, and paywalls are never bypassed.
"""

from __future__ import annotations

import hashlib
import ipaddress
import logging
import re
import socket
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from lxml import etree, html as lxml_html
from pypdf import PdfReader

from ..config import settings
from .paper_search import OPENALEX, fetch_json
from .unpaywall_provider import UnpaywallProvider

logger = logging.getLogger(__name__)

TEXT_CACHE = Path(__file__).resolve().parents[2] / "storage" / "cache" / "text"
MAX_BYTES = 12 * 1024 * 1024
MIN_FULLTEXT_CHARS = 1500
EPMC_REST = "https://www.ebi.ac.uk/europepmc/webservices/rest"


@dataclass
class FullTextResult:
    title: str
    doi: Optional[str]
    source_url: Optional[str]
    full_text: Optional[str]
    full_text_availability: str  # none | abstract_only | full_text
    pdf_url: Optional[str] = None
    xml_url: Optional[str] = None
    evidence_source: Optional[str] = None  # provenance: openalex / europepmc / unpaywall


# --------------------------------------------------------------------------
# Safe fetching
# --------------------------------------------------------------------------
def _host_is_public(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


def safe_url(url: str | None) -> str | None:
    """Return a normalized https URL only when it is publicly reachable."""
    if not url:
        return None
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return None
    if parsed.username or parsed.password:
        return None
    if not _host_is_public(parsed.hostname):
        return None
    return url.strip()


def fetch_bytes(url: str) -> tuple[Optional[bytes], str]:
    """Download a URL with size and content checks. Returns (bytes, content_type)."""
    url = safe_url(url) or ""
    if not url:
        return None, ""
    # Repositories rate-limit bursts (arXiv especially): retry once before
    # declaring that no open-access full text exists.
    for attempt in range(2):
        try:
            with httpx.stream("GET", url, timeout=30, follow_redirects=True,
                              headers={"User-Agent": "CiteVerify/1.0 (research verification)"}) as r:
                if r.status_code in (429, 503) and attempt == 0:
                    time.sleep(1.5)
                    continue
                if r.status_code != 200:
                    return None, ""
                chunks, total = [], 0
                for chunk in r.iter_bytes():
                    total += len(chunk)
                    if total > MAX_BYTES:
                        logger.info("Download exceeded size cap: %s", url)
                        return None, ""
                    chunks.append(chunk)
                ctype = r.headers.get("content-type", "").lower()
                return b"".join(chunks), ctype
        except httpx.HTTPError as exc:
            logger.info("Fetch failed for %s: %s", url, exc)
            if attempt == 0:
                time.sleep(1.5)
                continue
            return None, ""
    return None, ""


# --------------------------------------------------------------------------
# Text extraction
# --------------------------------------------------------------------------
def pdf_to_text(data: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            return ""
        parts = []
        for page in reader.pages[:80]:
            parts.append(page.extract_text() or "")
        return "\n\n".join(p for p in parts if p.strip())
    except Exception as exc:
        logger.info("PDF text extraction failed: %s", exc)
        return ""


def html_to_text(data: bytes) -> str:
    try:
        tree = lxml_html.fromstring(data)
        for bad in tree.xpath("//script|//style|//nav|//footer|//header"):
            bad.drop_tree()
        parts = []
        for el in tree.xpath("//p|//li|//h1|//h2|//h3|//h4//text()|//abstract"):
            text = el.text_content() if hasattr(el, "text_content") else str(el)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 40:
                parts.append(text)
        return "\n\n".join(parts)
    except Exception as exc:
        logger.info("HTML text extraction failed: %s", exc)
        return ""


SECTION_LABELS = {
    "abstract", "introduction", "background", "methods", "materials and methods",
    "method", "methodology", "results", "findings", "discussion", "conclusion",
    "conclusions", "limitations", "results and discussion", "related work",
}


def tei_to_text(xml_bytes: bytes) -> str:
    """Extract section-titled paragraph text from Europe PMC / JATS XML."""
    try:
        root = etree.fromstring(xml_bytes)
    except Exception as exc:
        logger.info("XML parse failed: %s", exc)
        return ""
    parts: list[str] = []

    abstract = root.xpath("//abstract")
    for node in abstract:
        text = re.sub(r"\s+", " ", "".join(node.itertext())).strip()
        if text:
            parts.append("Abstract\n\n" + text)

    for sec in root.xpath("//sec"):
        titles = sec.xpath("./title")
        if not titles:
            continue
        title = re.sub(r"\s+", " ", "".join(titles[0].itertext())).strip()
        paras = []
        for p in sec.xpath("./p"):
            text = re.sub(r"\s+", " ", "".join(p.itertext())).strip()
            if len(text) > 40:
                paras.append(text)
        if paras:
            parts.append(f"{title}\n\n" + "\n\n".join(paras))

    if not parts:
        for p in root.xpath("//body//p"):
            text = re.sub(r"\s+", " ", "".join(p.itertext())).strip()
            if len(text) > 40:
                parts.append(text)
    return "\n\n".join(parts)


def _cached_text(url: str) -> str:
    key = hashlib.sha1(url.encode()).hexdigest()
    path = TEXT_CACHE / f"{key}.txt"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _store_text(url: str, text: str) -> None:
    try:
        TEXT_CACHE.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1(url.encode()).hexdigest()
        (TEXT_CACHE / f"{key}.txt").write_text(text, encoding="utf-8")
    except OSError:
        pass


def _title_tokens(title: str | None) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]{5,}", (title or "").lower())][:10]


def looks_like_cited_paper(text: str, title: str | None, doi: str | None) -> bool:
    """Guard against a provider returning an unrelated open-access PDF."""
    lowered = (text or "").lower()
    if doi and doi.lower() in lowered:
        return True
    tokens = _title_tokens(title)
    if not tokens:
        return True  # nothing to compare against; rely on provenance
    head = lowered[:12000]
    hits = sum(1 for token in tokens if token in head)
    return hits >= max(2, int(len(tokens) * 0.6))


def _download_text(url: str, kind: str) -> str:
    cached = _cached_text(url)
    if cached:
        return cached
    data, ctype = fetch_bytes(url)
    if not data:
        return ""
    if kind == "pdf" or "pdf" in ctype or data[:5] == b"%PDF-":
        text = pdf_to_text(data)
        # Some repositories answer a PDF URL with an HTML landing/consent page.
        if len(text) < MIN_FULLTEXT_CHARS:
            text = html_to_text(data)
    elif "xml" in ctype or data.lstrip()[:1] == b"<":
        text = tei_to_text(data)
        if len(text) < MIN_FULLTEXT_CHARS:
            text = html_to_text(data)
    else:
        text = html_to_text(data)
    if len(text) >= MIN_FULLTEXT_CHARS:
        _store_text(url, text)
    return text


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def retrieve_full_text(
    *,
    doi: Optional[str] = None,
    title: Optional[str] = None,
    openalex_id: Optional[str] = None,
    pdf_url: Optional[str] = None,
    xml_url: Optional[str] = None,
    abstract: Optional[str] = None,
    pmcid: Optional[str] = None,
) -> FullTextResult:
    doi = (doi or "").lower() or None
    landing: Optional[str] = None
    pdf_candidates: list[str] = []
    abstract = abstract
    title = title

    # 1. Europe PMC full text (very reliable for biomedical OA articles)
    if pmcid or doi:
        try:
            query = f"PMCID:{pmcid}" if pmcid else f'DOI:"{doi}"'
            st, data = fetch_json(
                f"{EPMC_REST}/search",
                {"query": query, "format": "json", "resultType": "core", "pageSize": 1},
            )
            rec = None
            if st == 200 and data:
                results = (data.get("resultList") or {}).get("result") or []
                rec = results[0] if results else None
            if rec:
                pmcid = pmcid or rec.get("pmcid")
                abstract = abstract or re.sub(r"<[^>]+>", " ", rec.get("abstractText") or "").strip() or None
                title = title or rec.get("title")
                if pmcid and rec.get("isOpenAccess") == "Y":
                    xml_url = xml_url or f"{EPMC_REST}/{pmcid}/fullTextXML"
                    landing = landing or f"https://europepmc.org/article/{rec.get('source', 'MED')}/{rec.get('id')}"
        except Exception as exc:  # pragma: no cover
            logger.info("Europe PMC lookup failed: %s", exc)

    if xml_url and "/fullTextXML" in xml_url:
        text = _download_text(xml_url, "xml")
        if len(text) >= MIN_FULLTEXT_CHARS:
            return FullTextResult(
                title=title or "", doi=doi, source_url=landing or xml_url,
                full_text=text, full_text_availability="full_text",
                pdf_url=pdf_url, xml_url=xml_url, evidence_source="europepmc",
            )

    # 2. OpenAlex open-access locations
    if doi or openalex_id:
        try:
            path = f"{OPENALEX}/works/doi:{doi}" if doi else f"{OPENALEX}/works/{openalex_id.rsplit('/', 1)[-1]}"
            st, work = fetch_json(path)
            if st == 200 and work:
                title = title or work.get("display_name")
                abstract = abstract or _abstract_from_openalex(work)
                if not doi:
                    doi = (work.get("doi") or "").replace("https://doi.org/", "").lower() or None
                best = work.get("best_oa_location") or {}
                landing = landing or best.get("landing_page_url")
                for loc in [best] + (work.get("locations") or []):
                    if loc and loc.get("is_oa") and loc.get("pdf_url"):
                        pdf_candidates.append(loc["pdf_url"])
        except Exception as exc:  # pragma: no cover
            logger.info("OpenAlex full-text lookup failed: %s", exc)

    # 3. Unpaywall OA locations
    if doi:
        try:
            oa = UnpaywallProvider().find_open_access_full_text(doi=doi)
            if oa:
                pdf_candidates.append(oa)
        except Exception as exc:  # pragma: no cover
            logger.info("Unpaywall lookup failed: %s", exc)

    for candidate in [pdf_url, *pdf_candidates]:
        if not candidate:
            continue
        text = _download_text(candidate, "pdf")
        if len(text) >= MIN_FULLTEXT_CHARS and looks_like_cited_paper(text, title, doi):
            return FullTextResult(
                title=title or "", doi=doi, source_url=landing or candidate,
                full_text=text, full_text_availability="full_text",
                pdf_url=candidate, xml_url=xml_url, evidence_source="open_access_pdf",
            )

    # 4. Abstract only — explicitly labelled
    if abstract:
        return FullTextResult(
            title=title or "", doi=doi,
            source_url=landing or (f"https://doi.org/{doi}" if doi else None),
            full_text=None, full_text_availability="abstract_only",
            pdf_url=pdf_url, xml_url=xml_url, evidence_source="abstract",
        )

    return FullTextResult(
        title=title or "", doi=doi, source_url=landing,
        full_text=None, full_text_availability="none",
        pdf_url=pdf_url, xml_url=xml_url, evidence_source=None,
    )


def _abstract_from_openalex(work: dict) -> Optional[str]:
    inv = work.get("abstract_inverted_index")
    if not inv:
        return None
    words = {}
    for word, positions in inv.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words)) or None
