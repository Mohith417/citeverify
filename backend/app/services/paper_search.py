import hashlib
import html
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import quote, urlparse

import httpx
from rapidfuzz import fuzz

from ..config import settings
from .citation_extractor import surname

CACHE_DIR = Path(__file__).resolve().parents[2] / "storage" / "cache"
CROSSREF = "https://api.crossref.org"
OPENALEX = "https://api.openalex.org"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
# only these hosts may ever be contacted (prevents SSRF)
ALLOWED_HOSTS = {"api.crossref.org", "api.openalex.org", "www.ebi.ac.uk"}


@dataclass
class Candidate:
    title: str = ""
    authors: list = field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    url: str | None = None
    journal: str | None = None
    abstract: str | None = None
    openalex_id: str | None = None
    pmcid: str | None = None
    pdf_url: str | None = None
    xml_url: str | None = None
    is_oa: bool = False
    sources: list = field(default_factory=list)


# ---------------- HTTP (cached, host-restricted, retrying) ----------------

def fetch_json(url: str, params: dict | None = None, retries: int = 2):
    # returns (status_code, json_or_None); status 0 means network failure
    host = urlparse(url).hostname
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Host not allowed: {host}")
    params = dict(params or {})
    mailto = settings.contact_email
    headers = {"User-Agent": f"CiteVerify/0.5 (mailto:{mailto or 'unknown@example.com'})"}
    if mailto and host in ("api.crossref.org", "api.openalex.org"):
        params["mailto"] = mailto
    key = hashlib.sha1((url + json.dumps(sorted(params.items()), default=str)).encode()).hexdigest()
    path = CACHE_DIR / f"{key}.json"
    try:
        c = json.loads(path.read_text(encoding="utf-8"))
        return c["status"], c["data"]
    except Exception:
        pass
    send = dict(params)
    if host == "api.openalex.org" and settings.openalex_api_key:
        send["api_key"] = settings.openalex_api_key  # added after cache key, never stored
    for attempt in range(retries + 1):
        try:
            r = httpx.get(url, params=send, headers=headers, timeout=20)
        except httpx.HTTPError:
            time.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code in (200, 404):
            data = r.json() if r.status_code == 200 else None
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"status": r.status_code, "data": data}), encoding="utf-8")
            except OSError:
                pass
            return r.status_code, data
        return r.status_code, None
    return 0, None


# ---------------- parsing helpers ----------------

def strip_tags(s: str | None) -> str | None:
    if not s:
        return None
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip() or None


def abstract_from_inverted(inv: dict | None) -> str | None:
    if not inv:
        return None
    words = {}
    for w, positions in inv.items():
        for p in positions:
            words[p] = w
    return " ".join(words[i] for i in sorted(words)) or None


