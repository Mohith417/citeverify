import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.IGNORECASE)
YEAR_RE = re.compile(r"\b((?:19|20)\d{2})[a-z]?\b")
NUM_START = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)[.)])\s+")
AY_START = re.compile(r"^(?:[A-Z][A-Za-z'’\-]+,\s+(?:[A-Z]\.|[A-Z][a-z]+)|[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\s[A-Z]{1,3}[,.])")
DASH = "\u2013\u2014\u2212-"
MONTHS = {"january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december", "fig", "figure", "table"}


@dataclass
class ParsedRef:
    label: str
    text: str
    title: str | None = None
    authors: list = field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    flags: list = field(default_factory=list)


@dataclass
class Citation:
    marker: str
    kind: str  # numeric | author_year
    start: int
    end: int
    numbers: list = field(default_factory=list)
    author: str = ""
    year: str = ""


@dataclass
class Mapping:
    ref_index: int | None
    status: str  # matched | ambiguous | unmatched


# ---------------- reference list ----------------

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def split_reference_entries(text: str) -> list[tuple[str, str]]:
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    if sum(1 for l in lines if NUM_START.match(l)) >= 2:
        entries, cur = [], None
        for l in lines:
            m = NUM_START.match(l)
            if m:
                if cur:
                    entries.append(cur)
                cur = [m.group(1) or m.group(2), l[m.end():].strip()]
            elif cur:
                cur[1] += " " + l.strip()
        if cur:
            entries.append(cur)
        return [(a, _clean(b)) for a, b in entries]
    entries, cur = [], None
    for l in lines:
        prev_done = cur is not None and YEAR_RE.search(cur) and cur.rstrip()[-1] in ".)0123456789"
        if AY_START.match(l.strip()) and (cur is None or prev_done):
            if cur:
                entries.append(cur)
            cur = l.strip()
        elif cur is not None:
            cur += " " + l.strip()
    if cur:
        entries.append(cur)
    return [("", _clean(e)) for e in entries]


def surname(author: str) -> str:
    a = author.strip().rstrip(".")
    if "," in a:
        return a.split(",")[0].strip().lower()
    toks = a.split()
    if len(toks) > 1 and toks[-1].isupper() and len(toks[-1]) <= 3:
        toks = toks[:-1]
    return " ".join(toks).lower()


def _split_authors_apa(s: str) -> list[str]:
    parts = re.split(r"(?<=\.),\s*(?:&\s*)?|\s*&\s*|;\s*", s)
    return [p.strip().rstrip(",") for p in parts if p.strip() and "et al" not in p.lower()]


def parse_entry(label: str, text: str) -> ParsedRef:
    p = ParsedRef(label=label, text=text)
    m = DOI_RE.search(text)
    if m:
        p.doi = m.group(0).rstrip(".,;)").lower()
    apa = re.match(r"^(.*?)\(\s*((?:19|20)\d{2})[a-z]?\s*\)\.?\s*(.+)$", text)
    if apa and len(apa.group(1)) < 300:
        auth_s, year, rest = apa.groups()
        p.authors = _split_authors_apa(auth_s)
        p.year = int(year)
        t = re.match(r"(.+?)[.?](?:\s|$)", rest)
        p.title = _clean(t.group(1)) if t else None
    else:
        segs = re.split(r"\.\s+", text)
        if len(segs) > 1:
            p.authors = [a.strip() for a in segs[0].split(",") if a.strip() and "et al" not in a.lower()]
            p.title = _clean(segs[1]) or None
            ym = YEAR_RE.search(" ".join(segs[2:]))
        else:
            ym = YEAR_RE.search(text)
        if ym is None:
            ym = YEAR_RE.search(text)
        p.year = int(ym.group(1)) if ym else None
    if p.title is not None and len(p.title) < 8:
        p.title = None
    if not p.label and p.authors and p.year:
        p.label = f"{surname(p.authors[0]).title()} {p.year}"
    if not p.title or not p.year or not p.authors:
        p.flags.append("incomplete_reference")
    return p


def parse_references(entries: list[tuple[str, str]]) -> list[ParsedRef]:
    refs = [parse_entry(l, t) for l, t in entries]
    for j, b in enumerate(refs):
        for a in refs[:j]:
            same_doi = a.doi and a.doi == b.doi
            same_title = (a.title and b.title and
                          fuzz.token_sort_ratio(a.title.lower(), b.title.lower()) >= 95)
            if same_doi or same_title:
                b.flags.append("duplicate_reference")
                break
    return refs


# ---------------- in-text citations ----------------

NUM_CIT = re.compile(r"\[(\s*\d+\s*(?:[,\u2013\u2014\u2212-]\s*\d+\s*)*)\]")
PAREN = re.compile(r"\(([^()]*?(?:19|20)\d{2}[a-z]?[^()]*)\)")
NAME = r"[A-Z][A-Za-z'’\-]+"
ITEM = re.compile(
    r"(?:(?:e\.g\.,?|see|cf\.)\s+)?(" + NAME + r")(?:\s+et al\.?|\s+(?:and|&)\s+" + NAME +
    r")?,?\s+((?:19|20)\d{2}[a-z]?)")
NARR = re.compile(
    r"(" + NAME + r")(?:\s+et al\.?|\s+(?:and|&)\s+" + NAME + r")?\s+\(((?:19|20)\d{2}[a-z]?)\)")


def expand_numeric(s: str) -> list[int]:
    nums = []
    for part in re.split(r"\s*,\s*", s.strip()):
        m = re.match(r"^(\d+)\s*[\u2013\u2014\u2212-]\s*(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            nums.extend(range(a, b + 1) if a <= b and b - a <= 50 else [a, b])
        elif part.isdigit():
            nums.append(int(part))
    return nums


def find_citations(text: str) -> list[Citation]:
    out = []
    for m in NUM_CIT.finditer(text):
        nums = expand_numeric(m.group(1))
        if nums:
            out.append(Citation(m.group(0), "numeric", m.start(), m.end(), numbers=nums))
    for m in PAREN.finditer(text):
        for item in m.group(1).split(";"):
            im = ITEM.search(item.strip())
            if im and im.group(1).lower() not in MONTHS:
                out.append(Citation(m.group(0), "author_year", m.start(), m.end(),
                                    author=im.group(1), year=im.group(2)))
    for m in NARR.finditer(text):
        if m.group(1).lower() not in MONTHS:
            out.append(Citation(m.group(0), "author_year", m.start(), m.end(),
                                author=m.group(1), year=m.group(2)))
    return sorted(out, key=lambda c: c.start)


def map_citation(c: Citation, refs: list[ParsedRef]) -> list[Mapping]:
    if c.kind == "numeric":
        res = []
        for n in c.numbers:
            idx = [i for i, r in enumerate(refs) if r.label == str(n)]
            res.append(Mapping(idx[0], "matched") if len(idx) == 1 else Mapping(None, "unmatched"))
        return res
    cites = c.author.lower()
    year = int(c.year[:4])
    cands = []
    for i, r in enumerate(refs):
        if r.year != year or not r.authors:
            continue
        s = surname(r.authors[0])
        if s == cites or s.endswith(" " + cites):
            cands.append(i)
    if len(cands) == 1:
        return [Mapping(cands[0], "matched")]
    if len(cands) > 1:
        return [Mapping(i, "ambiguous") for i in cands]
    return [Mapping(None, "unmatched")]
