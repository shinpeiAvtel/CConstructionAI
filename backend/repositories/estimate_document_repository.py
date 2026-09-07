from sqlmodel import Session, select

from backend.models import (
    EstimateDocument,
    EstimateDocumentRawExtraction,
    QuoteItem,
)


def get_document_by_id(
    session: Session,
    document_id: int,
) -> EstimateDocument | None:
    return session.get(EstimateDocument, document_id)


def get_document_by_hash(
    session: Session,
    file_hash: str,
) -> EstimateDocument | None:
    return session.exec(
        select(EstimateDocument).where(
            EstimateDocument.file_hash == file_hash
        )
    ).first()


def create_document(
    session: Session,
    item: EstimateDocument,
) -> EstimateDocument:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def list_documents(
    session: Session,
    source_type: str | None,
    time_category: str | None,
    verification_status: str | None,
) -> list[EstimateDocument]:
    statement = select(EstimateDocument)

    if source_type:
        statement = statement.where(
            EstimateDocument.source_type == source_type
        )

    if time_category:
        statement = statement.where(
            EstimateDocument.time_category == time_category
        )

    if verification_status:
        statement = statement.where(
            EstimateDocument.verification_status == verification_status
        )

    statement = statement.order_by(
        EstimateDocument.upload_timestamp.desc(),
        EstimateDocument.id.desc(),
    )

    return session.exec(statement).all()


def create_quote_item(
    session: Session,
    item: QuoteItem,
) -> QuoteItem:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def get_quote_item_by_id(
    session: Session,
    item_id: int,
) -> QuoteItem | None:
    return session.get(QuoteItem, item_id)


def list_quote_items(
    session: Session,
    document_id: int,
    verification_status: str | None,
) -> list[QuoteItem]:
    statement = select(QuoteItem).where(
        QuoteItem.document_id == document_id
    )

    if verification_status:
        statement = statement.where(
            QuoteItem.verification_status == verification_status
        )

    statement = statement.order_by(
        QuoteItem.line_number,
        QuoteItem.id,
    )

    return session.exec(statement).all()


def get_next_line_number(
    session: Session,
    document_id: int,
) -> int:
    items = session.exec(
        select(QuoteItem)
        .where(QuoteItem.document_id == document_id)
        .order_by(QuoteItem.line_number.desc(), QuoteItem.id.desc())
    ).all()

    if not items:
        return 1

    return items[0].line_number + 1


def save_quote_item(
    session: Session,
    item: QuoteItem,
) -> QuoteItem:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def save_document(
    session: Session,
    item: EstimateDocument,
) -> EstimateDocument:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def create_raw_extraction(
    session: Session,
    item: EstimateDocumentRawExtraction,
) -> EstimateDocumentRawExtraction:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def list_raw_extractions(
    session: Session,
    document_id: int,
    stage: str | None,
) -> list[EstimateDocumentRawExtraction]:
    statement = select(EstimateDocumentRawExtraction).where(
        EstimateDocumentRawExtraction.document_id == document_id
    )

    if stage:
        statement = statement.where(
            EstimateDocumentRawExtraction.stage == stage
        )

    statement = statement.order_by(
        EstimateDocumentRawExtraction.created_at.desc(),
        EstimateDocumentRawExtraction.id.desc(),
    )

    return session.exec(statement).all()
