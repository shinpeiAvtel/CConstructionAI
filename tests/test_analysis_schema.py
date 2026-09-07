from datetime import date, datetime

from backend.schemas.analysis_schema import (
    AnalysisMetadata,
    DocumentAnalysisResult,
    DocumentSummary,
    LaborAnalysisResult,
    PriceRecommendation,
    QuoteItemAnalysis,
    VerificationSummary,
    WorkTypePriceStatistics,
)


def test_document_summary_generation():
    summary = DocumentSummary(
        document_id=101,
        source_filename="vendor_quote_001.pdf",
        source_type="VENDOR_QUOTE",
        vendor_name="Acme Security",
        project_code="PRJ-1001",
        quote_number="Q-2024-001",
        quote_date="2024-06-01",
        currency="JPY",
        subtotal=120000.0,
        tax=12000.0,
        total=132000.0,
        uploaded_at=datetime(2024, 6, 2, 9, 30, 0),
        verification_status="VERIFIED",
    )

    assert summary.document_id == 101
    assert summary.source_type == "VENDOR_QUOTE"
    assert summary.verification_status == "VERIFIED"


def test_quote_item_analysis_generation_keeps_raw_description():
    item = QuoteItemAnalysis(
        quote_item_id=7,
        line_number=2,
        raw_description="カードリーダー取付 一式",
        normalized_description="Card Reader Installation",
        work_type_code="ACS-CARD-READER-INSTALL",
        work_type_name="Card Reader Installation",
        quantity=2,
        unit="SET",
        source_unit_price=18000.0,
        calculated_unit_price=17500.0,
        normalized_unit_price=18000.0,
        source_amount=36000.0,
        calculated_amount=35000.0,
        mapping_confidence=0.91,
        verification_status="VERIFIED",
    )

    assert item.raw_description == "カードリーダー取付 一式"
    assert item.normalized_description == "Card Reader Installation"
    assert item.verification_status == "VERIFIED"


def test_nullable_fields_are_allowed_and_zero_is_distinct():
    item = QuoteItemAnalysis(
        quote_item_id=8,
        line_number=3,
        raw_description="Access Controller Mount",
        manufacturer=None,
        model_number=None,
        quantity=0,
        unit="SET",
        source_unit_price=0,
        source_amount=0,
        verification_status="NEEDS_REVIEW",
    )

    assert item.manufacturer is None
    assert item.model_number is None
    assert item.quantity == 0
    assert item.source_unit_price == 0
    assert item.source_amount == 0


def test_price_recommendation_default_human_review_required():
    recommendation = PriceRecommendation(
        work_type_code="ACS-CARD-READER-INSTALL",
        unit="SET",
        recommended_unit_price=18000.0,
        confidence="HIGH",
        confidence_score=0.89,
        reason="recent median is consistent",
        sample_count=52,
    )

    assert recommendation.human_review_required is True
    assert recommendation.confidence == "HIGH"


def test_labor_analysis_result_keeps_quoted_and_actual_separate():
    labor = LaborAnalysisResult(
        work_type_code="ACS-CARD-READER-INSTALL",
        labor_code="LAB-ACS-001",
        unit="SET",
        current_standard_labor=0.064,
        quoted_labor_sample_count=10,
        quoted_labor_mean=0.072,
        quoted_labor_median=0.071,
        actual_work_sample_count=12,
        actual_work_mean=0.081,
        actual_work_median=0.079,
        recommended_labor_candidate=0.08,
        difference_from_current_percent=12.5,
        confidence="MEDIUM",
        reason="quoted labor and actual work differ moderately",
    )

    assert labor.quoted_labor_mean == 0.072
    assert labor.actual_work_median == 0.079
    assert labor.quoted_labor_mean != labor.actual_work_mean


def test_work_type_price_statistics_fields():
    stats = WorkTypePriceStatistics(
        work_type_code="ACS-CARD-READER-INSTALL",
        work_type_name="Card Reader Installation",
        unit="SET",
        sample_count=52,
        minimum=15000.0,
        maximum=22000.0,
        mean=18420.0,
        median=17800.0,
        weighted_mean=18150.0,
        standard_deviation=2200.0,
        q1=16500.0,
        q3=19400.0,
        iqr=2900.0,
        lower_bound=12100.0,
        upper_bound=23800.0,
        outlier_count=2,
        outlier_ratio=0.038,
        recent_median=18200.0,
        analysis_period="LAST_12_MONTHS",
        verified_sample_count=48,
        unverified_sample_count=4,
        excluded_sample_count=1,
    )

    assert stats.sample_count == 52
    assert stats.verified_sample_count == 48
    assert stats.verified_sample_count < stats.sample_count


def test_document_analysis_result_nesting():
    document = DocumentSummary(
        document_id=55,
        source_filename="analysis_sample.pdf",
        source_type="CUSTOMER_QUOTE",
        vendor_name="Vendor A",
        project_code="PRJ-2001",
        quote_number="Q-2001",
        quote_date="2024-07-15",
        currency="JPY",
        total=500000.0,
        uploaded_at=datetime(2024, 7, 16, 13, 0, 0),
        verification_status="VERIFIED",
    )

    item = QuoteItemAnalysis(
        quote_item_id=11,
        line_number=1,
        raw_description="Controller 1 set",
        work_type_code="ACS-CARD-READER-INSTALL",
        verification_status="VERIFIED",
    )

    recommendation = PriceRecommendation(
        work_type_code="ACS-CARD-READER-INSTALL",
        unit="SET",
        recommended_unit_price=18000.0,
        confidence="HIGH",
        sample_count=10,
    )

    labor = LaborAnalysisResult(
        work_type_code="ACS-CARD-READER-INSTALL",
        labor_code="LAB-ACS-001",
        unit="SET",
        current_standard_labor=0.064,
        quoted_labor_sample_count=4,
        actual_work_sample_count=5,
        confidence="MEDIUM",
    )

    profile = VerificationSummary(
        total_items=1,
        verified_items=1,
        needs_review_items=0,
        unmapped_items=0,
        rejected_items=0,
        average_mapping_confidence=0.9,
        analysis_eligible_items=1,
        excluded_items=0,
    )

    metadata = AnalysisMetadata(
        analysis_version="analysis-v1",
        analyzed_at=datetime(2024, 7, 16, 14, 0, 0),
        document_id=55,
        date_from=date(2024, 1, 1),
        date_to=date(2024, 12, 31),
        verification_filter="VERIFIED",
        source_type_filter="CUSTOMER_QUOTE",
        outlier_method="IQR_1_5",
    )

    result = DocumentAnalysisResult(
        document=document,
        items=[item],
        work_type_analysis=[],
        price_recommendations=[recommendation],
        labor_analysis=[labor],
        verification_summary=profile,
        metadata=metadata,
    )

    assert result.document.document_id == 55
    assert result.items[0].raw_description == "Controller 1 set"
    assert result.price_recommendations[0].work_type_code == "ACS-CARD-READER-INSTALL"
    assert result.verification_summary.verified_items == 1


def test_serialization():
    summary = DocumentSummary(
        document_id=123,
        source_filename="sample.pdf",
        source_type="INTERNAL_ESTIMATE",
        verification_status="VERIFIED",
    )

    payload = summary.model_dump()

    assert payload["document_id"] == 123
    assert payload["source_filename"] == "sample.pdf"
    assert payload["verification_status"] == "VERIFIED"
    assert "source_type" in payload