def crossref_to_cand(item: dict) -> Candidate:
    year = None
    for k in ("issued", "published-print", "published-online", "created"):
        dp = (item.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            year = dp[0][0]
            break
    doi = (item.get("DOI") or "").lower() or None
    authors = [((a.get("given", "") + " " + a.get("family", "")).strip() or a.get("name", ""))
               for a in item.get("author", [])]
    return Candidate(
        title=((item.get("title") or [""])[0] or "").strip(), authors=[a for a in authors if a],
        year=year, doi=doi, url=item.get("URL") or (f"https://doi.org/{doi}" if doi else None),
        journal=(item.get("container-title") or [None])[0], abstract=strip_tags(item.get("abstract")),
        sources=["crossref"])


def openalex_to_cand(w: dict) -> Candidate:
    doi = (w.get("doi") or "").replace("https://doi.org/", "").lower() or None
    loc = w.get("best_oa_location") or {}
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
    pm = re.search(r"PMC\d+", (w.get("ids") or {}).get("pmcid") or "")
    return Candidate(
        title=(w.get("display_name") or w.get("title") or "").strip(),
        authors=[a["author"]["display_name"] for a in w.get("authorships", []) if a.get("author")],
        year=w.get("publication_year"), doi=doi, openalex_id=w.get("id"),
        url=loc.get("landing_page_url") or (f"https://doi.org/{doi}" if doi else w.get("id")),
        journal=src, abstract=abstract_from_inverted(w.get("abstract_inverted_index")),
        pmcid=pm.group(0) if pm else None, pdf_url=loc.get("pdf_url"),
        is_oa=bool((w.get("open_access") or {}).get("is_oa")), sources=["openalex"])


def epmc_to_cand(r: dict) -> Candidate:
    pmcid = r.get("pmcid")
    is_oa = r.get("isOpenAccess") == "Y"
    authors = [a.strip().rstrip(".") for a in (r.get("authorString") or "").split(", ") if a.strip()]
    year = int(r["pubYear"]) if str(r.get("pubYear", "")).isdigit() else None
    return Candidate(
        title=(r.get("title") or "").strip().rstrip("."), authors=authors, year=year,
        doi=(r.get("doi") or "").lower() or None,
        url=f"https://europepmc.org/article/{r.get('source')}/{r.get('id')}" if r.get("id") else None,
        journal=r.get("journalTitle"), abstract=strip_tags(r.get("abstractText")), pmcid=pmcid,
        xml_url=f"{EPMC}/{pmcid}/fullTextXML" if pmcid and is_oa else None,
        is_oa=is_oa, sources=["europepmc"])


# ---------------- source queries ----------------

def crossref_search(ref: dict) -> list[Candidate]:
    q = ref["title"]
    if ref.get("authors"):
        q += " " + surname(ref["authors"][0])
    st, data = fetch_json(f"{CROSSREF}/works", {"query.bibliographic": q, "rows": 5})
    items = ((data or {}).get("message") or {}).get("items", []) if st == 200 else []
    return [crossref_to_cand(i) for i in items]


def epmc_search(query: str) -> list[Candidate]:
    st, data = fetch_json(f"{EPMC}/search", {"query": query, "format": "json",
                                              "resultType": "core", "pageSize": 5})
    res = ((data or {}).get("resultList") or {}).get("result", []) if st == 200 else []
    return [epmc_to_cand(r) for r in res]


def openalex_search(title: str) -> list[Candidate]:
    st, data = fetch_json(f"{OPENALEX}/works", {"search": title, "per_page": 5})
    return [openalex_to_cand(w) for w in (data or {}).get("results", [])] if st == 200 else []


# ---------------- matching ----------------

def norm(s: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())).strip()


def title_sim(a: str | None, b: str | None) -> float:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    return max(fuzz.ratio(na, nb), fuzz.token_sort_ratio(na, nb)) / 100


def _clean_name(name: str) -> str:
    # drop accents / replacement characters so encoded PDF text still matches
    return re.sub(r"[^a-z]", "", name.lower())


def _last(name: str) -> str:
    t = name.replace(",", " ").split()
    return _clean_name(t[-1]) if t else ""


def author_ok(ref: dict, c: Candidate) -> bool | None:
    if not ref.get("authors") or not c.authors:
        return None
    rs = _clean_name(surname(ref["authors"][0]).split()[-1])
    if not rs:
        return None
    for author in c.authors:
        last = _last(author)
        if not last:
            continue
        if rs == last or fuzz.ratio(rs, last) >= 85 or last.startswith(rs[:4]) or rs.startswith(last[:4]):
            return True
    return False


def score(ref: dict, c: Candidate) -> float:
    ts = title_sim(ref.get("title"), c.title)
    au = author_ok(ref, c)
    yr = 0.0
    if ref.get("year") and c.year:
        d = abs(ref["year"] - c.year)
        yr = 1.0 if d == 0 else 0.5 if d == 1 else 0.0
    return 0.7 * ts + 0.2 * (1.0 if au else 0.0) + 0.1 * yr


def merge(cands: list[Candidate]) -> list[Candidate]:
    out = []
    for c in cands:
        hit = None
        for o in out:
            same_doi = c.doi and o.doi and c.doi == o.doi
            no_doi_same = (not c.doi or not o.doi) and title_sim(c.title, o.title) >= 0.97 \
                and (not c.year or not o.year or c.year == o.year)
            if same_doi or no_doi_same:
                hit = o
                break
        if hit:
            fill(hit, c)
            hit.sources = sorted(set(hit.sources) | set(c.sources))
        else:
            out.append(c)
    return out


