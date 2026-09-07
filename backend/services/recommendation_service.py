from __future__ import annotations

from backend.schemas.analysis_schema import PriceRecommendation

MIN_RECOMMENDATION_SAMPLE_COUNT = 5
HIGH_CONFIDENCE_MIN_SAMPLES = 10
MEDIUM_CONFIDENCE_MIN_SAMPLES = 5
MAX_HIGH_CONFIDENCE_OUTLIER_RATIO = 0.10
MAX_MEDIUM_CONFIDENCE_OUTLIER_RATIO = 0.25
LARGE_PRICE_GAP_THRESHOLD_PERCENT = 0.15
RECOMMENDATION_HISTORICAL_WEIGHT = 0.6
RECOMMENDATION_RECENT_WEIGHT = 0.4


def _safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _verified_ratio(stats) -> float:
    sample_count = int(getattr(stats, "sample_count", 0) or 0)
    verified_count = int(getattr(stats, "verified_sample_count", 0) or 0)
    if sample_count <= 0:
        return 0.0
    return min(1.0, max(0.0, verified_count / sample_count))


def _outlier_ratio(stats) -> float:
    ratio = _safe_float(getattr(stats, "outlier_ratio", None))
    if ratio is None:
        return 0.0
    return max(0.0, min(1.0, float(ratio)))


def _vendor_score(vendor_count: int | None) -> float:
    if vendor_count is None:
        return 0.7
    if vendor_count <= 1:
        return 0.2
    if vendor_count == 2:
        return 0.5
    return 1.0


def _recent_score(stats) -> float:
    recent_median = _safe_float(getattr(stats, "recent_median", None))
    return 1.0 if recent_median is not None else 0.5


def calculate_confidence(stats, vendor_count: int | None = None, recent_data_available: bool | None = None) -> float:
    sample_count = int(getattr(stats, "sample_count", 0) or 0)
    if sample_count == 0:
        return 0.0

    verified_ratio = _verified_ratio(stats)
    outlier_ratio = _outlier_ratio(stats)
    vendor_score = _vendor_score(vendor_count)
    recent_score = _recent_score(stats) if recent_data_available is None else (1.0 if recent_data_available else 0.5)

    sample_component = 0.0
    if sample_count < MIN_RECOMMENDATION_SAMPLE_COUNT:
        sample_component = 0.25
    elif sample_count < HIGH_CONFIDENCE_MIN_SAMPLES:
        sample_component = 0.55
    else:
        sample_component = 0.8

    verification_component = 0.25 + (verified_ratio * 0.75)
    outlier_component = 1.0 - min(1.0, outlier_ratio / 0.5)
    vendor_component = vendor_score
    recent_component = recent_score

    score = (
        0.30 * sample_component
        + 0.25 * verification_component
        + 0.20 * outlier_component
        + 0.15 * vendor_component
        + 0.10 * recent_component
    )

    return max(0.0, min(1.0, score))


def calculate_price_range(stats):
    historical_median = _safe_float(getattr(stats, "median", None))
    q1 = _safe_float(getattr(stats, "q1", None))
    q3 = _safe_float(getattr(stats, "q3", None))
    low = q1 if q1 is not None else None
    base = historical_median if historical_median is not None else None
    high = q3 if q3 is not None else None
    return low, base, high


def build_recommendation_reason(
    stats,
    recommendation_price: float | None,
    historical_median: float | None,
    recent_median: float | None,
    weighted_mean: float | None,
    confidence_label: str,
    vendor_count: int | None = None,
):
    sample_count = int(getattr(stats, "sample_count", 0) or 0)
    if sample_count == 0 or historical_median is None:
        return "Insufficient verified samples. Historical median is missing."

    parts = [
        f"Recommendation based on {sample_count} verified samples.",
        f"Historical median: {historical_median:,.0f} {getattr(stats, 'unit', '') or 'UNIT'}.",
    ]

    if recent_median is not None:
        parts.append(f"Recent median: {recent_median:,.0f} {getattr(stats, 'unit', '') or 'UNIT'}.")
        recent_gap = abs(recent_median - historical_median) / historical_median if historical_median else 0.0
        if recent_gap > LARGE_PRICE_GAP_THRESHOLD_PERCENT:
            parts.append("Recent price trend differs materially from historical median.")
    else:
        parts.append("Recent median unavailable; recommendation remains anchored to historical median.")

    outlier_ratio = _outlier_ratio(stats)
    if outlier_ratio is not None:
        parts.append(f"Outlier ratio: {outlier_ratio * 100:.1f}%.")

    if vendor_count is None:
        parts.append("Vendor count unavailable; diversity risk could not be fully assessed.")
    elif vendor_count == 1:
        parts.append("Single vendor concentration increases recommendation risk.")
    elif vendor_count == 2:
        parts.append("Limited vendor diversity requires additional human review.")
    else:
        parts.append(f"Vendor count: {vendor_count}.")

    if weighted_mean is not None and recommendation_price is not None and historical_median is not None:
        gap_ratio = abs(weighted_mean - recommendation_price) / recommendation_price if recommendation_price else 0.0
        if gap_ratio > LARGE_PRICE_GAP_THRESHOLD_PERCENT and weighted_mean > 0:
            parts.append("Large difference between median-based recommendation and weighted mean.")

    parts.append(f"Confidence: {confidence_label}.")
    return " ".join(parts)


