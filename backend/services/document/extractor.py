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
        """Extract text from file."""
        name = (filename or "").lower()
        if name.endswith(".pdf"):
            import pdfplumber
            pages = []
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    pages.append(page.extract_text() or "")
            return "\n".join(pages)
        if name.endswith(".docx"):
            import docx
            doc = docx.Document(file)
            return "\n".join(p.text for p in doc.paragraphs)
        # .txt or any other format
        return file.read().decode("utf-8", errors="replace")
