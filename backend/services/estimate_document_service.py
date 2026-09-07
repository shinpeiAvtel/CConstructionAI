from datetime import UTC, datetime
import hashlib
from pathlib import Path
import re

from fastapi import HTTPException
from sqlmodel import select
from sqlmodel import Session

from backend.database import DATA_DIR
from backend.models import (
    AuditLog,
    EstimateDocument,
    EstimateDocumentRawExtraction,
    QuoteItem,
    WorkTypeMaster,
)
from backend.repositories import estimate_document_repository
from backend.schemas.estimate_document_schema import (
    EstimateDocumentCreateRequest,
    QuoteItemCreateRequest,
    QuoteItemVerifyRequest,
)


ALLOWED_SOURCE_TYPES = {
    "INTERNAL_ESTIMATE",
    "VENDOR_QUOTE",
    "SUBCONTRACTOR_QUOTE",
    "SUPPLIER_QUOTE",
    "CUSTOMER_QUOTE",
    "OTHER",
}

ALLOWED_TIME_CATEGORIES = {
    "HISTORICAL",
    "CURRENT",
    "FUTURE",
}

ALLOWED_EXTRACTION_STATUSES = {
    "PENDING",
    "TEXT_EXTRACTED",
    "TABLE_DETECTED",
    "STRUCTURED",
    "NORMALIZED",
    "MAPPED",
    "NEEDS_REVIEW",
    "VERIFIED",
    "FAILED",
}

ALLOWED_VERIFICATION_STATUSES = {
    "NEEDS_REVIEW",
    "VERIFIED",
    "REJECTED",
}

ALLOWED_QUALITY_STATUSES = {
    "RAW",
    "AI_EXTRACTED",
    "NEEDS_REVIEW",
    "VERIFIED",
    "REJECTED",
}

ALLOWED_LABOR_DATA_SOURCES = {
    "QUOTED_LABOR",
    "ACTUAL_WORK",
}

LOW_CONFIDENCE_THRESHOLD = 0.5

TEXT_EXTRACTOR_NAME = "builtin_pdf_text_parser"
TEXT_EXTRACTOR_VERSION = "v1"

ESTIMATE_DOCUMENT_UPLOAD_DIR = DATA_DIR / "uploads" / "estimate_documents"
MAX_UPLOAD_SIZE_MB = 25
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _sanitize_uploaded_filename(filename: str) -> str:
    candidate = Path(filename).name.replace("\\", "/")
    candidate = candidate.rsplit("/", 1)[-1]
    candidate = re.sub(r"[^A-Za-z0-9._-]", "_", candidate)
    candidate = candidate.strip("._ ") or "document.pdf"
    if not candidate.lower().endswith(".pdf"):
        candidate = f"{candidate}.pdf"
    return candidate


def _normalize_upper(value: str) -> str:
    return value.strip().upper()


def _validate_in_set(value: str, allowed: set[str], field_name: str):
    if value not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name}: {value}",
        )


def _extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    # Stage 1 heuristic extraction for text-based PDFs.
    # OCR integration is intentionally deferred to a later phase.
    decoded = file_bytes.decode("latin-1", errors="ignore")

    segments: list[str] = []

    segments.extend(
        re.findall(r"\((.*?)\)\s*Tj", decoded, flags=re.DOTALL)
    )

    array_matches = re.findall(
        r"\[(.*?)\]\s*TJ",
        decoded,
        flags=re.DOTALL,
    )

    for array_block in array_matches:
        segments.extend(
            re.findall(r"\((.*?)\)", array_block, flags=re.DOTALL)
        )

    cleaned: list[str] = []
    for segment in segments:
        unescaped = re.sub(r"\\([()\\])", r"\1", segment)
        normalized = re.sub(r"\s+", " ", unescaped).strip()
        if normalized:
            cleaned.append(normalized)

    return "\n".join(cleaned)


