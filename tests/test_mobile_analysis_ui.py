from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from backend.database import engine, get_session
from backend.main import app
from backend.models import EstimateDocument


TEST_ENGINE = engine
SQLModel.metadata.create_all(TEST_ENGINE)


def _override_get_session():
    with Session(TEST_ENGINE) as session:
        yield session


app.dependency_overrides[get_session] = _override_get_session
client = TestClient(app)


def _reset_db():
    SQLModel.metadata.drop_all(TEST_ENGINE)
    SQLModel.metadata.create_all(TEST_ENGINE)


def _seed_document(source_filename: str = "sample.pdf", *, document_id: int | None = None):
    with Session(TEST_ENGINE) as session:
        document = EstimateDocument(
            source_filename=source_filename,
            file_hash="hash-mobile-ui",
            source_type="VENDOR_QUOTE",
            time_category="CURRENT",
            vendor_name="Alpha Builder",
            project_code="PRJ-ALPHA",
            project_name="Alpha Project",
            quote_number="Q-010",
            verification_status="VERIFIED",
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        if document_id is not None:
            document.id = document_id
            session.add(document)
            session.commit()
            session.refresh(document)
        return document.id


def test_mobile_page_returns_200_and_expected_content():
    response = client.get("/mobile")

    assert response.status_code == 200
    html = response.text
    assert "CConstructionAI" in html
    assert "Estimate Analysis" in html
    assert "Document ID" in html
    assert "Load Document" in html
    assert "Download Analysis Excel" in html
    assert 'meta name="viewport"' in html.lower()
    assert "width=device-width" in html.lower()
    assert "aria-live" in html


def test_mobile_page_has_initial_disabled_download_button():
    response = client.get("/mobile")

    assert response.status_code == 200
    html = response.text
    assert 'id="download-button"' in html
    assert 'disabled' in html
    assert 'aria-disabled="true"' in html


def test_mobile_static_css_and_js_are_available():
    css_response = client.get("/static/mobile_analysis.css")
    js_response = client.get("/static/mobile_analysis.js")

    assert css_response.status_code == 200
    assert js_response.status_code == 200
    assert "overflow-x: hidden;" in css_response.text
    assert "fetch(`/estimate-documents/${documentId}`" in js_response.text
    assert "fetch(url" in js_response.text


def test_estimate_document_lookup_has_existing_and_missing_behavior():
    _reset_db()
    document_id = _seed_document()

    existing_response = client.get(f"/estimate-documents/{document_id}")
    missing_response = client.get("/estimate-documents/999999")

    assert existing_response.status_code == 200
    payload = existing_response.json()
    assert payload["id"] == document_id
    assert payload["source_filename"] == "sample.pdf"
    assert payload["vendor_name"] == "Alpha Builder"
    assert payload["project_code"] == "PRJ-ALPHA"
    assert payload["verification_status"] == "VERIFIED"

    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Estimate document not found."


def test_mobile_js_uses_dynamic_document_id_and_export_endpoint():
    js_source = Path("backend/static/mobile_analysis.js").read_text(encoding="utf-8")

    assert "documentIdInput" in js_source
    assert "fetch(`/estimate-documents/${documentId}`" in js_source
    assert "const url = `/documents/${documentId}/analysis/export/excel`" in js_source
    assert "document_id = 1" not in js_source.lower()
    assert "documentId = Number(rawValue)" in js_source
    assert "Loading..." in js_source
    assert "Preparing Excel..." in js_source
    assert "Document not found" in js_source


def test_mobile_css_satisfies_mobile_requirements():
    css_source = Path("backend/static/mobile_analysis.css").read_text(encoding="utf-8")

    assert "font-size: 16px;" in css_source
    assert "min-height: 48px;" in css_source
    assert "display: grid;" in css_source
    assert "overflow-x: hidden;" in css_source
    assert "@media (max-width: 359px)" in css_source
    assert "grid-template-columns: 1fr;" in css_source


def test_status_region_and_accessibility_elements_exist():
    html = client.get("/mobile").text

    assert 'id="status-region"' in html
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html
    assert 'for="document-id"' in html
    assert 'type="submit"' in html
    assert 'type="button"' in html


def test_download_button_uses_analysis_excel_endpoint_not_legacy_estimate_route():
    js_source = Path("backend/static/mobile_analysis.js").read_text(encoding="utf-8")

    assert "/documents/${documentId}/analysis/export/excel" in js_source
    assert "/estimates/${documentId}/export/excel" not in js_source
    assert "/estimates/" not in js_source.lower()
    assert "documentId" in js_source


def test_mobile_page_does_not_use_inner_html_for_metadata():
    html = client.get("/mobile").text
    js_source = Path("backend/static/mobile_analysis.js").read_text(encoding="utf-8")

    assert "innerHTML" not in html.lower()
    assert "innerHTML" not in js_source.lower()
    assert "textContent" in js_source
