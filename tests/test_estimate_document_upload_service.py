from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

from backend.services import estimate_document_service


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as db_session:
        yield db_session


def test_upload_pdf_success(session: Session, tmp_path: Path):
    data = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n"

    document = estimate_document_service.upload_estimate_pdf(
        session=session,
        filename="vendor_q1.pdf",
        content_type="application/pdf",
        file_bytes=data,
        source_type="VENDOR_QUOTE",
        uploaded_by="tester",
        storage_dir=tmp_path,
    )

    assert document.id is not None
    assert document.source_filename == "vendor_q1.pdf"
    assert document.source_type == "VENDOR_QUOTE"
    assert document.file_hash
    assert document.source_file_path is not None
    assert Path(document.source_file_path).exists()


def test_upload_duplicate_hash_rejected(session: Session, tmp_path: Path):
    data = b"%PDF-1.4\nSAME\n"

    estimate_document_service.upload_estimate_pdf(
        session=session,
        filename="a.pdf",
        content_type="application/pdf",
        file_bytes=data,
        source_type="VENDOR_QUOTE",
        uploaded_by="tester",
        storage_dir=tmp_path,
    )

    with pytest.raises(HTTPException) as ex:
        estimate_document_service.upload_estimate_pdf(
            session=session,
            filename="b.pdf",
            content_type="application/pdf",
            file_bytes=data,
            source_type="VENDOR_QUOTE",
            uploaded_by="tester",
            storage_dir=tmp_path,
        )

    assert ex.value.status_code == 409


def test_upload_non_pdf_rejected(session: Session, tmp_path: Path):
    with pytest.raises(HTTPException) as ex:
        estimate_document_service.upload_estimate_pdf(
            session=session,
            filename="note.txt",
            content_type="text/plain",
            file_bytes=b"hello",
            source_type="OTHER",
            uploaded_by="tester",
            storage_dir=tmp_path,
        )

    assert ex.value.status_code == 400
