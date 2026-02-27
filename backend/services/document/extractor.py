"""
Document extractor — PDF, DOCX, and plain text → raw_text string.
Stub for Day 1; fully implemented in Day 2.
"""
from typing import IO


class DocumentExtractor:
    """
    Normalises all supported document formats to a single raw text string.
    Supported formats:
      - PDF  (via pdfplumber)
      - DOCX (via python-docx)
      - TXT  (passthrough)
    """

    def extract(self, file: IO[bytes], filename: str) -> str:
        """Extract text from file. Implemented Day 2."""
        raise NotImplementedError
