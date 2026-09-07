import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

from backend.schemas.estimate_document_schema import (
    EstimateDocumentCreateRequest,
    QuoteItemCreateRequest,
    QuoteItemVerifyRequest,
)
from backend.services import estimate_document_service, work_type_service
from backend.schemas.work_type_schema import WorkTypeCreate


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as db_session:
        yield db_session


def test_create_estimate_document_duplicate_hash_rejected(session: Session):
    request = EstimateDocumentCreateRequest(
        source_filename="vendor_quote_001.pdf",
        file_hash="abc123",
        source_type="VENDOR_QUOTE",
        time_category="HISTORICAL",
        uploaded_by="tester",
    )

    created = estimate_document_service.create_estimate_document(request, session)
    assert created.id is not None

    with pytest.raises(HTTPException) as ex:
        estimate_document_service.create_estimate_document(request, session)

    assert ex.value.status_code == 409


def test_quote_item_raw_description_is_preserved_after_verify(session: Session):
    doc = estimate_document_service.create_estimate_document(
        EstimateDocumentCreateRequest(
            source_filename="internal_001.pdf",
            file_hash="hash-raw-preserve",
            source_type="INTERNAL_ESTIMATE",
            uploaded_by="tester",
        ),
        session,
    )

    work_type_service.create_work_type(
        WorkTypeCreate(
            work_type_code="ACS-CARD-READER-INSTALL",
            category="ACCESS_CONTROL",
            work_type_name="Card Reader Installation",
        ),
        session,
    )

    item = estimate_document_service.create_quote_item(
        doc.id,
        QuoteItemCreateRequest(
            raw_description="カードリーダー取付 一式",
            quantity=2,
            amount=36000,
            work_type_code="ACS-CARD-READER-INSTALL",
            mapping_confidence=0.85,
        ),
        session,
    )

    verified = estimate_document_service.verify_quote_item(
        item.id,
        QuoteItemVerifyRequest(
            reviewer="reviewer1",
            verification_status="VERIFIED",
            normalized_description="Card Reader Installation",
            work_type_code="ACS-CARD-READER-INSTALL",
            mapping_confidence=0.92,
        ),
        session,
    )

    assert verified.raw_description == "カードリーダー取付 一式"
    assert verified.normalized_description == "Card Reader Installation"
    assert verified.verification_status == "VERIFIED"


def test_low_confidence_cannot_be_directly_verified(session: Session):
    doc = estimate_document_service.create_estimate_document(
        EstimateDocumentCreateRequest(
            source_filename="vendor_low_conf.pdf",
            file_hash="hash-low-conf",
            source_type="VENDOR_QUOTE",
            uploaded_by="tester",
        ),
        session,
    )

    item = estimate_document_service.create_quote_item(
        doc.id,
        QuoteItemCreateRequest(
            raw_description="Reader Install",
            mapping_confidence=0.4,
        ),
        session,
    )

    with pytest.raises(HTTPException) as ex:
        estimate_document_service.verify_quote_item(
            item.id,
            QuoteItemVerifyRequest(
                reviewer="reviewer2",
                verification_status="VERIFIED",
            ),
            session,
        )

    assert ex.value.status_code == 400
