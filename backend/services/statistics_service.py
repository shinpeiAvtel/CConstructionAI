from __future__ import annotations

from statistics import mean, median, pstdev, quantiles, StatisticsError

OUTLIER_IQR_MULTIPLIER = 1.5


def _safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_numeric_list(values):
    numeric_values: list[float] = []
    for value in values:
        parsed = _safe_float(value)
        if parsed is not None:
            numeric_values.append(parsed)
    return numeric_values


def calculate_iqr(values):
    numeric_values = sorted(_as_numeric_list(values))
    if len(numeric_values) < 4:
        return {
            "q1": None,
            "q3": None,
            "iqr": None,
            "lower_bound": None,
            "upper_bound": None,
            "outlier_method": "IQR_1.5_INCLUSIVE",
            "sample_count": len(numeric_values),
        }

    quartiles = quantiles(numeric_values, n=4, method="inclusive")
    q1 = float(quartiles[0])
    q3 = float(quartiles[2])
    iqr = q3 - q1

    lower_bound = q1 - OUTLIER_IQR_MULTIPLIER * iqr
    upper_bound = q3 + OUTLIER_IQR_MULTIPLIER * iqr

    return {
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_method": "IQR_1.5_INCLUSIVE",
        "sample_count": len(numeric_values),
    }


def detect_outliers(values):
    numeric_values = _as_numeric_list(values)
    if not numeric_values:
        return []

    stats = calculate_iqr(numeric_values)
    if stats["q1"] is None or stats["q3"] is None or stats["iqr"] is None:
        return [False for _ in numeric_values]

    lower_bound = stats["lower_bound"]
    upper_bound = stats["upper_bound"]

    flags: list[bool] = []
    for value in numeric_values:
        is_outlier = value < lower_bound or value > upper_bound
        flags.append(bool(is_outlier))
    return flags


def calculate_price_statistics(values, weights=None):
    numeric_values = _as_numeric_list(values)
    sample_count = len(numeric_values)

    if sample_count == 0:
        return {
            "sample_count": 0,
            "minimum": None,
            "maximum": None,
            "mean": None,
            "median": None,
            "weighted_mean": None,
            "standard_deviation": None,
            "q1": None,
            "q3": None,
            "iqr": None,
            "lower_bound": None,
            "upper_bound": None,
            "outlier_count": 0,
            "outlier_ratio": None,
            "outlier_flags": [],
        }

    minimum = min(numeric_values)
    maximum = max(numeric_values)

    try:
        mean_value = float(mean(numeric_values))
    except StatisticsError:
        mean_value = None

    try:
        median_value = float(median(numeric_values))
    except StatisticsError:
        median_value = None

    weighted_mean = None
    if weights is not None and len(weights) == sample_count:
        weighted_pairs = []
        for value, weight in zip(numeric_values, weights):
            weight_value = _safe_float(weight)
            if weight_value is not None and weight_value > 0:
                weighted_pairs.append((value, weight_value))
        if weighted_pairs:
            numerator = sum(value * weight for value, weight in weighted_pairs)
            denominator = sum(weight for _, weight in weighted_pairs)
            if denominator > 0:
                weighted_mean = float(numerator / denominator)

    try:
        standard_deviation = float(pstdev(numeric_values)) if sample_count > 1 else None
    except StatisticsError:
        standard_deviation = None

    iqr_stats = calculate_iqr(numeric_values)
    q1 = iqr_stats["q1"]
    q3 = iqr_stats["q3"]
    iqr = iqr_stats["iqr"]
    lower_bound = iqr_stats["lower_bound"]
    upper_bound = iqr_stats["upper_bound"]

    outlier_flags = detect_outliers(numeric_values)
    outlier_count = sum(1 for flag in outlier_flags if flag)
    outlier_ratio = None if sample_count == 0 else float(outlier_count / sample_count)

    return {
        "sample_count": sample_count,
        "minimum": minimum,
        "maximum": maximum,
        "mean": mean_value,
        "median": median_value,
        "weighted_mean": weighted_mean,
        "standard_deviation": standard_deviation,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_count": outlier_count,
        "outlier_ratio": outlier_ratio,
        "outlier_flags": outlier_flags,
    }


__all__ = [
    "OUTLIER_IQR_MULTIPLIER",
    "calculate_iqr",
    "detect_outliers",
    "calculate_price_statistics",
]