def fill(dst: Candidate, src: Candidate) -> None:
    for f in ("doi", "url", "journal", "abstract", "openalex_id", "pmcid", "pdf_url", "xml_url", "year"):
        if not getattr(dst, f) and getattr(src, f):
            setattr(dst, f, getattr(src, f))
    dst.is_oa = dst.is_oa or src.is_oa
    if not dst.authors and src.authors:
        dst.authors = src.authors


def _extra_flags(ref: dict, c: Candidate) -> list[str]:
    flags = []
    if author_ok(ref, c) is False:
        flags.append("author_mismatch")
    if ref.get("year") and c.year and abs(ref["year"] - c.year) > 1:
        flags.append("year_mismatch")
    return flags


def decide(ref: dict, cands: list[Candidate]) -> dict:
    flags, excluded = [], None
    ref_doi = (ref.get("doi") or "").lower()
    hit = next((c for c in cands if ref_doi and c.doi == ref_doi), None)
    if hit:
        if not ref.get("title"):
            return {"status": "matched", "confidence": 0.85, "best": hit, "ranked": [hit],
                    "flags": ["title_not_cross_checked"]}
        ts = title_sim(ref["title"], hit.title)
        if ts >= 0.6:
            if ts < 0.85:
                flags.append("title_mismatch")
            return {"status": "matched", "confidence": round(min(1.0, 0.7 + 0.3 * ts), 2), "best": hit,
                    "ranked": [hit], "flags": flags + _extra_flags(ref, hit)}
        flags.append("doi_mismatch")  # DOI resolves to a different paper
        excluded = hit
    pool = sorted(((score(ref, c), c) for c in cands if c is not excluded), key=lambda x: -x[0])
    ranked = [c for _, c in pool[:3]]
    if not pool or not ref.get("title"):
        return {"status": "not_found", "confidence": 0.0, "best": None, "ranked": ranked, "flags": flags}
    best_s, best = pool[0]
    ts = title_sim(ref["title"], best.title)
    rival = len(pool) > 1 and pool[1][0] >= best_s - 0.05 and title_sim(ref["title"], pool[1][1].title) >= 0.85
    if ts >= 0.92 and best_s >= 0.75 and not rival:
        return {"status": "matched", "confidence": round(best_s, 2), "best": best, "ranked": ranked,
                "flags": flags + _extra_flags(ref, best)}
    if best_s >= 0.55:
        return {"status": "ambiguous", "confidence": round(best_s, 2), "best": None, "ranked": ranked,
                "flags": flags}
    return {"status": "not_found", "confidence": round(best_s, 2), "best": None, "ranked": ranked, "flags": flags}


def discover(ref: dict) -> dict:
    # priority: DOI -> title (+author/year via Crossref query) -> OpenAlex search only as last resort
    cands, extra = [], []
    doi = (ref.get("doi") or "").lower() or None
    title = ref.get("title")
    if doi:
        st, data = fetch_json(f"{CROSSREF}/works/{quote(doi, safe='/')}")
        if st == 200 and data:
            cands.append(crossref_to_cand(data["message"]))
        elif st == 404:
            extra.append("doi_not_found")
        cands += epmc_search(f'DOI:"{doi}"')
    res = decide(ref, merge(cands))
    if res["status"] != "matched" and title:
        cands += crossref_search(ref)
        cands += epmc_search('TITLE:"' + title.replace('"', " ") + '"')
        res = decide(ref, merge(cands))
        if res["status"] == "not_found":
            cands += openalex_search(title)
            res = decide(ref, merge(cands))
    best = res["best"]
    if res["status"] == "matched" and best and best.doi:  # DOI lookups on OpenAlex are free
        st, data = fetch_json(f"{OPENALEX}/works/doi:{best.doi}")
        if st == 200 and data:
            fill(best, openalex_to_cand(data))
            best.sources = sorted(set(best.sources) | {"openalex"})
    flags = list(dict.fromkeys(extra + res["flags"]))
    return {"status": res["status"], "confidence": res["confidence"],
            "best": asdict(best) if best else None,
            "candidates": [asdict(c) for c in res["ranked"]], "flags": flags}
