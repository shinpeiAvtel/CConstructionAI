from backend.services.labor_analysis_service import (
    analyze_actual_work,
    analyze_quoted_labor,
    build_labor_analysis_result,
    calculate_revision_eligibility,
    compare_labor,
    recommend_labor_candidate,
)


def make_quote_item(**overrides):
    data = {
        "id": 1,
        "document_id": 1,
        "line_number": 1,
        "raw_description": "Install card reader",
        "work_type_code": "ACS-01",
        "quantity": 10.0,
        "unit": "SET",
        "verification_status": "VERIFIED",
        "quoted_person_days": 2.0,
        "quoted_labor_amount": 120000.0,
    }
    data.update(overrides)
    return type("Item", (), data)()


def make_actual_record(**overrides):
    data = {
        "id": 1,
        "project_code": "PRJ-1",
        "labor_code": "LAB-1",
        "quantity": 10.0,
        "workers": 2.0,
        "work_minutes": 480.0,
        "work_date": "2024-01-01",
        "site_condition": "NORMAL",
    }
    data.update(overrides)
    return type("Record", (), data)()


def test_no_quoted_samples_returns_empty_stats():
    result = analyze_quoted_labor([])
    assert result["sample_count"] == 0
    assert result["mean"] is None
    assert result["median"] is None


def test_no_actual_samples_returns_empty_stats():
    result = analyze_actual_work([], minutes_per_person_day=480)
    assert result["sample_count"] == 0
    assert result["mean"] is None
    assert result["median"] is None


def test_quoted_only_calculation():
    result = analyze_quoted_labor([make_quote_item(quoted_person_days=2.0, quantity=10.0)])
    assert result["sample_count"] == 1
    assert result["mean"] == 0.2
    assert result["median"] == 0.2


def test_actual_only_calculation():
    result = analyze_actual_work([make_actual_record(quantity=10.0, workers=2.0, work_minutes=480.0)], minutes_per_person_day=480)
    assert result["sample_count"] == 1
    assert result["mean"] == 0.2
    assert result["median"] == 0.2


def test_quoted_and_actual_are_compared():
    quoted = analyze_quoted_labor([make_quote_item(quoted_person_days=2.0, quantity=10.0)])
    actual = analyze_actual_work([make_actual_record(quantity=10.0, workers=2.0, work_minutes=480.0)], minutes_per_person_day=480)
    compared = compare_labor(quoted, actual, current_standard_labor=0.08)
    assert compared["current_standard_labor"] == 0.08
    assert compared["quoted_median"] == 0.2
    assert compared["actual_median"] == 0.2


def test_current_standard_only_sets_no_candidate():
    comparison = compare_labor({"sample_count": 0, "mean": None, "median": None}, {"sample_count": 0, "mean": None, "median": None}, current_standard_labor=0.08)
    candidate = recommend_labor_candidate(comparison)
    assert candidate is None


def test_actual_median_is_preferred_candidate():
    comparison = {
        "current_standard_labor": 0.08,
        "quoted_median": 0.07,
        "actual_median": 0.09,
        "quoted_sample_count": 10,
        "actual_sample_count": 12,
    }
    candidate = recommend_labor_candidate(comparison)
    assert candidate == 0.09


def test_quoted_median_fallback_when_actual_is_insufficient():
    comparison = {
        "current_standard_labor": 0.08,
        "quoted_median": 0.07,
        "actual_median": None,
        "quoted_sample_count": 12,
        "actual_sample_count": 2,
    }
    candidate = recommend_labor_candidate(comparison)
    assert candidate == 0.07


def test_no_candidate_when_samples_are_insufficient():
    comparison = {
        "current_standard_labor": 0.08,
        "quoted_median": 0.07,
        "actual_median": None,
        "quoted_sample_count": 2,
        "actual_sample_count": 1,
    }
    candidate = recommend_labor_candidate(comparison)
    assert candidate is None


def test_difference_from_current_percent_is_calculated():
    comparison = {
        "current_standard_labor": 0.08,
        "quoted_median": 0.07,
        "actual_median": 0.09,
        "quoted_sample_count": 10,
        "actual_sample_count": 12,
    }
    candidate = recommend_labor_candidate(comparison)
    diff = (candidate - comparison["current_standard_labor"]) / comparison["current_standard_labor"] * 100
    assert abs(diff - 12.5) < 1e-9


def test_missing_current_standard_returns_none_difference():
    comparison = {
        "current_standard_labor": None,
        "quoted_median": 0.07,
        "actual_median": 0.09,
        "quoted_sample_count": 10,
        "actual_sample_count": 12,
    }
    candidate = recommend_labor_candidate(comparison)
    assert candidate == 0.09
    assert compare_labor({"sample_count": 0, "mean": None, "median": None}, {"sample_count": 0, "mean": None, "median": None}, current_standard_labor=None)["difference_from_current_percent"] is None


def test_different_units_are_kept_separate():
    quoted = analyze_quoted_labor([make_quote_item(unit="SET", quoted_person_days=2.0, quantity=10.0), make_quote_item(unit="EA", quoted_person_days=3.0, quantity=5.0)])
    assert quoted["unit_groups"] == 2


def test_verified_quotes_only_are_used():
    quoted = analyze_quoted_labor([
        make_quote_item(verification_status="VERIFIED", quoted_person_days=2.0, quantity=10.0),
        make_quote_item(verification_status="NEEDS_REVIEW", quoted_person_days=5.0, quantity=10.0),
    ])
    assert quoted["sample_count"] == 1


def test_actual_iqr_outlier_is_preserved_without_removing_source_data():
    actual = analyze_actual_work([
        make_actual_record(id=1, quantity=10.0, workers=1.0, work_minutes=120.0),
        make_actual_record(id=2, quantity=10.0, workers=1.0, work_minutes=120.0),
        make_actual_record(id=3, quantity=10.0, workers=1.0, work_minutes=130.0),
        make_actual_record(id=4, quantity=10.0, workers=1.0, work_minutes=140.0),
        make_actual_record(id=5, quantity=10.0, workers=1.0, work_minutes=150.0),
        make_actual_record(id=6, quantity=10.0, workers=10.0, work_minutes=1200.0),
    ], minutes_per_person_day=480)
    assert actual["sample_count"] == 6
    assert actual["outlier_count"] >= 0


def test_revision_eligibility_is_false_for_small_sample():
    result = calculate_revision_eligibility(2, 20.0, 10.0, 0.1)
    assert result["eligible"] is False
    assert "Insufficient valid sample count" in result["reasons"][0]


def test_revision_eligibility_is_true_for_strong_data():
    result = calculate_revision_eligibility(10, 20.0, 10.0, 0.1)
    assert result["eligible"] is True


def test_build_labor_analysis_result_uses_derived_candidates_and_reason():
    quoted = analyze_quoted_labor([make_quote_item(quoted_person_days=2.0, quantity=10.0)])
    actual = analyze_actual_work([make_actual_record(quantity=10.0, workers=2.0, work_minutes=480.0)], minutes_per_person_day=480)
    result = build_labor_analysis_result(
        work_type_code="ACS-01",
        labor_code="LAB-1",
        unit="SET",
        quoted_labor=quoted,
        actual_work=actual,
        current_standard_labor=0.08,
        minutes_per_person_day=480,
    )
    assert result.work_type_code == "ACS-01"
    assert result.labor_code == "LAB-1"
    assert result.human_review_required is True
    assert result.confidence in {"HIGH", "MEDIUM", "LOW", "INSUFFICIENT"}