def upload_estimate_pdf(
    *,
    session: Session,
    filename: str,
    content_type: str | None,
    file_bytes: bytes,
    source_type: str,
    time_category: str = "CURRENT",
    vendor_name: str | None = None,
    project_code: str | None = None,
    project_name: str | None = None,
    quote_number: str | None = None,
    quote_date: str | None = None,
    site: str | None = None,
    project_type: str | None = None,
    uploaded_by: str | None = None,
    notes: str | None = None,
    storage_dir: Path | None = None,
) -> EstimateDocument:
    if not filename or not filename.strip():
        raise HTTPException(
            status_code=400,
            detail="filename is required.",
        )

    if content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty.",
        )

    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded PDF exceeds the {MAX_UPLOAD_SIZE_MB} MB limit.",
        )

    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid PDF.",
        )

    safe_original_name = _sanitize_uploaded_filename(filename)

    if not safe_original_name.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="File extension must be .pdf.",
        )

    file_hash = hashlib.sha256(file_bytes).hexdigest()

    duplicate = estimate_document_repository.get_document_by_hash(
        session,
        file_hash,
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=(
                "Duplicate document detected by file_hash. "
                f"Existing document_id: {duplicate.id}"
            ),
        )

    target_dir = storage_dir or ESTIMATE_DOCUMENT_UPLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    file_name = f"{timestamp}_{file_hash[:12]}_{safe_original_name}"
    destination = target_dir / file_name
    destination.write_bytes(file_bytes)

    document = create_estimate_document(
        EstimateDocumentCreateRequest(
            source_filename=safe_original_name,
            file_hash=file_hash,
            source_type=source_type,
            time_category=time_category,
            vendor_name=vendor_name,
            project_code=project_code,
            project_name=project_name,
            quote_number=quote_number,
            quote_date=quote_date,
            site=site,
            project_type=project_type,
            source_storage_type="LOCAL",
            source_file_path=str(destination.as_posix()),
            extraction_status="PENDING",
            verification_status="NEEDS_REVIEW",
            quality_status="RAW",
            uploaded_by=uploaded_by,
            notes=notes,
        ),
        session,
    )

    upload_audit = AuditLog(
        action="ESTIMATE_DOCUMENT_UPLOADED",
        entity_type="EstimateDocument",
        entity_id=document.id,
        actor=(uploaded_by or "system"),
        comment=f"file_hash={file_hash}",
    )

    session.add(upload_audit)
    session.commit()

    return document


def run_text_extraction(
    document_id: int,
    session: Session,
    actor: str | None = None,
):
    document = estimate_document_repository.get_document_by_id(session, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Estimate document not found.",
        )

    if document.source_storage_type != "LOCAL":
        raise HTTPException(
            status_code=400,
            detail="Text extraction currently supports LOCAL storage only.",
        )

    if not document.source_file_path:
        raise HTTPException(
            status_code=400,
            detail="Document source_file_path is empty.",
        )

    source_path = Path(document.source_file_path)
    if not source_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Stored PDF file not found.",
        )

    file_bytes = source_path.read_bytes()
    raw_text = _extract_text_from_pdf_bytes(file_bytes)

    requires_ocr = len(raw_text.strip()) == 0

    extraction_status = "NEEDS_OCR" if requires_ocr else "TEXT_EXTRACTED"
    document_status = "NEEDS_REVIEW" if requires_ocr else "TEXT_EXTRACTED"

    extraction = estimate_document_repository.create_raw_extraction(
        session,
        EstimateDocumentRawExtraction(
            document_id=document.id,
            stage="TEXT_EXTRACTION",
            extraction_status=extraction_status,
            requires_ocr=requires_ocr,
            extractor_name=TEXT_EXTRACTOR_NAME,
            extractor_version=TEXT_EXTRACTOR_VERSION,
            raw_text=raw_text,
            raw_payload=None,
            created_at=datetime.now(),
        ),
    )

    document.extraction_status = document_status
    document.updated_at = datetime.now()
    estimate_document_repository.save_document(session, document)

    audit_action = "ESTIMATE_TEXT_EXTRACTION_NEEDS_OCR" if requires_ocr else "ESTIMATE_TEXT_EXTRACTED"
    audit = AuditLog(
        action=audit_action,
        entity_type="EstimateDocument",
        entity_id=document.id,
        actor=(actor or "system"),
        comment=(
            f"extraction_id={extraction.id}; "
            f"text_length={len(raw_text)}"
        ),
    )
    session.add(audit)
    session.commit()

    return {
        "document_id": document.id,
        "extraction_id": extraction.id,
        "extraction_status": extraction.extraction_status,
        "requires_ocr": extraction.requires_ocr,
        "extracted_text_length": len(raw_text),
    }


def list_raw_extractions(
    document_id: int,
    session: Session,
    stage: str | None = None,
):
    document = estimate_document_repository.get_document_by_id(session, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Estimate document not found.",
        )

    normalized_stage = _normalize_upper(stage) if stage else None

    return estimate_document_repository.list_raw_extractions(
        session,
        document_id,
        normalized_stage,
    )


