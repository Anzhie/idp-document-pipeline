import math
import pytest
from src.extractors.utils import (
    extract_document_number,
    extract_shipping,
    extract_tax,
    extract_total,
    is_footer_row,
    is_my_company,
    is_valid_line_item,
    safe_float,
)


def test_safe_float_variations():
    """Test safe_float conversions with various input formats and edge cases."""
    assert safe_float(None) == 0.0
    assert safe_float(15.5) == 15.5
    assert safe_float(math.nan) == 0.0
    assert safe_float("nan") == 0.0
    assert safe_float("1,234.56") == 1234.56
    assert safe_float("120,00") == 120.00
    assert safe_float("$45.99") == 45.99
    assert safe_float("invalid_str") == 0.0


def test_is_my_company():
    """Test self-company recognition pattern."""
    assert is_my_company("Small Book Store Inc.") is True
    assert is_my_company("ClearLine Hygiene GmbH") is False
    assert is_my_company("") is False


def test_is_valid_line_item():
    """Test line item validation logic against rules 1-3."""
    # Empty description
    assert is_valid_line_item("  ", 1.0, 10.0, 10.0) is False
    
    # Rule 1: No qty and no prices
    assert is_valid_line_item("Paper Towels", 0.0, 0.0, 0.0) is False
    
    # Rule 2: Header leak
    assert is_valid_line_item("Description", 1.0, 10.0, 10.0) is False
    assert is_valid_line_item("QTY", 1.0, 10.0, 10.0) is False
    
    # Rule 3: Address or email in description
    assert is_valid_line_item("contact@supplier.com", 1.0, 10.0, 10.0) is False
    assert is_valid_line_item("12345 Main Street", 1.0, 10.0, 10.0) is False
    
    # Valid item
    assert is_valid_line_item("Heavy Cleaner 10L", 2.0, 45.0, 90.0) is True


def test_is_footer_row():
    """Test footer/totals detection."""
    assert is_footer_row("Subtotal:") is True
    assert is_footer_row("GRAND TOTAL") is True
    assert is_footer_row("VAT 19%") is True
    assert is_footer_row("Regular Line Item Description") is False


def test_extract_header_fields():
    """Test regex extraction for document metadata."""
    sample_text = """
    INVOICE NUMBER: INV-2026-99
    CUSTOMER: Acme Corp
    Subtotal: $100.00
    TAX: $19.00
    SHIPPING: $5.00
    TOTAL AMOUNT: $124.00
    """
    assert extract_document_number(sample_text) == "INV-2026-99"
    assert extract_tax(sample_text) == 19.00
    assert extract_shipping(sample_text) == 5.00
    assert extract_total(sample_text) == 124.00