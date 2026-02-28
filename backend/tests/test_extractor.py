"""
Unit tests for services/document/extractor.py.
pdfplumber and python-docx are mocked so no real files are needed.
"""
import io
from unittest.mock import MagicMock, patch

import pytest

from services.document.extractor import DocumentExtractor


@pytest.fixture
def extractor():
    return DocumentExtractor()


class TestDocumentExtractor:
    def test_pdf_extraction(self, extractor):
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page one text"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page two text"

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page1, mock_page2]

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = extractor.extract(io.BytesIO(b"fake pdf"), "document.pdf")

        assert "Page one text" in result
        assert "Page two text" in result

    def test_pdf_handles_none_page_text(self, extractor):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = extractor.extract(io.BytesIO(b"fake pdf"), "report.pdf")

        assert result == ""

    def test_docx_extraction(self, extractor):
        mock_para1 = MagicMock()
        mock_para1.text = "First paragraph"
        mock_para2 = MagicMock()
        mock_para2.text = "Second paragraph"

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2]

        with patch("docx.Document", return_value=mock_doc):
            result = extractor.extract(io.BytesIO(b"fake docx"), "contract.docx")

        assert "First paragraph" in result
        assert "Second paragraph" in result

    def test_txt_fallback(self, extractor):
        content = b"Plain text content here."
        result = extractor.extract(io.BytesIO(content), "notes.txt")
        assert result == "Plain text content here."

    def test_unknown_extension_fallback(self, extractor):
        content = b"Some raw bytes"
        result = extractor.extract(io.BytesIO(content), "file.csv")
        assert result == "Some raw bytes"

    def test_txt_with_non_utf8_bytes(self, extractor):
        content = b"Hello \xff world"
        result = extractor.extract(io.BytesIO(content), "data.txt")
        assert "Hello" in result
        assert "world" in result
