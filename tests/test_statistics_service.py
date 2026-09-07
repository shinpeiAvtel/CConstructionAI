from backend.services.statistics_service import calculate_iqr, calculate_price_statistics, detect_outliers


def test_empty_sample_returns_none_metrics():
    stats = calculate_price_statistics([])
    assert stats["sample_count"] == 0
    assert stats["mean"] is None
    assert stats["median"] is None
    assert stats["weighted_mean"] is None
    assert stats["outlier_count"] == 0


def test_one_sample_stats():
    stats = calculate_price_statistics([100])
    assert stats["sample_count"] == 1
    assert stats["mean"] == 100.0
    assert stats["median"] == 100.0
    assert stats["standard_deviation"] is None
    assert stats["q1"] is None
    assert stats["iqr"] is None


def test_two_or_three_samples_basic_values():
    stats = calculate_price_statistics([100, 200, 300])
    assert stats["minimum"] == 100.0
    assert stats["maximum"] == 300.0
    assert stats["mean"] == 200.0
    assert stats["median"] == 200.0
    assert stats["sample_count"] == 3


def test_iqr_for_four_or_more_samples():
    stats = calculate_price_statistics([100, 200, 300, 400, 500])
    assert stats["q1"] is not None
    assert stats["q3"] is not None
    assert stats["iqr"] is not None
    assert stats["lower_bound"] is not None
    assert stats["upper_bound"] is not None


def test_low_outlier_detection():
    stats = calculate_price_statistics([10, 12, 13, 14, 15, 100])
    assert stats["outlier_count"] >= 1
    assert stats["outlier_ratio"] is not None


def test_high_outlier_detection():
    stats = calculate_price_statistics([10, 12, 13, 14, 15, 1000])
    assert stats["outlier_count"] >= 1


def test_no_outlier_below_bound():
    stats = calculate_price_statistics([10, 12, 13, 14, 15, 16])
    assert stats["outlier_count"] == 0


def test_weighted_mean_with_valid_weights():
    stats = calculate_price_statistics([100, 200, 300], weights=[1, 2, 3])
    assert stats["weighted_mean"] is not None
    assert stats["weighted_mean"] > 200


def test_invalid_weight_excluded():
    stats = calculate_price_statistics([100, 200, 300], weights=[1, -1, 3])
    assert stats["weighted_mean"] is not None


def test_invalid_weight_none_falls_back_to_none():
    stats = calculate_price_statistics([100, 200, 300], weights=[None, 2, 3])
    assert stats["weighted_mean"] is not None


def test_calculate_iqr_returns_none_for_small_sample():
    result = calculate_iqr([1, 2, 3])
    assert result["q1"] is None
    assert result["q3"] is None
    assert result["iqr"] is None


def test_detect_outliers_returns_false_when_no_outliers():
    flags = detect_outliers([10, 12, 13, 14, 15, 16])
    assert all(flag is False for flag in flags)
