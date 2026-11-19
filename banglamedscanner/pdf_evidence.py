"""Conservative page proof against official open-access PMC Cloud PDFs.

The source excerpt must match actual extracted PDF text at the returned viewer
page. A publisher's article pagination, XML section, or an LLM guess is never
used as a PDF page. PDF unavailable -> (None, None).
"""
from __future__ import annotations

import re

from . import claim_locator as original

WORD = re.compile(r'[a-z0-9]+', re.I)


def _tokens(s):
    s = str(s).replace('\u00ad', '').replace('-\n', '')
    return WORD.findall(s.casefold())


def _sequence_present(haystack, needle):
    n = len(needle)
    if not n or len(haystack) < n:
        return False
    for i in range(len(haystack) - n + 1):
        if haystack[i:i+n] == needle:
            return True
    return False


def verified_page_from_text(pages, excerpt):
    """Strong reproducible phrase agreement, not mere keyword overlap.

    For long abstract excerpts, PDF line breaks, hyphenation and minor
    editorial variation may prevent a full contiguous match. Require at least
    12 consecutive original words and >= 70% total token presence on ONE page.
    For short excerpts require the entire string in token order.
    """
    needle = _tokens(excerpt)
    if len(needle) < 7:
        return None
    for i, page_text in enumerate(pages[:original.MAX_PDF_PAGE_SCAN]):
        page = _tokens(page_text)
        if not page:
            continue
        if _sequence_present(page, needle):
            return i + 1
        if len(needle) < 16:
            continue
        overlap = len(set(needle) & set(page)) / max(1, len(set(needle)))
        if overlap < 0.70:
            continue
        # A specific consecutive span is stronger than a bag-of-words match.
        if any(_sequence_present(page, needle[j:j+12])
               for j in range(0, len(needle)-11)):
            return i + 1
    return None


def locate_verified_pdf_page(pmcid, excerpt, *, transport=None):
    """Only return 1-indexed viewer page backed by an actual PDF text match."""
    if not pmcid or len(_tokens(excerpt)) < 7:
        return None, None
    url = original._s3_pdf_url(pmcid, transport=transport)
    if not url:
        return None, None
    try:
        pdf = original._url_bytes(url, original.MAX_PDF, transport=transport)
        pages = original._pdf_text_pages(pdf)
        return verified_page_from_text(pages, excerpt), url
    except Exception:
        return None, None
