from datetime import datetime

from sqlmodel import SQLModel


class EstimateDocumentCreateRequest(SQLModel):
    source_filename: str
    file_hash: str
    source_type: str
    time_category: str = "CURRENT"

    vendor_name: str | None = None
    project_code: str | None = None
    project_name: str | None = None
    quote_number: str | None = None
    quote_date: str | None = None
    site: str | None = None
    project_type: str | None = None

    source_storage_type: str = "LOCAL"
    source_file_path: str | None = None

    extraction_status: str = "PENDING"
    verification_status: str = "NEEDS_REVIEW"
    quality_status: str = "RAW"

    uploaded_by: str | None = None
    notes: str | None = None


class EstimateDocumentRead(SQLModel):
    id: int
    source_filename: str
    file_hash: str
    source_type: str
    time_category: str

    vendor_name: str | None = None
    project_code: str | None = None
    project_name: str | None = None
    quote_number: str | None = None
    quote_date: str | None = None
    site: str | None = None
    project_type: str | None = None

    source_storage_type: str
    source_file_path: str | None = None

    extraction_status: str
    verification_status: str
    quality_status: str

    notes: str | None = None

    upload_timestamp: datetime
    created_at: datetime
    updated_at: datetime


class EstimateDocumentListResponse(SQLModel):
    count: int
    records: list[EstimateDocumentRead]


class EstimateDocumentUploadResponse(SQLModel):
    document_id: int
    filename: str
    source_type: str
    project_code: str | None = None
    vendor_name: str | None = None
    quote_date: str | None = None
    verification_status: str
    duplicate: bool = False
    existing_document_id: int | None = None


class QuoteItemCreateRequest(SQLModel):
    raw_description: str
    quantity: float | None = None
    unit: str | None = None
    amount: float | None = None

    source_unit_price: float | None = None
    normalized_unit_price: float | None = None

    normalized_description: str | None = None
    work_type_code: str | None = None
    mapping_confidence: float | None = None
    mapping_method: str | None = None

    item_name: str | None = None
    material_name: str | None = None
    labor_name: str | None = None

    manufacturer: str | None = None
    model_number: str | None = None
    vendor_name: str | None = None

    quoted_person_days: float | None = None
    quoted_workers: float | None = None
    quoted_work_minutes: float | None = None
    quoted_labor_amount: float | None = None

    labor_data_source: str = "QUOTED_LABOR"
    quality_status: str = "AI_EXTRACTED"

    notes: str | None = None


class QuoteItemVerifyRequest(SQLModel):
    reviewer: str
    verification_status: str

    normalized_description: str | None = None
    work_type_code: str | None = None
    mapping_confidence: float | None = None
    mapping_method: str | None = None

    normalized_unit_price: float | None = None
    quality_status: str | None = None

    comment: str | None = None


class QuoteItemRead(SQLModel):
    id: int
    document_id: int
    line_number: int

    raw_description: str
    normalized_description: str | None = None

    work_type_code: str | None = None
    mapping_confidence: float | None = None
    mapping_method: str | None = None
    mapping_verification_status: str

    item_name: str | None = None
    material_name: str | None = None
    labor_name: str | None = None

    quantity: float | None = None
    unit: str | None = None
    amount: float | None = None

    source_unit_price: float | None = None
    calculated_unit_price: float | None = None
    normalized_unit_price: float | None = None

    currency: str

    manufacturer: str | None = None
    model_number: str | None = None
    vendor_name: str | None = None

    quoted_person_days: float | None = None
    quoted_workers: float | None = None
    quoted_work_minutes: float | None = None
    quoted_labor_amount: float | None = None
    labor_data_source: str

    quality_status: str
    verification_status: str

    notes: str | None = None
    review_comment: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


class QuoteItemListResponse(SQLModel):
    count: int
    records: list[QuoteItemRead]


class TextExtractionRunResponse(SQLModel):
    document_id: int
    extraction_id: int
    extraction_status: str
    requires_ocr: bool
    extracted_text_length: int


class EstimateDocumentRawExtractionRead(SQLModel):
    id: int
    document_id: int
    stage: str
    extraction_status: str
    requires_ocr: bool
    extractor_name: str | None = None
    extractor_version: str | None = None
    raw_text: str
    raw_payload: str | None = None
    created_at: datetime


class EstimateDocumentRawExtractionListResponse(SQLModel):
    count: int
    records: list[EstimateDocumentRawExtractionRead]
