from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from backend.database import get_session
from backend.main import app
from backend.models import EstimateDocument
from backend.services import estimate_document_service


@pytest.fixture
def test_engine(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test_upload.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client_with_test_db(test_engine):
    def _override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def valid_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


def _reset_db(engine):
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_upload_page_200_and_expected_mobile_fields(client_with_test_db):
    response = client_with_test_db.get("/upload")

    assert response.status_code == 200
    html = response.text
    assert "CConstructionAI Upload" in html
    assert "Estimate PDF Intake" in html
    assert "Upload PDF" in html
    assert 'accept="application/pdf,.pdf"' in html
    assert 'type="file"' in html


def test_upload_api_accepts_valid_pdf_and_creates_document(valid_pdf_bytes, client_with_test_db, test_engine):
    _reset_db(test_engine)

    response = client_with_test_db.post(
        "/estimate-documents/upload",
        files={"file": ("sample.pdf", valid_pdf_bytes, "application/pdf")},
        data={
            "source_type": "VENDOR_QUOTE",
            "project_code": "PRJ-001",
            "vendor_name": "Alpha Builder",
            "quote_date": "2026-09-01",
            "notes": "Sample upload",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["duplicate"] is False
    assert payload["document_id"] > 0
    assert payload["filename"] == "sample.pdf"
    assert payload["source_type"] == "VENDOR_QUOTE"
    assert payload["project_code"] == "PRJ-001"
    assert payload["vendor_name"] == "Alpha Builder"
    assert payload["verification_status"] == "NEEDS_REVIEW"

    with Session(test_engine) as session:
        doc = session.get(EstimateDocument, payload["document_id"])
        assert doc is not None
        assert doc.file_hash
        assert doc.source_filename == "sample.pdf"
        assert doc.verification_status == "NEEDS_REVIEW"
        assert Path(doc.source_file_path).exists()
        assert Path(doc.source_file_path).read_bytes().startswith(b"%PDF-")
        assert session.exec(select(EstimateDocument)).all() == [doc]


def test_upload_rejects_non_pdf_extension_and_wrong_mime(client_with_test_db, test_engine):
    _reset_db(test_engine)

    bad_ext = client_with_test_db.post(
        "/estimate-documents/upload",
        files={"file": ("sample.txt", b"hello", "text/plain")},
        data={"source_type": "VENDOR_QUOTE"},
    )
    wrong_mime = client_with_test_db.post(
        "/estimate-documents/upload",
        files={"file": ("sample.pdf", b"%PDF-1.4\nnot really", "text/plain")},
        data={"source_type": "VENDOR_QUOTE"},
    )

    assert bad_ext.status_code == 400
    assert wrong_mime.status_code == 400


def test_upload_rejects_empty_file_and_fake_pdf_and_oversize(client_with_test_db, test_engine):
    _reset_db(test_engine)

    empty_response = client_with_test_db.post(
        "/estimate-documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
        data={"source_type": "VENDOR_QUOTE"},
    )
    fake_response = client_with_test_db.post(
        "/estimate-documents/upload",
        files={"file": ("fake.pdf", b"NOT PDF CONTENT", "application/pdf")},
        data={"source_type": "VENDOR_QUOTE"},
    )
    oversize = b"%PDF-1.4\n" + b"A" * (estimate_document_service.MAX_UPLOAD_SIZE_BYTES + 10)
    oversized_response = client_with_test_db.post(
        "/estimate-documents/upload",
        files={"file": ("big.pdf", oversize, "application/pdf")},
        data={"source_type": "VENDOR_QUOTE"},
    )

    assert empty_response.status_code == 400
    assert fake_response.status_code == 400
    assert oversized_response.status_code == 413


def test_duplicate_pdf_returns_duplicate_true_without_second_record(valid_pdf_bytes, client_with_test_db, test_engine):
    _reset_db(test_engine)

    first = client_with_test_db.post(
        "/estimate-documents/upload",
        files={"file": ("duplicate.pdf", valid_pdf_bytes, "application/pdf")},
        data={"source_type": "VENDOR_QUOTE"},
    )
    second = client_with_test_db.post(
        "/estimate-documents/upload",
        files={"file": ("duplicate-copy.pdf", valid_pdf_bytes, "application/pdf")},
        data={"source_type": "VENDOR_QUOTE"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert second.json()["existing_document_id"] == first.json()["document_id"]

    with Session(test_engine) as session:
        count = len(session.exec(select(EstimateDocument)).all())
        assert count == 1


def test_path_traversal_filename_is_sanitized(valid_pdf_bytes, client_with_test_db, test_engine):
    _reset_db(test_engine)

    response = client_with_test_db.post(
        "/estimate-documents/upload",
        files={"file": ("../..\\escape.pdf", valid_pdf_bytes, "application/pdf")},
        data={"source_type": "VENDOR_QUOTE"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "escape.pdf"
    with Session(test_engine) as session:
        document = session.get(EstimateDocument, payload["document_id"])
        assert document is not None
        assert Path(document.source_file_path).name != "../..\\escape.pdf"
        assert ".." not in Path(document.source_file_path).name


def test_upload_ui_exposes_analysis_and_excel_links(client_with_test_db):
    html = client_with_test_db.get("/upload").text

    assert "View Analysis" in html
    assert "Download Analysis Excel" in html
    assert "/mobile?document_id=" in html
    assert "/documents/" in html and "/analysis/export/excel" in html
