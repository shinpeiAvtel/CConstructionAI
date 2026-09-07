from sqlalchemy import or_
from sqlmodel import Session, select

from backend.models import WorkTypeMaster


def get_by_code(
    session: Session,
    work_type_code: str,
) -> WorkTypeMaster | None:
    return session.exec(
        select(WorkTypeMaster).where(
            WorkTypeMaster.work_type_code == work_type_code
        )
    ).first()


def create(
    session: Session,
    item: WorkTypeMaster,
) -> WorkTypeMaster:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def list_work_types(
    session: Session,
    active: bool | None,
    category: str | None,
    sub_category: str | None,
    q: str | None,
) -> list[WorkTypeMaster]:
    statement = select(WorkTypeMaster)

    if active is not None:
        statement = statement.where(
            WorkTypeMaster.active == active
        )

    if category:
        statement = statement.where(
            WorkTypeMaster.category == category
        )

    if sub_category:
        statement = statement.where(
            WorkTypeMaster.sub_category == sub_category
        )

    if q:
        keyword = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                WorkTypeMaster.work_type_code.ilike(keyword),
                WorkTypeMaster.work_type_name.ilike(keyword),
                WorkTypeMaster.description.ilike(keyword),
            )
        )

    statement = statement.order_by(
        WorkTypeMaster.work_type_code
    )

    return session.exec(statement).all()
