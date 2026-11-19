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


def _num_start(line: str):
    """Numbered-entry match that never mistakes a year for a label."""
    m = NUM_START.match(line)
    if not m:
        return None
    if m.group(2) and len(m.group(2)) == 4 and 1900 <= int(m.group(2)) <= 2099:
        return None  # "2018. Title…" is a year, not reference 2018
    return m


def split_reference_entries(text: str) -> list[tuple[str, str]]:
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    numbered = sum(1 for l in lines if _num_start(l))
    if numbered >= 3 or (numbered >= 2 and len(lines) <= 12):
        entries, cur = [], None
        for l in lines:
            m = _num_start(l)
            if m:
                if cur:
                    entries.append(cur)
                cur = [m.group(1) or m.group(2), l[m.end():].strip()]
            elif cur:
                cur[1] += " " + l.strip()
        if cur:
            entries.append(cur)
        return [(a, _clean(b)) for a, b in entries]
    # Two author-year shapes show up in real bibliographies and they need
    # different splitters; take whichever recovers more entries.
    split_variants = [
        _split_author_year(lines),
        _split_year_lines(lines),
        _split_period_blocks(lines),
    ]
    return max(split_variants, key=len)


def _split_author_year(lines: list[str]) -> list[tuple[str, str]]:
    """Entries that start with a surname, e.g. "Smith, J., & Lee, K. (2019). …"."""
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


VENUE_START = re.compile(
    r"^(?:in\b|proceedings|proc\.|pages|association|arxiv|corr|journal|transactions|"
    r"ieee|acm|conference|workshop|press|vol\.|no\.|pp\.|available|retrieved|url|doi|"
    r"http|and\b|technical|advances|preprint|editor|ed\.)",
    re.IGNORECASE,
)


def _starts_author_line(line: str) -> bool:
    """"Mandar Joshi, Eunsol Choi, …" — a wrapped author list, not a venue."""
    if not line or VENUE_START.match(line):
        return False
    if not re.match(r"^[A-Z][A-Za-z'’.\-]+", line):
        return False
    return "," in line[:80] or line.count(" and ") > 0


def _split_period_blocks(lines: list[str]) -> list[tuple[str, str]]:
    """Split where a finished entry (ends with a period) is followed by a new
    author list. This is the shape ACL/EMNLP extracts produce, where the year
    sits in the middle of the entry instead of on its own line."""
    entries, cur = [], None
    for i, l in enumerate(lines):
        s = l.strip()
        prev = lines[i - 1].strip() if i else ""
        starts = cur is None or (
            prev.endswith(".") and not prev.endswith("et al.") and _starts_author_line(s)
        )
        if starts:
            if cur:
                entries.append(cur)
            cur = s
        else:
            cur += " " + s
    if cur:
        entries.append(cur)
    return [("", _clean(e)) for e in entries]


def _split_year_lines(lines: list[str]) -> list[tuple[str, str]]:
    """Entries whose year sits on its own line after the author list (ACL style)."""
    year_line = re.compile(r"^(?:19|20)\d{2}[a-z]?[.\s]")
    if sum(1 for l in lines if year_line.match(l.strip())) < 3:
        return []
    entries, cur = [], None
    for i, l in enumerate(lines):
        s = l.strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        starts_entry = bool(year_line.match(nxt)) and not year_line.match(s) \
            and not s.endswith(("-", ",")) and cur is not None and YEAR_RE.search(cur)
        if cur is None or starts_entry:
            if cur:
                entries.append(cur)
            cur = s
        else:
            cur += " " + s
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


INITIAL = re.compile(r"^[A-Z]\.?$")

# IEEE / Vancouver entries start with initials + surname, e.g.
# "X. Tang, X. Zhang, X. Gao, et al., “A novel interpretation of…,” IEEE Trans…"
IEEE_AUTHOR = re.compile(r"(?:[A-Z]\.\s*)+(?:[a-z]{2,3}\s+)?[A-Z][A-Za-z'’\-]+")
IEEE_SEP = re.compile(r"\s*(?:,\s*(?:and\s+)?|\s+and\s+|\s*&\s*)")
IEEE_ET_AL = re.compile(r"et\s+al\.?,?\s*")
# Where the title stops and the venue starts in an IEEE-style entry.
VENUE_HINT = re.compile(
    r",\s*(?:in\s|in\s+proceedings|proceedings|proc\.|ieee|acm|journal|j\.|arxiv|corr|"
    r"vol\.|pp\.|no\.|conference|workshop|press|springer|elsevier|transactions|int\.|"
    r"international|advances|lecture notes|preprint|technical report)",
    re.IGNORECASE,
)
QUOTE_CHARS = "\u201c\u201d\"\u201e\ufffd\u00ab\u00bb"


def _strip_quotes(s: str) -> str:
    return s.strip().strip(QUOTE_CHARS).strip().rstrip(".,;")


