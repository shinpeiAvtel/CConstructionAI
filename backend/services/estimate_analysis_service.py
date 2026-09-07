from __future__ import annotations

from datetime import datetime

from backend.models import EstimateDocument, QuoteItem, WorkTypeMaster
from backend.schemas.analysis_schema import (
    AnalysisMetadata,
    DocumentAnalysisResult,
    DocumentSummary,
    QuoteItemAnalysis,
    VerificationSummary,
    WorkTypePriceStatistics,
)
from backend.services.recommendation_service import recommend_unit_price
from backend.services.statistics_service import calculate_price_statistics

ANALYSIS_VERSION = "analysis-v1"
OUTLIER_METHOD = "IQR_1.5_INCLUSIVE"


def _normalize_verification_status(value):
    if value is None:
        return "NEEDS_REVIEW"
    return str(value).upper()


def _resolve_analysis_unit_price(item):
    candidates = [
        getattr(item, "normalized_unit_price", None),
        getattr(item, "calculated_unit_price", None),
        getattr(item, "source_unit_price", None),
    ]

    for candidate in candidates:
        if candidate is not None:
            return float(candidate)
    return None


def _resolve_analysis_amount(item):
    source_amount = getattr(item, "amount", None)
    if source_amount is not None:
        return float(source_amount)
    quantity = getattr(item, "quantity", None)
    unit_price = _resolve_analysis_unit_price(item)
    if quantity is not None and unit_price is not None and quantity > 0:
        return float(quantity * unit_price)
    return None


def _resolve_work_type_context(item, work_type_map=None):
    work_type_code = getattr(item, "work_type_code", None)
    work_type = None
    if work_type_map and work_type_code:
        work_type = work_type_map.get(str(work_type_code).strip().upper())
    if work_type is None:
        return {
            "work_type_name": None,
            "category": None,
            "sub_category": None,
        }
    return {
        "work_type_name": work_type.work_type_name,
        "category": work_type.category,
        "sub_category": work_type.sub_category,
    }


def build_document_summary(document: EstimateDocument) -> DocumentSummary:
    return DocumentSummary(
        document_id=document.id,
        source_filename=document.source_filename,
        source_type=document.source_type,
        vendor_name=document.vendor_name,
        project_code=document.project_code,
        quote_number=document.quote_number,
        quote_date=document.quote_date,
        currency=document.currency if hasattr(document, "currency") else None,
        subtotal=getattr(document, "subtotal", None),
        tax=getattr(document, "tax", None),
        total=getattr(document, "total", None),
        uploaded_at=document.upload_timestamp,
        verification_status=document.verification_status,
    )


def build_quote_item_analysis(quote_item: QuoteItem, work_type: WorkTypeMaster | None = None) -> QuoteItemAnalysis:
    quantity = getattr(quote_item, "quantity", None)
    unit = getattr(quote_item, "unit", None)
    source_amount = getattr(quote_item, "amount", None)
    calculated_amount = None
    if quantity is not None and quantity > 0:
        unit_price = _resolve_analysis_unit_price(quote_item)
        if unit_price is not None:
            calculated_amount = float(quantity * unit_price)

    analysis = QuoteItemAnalysis(
        quote_item_id=quote_item.id,
        line_number=getattr(quote_item, "line_number", None),
        raw_description=getattr(quote_item, "raw_description", ""),
        normalized_description=getattr(quote_item, "normalized_description", None),
        work_type_code=getattr(quote_item, "work_type_code", None),
        work_type_name=(work_type.work_type_name if work_type else None),
        category=(work_type.category if work_type else None),
        sub_category=(work_type.sub_category if work_type else None),
        manufacturer=getattr(quote_item, "manufacturer", None),
        model_number=getattr(quote_item, "model_number", None),
        quantity=quantity,
        unit=unit,
        source_unit_price=getattr(quote_item, "source_unit_price", None),
        calculated_unit_price=getattr(quote_item, "calculated_unit_price", None),
        normalized_unit_price=getattr(quote_item, "normalized_unit_price", None),
        source_amount=source_amount,
        calculated_amount=calculated_amount,
        quoted_person_days=getattr(quote_item, "quoted_person_days", None),
        quoted_labor_amount=getattr(quote_item, "quoted_labor_amount", None),
        mapping_confidence=getattr(quote_item, "mapping_confidence", None),
        verification_status=_normalize_verification_status(getattr(quote_item, "verification_status", None)),
        is_outlier=False,
        outlier_reason=None,
    )
    return analysis


def build_verification_summary(items) -> VerificationSummary:
    total_items = len(items)
    verified_items = sum(1 for item in items if _normalize_verification_status(getattr(item, "verification_status", None)) == "VERIFIED")
    needs_review_items = sum(1 for item in items if _normalize_verification_status(getattr(item, "verification_status", None)) == "NEEDS_REVIEW")
    rejected_items = sum(1 for item in items if _normalize_verification_status(getattr(item, "verification_status", None)) == "REJECTED")
    unmapped_items = sum(1 for item in items if not getattr(item, "work_type_code", None))

    valid_confidence_values = []
    for item in items:
        value = getattr(item, "mapping_confidence", None)
        if value is not None:
            try:
                valid_confidence_values.append(float(value))
            except (TypeError, ValueError):
                continue

    average_mapping_confidence = None
    if valid_confidence_values:
        average_mapping_confidence = sum(valid_confidence_values) / len(valid_confidence_values)

    analysis_eligible_items = verified_items
    excluded_items = total_items - analysis_eligible_items

    return VerificationSummary(
        total_items=total_items,
        verified_items=verified_items,
        needs_review_items=needs_review_items,
        unmapped_items=unmapped_items,
        rejected_items=rejected_items,
        average_mapping_confidence=average_mapping_confidence,
        analysis_eligible_items=analysis_eligible_items,
        excluded_items=excluded_items,
    )


