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


def find_reference_section(pages):
    # last matching heading in the document -> (page_number, start, end) or None
    for page_no, text in reversed(pages):
        matches = list(REF_HEADING.finditer(text))
        if matches:
            m = matches[-1]
            return page_no, m.start(), m.end()
    return None


def split_body_and_references(pages):
    # returns (body_pages, reference_text). reference_text is "" if no heading found
    loc = find_reference_section(pages)
    if loc is None:
        return pages, ""
    page_no, start, end = loc
    body = [(n, t) for n, t in pages if n < page_no]
    body.append((page_no, dict(pages)[page_no][:start]))
    ref_parts = [dict(pages)[page_no][end:]] + [t for n, t in pages if n > page_no]
    return body, "\n".join(ref_parts).strip()
