from unittest.mock import MagicMock, patch

from src.extractors.llm_extractor import LLMExtractor
from src.schemas import ExtractedItem, ProcessingResult


def test_extract_empty_text() -> None:
    """Tests that empty or whitespace text returns a default ProcessingResult without calling the LLM."""
    extractor = LLMExtractor()
    result = extractor.extract("   ")

    assert result.customer_raw == "UNKNOWN"
    assert result.needs_review is True
    assert "Empty document text provided" in result.review_reasons
    assert result.items == []


@patch("src.extractors.llm_extractor.ChatOllama")
def test_extract_success_mocked(mock_chat_ollama: MagicMock) -> None:
    """Tests successful data extraction flow with a mocked local LLM chain (zero network requests)."""
    expected_result = ProcessingResult(
        document_number="PO-2026-8891",
        customer_raw="ClearLine Hygiene GmbH",
        items=[
            ExtractedItem(
                raw_description="Heavy-duty cleaner 10l",
                quantity=2.0,
                unit_price=45.0,
                total_price=90.0,
            )
        ],
        needs_review=False,
    )

    # Initialize extractor (uses ChatOllama locally)
    extractor = LLMExtractor()

    # Mock the LangChain execution chain completely to prevent actual model invocation
    extractor.chain = MagicMock()
    extractor.chain.invoke.return_value = expected_result

    sample_text = "PURCHASE ORDER: PO-2026-8891\nCustomer: ClearLine Hygiene GmbH"
    result = extractor.extract(sample_text)

    # Assertions
    assert result == expected_result
    assert result.document_number == "PO-2026-8891"
    assert len(result.items) == 1
    assert result.items[0].total_price == 90.0
    extractor.chain.invoke.assert_called_once_with({"document_text": sample_text})