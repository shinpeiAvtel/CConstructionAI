from datetime import datetime

from sqlmodel import SQLModel


class WorkTypeCreate(SQLModel):
    work_type_code: str
    category: str
    sub_category: str | None = None
    work_type_name: str
    description: str | None = None
    default_unit: str | None = None
    active: bool = True


class WorkTypeRead(SQLModel):
    id: int
    work_type_code: str
    category: str
    sub_category: str | None = None
    work_type_name: str
    description: str | None = None
    default_unit: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime


class WorkTypeListResponse(SQLModel):
    count: int
    records: list[WorkTypeRead]
