import pandas as pd
import pytest
from src.extractors.spreadsheet_extractor import SpreadsheetExtractor


def test_spreadsheet_extractor_invalid_input():
    """Verify SpreadsheetExtractor returns None for non-DataFrame or empty inputs."""
    extractor = SpreadsheetExtractor()
    assert extractor.extract(None) is None
    assert extractor.extract(pd.DataFrame()) is None


def test_spreadsheet_extractor_success():
    """Test full extraction from a pandas DataFrame with header offsets and numeric formatting."""
    raw_data = [
        ["PO NUMBER: PO-9900", None, None, None],
        ["CUSTOMER: Delta Logistics", None, None, None],
        [None, None, None, None],  # Garbage row
        ["Product Details", "Quantity", "Price Each", "Line Total"],  # Table header
        ["Floor Polish 5L", "3", "25.00 €", "75.00 €"],
        ["Microfiber Cloths", "10", "2,50", "25,00"],  # EU comma formatting
        ["Total", None, None, "100.00 €"]  # Footer row
    ]
    df = pd.DataFrame(raw_data)
    
    extractor = SpreadsheetExtractor()
    result = extractor.extract(df)
    
    assert result is not None
    assert result.document_number == "PO-9900"
    assert result.customer_raw == "Delta Logistics"
    assert len(result.items) == 2
    assert result.items[0].raw_description == "Floor Polish 5L"
    assert result.items[0].quantity == 3.0
    assert result.items[0].unit_price == 25.00
    assert result.items[1].quantity == 10.0
    assert result.items[1].unit_price == 2.50


def test_spreadsheet_extractor_autocalculate_total():
    """Test total_price calculation when total column is 0.0 or missing."""
    data = [
        ["Description", "Qty", "Unit Price", "Total"],
        ["Hand Sanitizer", "4", "5.00", "0.00"]
    ]
    df = pd.DataFrame(data[1:], columns=data[0])
    
    extractor = SpreadsheetExtractor()
    result = extractor.extract(df)
    
    assert result is not None
    assert len(result.items) == 1
    assert result.items[0].total_price == 20.00  # 4 * 5.00


def test_spreadsheet_extractor_numeric_cleaning():
    """Test _clean_numeric_value internal logic."""
    extractor = SpreadsheetExtractor()
    
    assert extractor._clean_numeric_value(100) == 100.0
    assert extractor._clean_numeric_value("1,234.56") == 1234.56
    assert extractor._clean_numeric_value("1.234,56") == 1234.56
    assert extractor._clean_numeric_value("$50.00") == 50.0
    assert extractor._clean_numeric_value(None) == 0.0