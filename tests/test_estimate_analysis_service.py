from datetime import datetime

from backend.models import EstimateDocument, QuoteItem, WorkTypeMaster
from backend.services.estimate_analysis_service import (
    build_document_analysis,
    build_document_summary,
    build_quote_item_analysis,
    build_verification_summary,
)


def test_build_document_summary_from_existing_document():
    document = EstimateDocument(
        id=1,
        source_filename="vendor_quote.pdf",
        file_hash="abc",
        source_type="VENDOR_QUOTE",
        vendor_name="Vendor A",
        project_code="PRJ-1",
        quote_number="Q-001",
        quote_date="2024-01-01",
        verification_status="VERIFIED",
        upload_timestamp=datetime(2024, 2, 1, 10, 0, 0),
    )

    summary = build_document_summary(document)
    assert summary.document_id == 1
    assert summary.source_filename == "vendor_quote.pdf"
    assert summary.verification_status == "VERIFIED"


def test_build_quote_item_analysis_keeps_raw_description():
    item = QuoteItem(
        id=7,
        document_id=1,
        line_number=2,
        raw_description="カードリーダー取付 一式",
        normalized_description="Card Reader Installation",
        work_type_code="ACS-CARD-READER-INSTALL",
        quantity=2,
        unit="SET",
        amount=36000.0,
        source_unit_price=18000.0,
        calculated_unit_price=17500.0,
        normalized_unit_price=18000.0,
        mapping_confidence=0.91,
        verification_status="VERIFIED",
    )

    result = build_quote_item_analysis(item)
    assert result.raw_description == "カードリーダー取付 一式"
    assert result.normalized_description == "Card Reader Installation"
    assert result.verification_status == "VERIFIED"


def test_verification_summary_uses_verified_only_for_eligible_count():
    items = [
        QuoteItem(id=1, document_id=1, line_number=1, raw_description="A", work_type_code="W1", mapping_confidence=0.9, verification_status="VERIFIED"),
        QuoteItem(id=2, document_id=1, line_number=2, raw_description="B", work_type_code="W1", mapping_confidence=0.7, verification_status="NEEDS_REVIEW"),
        QuoteItem(id=3, document_id=1, line_number=3, raw_description="C", mapping_confidence=None, verification_status="REJECTED"),
    ]

    summary = build_verification_summary(items)
    assert summary.total_items == 3
    assert summary.verified_items == 1
    assert summary.needs_review_items == 1
    assert summary.rejected_items == 1
    assert summary.average_mapping_confidence == 0.8
    assert summary.analysis_eligible_items == 1
    assert summary.excluded_items == 2


def test_work_type_enrichment_uses_master_when_available():
    work_type = WorkTypeMaster(
        work_type_code="ACS-CARD-READER-INSTALL",
        category="ACCESS_CONTROL",
        sub_category="CARD_READER",
        work_type_name="Card Reader Installation",
    )

    item = QuoteItem(
        id=5,
        document_id=1,
        line_number=1,
        raw_description="Reader install",
        work_type_code="ACS-CARD-READER-INSTALL",
        quantity=2,
        unit="SET",
        amount=36000,
        source_unit_price=18000,
        verification_status="VERIFIED",
    )

    result = build_quote_item_analysis(item, work_type=work_type)
    assert result.work_type_name == "Card Reader Installation"
    assert result.category == "ACCESS_CONTROL"
    assert result.sub_category == "CARD_READER"


def test_document_analysis_result_construction():
    document = EstimateDocument(
        id=10,
        source_filename="quote.pdf",
        file_hash="hash-10",
        source_type="INTERNAL_ESTIMATE",
        verification_status="VERIFIED",
        upload_timestamp=datetime(2024, 1, 1, 9, 0, 0),
    )

    item = QuoteItem(
        id=9,
        document_id=10,
        line_number=1,
        raw_description="Controller",
        work_type_code="ACS-CARD-READER-INSTALL",
        quantity=2,
        unit="SET",
        amount=25000,
        source_unit_price=12500,
        verification_status="VERIFIED",
    )

    work_type = WorkTypeMaster(
        work_type_code="ACS-CARD-READER-INSTALL",
        category="ACCESS_CONTROL",
        sub_category="CARD_READER",
        work_type_name="Card Reader Installation",
    )

    result = build_document_analysis(document, [item], [work_type])
    assert result.document.document_id == 10
    assert result.items[0].raw_description == "Controller"
    assert result.verification_summary.verified_items == 1
    assert result.metadata.analysis_version == "analysis-v1"
    assert result.metadata.outlier_method == "IQR_1.5_INCLUSIVE"
