from __future__ import annotations

from backend.schemas.analysis_schema import LaborAnalysisResult
from backend.services.statistics_service import calculate_iqr, calculate_price_statistics

MIN_ACTUAL_WORK_SAMPLE_COUNT = 5
MIN_QUOTED_LABOR_SAMPLE_COUNT = 5
REVISION_MIN_SAMPLE_COUNT = 10
REVISION_DIFFERENCE_THRESHOLD_PERCENT = 15.0
REVISION_MAX_MEAN_MEDIAN_GAP_PERCENT = 20.0
REVISION_MAX_OUTLIER_RATIO = 0.25
OUTLIER_IQR_MULTIPLIER = 1.5


def _safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_verification_status(value):
    if value is None:
        return "NEEDS_REVIEW"
    return str(value).upper()


def _quoted_labor_per_unit(item):
    quantity = _safe_float(getattr(item, "quantity", None))
    quoted_person_days = _safe_float(getattr(item, "quoted_person_days", None))
    if quoted_person_days is None or quantity is None or quantity <= 0:
        return None
    return quoted_person_days / quantity


def _actual_labor_per_unit(record, minutes_per_person_day):
    if minutes_per_person_day is None or minutes_per_person_day <= 0:
        return None
    quantity = _safe_float(getattr(record, "quantity", None))
    workers = _safe_float(getattr(record, "workers", None))
    work_minutes = _safe_float(getattr(record, "work_minutes", None))
    if quantity is None or quantity <= 0:
        return None
    if workers is None or workers <= 0:
        return None
    if work_minutes is None or work_minutes <= 0:
        return None
    actual_person_days = (workers * work_minutes) / minutes_per_person_day
    return actual_person_days / quantity


def _build_stats(values):
    numeric = [float(v) for v in values if v is not None]
    if not numeric:
        return {
            "sample_count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
            "q1": None,
            "q3": None,
            "iqr": None,
            "lower_bound": None,
            "upper_bound": None,
            "outlier_count": 0,
            "outlier_ratio": None,
            "outlier_flags": [],
        }
    stats = calculate_price_statistics(numeric)
    return {
        "sample_count": stats["sample_count"],
        "mean": stats["mean"],
        "median": stats["median"],
        "minimum": stats["minimum"],
        "maximum": stats["maximum"],
        "q1": stats["q1"],
        "q3": stats["q3"],
        "iqr": stats["iqr"],
        "lower_bound": stats["lower_bound"],
        "upper_bound": stats["upper_bound"],
        "outlier_count": stats["outlier_count"],
        "outlier_ratio": stats["outlier_ratio"],
        "outlier_flags": stats["outlier_flags"],
    }