def create_estimate_document(
    request: EstimateDocumentCreateRequest,
    session: Session,
) -> EstimateDocument:
    file_hash = request.file_hash.strip().lower()

    if not file_hash:
        raise HTTPException(
            status_code=400,
            detail="file_hash is required.",
        )

    source_type = _normalize_upper(request.source_type)
    time_category = _normalize_upper(request.time_category)
    extraction_status = _normalize_upper(request.extraction_status)
    verification_status = _normalize_upper(request.verification_status)
    quality_status = _normalize_upper(request.quality_status)

    _validate_in_set(source_type, ALLOWED_SOURCE_TYPES, "source_type")
    _validate_in_set(time_category, ALLOWED_TIME_CATEGORIES, "time_category")
    _validate_in_set(
        extraction_status,
        ALLOWED_EXTRACTION_STATUSES,
        "extraction_status",
    )
    _validate_in_set(
        verification_status,
        ALLOWED_VERIFICATION_STATUSES,
        "verification_status",
    )
    _validate_in_set(quality_status, ALLOWED_QUALITY_STATUSES, "quality_status")

    duplicate = estimate_document_repository.get_document_by_hash(
        session,
        file_hash,
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=(
                "Duplicate document detected by file_hash. "
                f"Existing document_id: {duplicate.id}"
            ),
        )

    now = datetime.now()

    item = EstimateDocument(
        source_filename=request.source_filename,
        file_hash=file_hash,
        source_type=source_type,
        time_category=time_category,
        vendor_name=request.vendor_name,
        project_code=request.project_code,
        project_name=request.project_name,
        quote_number=request.quote_number,
        quote_date=request.quote_date,
        site=request.site,
        project_type=request.project_type,
        source_storage_type=request.source_storage_type,
        source_file_path=request.source_file_path,
        extraction_status=extraction_status,
        verification_status=verification_status,
        quality_status=quality_status,
        notes=request.notes,
        upload_timestamp=now,
        created_at=now,
        updated_at=now,
    )

    created = estimate_document_repository.create_document(session, item)

    audit = AuditLog(
        action="ESTIMATE_DOCUMENT_CREATED",
        entity_type="EstimateDocument",
        entity_id=created.id,
        actor=(request.uploaded_by or "system"),
        comment=f"source_filename={created.source_filename}",
    )

    session.add(audit)
    session.commit()

    return created


def list_estimate_documents(
    session: Session,
    source_type: str | None,
    time_category: str | None,
    verification_status: str | None,
) -> list[EstimateDocument]:
    normalized_source_type = _normalize_upper(source_type) if source_type else None
    normalized_time_category = _normalize_upper(time_category) if time_category else None
    normalized_verification_status = (
        _normalize_upper(verification_status) if verification_status else None
    )

    if normalized_source_type:
        _validate_in_set(
            normalized_source_type,
            ALLOWED_SOURCE_TYPES,
            "source_type",
        )

    if normalized_time_category:
        _validate_in_set(
            normalized_time_category,
            ALLOWED_TIME_CATEGORIES,
            "time_category",
        )

    if normalized_verification_status:
        _validate_in_set(
            normalized_verification_status,
            ALLOWED_VERIFICATION_STATUSES,
            "verification_status",
        )

    return estimate_document_repository.list_documents(
        session,
        normalized_source_type,
        normalized_time_category,
        normalized_verification_status,
    )


def create_quote_item(
    document_id: int,
    request: QuoteItemCreateRequest,
    session: Session,
) -> QuoteItem:
    document = estimate_document_repository.get_document_by_id(session, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Estimate document not found.",
        )

    if not request.raw_description.strip():
        raise HTTPException(
            status_code=400,
            detail="raw_description is required.",
        )

    labor_data_source = _normalize_upper(request.labor_data_source)
    _validate_in_set(
        labor_data_source,
        ALLOWED_LABOR_DATA_SOURCES,
        "labor_data_source",
    )

    quality_status = _normalize_upper(request.quality_status)
    _validate_in_set(quality_status, ALLOWED_QUALITY_STATUSES, "quality_status")

    if request.mapping_confidence is not None:
        if request.mapping_confidence < 0 or request.mapping_confidence > 1:
            raise HTTPException(
                status_code=400,
                detail="mapping_confidence must be between 0 and 1.",
            )

    if request.quantity is not None and request.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="quantity cannot be negative.",
        )

    if request.amount is not None and request.amount < 0:
        raise HTTPException(
            status_code=400,
            detail="amount cannot be negative.",
        )

    if request.work_type_code:
        work_type = session.exec(
            select(WorkTypeMaster).where(
                WorkTypeMaster.work_type_code == request.work_type_code.strip().upper()
            )
        ).first()
        if not work_type:
            raise HTTPException(
                status_code=404,
                detail="work_type_code not found in WorkTypeMaster.",
            )

    line_number = estimate_document_repository.get_next_line_number(
        session,
        document_id,
    )

    calculated_unit_price = None
    if (
        request.amount is not None
        and request.quantity is not None
        and request.quantity > 0
    ):
        calculated_unit_price = request.amount / request.quantity

    mapping_verification_status = "NEEDS_REVIEW"

    now = datetime.now()

    item = QuoteItem(
        document_id=document_id,
        line_number=line_number,
        raw_description=request.raw_description,
        normalized_description=request.normalized_description,
        work_type_code=(request.work_type_code.strip().upper() if request.work_type_code else None),
        mapping_confidence=request.mapping_confidence,
        mapping_method=request.mapping_method,
        mapping_verification_status=mapping_verification_status,
        item_name=request.item_name,
        material_name=request.material_name,
        labor_name=request.labor_name,
        quantity=request.quantity,
        unit=request.unit,
        amount=request.amount,
        source_unit_price=request.source_unit_price,
        calculated_unit_price=calculated_unit_price,
        normalized_unit_price=request.normalized_unit_price,
        manufacturer=request.manufacturer,
        model_number=request.model_number,
        vendor_name=request.vendor_name,
        quoted_person_days=request.quoted_person_days,
        quoted_workers=request.quoted_workers,
        quoted_work_minutes=request.quoted_work_minutes,
        quoted_labor_amount=request.quoted_labor_amount,
        labor_data_source=labor_data_source,
        quality_status=quality_status,
        verification_status="NEEDS_REVIEW",
        notes=request.notes,
        created_at=now,
        updated_at=now,
    )

    return estimate_document_repository.create_quote_item(session, item)


