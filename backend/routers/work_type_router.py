from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.database import get_session
from backend.schemas.work_type_schema import (
    WorkTypeCreate,
    WorkTypeListResponse,
    WorkTypeRead,
)
from backend.services import work_type_service


router = APIRouter(tags=["work-types"])


@router.post(
    "/work-types",
    response_model=WorkTypeRead,
    status_code=201,
)
def create_work_type(
    request: WorkTypeCreate,
    session: Session = Depends(get_session),
):
    return work_type_service.create_work_type(
        request,
        session,
    )


@router.get(
    "/work-types",
    response_model=WorkTypeListResponse,
)
def read_work_types(
    active: bool | None = None,
    category: str | None = None,
    sub_category: str | None = None,
    q: str | None = None,
    session: Session = Depends(get_session),
):
    records = work_type_service.list_work_types(
        session=session,
        active=active,
        category=category,
        sub_category=sub_category,
        q=q,
    )

    return {
        "count": len(records),
        "records": records,
    }
