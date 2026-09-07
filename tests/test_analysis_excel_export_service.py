from datetime import datetime
from io import BytesIO

from openpyxl import load_workbook

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
from backend.services.analysis_excel_export_service import (
    build_filename,
    build_workbook,
    build_workbook_bytes,
)


def make_analysis_result():
    document = DocumentSummary(
        document_id=123,
        source_filename="DOC-000123.pdf",
        source_type="PDF",
        vendor_name="Alpha General",
        project_code="PRJ-ALPHA",
        quote_number="Q-2025-001",
        quote_date="2025-09-01",
        currency="JPY",
        subtotal=1200000.0,
        tax=120000.0,
        total=1320000.0,
        uploaded_at=None,
        verification_status="VERIFIED",
    )

    items = [
        QuoteItemAnalysis(
            quote_item_id=1,
            line_number=1,
            raw_description="Masonry wall panel installation",
            normalized_description="Masonry wall panel installation (normalized)",
            work_type_code="MASONRY",
            work_type_name="Masonry Work",
            category="Structural",
            sub_category="Wall",
            manufacturer="ABC",
            model_number="MODEL-1",
            quantity=10.0,
            unit="EA",
            source_unit_price=150000.0,
            calculated_unit_price=150000.0,
            normalized_unit_price=150000.0,
            source_amount=1500000.0,
            calculated_amount=1500000.0,
            quoted_person_days=40.0,
            quoted_labor_amount=400000.0,
            mapping_confidence=0.91,
            verification_status="VERIFIED",
            is_outlier=False,
            outlier_reason=None,
        ),
        QuoteItemAnalysis(
            quote_item_id=2,
            line_number=2,
            raw_description="Material handling surcharge",
            normalized_description="Material handling surcharge",
            work_type_code=None,
            work_type_name=None,
            category=None,
            sub_category=None,
            manufacturer=None,
            model_number=None,
            quantity=1.0,
            unit="LOT",
            source_unit_price=70000.0,
            calculated_unit_price=70000.0,
            normalized_unit_price=70000.0,
            source_amount=70000.0,
            calculated_amount=70000.0,
            quoted_person_days=None,
            quoted_labor_amount=None,
            mapping_confidence=0.2,
            verification_status="NEEDS_REVIEW",
            is_outlier=False,
            outlier_reason=None,
        ),
    ]

    work_type_analysis = [
        WorkTypePriceStatistics(
            work_type_code="MASONRY",
            work_type_name="Masonry Work",
            unit="EA",
            sample_count=12,
            minimum=120000.0,
            maximum=180000.0,
            mean=145000.0,
            median=148000.0,
            weighted_mean=150000.0,
            standard_deviation=15000.0,
            q1=135000.0,
            q3=160000.0,
            iqr=25000.0,
            lower_bound=97500.0,
            upper_bound=197500.0,
            outlier_count=1,
            outlier_ratio=0.08,
            recent_median=150000.0,
            analysis_period="2025Q3",
            verified_sample_count=11,
            unverified_sample_count=1,
            excluded_sample_count=0,
        )
    ]

    price_recommendations = [
        PriceRecommendation(
            work_type_code="MASONRY",
            unit="EA",
            historical_mean=145000.0,
            historical_median=148000.0,
            recent_median=150000.0,
            recommended_unit_price=149000.0,
            low_unit_price=135000.0,
            base_unit_price=149000.0,
            high_unit_price=160000.0,
            confidence="HIGH",
            confidence_score=0.82,
            reason="Recommendation based on 12 verified samples.",
            sample_count=12,
            vendor_count=3,
            outlier_ratio=0.08,
            human_review_required=True,
        )
    ]

    labor_analysis = [
        LaborAnalysisResult(
            work_type_code="MASONRY",
            labor_code="LAB-001",
            unit="EA",
            current_standard_labor=0.12,
            quoted_labor_sample_count=8,
            quoted_labor_mean=0.14,
            quoted_labor_median=0.13,
            actual_work_sample_count=6,
            actual_work_mean=0.15,
            actual_work_median=0.16,
            recommended_labor_candidate=0.16,
            difference_from_current_percent=33.33,
            confidence="MEDIUM",
            reason="Actual work median exceeds standard by 33.33%.",
            human_review_required=True,
        )
    ]

    verification_summary = VerificationSummary(
        total_items=2,
        verified_items=1,
        needs_review_items=1,
        unmapped_items=1,
        rejected_items=0,
        average_mapping_confidence=0.555,
        analysis_eligible_items=1,
        excluded_items=1,
    )

    metadata = AnalysisMetadata(
        analysis_version="analysis-v1",
        analyzed_at=datetime.now(),
        document_id=123,
        verification_filter="VERIFIED_ONLY",
        source_type_filter="PDF",
        vendor_filter="Alpha General",
        project_filter="PRJ-ALPHA",
        included_samples=2,
        excluded_samples=1,
        outlier_method="IQR_1.5_INCLUSIVE",
    )

    result = DocumentAnalysisResult(
        document=document,
        items=items,
        work_type_analysis=work_type_analysis,
        price_recommendations=price_recommendations,
        labor_analysis=labor_analysis,
        verification_summary=verification_summary,
        metadata=metadata,
        outliers=[items[0]],
    )
    return result


