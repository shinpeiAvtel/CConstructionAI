from backend.schemas.analysis_schema import WorkTypePriceStatistics
from backend.services.recommendation_service import (
    calculate_confidence,
    calculate_price_range,
    build_recommendation_reason,
    recommend_unit_price,
)


def make_stats(**overrides):
    data = {
        "work_type_code": "MASONRY",
        "work_type_name": "Masonry Work",
        "unit": "EA",
        "sample_count": 12,
        "minimum": 15000.0,
        "maximum": 24000.0,
        "mean": 18500.0,
        "median": 18000.0,
        "weighted_mean": 17600.0,
        "standard_deviation": 3000.0,
        "q1": 16000.0,
        "q3": 21000.0,
        "iqr": 5000.0,
        "lower_bound": 8500.0,
        "upper_bound": 28500.0,
        "outlier_count": 1,
        "outlier_ratio": 0.08,
        "recent_median": 18500.0,
        "analysis_period": "2025Q1",
        "verified_sample_count": 12,
        "unverified_sample_count": 0,
        "excluded_sample_count": 0,
    }
    data.update(overrides)
    return WorkTypePriceStatistics(**data)


def test_no_samples_returns_insufficient_recommendation():
    recommendation = recommend_unit_price(make_stats(sample_count=0, median=None, mean=None, q1=None, q3=None, verified_sample_count=0))
    assert recommendation.recommended_unit_price is None
    assert recommendation.confidence == "INSUFFICIENT"
    assert recommendation.human_review_required is True
    assert "Insufficient" in recommendation.reason


def test_insufficient_samples_apply_low_confidence_and_human_review():
    recommendation = recommend_unit_price(make_stats(sample_count=4, median=18000.0, q1=16000.0, q3=20000.0, verified_sample_count=4))
    assert recommendation.recommended_unit_price == 18000.0
    assert recommendation.confidence == "LOW"
    assert recommendation.human_review_required is True


def test_median_only_recommendation_uses_historical_median():
    recommendation = recommend_unit_price(make_stats(sample_count=8, median=18000.0, recent_median=None, verified_sample_count=8))
    assert recommendation.recommended_unit_price == 18000.0
    assert recommendation.base_unit_price == 18000.0
    assert recommendation.historical_median == 18000.0


def test_historical_and_recent_median_are_blended_when_quality_is_sufficient():
    recommendation = recommend_unit_price(make_stats(sample_count=12, median=18000.0, recent_median=18500.0, verified_sample_count=12, outlier_ratio=0.05, q1=16000.0, q3=21000.0))
    assert recommendation.recommended_unit_price == 18200.0
    assert recommendation.recent_median == 18500.0
    assert recommendation.historical_median == 18000.0


def test_weight_calculation_uses_historical_and_recent_weights():
    recommendation = recommend_unit_price(make_stats(sample_count=12, median=20000.0, recent_median=22000.0, verified_sample_count=12))
    expected = (20000.0 * 0.6) + (22000.0 * 0.4)
    assert recommendation.base_unit_price == expected
    assert recommendation.recommended_unit_price == expected


def test_q1_sets_low_price_and_q3_sets_high_price():
    recommendation = recommend_unit_price(make_stats(sample_count=12, median=18000.0, q1=16000.0, q3=21000.0, verified_sample_count=12))
    assert recommendation.low_unit_price == 16000.0
    assert recommendation.high_unit_price == 21000.0


def test_missing_q1_q3_sets_range_to_none():
    recommendation = recommend_unit_price(make_stats(sample_count=8, median=18000.0, q1=None, q3=None, verified_sample_count=8))
    assert recommendation.low_unit_price is None
    assert recommendation.high_unit_price is None


def test_high_confidence_rule_is_applied_for_strong_data():
    recommendation = recommend_unit_price(make_stats(sample_count=18, median=18000.0, recent_median=18500.0, outlier_ratio=0.03, verified_sample_count=18, q1=16000.0, q3=21000.0))
    assert recommendation.confidence == "HIGH"
    assert recommendation.confidence_score >= 0.7


def test_medium_confidence_for_good_but_not_strong_data():
    recommendation = recommend_unit_price(make_stats(sample_count=7, median=18000.0, recent_median=18500.0, outlier_ratio=0.12, verified_sample_count=7, q1=16000.0, q3=21000.0))
    assert recommendation.confidence == "MEDIUM"


def test_low_confidence_for_weaker_quality_data():
    recommendation = recommend_unit_price(make_stats(sample_count=6, median=18000.0, recent_median=20000.0, outlier_ratio=0.3, verified_sample_count=6, q1=15000.0, q3=22000.0))
    assert recommendation.confidence == "LOW"


