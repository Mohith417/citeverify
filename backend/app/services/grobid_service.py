"""GROBID service wrapper for scientific document structure extraction.

Calls a locally running GROBID instance (Docker) to extract TEI XML,
bibliographic references, and citation structures. Falls back gracefully
when GROBID is unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class GrobidService:
    """Client for a local GROBID service."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or settings.grobid_url or "http://localhost:8070").rstrip("/")
        self._client: Optional[httpx.Client] = None

    def _client_instance(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30)
        return self._client

    def is_available(self) -> bool:
        try:
            r = self._client_instance().get(f"{self.base_url}/api/isalive", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def process_fulltext(self, pdf_bytes: bytes) -> Optional[str]:
        """Send a PDF to GROBID /processFulltextDocument and return TEI XML."""
        if not self.is_available():
            return None
        try:
            files = {"input": ("document.pdf", pdf_bytes, "application/pdf")}
            r = self._client_instance().post(f"{self.base_url}/api/processFulltextDocument", files=files)
            if r.status_code == 200:
                return r.text
        except Exception as exc:  # pragma: no cover
            logger.warning("GROBID fulltext processing failed: %s", exc)
        return None

    def process_references(self, pdf_bytes: bytes) -> Optional[str]:
        """Send a PDF to GROBID /processReferences and return TEI XML."""
        if not self.is_available():
            return None
        try:
            files = {"input": ("document.pdf", pdf_bytes, "application/pdf")}
            r = self._client_instance().post(f"{self.base_url}/api/processReferences", files=files)
            if r.status_code == 200:
                return r.text
        except Exception as exc:  # pragma: no cover
            logger.warning("GROBID references processing failed: %s", exc)
        return None

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None


# Module-level singleton
grobid_service = GrobidService()