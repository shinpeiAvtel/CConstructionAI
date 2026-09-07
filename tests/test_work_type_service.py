import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

from backend.schemas.work_type_schema import WorkTypeCreate
from backend.services import work_type_service


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as db_session:
        yield db_session


def test_create_work_type_success(session: Session):
    created = work_type_service.create_work_type(
        WorkTypeCreate(
            work_type_code="acs-card-reader-install",
            category="ACCESS_CONTROL",
            sub_category="CARD_READER",
            work_type_name="Card Reader Installation",
            default_unit="unit",
        ),
        session,
    )

    assert created.id is not None
    assert created.work_type_code == "ACS-CARD-READER-INSTALL"
    assert created.category == "ACCESS_CONTROL"


def test_create_work_type_duplicate_rejected(session: Session):
    request = WorkTypeCreate(
        work_type_code="ACS-CARD-READER-INSTALL",
        category="ACCESS_CONTROL",
        work_type_name="Card Reader Installation",
    )

    work_type_service.create_work_type(request, session)

    with pytest.raises(HTTPException) as ex:
        work_type_service.create_work_type(request, session)

    assert ex.value.status_code == 409


def test_list_work_types_filter_active(session: Session):
    work_type_service.create_work_type(
        WorkTypeCreate(
            work_type_code="WT-ACTIVE",
            category="CAT-A",
            work_type_name="Active Type",
            active=True,
        ),
        session,
    )

    work_type_service.create_work_type(
        WorkTypeCreate(
            work_type_code="WT-INACTIVE",
            category="CAT-A",
            work_type_name="Inactive Type",
            active=False,
        ),
        session,
    )

    active_only = work_type_service.list_work_types(
        session=session,
        active=True,
        category=None,
        sub_category=None,
        q=None,
    )

    assert len(active_only) == 1
    assert active_only[0].work_type_code == "WT-ACTIVE"
