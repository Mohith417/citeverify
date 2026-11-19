import re

from pypdf import PdfReader

MAX_PAGES = 100
MIN_CHARS_PER_PAGE = 100  # below this average the PDF is treated as scanned/image-only

REF_HEADING = re.compile(
    r"^[ \t]*(?:\d+\.?[ \t]*)?(references|bibliography|literature cited|works cited)[ \t]*:?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


class PDFError(Exception):
    pass


def extract_pages(path) -> list[tuple[int, str]]:
    # returns [(page_number starting at 1, text), ...]
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted and not reader.decrypt(""):
            raise PDFError("PDF is password-protected.")
        if len(reader.pages) > MAX_PAGES:
            raise PDFError(f"PDF has more than {MAX_PAGES} pages (processing limit).")
        return [(i, page.extract_text() or "") for i, page in enumerate(reader.pages, start=1)]
    except PDFError:
        raise
    except Exception as e:
        raise PDFError(f"Could not read PDF: {e}") from e


def needs_ocr(pages: list[tuple[int, str]]) -> bool:
    if not pages:
        return True
    chars = sum(len(re.sub(r"\s", "", t)) for _, t in pages)
    return chars / len(pages) < MIN_CHARS_PER_PAGE


ENTRY_HINT = re.compile(r"(?:(?:19|20)\d{2}|doi\.org|\[\d+\]|^\s*\d+[.)]\s)", re.IGNORECASE)


def _looks_like_bibliography(text: str) -> bool:
    """A heading is only the bibliography if entries actually follow it.

    Papers rarely have a second "References" heading, but appendices,
    questionnaires and prose after a false heading do not look like a list of
    publications. Requiring year-bearing or numbered lines stops the parser
    from starting at the wrong heading (which left a 60-reference paper with
    8 parsed entries, and a 77-page report pointing at page 37).
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    hints = [line for line in lines if ENTRY_HINT.search(line)]
    numbered = sum(1 for line in lines if re.match(r"^(?:\[\d+\]|\d+[.)])\s", line))
    if numbered >= 2:
        return True
    if len(hints) >= 3 and len(hints) >= 0.25 * len(lines):
        return True
    return len(lines) <= 6 and bool(hints)


def find_reference_section(pages):
    # last heading whose own page (plus the next one) really looks like a bibliography
    by_page = dict(pages)
    for page_no, text in reversed(pages):
        for m in reversed(list(REF_HEADING.finditer(text))):
            following = text[m.end():]
            if page_no + 1 in by_page:
                following += "\n" + by_page[page_no + 1]
            if _looks_like_bibliography(following):
                return page_no, m.start(), m.end()
    return None


YEAR_TOKEN = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")


def _reference_like(page_text: str) -> bool:
    """A page continues the bibliography when it still carries publication years.

    Appendices follow the bibliography and are full of prose (sample answers,
    prompts, tables); those pages would otherwise be parsed as references.
    """
    return len(YEAR_TOKEN.findall(page_text)) >= 3


def split_body_and_references(pages):
    # returns (body_pages, reference_text). reference_text is "" if no heading found
    loc = find_reference_section(pages)
    if loc is None:
        return pages, ""
    page_no, start, end = loc
    by_page = dict(pages)
    body = [(n, t) for n, t in pages if n < page_no]
    body.append((page_no, by_page[page_no][:start]))
    ref_parts = [by_page[page_no][end:]]
    for n, t in pages:
        if n <= page_no:
            continue
        if not _reference_like(t):
            break  # appendix or supplementary material starts here
        ref_parts.append(t)
    return body, "\n".join(ref_parts).strip()