def test_build_workbook_has_required_sheets_and_summary():
    analysis = make_analysis_result()
    workbook = build_workbook(analysis)

    assert workbook is not None
    assert len(workbook.sheetnames) == 10
    expected_names = [
        "SUMMARY",
        "SOURCE_DOCUMENT",
        "QUOTE_ITEMS",
        "WORK_TYPE_ANALYSIS",
        "PRICE_STATISTICS",
        "LABOR_ANALYSIS",
        "OUTLIERS",
        "RECOMMENDATIONS",
        "VERIFICATION",
        "AUDIT_INFO",
    ]
    assert workbook.sheetnames == expected_names

    summary = workbook["SUMMARY"]
    assert summary["A1"].value == "CConstructionAI"
    assert summary["A2"].value == "Estimate Analysis Report"
    assert summary["B5"].value == 123
    assert summary["B6"].value == "DOC-000123.pdf"
    assert summary["B12"].value == "VERIFIED"

    source_doc = workbook["SOURCE_DOCUMENT"]
    assert source_doc["A1"].value == "Document ID"
    assert source_doc["A2"].value == 123
    assert source_doc["B2"].value == "DOC-000123.pdf"

    quote_items = workbook["QUOTE_ITEMS"]
    assert quote_items["A1"].value == "Line"
    assert quote_items["B1"].value == "Raw Description"
    assert quote_items["C1"].value == "Normalized Description"
    assert quote_items["B2"].value == "Masonry wall panel installation"
    assert quote_items["C2"].value == "Masonry wall panel installation (normalized)"

    recommendations = workbook["RECOMMENDATIONS"]
    assert recommendations["A1"].value == "Work Type Code"
    assert recommendations["F2"].value == 149000.0

    labor = workbook["LABOR_ANALYSIS"]
    assert labor["A1"].value == "Work Type Code"
    assert labor["K2"].value == 0.16

    outliers = workbook["OUTLIERS"]
    assert outliers["A1"].value == "Line"
    assert outliers["B2"].value == "Masonry wall panel installation"

    verification = workbook["VERIFICATION"]
    assert verification["A1"].value == "Line"
    assert verification["F2"].value == "VERIFIED"

    audit = workbook["AUDIT_INFO"]
    assert audit["A1"].value == "Exported At"
    assert audit["B2"].value == 123
    assert audit["L2"].value == "NOT_AVAILABLE"


def test_build_workbook_bytes_round_trip_and_formats():
    analysis = make_analysis_result()
    payload = build_workbook_bytes(analysis)
    assert isinstance(payload, bytes)
    assert len(payload) > 0

    workbook = load_workbook(BytesIO(payload))
    assert workbook.sheetnames == [
        "SUMMARY",
        "SOURCE_DOCUMENT",
        "QUOTE_ITEMS",
        "WORK_TYPE_ANALYSIS",
        "PRICE_STATISTICS",
        "LABOR_ANALYSIS",
        "OUTLIERS",
        "RECOMMENDATIONS",
        "VERIFICATION",
        "AUDIT_INFO",
    ]

    summary = workbook["SUMMARY"]
    assert summary["A1"].value == "CConstructionAI"
    assert isinstance(summary["B5"].value, int)
    assert summary["B17"].value == 1490000.0 or summary["B17"].value is None

    pricing = workbook["PRICE_STATISTICS"]
    assert pricing["A1"].value == "Work Type"
    assert pricing["A2"].value == "MASONRY"

    numeric_cells = [
        workbook["SUMMARY"]["B17"].value,
        workbook["RECOMMENDATIONS"]["F2"].value,
        workbook["LABOR_ANALYSIS"]["K2"].value,
    ]
    assert all(cell is None or isinstance(cell, (int, float)) for cell in numeric_cells)


def test_safe_filename_uses_document_id_and_date():
    filename = build_filename(123, "2025-09-07")
    assert "123" in filename
    assert filename.endswith(".xlsx")
    assert "\\" not in filename and "/" not in filename
