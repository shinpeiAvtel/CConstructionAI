from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from backend.database import get_session
from backend.models import WorkTypeMaster
from backend.repositories import estimate_document_repository
from backend.schemas.estimate_document_schema import (
    EstimateDocumentRawExtractionListResponse,
    EstimateDocumentCreateRequest,
    EstimateDocumentListResponse,
    EstimateDocumentRead,
    EstimateDocumentUploadResponse,
    QuoteItemCreateRequest,
    QuoteItemListResponse,
    QuoteItemRead,
    QuoteItemVerifyRequest,
    TextExtractionRunResponse,
)
from backend.services import estimate_document_service
from backend.services.estimate_analysis_service import build_document_analysis
from backend.services.analysis_excel_export_service import build_filename, build_workbook_bytes


router = APIRouter(tags=["estimate-documents"])


@router.post(
    "/documents/estimates/upload",
    response_model=EstimateDocumentRead,
    status_code=201,
)
async def upload_estimate_document(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    time_category: str = Form("CURRENT"),
    vendor_name: str | None = Form(None),
    project_code: str | None = Form(None),
    project_name: str | None = Form(None),
    quote_number: str | None = Form(None),
    quote_date: str | None = Form(None),
    site: str | None = Form(None),
    project_type: str | None = Form(None),
    uploaded_by: str | None = Form(None),
    notes: str | None = Form(None),
    session: Session = Depends(get_session),
):
    contents = await file.read()

    return estimate_document_service.upload_estimate_pdf(
        session=session,
        filename=file.filename or "",
        content_type=file.content_type,
        file_bytes=contents,
        source_type=source_type,
        time_category=time_category,
        vendor_name=vendor_name,
        project_code=project_code,
        project_name=project_name,
        quote_number=quote_number,
        quote_date=quote_date,
        site=site,
        project_type=project_type,
        uploaded_by=uploaded_by,
        notes=notes,
    )


@router.post(
    "/estimate-documents",
    response_model=EstimateDocumentRead,
    status_code=201,
)
def create_estimate_document(
    request: EstimateDocumentCreateRequest,
    session: Session = Depends(get_session),
):
    return estimate_document_service.create_estimate_document(request, session)


@router.post(
    "/estimate-documents/upload",
    response_model=EstimateDocumentUploadResponse,
)
async def upload_estimate_document_mobile(
    file: UploadFile = File(...),
    source_type: str = Form("VENDOR_QUOTE"),
    project_code: str | None = Form(None),
    vendor_name: str | None = Form(None),
    quote_date: str | None = Form(None),
    notes: str | None = Form(None),
    session: Session = Depends(get_session),
):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")
    if len(contents) > estimate_document_service.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"Uploaded PDF exceeds the {estimate_document_service.MAX_UPLOAD_SIZE_MB} MB limit.")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File extension must be .pdf.")
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF.")
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_hash = __import__("hashlib").sha256(contents).hexdigest()
    duplicate = estimate_document_repository.get_document_by_hash(session, file_hash)
    if duplicate:
        return EstimateDocumentUploadResponse(
            document_id=duplicate.id,
            filename=duplicate.source_filename,
            source_type=duplicate.source_type,
            project_code=duplicate.project_code,
            vendor_name=duplicate.vendor_name,
            quote_date=duplicate.quote_date,
            verification_status=duplicate.verification_status,
            duplicate=True,
            existing_document_id=duplicate.id,
        )

    document = estimate_document_service.upload_estimate_pdf(
        session=session,
        filename=file.filename or "",
        content_type="application/pdf",
        file_bytes=contents,
        source_type=source_type,
        vendor_name=vendor_name,
        project_code=project_code,
        quote_date=quote_date,
        notes=notes,
    )

    return EstimateDocumentUploadResponse(
        document_id=document.id,
        filename=document.source_filename,
        source_type=document.source_type,
        project_code=document.project_code,
        vendor_name=document.vendor_name,
        quote_date=document.quote_date,
        verification_status=document.verification_status,
        duplicate=False,
    )


@router.post(
    "/estimate-documents/{document_id}/extract-text",
    response_model=TextExtractionRunResponse,
)
def extract_estimate_document_text(
    document_id: int,
    actor: str | None = None,
    session: Session = Depends(get_session),
):
    return estimate_document_service.run_text_extraction(
        document_id=document_id,
        session=session,
        actor=actor,
    )


@router.get(
    "/estimate-documents/{document_id}/raw-extractions",
    response_model=EstimateDocumentRawExtractionListResponse,
)
def read_estimate_document_raw_extractions(
    document_id: int,
    stage: str | None = None,
    session: Session = Depends(get_session),
):
    records = estimate_document_service.list_raw_extractions(
        document_id=document_id,
        session=session,
        stage=stage,
    )

    return {
        "count": len(records),
        "records": records,
    }


@router.get(
    "/estimate-documents/{document_id}",
    response_model=EstimateDocumentRead,
)
def read_estimate_document(
    document_id: int,
    session: Session = Depends(get_session),
):
    document = estimate_document_repository.get_document_by_id(
        session=session,
        document_id=document_id,
    )
    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Estimate document not found.",
        )
    return document


@router.get(
    "/estimate-documents",
    response_model=EstimateDocumentListResponse,
)
def read_estimate_documents(
    source_type: str | None = None,
    time_category: str | None = None,
    verification_status: str | None = None,
    session: Session = Depends(get_session),
):
    records = estimate_document_service.list_estimate_documents(
        session=session,
        source_type=source_type,
        time_category=time_category,
        verification_status=verification_status,
    )

    return {
        "count": len(records),
        "records": records,
    }


@router.post(
    "/estimate-documents/{document_id}/quote-items",
    response_model=QuoteItemRead,
    status_code=201,
)
def create_quote_item(
    document_id: int,
    request: QuoteItemCreateRequest,
    session: Session = Depends(get_session),
):
    return estimate_document_service.create_quote_item(
        document_id,
        request,
        session,
    )


@router.get(
    "/estimate-documents/{document_id}/quote-items",
    response_model=QuoteItemListResponse,
)
def read_quote_items(
    document_id: int,
    verification_status: str | None = None,
    session: Session = Depends(get_session),
):
    records = estimate_document_service.list_quote_items(
        document_id=document_id,
        verification_status=verification_status,
        session=session,
    )

    return {
        "count": len(records),
        "records": records,
    }


@router.post(
    "/estimate-documents/quote-items/{item_id}/verify",
    response_model=QuoteItemRead,
)
def verify_quote_item(
    item_id: int,
    request: QuoteItemVerifyRequest,
    session: Session = Depends(get_session),
):
    return estimate_document_service.verify_quote_item(
        item_id,
        request,
        session,
    )


@router.get(
    "/documents/{document_id}/analysis/export/excel",
    response_class=StreamingResponse,
    responses={
        200: {"content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}},
        404: {"description": "Estimate document not found."},
    },
)
def export_document_analysis_excel(
    document_id: int,
    session: Session = Depends(get_session),
):
    document = estimate_document_repository.get_document_by_id(
        session=session,
        document_id=document_id,
    )
    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Estimate document not found.",
        )

    quote_items = estimate_document_repository.list_quote_items(
        session=session,
        document_id=document_id,
        verification_status=None,
    )
    work_types = session.exec(select(WorkTypeMaster)).all()
    analysis = build_document_analysis(
        document=document,
        quote_items=quote_items,
        work_types=work_types,
    )

    workbook_bytes = build_workbook_bytes(analysis)
    filename = build_filename(
        document.id,
        analysis.metadata.analyzed_at,
    )

    return StreamingResponse(
        BytesIO(workbook_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