def _calculate_group_statistics(group_items):
    values = []
    weights = []
    for item in group_items:
        candidate_value = _resolve_analysis_unit_price(item)
        if candidate_value is None:
            continue
        values.append(candidate_value)
        quantity = getattr(item, "quantity", None)
        if quantity is not None and float(quantity) > 0:
            weights.append(float(quantity))
        else:
            weights.append(1.0)

    stats = calculate_price_statistics(values, weights)
    outlier_flags = stats.get("outlier_flags", [])

    for index, item in enumerate(group_items):
        item.is_outlier = False
        item.outlier_reason = None

    for index, item in enumerate(group_items):
        if index < len(outlier_flags) and outlier_flags[index]:
            item.is_outlier = True
            item.outlier_reason = "UNIT_PRICE_ABOVE_IQR_UPPER_BOUND" if _resolve_analysis_unit_price(item) is not None and _resolve_analysis_unit_price(item) > (stats.get("upper_bound") or 0) else "UNIT_PRICE_BELOW_IQR_LOWER_BOUND"

    return WorkTypePriceStatistics(
        work_type_code=group_items[0].work_type_code or "UNKNOWN",
        work_type_name=group_items[0].work_type_name,
        unit=group_items[0].unit,
        sample_count=stats["sample_count"],
        minimum=stats["minimum"],
        maximum=stats["maximum"],
        mean=stats["mean"],
        median=stats["median"],
        weighted_mean=stats["weighted_mean"],
        standard_deviation=stats["standard_deviation"],
        q1=stats["q1"],
        q3=stats["q3"],
        iqr=stats["iqr"],
        lower_bound=stats["lower_bound"],
        upper_bound=stats["upper_bound"],
        outlier_count=stats["outlier_count"],
        outlier_ratio=stats["outlier_ratio"],
        recent_median=None,
        analysis_period=None,
        verified_sample_count=sum(1 for item in group_items if _normalize_verification_status(getattr(item, "verification_status", None)) == "VERIFIED"),
        unverified_sample_count=sum(1 for item in group_items if _normalize_verification_status(getattr(item, "verification_status", None)) != "VERIFIED"),
        excluded_sample_count=0,
    )


def calculate_work_type_statistics(items):
    grouped = {}
    for item in items:
        if _normalize_verification_status(getattr(item, "verification_status", None)) != "VERIFIED":
            continue
        group_key = (
            str(getattr(item, "work_type_code", "") or "UNKNOWN").strip().upper(),
            getattr(item, "unit", None),
        )
        grouped.setdefault(group_key, []).append(item)

    results = []
    for _, group_items in grouped.items():
        if not group_items:
            continue
        results.append(_calculate_group_statistics(group_items))
    return results


def build_price_recommendations(work_type_analysis):
    recommendations = []
    for stats in work_type_analysis or []:
        recommendations.append(recommend_unit_price(stats, vendor_count=None))
    return recommendations


def build_document_analysis(document, quote_items, work_types):
    work_type_map = {}
    for work_type in work_types or []:
        work_type_map[str(work_type.work_type_code).strip().upper()] = work_type

    item_dtos = []
    for quote_item in quote_items or []:
        work_type = None
        if getattr(quote_item, "work_type_code", None):
            code = str(quote_item.work_type_code).strip().upper()
            work_type = work_type_map.get(code)
        item_dtos.append(build_quote_item_analysis(quote_item, work_type=work_type))

    analysis_items = item_dtos
    work_type_analysis = calculate_work_type_statistics(analysis_items)
    verification_summary = build_verification_summary(analysis_items)
    price_recommendations = build_price_recommendations(work_type_analysis)

    metadata = AnalysisMetadata(
        analysis_version=ANALYSIS_VERSION,
        analyzed_at=datetime.now(),
        document_id=document.id,
        included_samples=len(analysis_items),
        excluded_samples=verification_summary.excluded_items,
        outlier_method=OUTLIER_METHOD,
    )

    return DocumentAnalysisResult(
        document=build_document_summary(document),
        items=analysis_items,
        work_type_analysis=work_type_analysis,
        price_recommendations=price_recommendations,
        labor_analysis=[],
        verification_summary=verification_summary,
        metadata=metadata,
        outliers=[item for item in analysis_items if item.is_outlier],
    )


__all__ = [
    "ANALYSIS_VERSION",
    "OUTLIER_METHOD",
    "build_document_summary",
    "build_quote_item_analysis",
    "build_verification_summary",
    "calculate_work_type_statistics",
    "build_document_analysis",
]