def test_insufficient_confidence_for_zero_samples():
    recommendation = recommend_unit_price(make_stats(sample_count=0, median=None, q1=None, q3=None, verified_sample_count=0))
    assert recommendation.confidence == "INSUFFICIENT"


def test_high_outlier_ratio_reduces_confidence_and_requires_review():
    recommendation = recommend_unit_price(make_stats(sample_count=12, median=18000.0, outlier_ratio=0.35, verified_sample_count=12))
    assert recommendation.confidence in {"LOW", "INSUFFICIENT"}
    assert recommendation.human_review_required is True


def test_single_vendor_sets_risk_flag_in_reason():
    recommendation = recommend_unit_price(make_stats(sample_count=10, median=18000.0, verified_sample_count=10, q1=16000.0, q3=21000.0), vendor_count=1)
    assert "single vendor" in recommendation.reason.lower()
    assert recommendation.human_review_required is True


def test_multiple_vendors_do_not_trigger_single_vendor_risk():
    recommendation = recommend_unit_price(make_stats(sample_count=10, median=18000.0, verified_sample_count=10, q1=16000.0, q3=21000.0), vendor_count=4)
    assert 'single vendor' not in recommendation.reason.lower()


def test_missing_vendor_count_is_allowed():
    recommendation = recommend_unit_price(make_stats(sample_count=10, median=18000.0, verified_sample_count=10, q1=16000.0, q3=21000.0), vendor_count=None)
    assert recommendation.vendor_count is None
    assert recommendation.confidence in {"HIGH", "MEDIUM"}


def test_missing_recent_median_uses_historical_only():
    recommendation = recommend_unit_price(make_stats(sample_count=10, median=18000.0, recent_median=None, verified_sample_count=10, outlier_ratio=0.05, q1=16000.0, q3=21000.0))
    assert recommendation.recommended_unit_price == 18000.0
    assert "historical median" in recommendation.reason.lower()


def test_large_historical_recent_gap_is_recorded_in_reason():
    recommendation = recommend_unit_price(make_stats(sample_count=12, median=18000.0, recent_median=26000.0, verified_sample_count=12))
    assert "differs materially" in recommendation.reason.lower()


def test_large_weighted_mean_gap_reduces_confidence_or_adds_reason():
    recommendation = recommend_unit_price(make_stats(sample_count=12, median=18000.0, weighted_mean=24500.0, recent_median=18500.0, verified_sample_count=12))
    assert "weighted mean" in recommendation.reason.lower()
    assert recommendation.human_review_required is True


def test_human_review_required_by_default_for_any_recommendation():
    recommendation = recommend_unit_price(make_stats(sample_count=12, median=18000.0, verified_sample_count=12))
    assert recommendation.human_review_required is True


def test_unit_is_preserved_in_recommendation():
    recommendation = recommend_unit_price(make_stats(sample_count=10, median=18000.0, unit='EA', verified_sample_count=10))
    assert recommendation.unit == 'EA'


def test_raw_source_data_is_not_modified():
    stats = make_stats(sample_count=12, median=18000.0, recent_median=18500.0, verified_sample_count=12)
    original = stats.median
    recommendation = recommend_unit_price(stats)
    assert stats.median == original
    assert recommendation.historical_median == original
    assert recommendation.base_unit_price == 18200.0


def test_price_recommendation_dto_serializes_cleanly():
    recommendation = recommend_unit_price(make_stats(sample_count=12, median=18000.0, recent_median=18500.0, verified_sample_count=12))
    payload = recommendation.model_dump()
    assert payload["work_type_code"] == "MASONRY"
    assert payload["recommended_unit_price"] == 18200.0
    assert payload["confidence"] in {"HIGH", "MEDIUM", "LOW", "INSUFFICIENT"}


def test_calculate_confidence_score_returns_float_between_zero_and_one():
    score = calculate_confidence(make_stats(sample_count=10, median=18000.0, verified_sample_count=10, outlier_ratio=0.08, q1=16000.0, q3=21000.0), vendor_count=4)
    assert 0.0 <= score <= 1.0


def test_calculate_price_range_uses_q1_and_q3():
    low, base, high = calculate_price_range(make_stats(sample_count=12, median=18000.0, q1=16000.0, q3=21000.0))
    assert low == 16000.0
    assert base == 18000.0
    assert high == 21000.0


def test_build_recommendation_reason_contains_explanation():
    reason = build_recommendation_reason(
        make_stats(sample_count=12, median=18000.0, recent_median=18500.0, outlier_ratio=0.08, verified_sample_count=12),
        recommendation_price=18100.0,
        historical_median=18000.0,
        recent_median=18500.0,
        weighted_mean=17600.0,
        confidence_label="HIGH",
        vendor_count=4,
    )
    assert "historical median" in reason.lower()
    assert "recent median" in reason.lower()
    assert "outlier" in reason.lower()