def _split_ieee(text: str):
    """Parse "Initials Surname, Initials Surname, et al., Title, Venue, 2020".

    Returns (authors, title, rest) or None when the entry is not in that shape.
    Initials are never mistaken for the end of the author list (the old bug that
    turned "X. Tang, X. Zhang…" into an author called "X").
    """
    first = IEEE_AUTHOR.match(re.sub(r"^(?:and|&)\s+", "", text))
    text = re.sub(r"^(?:and|&)\s+", "", text)
    if not first:
        return None
    authors = [first.group(0)]
    pos = first.end()
    while True:
        sep = IEEE_SEP.match(text, pos)
        if not sep:
            break
        nxt = sep.end()
        etal = IEEE_ET_AL.match(text, nxt)
        if etal:
            pos = etal.end()
            break
        nxt_author = IEEE_AUTHOR.match(text, nxt)
        if not nxt_author:
            break
        authors.append(nxt_author.group(0))
        pos = nxt_author.end()

    rest = text[pos:].lstrip(" ,.;:")
    rest = rest.lstrip(QUOTE_CHARS).strip()
    if not rest:
        return None
    # IEEE titles are quoted; when the closing quote survived, prefer it.
    closing = rest.find("\u201d")
    title = None
    if 8 <= closing <= 320:
        title = rest[:closing]
        rest = rest[closing + 1:].lstrip(" ,.;:" + QUOTE_CHARS)
    else:
        cut = VENUE_HINT.search(rest)
        candidate = rest[: cut.start()] if cut else rest
        candidate = re.split(r"\.\s+(?=[A-Z])", candidate, maxsplit=1)[0] if candidate.count(". ") else candidate
        candidate = _strip_quotes(candidate)
        if len(candidate.split()) >= 3:
            title = candidate
    title = _strip_quotes(title) if title else None
    if title and len(title.split()) < 2:
        title = None
    return [a for a in (x.strip().rstrip(".") for x in authors) if a], title, rest


def _dehyphenate(s: str) -> str:
    # PDF text often breaks words across lines: "Convolu- tional" -> "Convolutional"
    return re.sub(r"([A-Za-z])-\s+([a-z])", r"\1\2", s)


def _split_authors_rest(text: str) -> tuple[str, str]:
    """Split "Authors. Title..." without tripping over initials ("Quoc V. Le").

    A candidate split is only accepted when what follows really looks like a
    title (three or more words in its first sentence); this keeps Vancouver
    author lists such as "Smith J, Lee K." intact.
    """
    fallback: tuple[str, str] | None = None
    for m in re.finditer(r"\.\s+", text):
        head, rest = text[: m.start()], text[m.start() + 2:]
        prev = head.split()[-1] if head.split() else ""
        initial = bool(INITIAL.match(prev)) or prev.lower() in ("al.", "etal.")
        first = re.split(r"\.\s+|\.[\s]*$", rest, maxsplit=1)[0]
        if not initial and len(first.split()) >= 3:
            return head, rest
        if fallback is None:
            fallback = (head, rest)
    return fallback or ("", text)


# ACM entries put the year right after the authors: "M. Bostock, V. Ogievetsky,
# and J. Heer. 2011. D3 Data-Driven Documents. IEEE TVCG 17(12), 2301-2309."
ACM_ENTRY = re.compile(
    r"^(?P<auth>.{0,300}?)\.\s+(?P<year>(?:19|20)\d{2})[a-z]?\.\s+(?P<rest>.{8,})$",
    re.S,
)


def _split_acm(text: str):
    """Parse "Authors. Year. Title. Venue." entries, keeping the title intact."""
    m = ACM_ENTRY.match(text)
    if not m:
        return None
    auth = m.group("auth").strip().rstrip(".")
    if not auth or len(auth) > 280 or any(q in auth for q in QUOTE_CHARS):
        return None
    authors = [a.strip().rstrip(".") for a in re.split(r",\s*(?:and\s+)?|\s+and\s+", auth) if a.strip()]
    looks_like_title = len(auth.split()) >= 3 and not re.match(r"^(?:[A-Z]\.\s*)+", auth)
    if not authors or any(len(a.split()) > 5 for a in authors):
        if not looks_like_title:
            return None
        rest = auth + ". " + m.group("rest")
        authors = []
    else:
        rest = m.group("rest").strip()

    title = re.split(r"\.\s+(?=[A-Z])", rest, maxsplit=1)[0]
    title = _strip_quotes(title)
    if len(title.split()) < 3:
        return None
    return authors, title, int(m.group("year"))


def _last_year(text: str) -> int | None:
    """Page ranges contain years too (15(1):1929-1958, 2014): prefer the last one."""
    years = [int(y) for y in re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", text)]
    years = [y for y in years if 1900 <= y <= 2100]
    return years[-1] if years else None


def parse_entry(label: str, text: str) -> ParsedRef:
    p = ParsedRef(label=label, text=text)
    text = _dehyphenate(_clean(text))
    p.text = text
    m = DOI_RE.search(text)
    if m:
        p.doi = m.group(0).rstrip(".,;)").lower()
    acm = _split_acm(text)
    apa = re.match(r"^(.*?)\(\s*((?:19|20)\d{2})[a-z]?\s*\)\.?\s*(.+)$", text)
    if acm:
        p.authors, p.title, p.year = acm
    elif apa and len(apa.group(1)) < 300:
        auth_s, year, rest = apa.groups()
        p.authors = _split_authors_apa(auth_s)
        p.year = int(year)
        t = re.match(r"(.+?)[.?](?:\s|$)", rest)
        p.title = _clean(t.group(1)) if t else None
    else:
        ieee = _split_ieee(text)
        if ieee and ieee[1]:
            p.authors, p.title = ieee[0], ieee[1]
        else:
            auth_s, rest = _split_authors_rest(text)
            if ieee:
                p.authors = ieee[0]
            elif auth_s:
                p.authors = [
                    a.strip().rstrip(".")
                    for a in re.split(r",\s*|\s+and\s+", auth_s)
                    if a.strip() and "et al" not in a.lower()
                ]
            t = re.split(r"\.\s+|,\s+(?:19|20)\d{2}\b", rest, maxsplit=1)[0]
            p.title = _clean(t) or None
        p.year = p.year or _last_year(text)
    if p.title is not None and len(p.title) < 8:
        p.title = None
    if not p.label and p.authors and p.year:
        p.label = f"{surname(p.authors[0]).title()} {p.year}"
    if not p.title or not p.year:
        p.flags.append("incomplete_reference")
    elif not p.authors:
        p.flags.append("no_authors")
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
