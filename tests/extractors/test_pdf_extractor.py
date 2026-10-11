from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.extractors.pdf_extractor import PDFExtractor


def test_pdf_extractor_invalid_input():
    """Verify PDFExtractor handles invalid path or non-pdf extensions."""
    extractor = PDFExtractor()
    assert extractor.extract("non_existent.pdf") is None
    assert extractor.extract("document.xlsx") is None


@patch("src.extractors.pdf_extractor.Path.exists")
@patch("src.extractors.pdf_extractor.pdfplumber.open")
def test_pdf_extractor_native_table_parsing(mock_pdf_open, mock_exists):
    """Test PDF table extraction with header mapping and row parsing."""
    mock_exists.return_value = True
    
    # Mock page and pdfplumber with standard headers matching COLUMN_ALIASES
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "INVOICE # INV-555\nCUSTOMER: Global Corp"
    mock_page.extract_tables.return_value = [
        [
            ["Description", "Qty", "Unit Price", "Total"],  # Standard headers for fuzzy matching
            ["Industrial Soap", "5", "10.00", "50.00"],
            ["Total", "", "", "50.00"]  # Footer row candidate
        ]
    ]
    
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf
    
    extractor = PDFExtractor()
    result = extractor.extract("sample.pdf")
    
    assert result is not None
    assert result.document_number == "INV-555"
    assert result.customer_raw == "Global Corp"
    assert len(result.items) == 1
    assert result.items[0].raw_description == "Industrial Soap"
    assert result.items[0].quantity == 5.0


@patch("src.extractors.pdf_extractor.Path.exists")
@patch("src.extractors.pdf_extractor.pdfplumber.open")
def test_pdf_extractor_text_line_fallback(mock_pdf_open, mock_exists):
    """Test text line fallback parsing for unstructured or pipe-delimited PDFs."""
    mock_exists.return_value = True
    
    sample_text = """
    PURCHASE ORDER: PO-777
    Vendor Name
    Item Description | Qty | Price | Total
    Disinfectant Wipes | 10 | 5.0 | 50.0
    Subtotal 50.0
    """
    mock_page = MagicMock()
    mock_page.extract_text.return_value = sample_text
    mock_page.extract_tables.return_value = []  # No native tables
    
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf
    
    extractor = PDFExtractor()
    result = extractor.extract("unstructured.pdf")
    
    assert result is not None
    assert result.document_number == "PO-777"
    assert len(result.items) == 1
    assert result.items[0].raw_description == "Disinfectant Wipes"


@patch("src.extractors.pdf_extractor.Path.exists")
@patch("src.extractors.pdf_extractor.pdfplumber.open")
def test_pdf_extractor_no_items_found(mock_pdf_open, mock_exists):
    """Verify PDFExtractor returns None if no line items could be parsed."""
    mock_exists.return_value = True
    
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Just some text without items"
    mock_page.extract_tables.return_value = []
    
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf
    
    extractor = PDFExtractor()
    assert extractor.extract("empty.pdf") is None