def _resolve_label(score: float, sample_count: int, outlier_ratio: float) -> str:
    if sample_count == 0:
        return "INSUFFICIENT"
    if score >= 0.75 and sample_count >= HIGH_CONFIDENCE_MIN_SAMPLES and outlier_ratio <= MAX_HIGH_CONFIDENCE_OUTLIER_RATIO:
        return "HIGH"
    if score >= 0.45 and sample_count >= MEDIUM_CONFIDENCE_MIN_SAMPLES and outlier_ratio <= MAX_MEDIUM_CONFIDENCE_OUTLIER_RATIO:
        return "MEDIUM"
    if sample_count < MIN_RECOMMENDATION_SAMPLE_COUNT:
        return "LOW"
    return "LOW"


def recommend_unit_price(
    stats,
    vendor_count: int | None = None,
    data_age: str | None = None,
    project_similarity: float | None = None,
    region_similarity: float | None = None,
):
    sample_count = int(getattr(stats, "sample_count", 0) or 0)
    historical_median = _safe_float(getattr(stats, "median", None))
    recent_median = _safe_float(getattr(stats, "recent_median", None))
    weighted_mean = _safe_float(getattr(stats, "weighted_mean", None))
    outlier_ratio = _outlier_ratio(stats)
    verified_ratio = _verified_ratio(stats)

    if sample_count == 0 or historical_median is None:
        recommendation = PriceRecommendation(
            work_type_code=getattr(stats, "work_type_code", "UNKNOWN"),
            unit=getattr(stats, "unit", None),
            historical_mean=_safe_float(getattr(stats, "mean", None)),
            historical_median=historical_median,
            recent_median=recent_median,
            recommended_unit_price=None,
            low_unit_price=None,
            base_unit_price=None,
            high_unit_price=None,
            confidence="INSUFFICIENT",
            confidence_score=0.0,
            reason="Insufficient verified samples.",
            sample_count=sample_count,
            vendor_count=vendor_count,
            outlier_ratio=outlier_ratio,
            human_review_required=True,
        )
        return recommendation

    low, base, high = calculate_price_range(stats)
    recommended_price = float(historical_median)

    if sample_count >= MIN_RECOMMENDATION_SAMPLE_COUNT and recent_median is not None and verified_ratio >= 0.7:
        blended = (historical_median * RECOMMENDATION_HISTORICAL_WEIGHT) + (recent_median * RECOMMENDATION_RECENT_WEIGHT)
        recent_gap = abs(recent_median - historical_median) / historical_median if historical_median else 0.0
        if recent_gap <= LARGE_PRICE_GAP_THRESHOLD_PERCENT:
            recommended_price = blended
    elif sample_count < MIN_RECOMMENDATION_SAMPLE_COUNT:
        recommended_price = historical_median

    confidence_score = calculate_confidence(stats, vendor_count=vendor_count)
    confidence_label = _resolve_label(confidence_score, sample_count, outlier_ratio)

    if sample_count < MIN_RECOMMENDATION_SAMPLE_COUNT:
        confidence_label = "LOW"

    if outlier_ratio > MAX_MEDIUM_CONFIDENCE_OUTLIER_RATIO:
        confidence_label = "LOW"

    if vendor_count == 1:
        confidence_label = "LOW" if confidence_label != "INSUFFICIENT" else "INSUFFICIENT"

    if sample_count == 0:
        confidence_label = "INSUFFICIENT"

    reason = build_recommendation_reason(
        stats,
        recommendation_price=recommended_price,
        historical_median=historical_median,
        recent_median=recent_median,
        weighted_mean=weighted_mean,
        confidence_label=confidence_label,
        vendor_count=vendor_count,
    )

    if vendor_count == 1:
        reason = f"{reason} Single vendor risk requires human review."
    if weighted_mean is not None and recommended_price is not None:
        gap_ratio = abs(weighted_mean - recommended_price) / recommended_price if recommended_price else 0.0
        if gap_ratio > LARGE_PRICE_GAP_THRESHOLD_PERCENT:
            reason = f"{reason} Large difference between median-based recommendation and weighted mean."

    if sample_count < MIN_RECOMMENDATION_SAMPLE_COUNT:
        reason = f"{reason} Reference value used because sample_count is below minimum threshold."

    recommendation = PriceRecommendation(
        work_type_code=getattr(stats, "work_type_code", "UNKNOWN"),
        unit=getattr(stats, "unit", None),
        historical_mean=_safe_float(getattr(stats, "mean", None)),
        historical_median=historical_median,
        recent_median=recent_median,
        recommended_unit_price=recommended_price,
        low_unit_price=low,
        base_unit_price=recommended_price,
        high_unit_price=high,
        confidence=confidence_label,
        confidence_score=confidence_score,
        reason=reason,
        sample_count=sample_count,
        vendor_count=vendor_count,
        outlier_ratio=outlier_ratio,
        human_review_required=True,
    )
    return recommendation


__all__ = [
    "MIN_RECOMMENDATION_SAMPLE_COUNT",
    "RECOMMENDATION_HISTORICAL_WEIGHT",
    "RECOMMENDATION_RECENT_WEIGHT",
    "calculate_confidence",
    "calculate_price_range",
    "build_recommendation_reason",
    "recommend_unit_price",
]
