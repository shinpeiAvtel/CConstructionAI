from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from backend.services import estimate_document_service


def _create_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_text_extraction_from_text_pdf_like_bytes(tmp_path: Path):
    with _create_session() as session:
        # Minimal text-based PDF-like payload containing Tj/TJ operators.
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"BT /F1 10 Tf 100 700 Td (Card Reader Installation) Tj ET\n"
            b"BT /F1 10 Tf 100 680 Td [(Vendor) 120 ( Quote)] TJ ET\n"
        )

        doc = estimate_document_service.upload_estimate_pdf(
            session=session,
            filename="text_based.pdf",
            content_type="application/pdf",
            file_bytes=pdf_bytes,
            source_type="VENDOR_QUOTE",
            uploaded_by="tester",
            storage_dir=tmp_path,
        )

        result = estimate_document_service.run_text_extraction(
            document_id=doc.id,
            session=session,
            actor="tester",
        )

        assert result["requires_ocr"] is False
        assert result["extraction_status"] == "TEXT_EXTRACTED"
        assert result["extracted_text_length"] > 0

        records = estimate_document_service.list_raw_extractions(
            document_id=doc.id,
            session=session,
            stage="TEXT_EXTRACTION",
        )

        assert len(records) == 1
        assert "Card Reader Installation" in records[0].raw_text
        assert "Vendor" in records[0].raw_text


def test_text_extraction_needs_ocr_for_non_text_pdf_like_bytes(tmp_path: Path):
    with _create_session() as session:
        pdf_bytes = b"%PDF-1.4\n%binary-image-only-content\n"

        doc = estimate_document_service.upload_estimate_pdf(
            session=session,
            filename="scan_like.pdf",
            content_type="application/pdf",
            file_bytes=pdf_bytes,
            source_type="SUPPLIER_QUOTE",
            uploaded_by="tester",
            storage_dir=tmp_path,
        )

        result = estimate_document_service.run_text_extraction(
            document_id=doc.id,
            session=session,
            actor="tester",
        )

        assert result["requires_ocr"] is True
        assert result["extraction_status"] == "NEEDS_OCR"

        records = estimate_document_service.list_raw_extractions(
            document_id=doc.id,
            session=session,
            stage="TEXT_EXTRACTION",
        )

        assert len(records) == 1
        assert records[0].requires_ocr is True