def list_quote_items(
    document_id: int,
    verification_status: str | None,
    session: Session,
) -> list[QuoteItem]:
    document = estimate_document_repository.get_document_by_id(session, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Estimate document not found.",
        )

    normalized_verification_status = (
        _normalize_upper(verification_status) if verification_status else None
    )

    if normalized_verification_status:
        _validate_in_set(
            normalized_verification_status,
            ALLOWED_VERIFICATION_STATUSES,
            "verification_status",
        )

    return estimate_document_repository.list_quote_items(
        session,
        document_id,
        normalized_verification_status,
    )


def verify_quote_item(
    item_id: int,
    request: QuoteItemVerifyRequest,
    session: Session,
) -> QuoteItem:
    item = estimate_document_repository.get_quote_item_by_id(session, item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Quote item not found.",
        )

    new_verification_status = _normalize_upper(request.verification_status)
    _validate_in_set(
        new_verification_status,
        ALLOWED_VERIFICATION_STATUSES,
        "verification_status",
    )

    if request.mapping_confidence is not None:
        if request.mapping_confidence < 0 or request.mapping_confidence > 1:
            raise HTTPException(
                status_code=400,
                detail="mapping_confidence must be between 0 and 1.",
            )
        item.mapping_confidence = request.mapping_confidence

    if request.work_type_code:
        normalized_work_type_code = request.work_type_code.strip().upper()
        work_type = session.exec(
            select(WorkTypeMaster).where(
                WorkTypeMaster.work_type_code == normalized_work_type_code
            )
        ).first()
        if not work_type:
            raise HTTPException(
                status_code=404,
                detail="work_type_code not found in WorkTypeMaster.",
            )
        item.work_type_code = normalized_work_type_code

    if request.normalized_description is not None:
        item.normalized_description = request.normalized_description

    if request.mapping_method is not None:
        item.mapping_method = request.mapping_method

    if request.normalized_unit_price is not None:
        item.normalized_unit_price = request.normalized_unit_price

    if request.quality_status is not None:
        normalized_quality_status = _normalize_upper(request.quality_status)
        _validate_in_set(
            normalized_quality_status,
            ALLOWED_QUALITY_STATUSES,
            "quality_status",
        )
        item.quality_status = normalized_quality_status

    confidence_value = item.mapping_confidence
    if (
        new_verification_status == "VERIFIED"
        and confidence_value is not None
        and confidence_value < LOW_CONFIDENCE_THRESHOLD
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Low confidence mapping cannot be directly VERIFIED. "
                "Keep NEEDS_REVIEW or update confidence after human check."
            ),
        )

    item.verification_status = new_verification_status
    item.mapping_verification_status = new_verification_status
    item.reviewed_by = request.reviewer
    item.review_comment = request.comment
    item.reviewed_at = datetime.now()
    item.updated_at = datetime.now()

    saved = estimate_document_repository.save_quote_item(session, item)

    audit = AuditLog(
        action="QUOTE_ITEM_VERIFIED",
        entity_type="QuoteItem",
        entity_id=saved.id,
        actor=request.reviewer,
        comment=(
            f"verification_status={saved.verification_status}; "
            f"work_type_code={saved.work_type_code}"
        ),
    )

    session.add(audit)
    session.commit()

    return saved