def analyze_quoted_labor(items):
    verified_items = [item for item in items if _normalize_verification_status(getattr(item, "verification_status", None)) == "VERIFIED"]
    grouped = {}
    for item in verified_items:
        key = (getattr(item, "work_type_code", None), getattr(item, "unit", None))
        grouped.setdefault(key, []).append(item)

    groups = []
    for (work_type_code, unit), group_items in grouped.items():
        values = [_quoted_labor_per_unit(item) for item in group_items]
        stats = _build_stats(values)
        groups.append({
            "work_type_code": work_type_code,
            "unit": unit,
            "sample_count": stats["sample_count"],
            "mean": stats["mean"],
            "median": stats["median"],
            "minimum": stats["minimum"],
            "maximum": stats["maximum"],
            "q1": stats["q1"],
            "q3": stats["q3"],
            "iqr": stats["iqr"],
            "lower_bound": stats["lower_bound"],
            "upper_bound": stats["upper_bound"],
            "outlier_count": stats["outlier_count"],
            "outlier_ratio": stats["outlier_ratio"],
            "unit_groups": len(grouped),
        })

    if not groups:
        return {
            "sample_count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
            "q1": None,
            "q3": None,
            "iqr": None,
            "lower_bound": None,
            "upper_bound": None,
            "outlier_count": 0,
            "outlier_ratio": None,
            "unit_groups": 0,
        }

    all_values = [value for group in groups for value in [group["mean"], group["median"]] if value is not None]
    representative = {
        "sample_count": sum(group["sample_count"] for group in groups),
        "mean": sum(value for value in all_values if value is not None) / len(all_values) if all_values else None,
        "median": sorted(all_values)[len(all_values) // 2] if all_values else None,
        "minimum": min(value for value in all_values if value is not None) if all_values else None,
        "maximum": max(value for value in all_values if value is not None) if all_values else None,
        "q1": None,
        "q3": None,
        "iqr": None,
        "lower_bound": None,
        "upper_bound": None,
        "outlier_count": sum(group["outlier_count"] for group in groups),
        "outlier_ratio": (sum(group["outlier_count"] for group in groups) / sum(group["sample_count"] for group in groups)) if sum(group["sample_count"] for group in groups) else None,
        "unit_groups": len(groups),
    }
    return representative


def analyze_actual_work(records, minutes_per_person_day):
    valid_records = []
    for record in records or []:
        value = _actual_labor_per_unit(record, minutes_per_person_day)
        if value is not None:
            valid_records.append({"record": record, "value": value})

    values = [item["value"] for item in valid_records]
    stats = _build_stats(values)

    return {
        "sample_count": stats["sample_count"],
        "mean": stats["mean"],
        "median": stats["median"],
        "minimum": stats["minimum"],
        "maximum": stats["maximum"],
        "q1": stats["q1"],
        "q3": stats["q3"],
        "iqr": stats["iqr"],
        "lower_bound": stats["lower_bound"],
        "upper_bound": stats["upper_bound"],
        "outlier_count": stats["outlier_count"],
        "outlier_ratio": stats["outlier_ratio"],
        "all_samples": len(valid_records),
        "non_outlier_samples": len(valid_records) - stats["outlier_count"],
        "outlier_flags": stats["outlier_flags"],
    }


def compare_labor(quoted_labor, actual_work, current_standard_labor=None):
    quoted_median = _safe_float(quoted_labor.get("median")) if isinstance(quoted_labor, dict) else None
    actual_median = _safe_float(actual_work.get("median")) if isinstance(actual_work, dict) else None
    quoted_sample_count = int(quoted_labor.get("sample_count", 0) or 0) if isinstance(quoted_labor, dict) else 0
    actual_sample_count = int(actual_work.get("sample_count", 0) or 0) if isinstance(actual_work, dict) else 0
    quoted_outlier_ratio = _safe_float(quoted_labor.get("outlier_ratio")) if isinstance(quoted_labor, dict) else None
    actual_outlier_ratio = _safe_float(actual_work.get("outlier_ratio")) if isinstance(actual_work, dict) else None

    difference_from_current_percent = None
    if current_standard_labor is not None and current_standard_labor > 0 and actual_median is not None:
        difference_from_current_percent = ((actual_median - current_standard_labor) / current_standard_labor) * 100

    return {
        "current_standard_labor": current_standard_labor,
        "quoted_median": quoted_median,
        "actual_median": actual_median,
        "quoted_sample_count": quoted_sample_count,
        "actual_sample_count": actual_sample_count,
        "quoted_outlier_ratio": quoted_outlier_ratio,
        "actual_outlier_ratio": actual_outlier_ratio,
        "difference_from_current_percent": difference_from_current_percent,
        "conflict": False,
    }


def recommend_labor_candidate(comparison):
    actual_sample_count = int(comparison.get("actual_sample_count", 0) or 0)
    quoted_sample_count = int(comparison.get("quoted_sample_count", 0) or 0)
    actual_median = _safe_float(comparison.get("actual_median"))
    quoted_median = _safe_float(comparison.get("quoted_median"))

    if actual_sample_count >= MIN_ACTUAL_WORK_SAMPLE_COUNT and actual_median is not None:
        return actual_median
    if quoted_sample_count >= MIN_QUOTED_LABOR_SAMPLE_COUNT and quoted_median is not None:
        return quoted_median
    return None


def calculate_revision_eligibility(sample_count, difference_percent, mean_median_gap_percent, outlier_ratio):
    checks = {
        "sample_count_ok": sample_count >= REVISION_MIN_SAMPLE_COUNT,
        "difference_ok": abs(difference_percent) >= REVISION_DIFFERENCE_THRESHOLD_PERCENT,
        "consistency_ok": mean_median_gap_percent <= REVISION_MAX_MEAN_MEDIAN_GAP_PERCENT,
        "outlier_ratio_ok": outlier_ratio <= REVISION_MAX_OUTLIER_RATIO,
    }
    reasons = []
    if not checks["sample_count_ok"]:
        reasons.append("Insufficient valid sample count.")
    if not checks["difference_ok"]:
        reasons.append("Difference from current standard is below revision threshold.")
    if not checks["consistency_ok"]:
        reasons.append("Weighted average and median are not sufficiently consistent.")
    if not checks["outlier_ratio_ok"]:
        reasons.append("Outlier ratio is too high.")
    return {
        "eligible": all(checks.values()),
        "checks": checks,
        "reasons": reasons,
    }


def _confidence_label(score):
    if score >= 0.75:
        return "HIGH"
    if score >= 0.45:
        return "MEDIUM"
    if score >= 0.2:
        return "LOW"
    return "INSUFFICIENT"


def _calculate_confidence(actual_sample_count, quoted_sample_count, outlier_ratio, difference_from_current_percent, quoted_vs_actual_gap):
    if actual_sample_count == 0 and quoted_sample_count == 0:
        return 0.0

    sample_score = 0.0
    if actual_sample_count >= MIN_ACTUAL_WORK_SAMPLE_COUNT:
        sample_score += 0.5
    elif actual_sample_count > 0:
        sample_score += 0.2
    if quoted_sample_count >= MIN_QUOTED_LABOR_SAMPLE_COUNT:
        sample_score += 0.25
    elif quoted_sample_count > 0:
        sample_score += 0.1

    outlier_score = 1.0 - min(1.0, outlier_ratio or 0.0)
    difference_score = 1.0 if difference_from_current_percent is None else max(0.0, 1.0 - min(1.0, abs(difference_from_current_percent) / 100.0))
    conflict_score = 1.0 if quoted_vs_actual_gap is None else max(0.0, 1.0 - min(1.0, quoted_vs_actual_gap / 0.75))

    score = (0.45 * sample_score) + (0.2 * outlier_score) + (0.2 * difference_score) + (0.15 * conflict_score)
    return max(0.0, min(1.0, score))


def build_labor_analysis_result(
    work_type_code,
    labor_code,
    unit,
    quoted_labor,
    actual_work,
    current_standard_labor,
    minutes_per_person_day,
):
    candidate = recommend_labor_candidate(compare_labor(quoted_labor, actual_work, current_standard_labor))
    comparison = compare_labor(quoted_labor, actual_work, current_standard_labor)
    actual_sample_count = int(comparison.get("actual_sample_count", 0) or 0)
    quoted_sample_count = int(comparison.get("quoted_sample_count", 0) or 0)
    actual_outlier_ratio = _safe_float(comparison.get("actual_outlier_ratio")) or 0.0
    quoted_outlier_ratio = _safe_float(comparison.get("quoted_outlier_ratio")) or 0.0
    outlier_ratio = max(actual_outlier_ratio, quoted_outlier_ratio)
    quoted_median = _safe_float(comparison.get("quoted_median"))
    actual_median = _safe_float(comparison.get("actual_median"))
    quoted_vs_actual_gap = None
    if quoted_median is not None and actual_median is not None and actual_median > 0:
        quoted_vs_actual_gap = abs(quoted_median - actual_median) / actual_median

    difference_from_current_percent = comparison.get("difference_from_current_percent")
    confidence_score = _calculate_confidence(actual_sample_count, quoted_sample_count, outlier_ratio, difference_from_current_percent, quoted_vs_actual_gap)
    confidence = _confidence_label(confidence_score)

    if candidate is None:
        confidence = "INSUFFICIENT"

    reason_parts = []
    if actual_median is not None:
        reason_parts.append(f"Actual work median is {actual_median:.4f} person-days/unit from {actual_sample_count} verified actual records.")
    elif quoted_median is not None:
        reason_parts.append(f"Quoted labor median is {quoted_median:.4f} person-days/unit; actual work data is insufficient.")
    else:
        reason_parts.append("No sufficient labor evidence is available.")

    if current_standard_labor is not None and current_standard_labor > 0:
        reason_parts.append(f"Current standard is {current_standard_labor:.4f}.")
    if quoted_median is not None:
        reason_parts.append(f"Quoted labor median is {quoted_median:.4f}.")
    if difference_from_current_percent is not None:
        reason_parts.append(f"Difference is {difference_from_current_percent:.2f}%.")
    if quoted_vs_actual_gap is not None and quoted_vs_actual_gap > 0.25:
        reason_parts.append("Quoted labor materially understates actual field performance.")
    reason = " ".join(reason_parts)

    revision_eligibility = calculate_revision_eligibility(
        actual_sample_count,
        difference_from_current_percent if difference_from_current_percent is not None else 0.0,
        abs((actual_median - quoted_median) / quoted_median * 100) if actual_median is not None and quoted_median and quoted_median > 0 else 0.0,
        outlier_ratio,
    )

    recommendation = LaborAnalysisResult(
        work_type_code=work_type_code,
        labor_code=labor_code,
        unit=unit,
        current_standard_labor=current_standard_labor,
        quoted_labor_sample_count=quoted_sample_count,
        quoted_labor_mean=_safe_float(quoted_labor.get("mean")) if isinstance(quoted_labor, dict) else None,
        quoted_labor_median=quoted_median,
        actual_work_sample_count=actual_sample_count,
        actual_work_mean=_safe_float(actual_work.get("mean")) if isinstance(actual_work, dict) else None,
        actual_work_median=actual_median,
        recommended_labor_candidate=candidate,
        difference_from_current_percent=difference_from_current_percent,
        confidence=confidence,
        reason=reason,
        human_review_required=True,
    )
    return recommendation


__all__ = [
    "MIN_ACTUAL_WORK_SAMPLE_COUNT",
    "MIN_QUOTED_LABOR_SAMPLE_COUNT",
    "REVISION_MIN_SAMPLE_COUNT",
    "REVISION_DIFFERENCE_THRESHOLD_PERCENT",
    "REVISION_MAX_MEAN_MEDIAN_GAP_PERCENT",
    "REVISION_MAX_OUTLIER_RATIO",
    "analyze_quoted_labor",
    "analyze_actual_work",
    "compare_labor",
    "recommend_labor_candidate",
    "calculate_revision_eligibility",
    "build_labor_analysis_result",
]
