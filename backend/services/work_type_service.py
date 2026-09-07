from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session

from backend.models import WorkTypeMaster
from backend.repositories import work_type_repository
from backend.schemas.work_type_schema import WorkTypeCreate


def create_work_type(
    request: WorkTypeCreate,
    session: Session,
) -> WorkTypeMaster:
    normalized_code = request.work_type_code.strip().upper()

    if not normalized_code:
        raise HTTPException(
            status_code=400,
            detail="work_type_code is required.",
        )

    existing = work_type_repository.get_by_code(
        session,
        normalized_code,
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This work_type_code already exists.",
        )

    now = datetime.now()

    item = WorkTypeMaster(
        work_type_code=normalized_code,
        category=request.category,
        sub_category=request.sub_category,
        work_type_name=request.work_type_name,
        description=request.description,
        default_unit=request.default_unit,
        active=request.active,
        created_at=now,
        updated_at=now,
    )

    return work_type_repository.create(
        session,
        item,
    )


def list_work_types(
    session: Session,
    active: bool | None,
    category: str | None,
    sub_category: str | None,
    q: str | None,
) -> list[WorkTypeMaster]:
    return work_type_repository.list_work_types(
        session=session,
        active=active,
        category=category,
        sub_category=sub_category,
        q=q,
    )
