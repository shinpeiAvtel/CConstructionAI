from datetime import date, datetime

from sqlmodel import SQLModel


# =========================================================
# Analysis DTO / Response Contracts
# =========================================================
# These are response-only contracts. They are intentionally NOT
# table-backed models and are not used for persistence.
#
# Future service boundary:
# - EstimateAnalysisService.build_document_summary()
# - EstimateAnalysisService.build_quote_item_analysis()
# - EstimateAnalysisService.build_verification_summary()
# - StatisticsService.calculate_iqr()
# - StatisticsService.detect_outliers()
# - StatisticsService.calculate_price_statistics()
# - LaborAnalysisService.analyze_quoted_labor()
# - LaborAnalysisService.analyze_actual_work()
# - LaborAnalysisService.compare_labor()
# - RecommendationService.recommend_unit_price()
# - ExcelAnalysisExportService (future)
# =========================================================


class DocumentSummary(SQLModel):
    document_id: int
    source_filename: str
    source_type: str
    vendor_name: str | None = None
    project_code: str | None = None
    quote_number: str | None = None
    quote_date: str | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    uploaded_at: datetime | None = None
    verification_status: str


class QuoteItemAnalysis(SQLModel):
    quote_item_id: int
    line_number: int | None = None

    raw_description: str
    normalized_description: str | None = None

    work_type_code: str | None = None
    work_type_name: str | None = None
    category: str | None = None
    sub_category: str | None = None

    manufacturer: str | None = None
    model_number: str | None = None

    quantity: float | None = None
    unit: str | None = None

    source_unit_price: float | None = None
    calculated_unit_price: float | None = None
    normalized_unit_price: float | None = None

    source_amount: float | None = None
    calculated_amount: float | None = None

    quoted_person_days: float | None = None
    quoted_labor_amount: float | None = None

    mapping_confidence: float | None = None
    verification_status: str

    is_outlier: bool = False
    outlier_reason: str | None = None


class WorkTypePriceStatistics(SQLModel):
    work_type_code: str
    work_type_name: str | None = None
    unit: str | None = None

    sample_count: int = 0

    minimum: float | None = None
    maximum: float | None = None
    mean: float | None = None
    median: float | None = None
    weighted_mean: float | None = None
    standard_deviation: float | None = None

    q1: float | None = None
    q3: float | None = None
    iqr: float | None = None

    lower_bound: float | None = None
    upper_bound: float | None = None

    outlier_count: int = 0
    outlier_ratio: float | None = None

    recent_median: float | None = None
    analysis_period: str | None = None

    verified_sample_count: int = 0
    unverified_sample_count: int = 0
    excluded_sample_count: int = 0


class PriceRecommendation(SQLModel):
    work_type_code: str
    unit: str | None = None

    historical_mean: float | None = None
    historical_median: float | None = None
    recent_median: float | None = None

    recommended_unit_price: float | None = None

    low_unit_price: float | None = None
    base_unit_price: float | None = None
    high_unit_price: float | None = None

    confidence: str
    confidence_score: float | None = None
    reason: str | None = None

    sample_count: int = 0
    vendor_count: int | None = None
    outlier_ratio: float | None = None

    human_review_required: bool = True


class LaborAnalysisResult(SQLModel):
    work_type_code: str
    labor_code: str | None = None
    unit: str | None = None

    current_standard_labor: float | None = None

    quoted_labor_sample_count: int = 0
    quoted_labor_mean: float | None = None
    quoted_labor_median: float | None = None

    actual_work_sample_count: int = 0
    actual_work_mean: float | None = None
    actual_work_median: float | None = None

    recommended_labor_candidate: float | None = None
    difference_from_current_percent: float | None = None

    confidence: str
    reason: str | None = None
    human_review_required: bool = True


class VerificationSummary(SQLModel):
    total_items: int = 0
    verified_items: int = 0
    needs_review_items: int = 0
    unmapped_items: int = 0
    rejected_items: int = 0

    average_mapping_confidence: float | None = None

    analysis_eligible_items: int = 0
    excluded_items: int = 0


class AnalysisMetadata(SQLModel):
    analysis_version: str
    analyzed_at: datetime
    document_id: int

    date_from: date | None = None
    date_to: date | None = None

    verification_filter: str | None = None
    source_type_filter: str | None = None
    vendor_filter: str | None = None
    project_filter: str | None = None

    included_samples: int = 0
    excluded_samples: int = 0

    outlier_method: str


class DocumentAnalysisResult(SQLModel):
    document: DocumentSummary
    items: list[QuoteItemAnalysis]
    work_type_analysis: list[WorkTypePriceStatistics]
    price_recommendations: list[PriceRecommendation]
    labor_analysis: list[LaborAnalysisResult]
    verification_summary: VerificationSummary
    metadata: AnalysisMetadata
    outliers: list[QuoteItemAnalysis] | None = None


__all__ = [
    "DocumentSummary",
    "QuoteItemAnalysis",
    "WorkTypePriceStatistics",
    "PriceRecommendation",
    "LaborAnalysisResult",
    "VerificationSummary",
    "AnalysisMetadata",
    "DocumentAnalysisResult",
]
