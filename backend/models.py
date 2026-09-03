from datetime import datetime

from sqlmodel import Field, SQLModel


# =========================================================
# 歩掛マスター
# =========================================================

class LaborMaster(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    code: str = Field(index=True, unique=True)
    category: str = Field(index=True)
    name: str
    unit: str

    standard_minutes: float

    description: str | None = None

    sample_count: int = 0
    active: bool = True
    revision: int = 1

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# =========================================================
# 会社設定マスター
# =========================================================

class CompanySetting(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    setting_code: str = Field(index=True, unique=True)

    setting_name: str

    value: float

    unit: str | None = None

    description: str | None = None

    active: bool = True

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# =========================================================
# 人工単価マスター
# =========================================================

class LaborCostMaster(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    cost_code: str = Field(index=True, unique=True)

    role_name: str

    unit_price: float

    currency: str = "JPY"

    description: str | None = None

    active: bool = True

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# =========================================================
# 労務積算リクエスト
# =========================================================

class LaborEstimateRequest(SQLModel):
    labor_code: str

    quantity: float

    correction_factor: float = 1.0

    cost_code: str


    # =========================================================
# PROJECT MASTER
# =========================================================

class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    project_code: str = Field(
        index=True,
        unique=True,
    )

    project_name: str

    customer: str | None = None

    location: str | None = None

    status: str = "ACTIVE"

    description: str | None = None

    created_at: datetime = Field(
        default_factory=datetime.now
    )

    updated_at: datetime = Field(
        default_factory=datetime.now
    )


# =========================================================
# ACTUAL WORK RECORD
# =========================================================

class ActualWorkRecord(SQLModel, table=True):
    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    project_code: str = Field(index=True)

    labor_code: str = Field(index=True)

    work_date: str

    quantity: float

    workers: float

    work_minutes: float

    site_condition: str = "NORMAL"

    description: str | None = None

    created_at: datetime = Field(
        default_factory=datetime.now
    )


    # =========================================================
# ACTUAL WORK UPDATE REQUEST
# =========================================================

class ActualWorkUpdate(SQLModel):
    project_code: str | None = None
    labor_code: str | None = None
    work_date: str | None = None
    quantity: float | None = None
    workers: float | None = None
    work_minutes: float | None = None
    site_condition: str | None = None
    description: str | None = None

    # =========================================================
# STANDARD REVISION CANDIDATE
# =========================================================

class StandardRevisionCandidate(
    SQLModel,
    table=True,
):
    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    labor_code: str = Field(
        index=True,
    )

    current_revision: int

    current_standard_minutes: float

    proposed_standard_minutes: float

    minutes_per_person_day: float

    proposed_labor_per_unit: float

    sample_count: int

    outlier_count: int

    weighted_actual_labor_per_unit: float

    median_actual_labor_per_unit: float

    difference_percent: float

    status: str = Field(
        default="PENDING",
        index=True,
    )

    reason: str | None = None

    reviewer: str | None = None

    review_comment: str | None = None

    created_at: datetime = Field(
        default_factory=datetime.now,
    )

    reviewed_at: datetime | None = None


# =========================================================
# STANDARD REVISION REVIEW REQUEST
# =========================================================

class StandardRevisionReviewRequest(SQLModel):
    reviewer: str
    comment: str | None = None

    # =========================================================
# AUDIT LOG
# =========================================================

class AuditLog(SQLModel, table=True):
    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    action: str = Field(
        index=True,
    )

    entity_type: str = Field(
        index=True,
    )

    entity_id: int | None = Field(
        default=None,
        index=True,
    )

    labor_code: str | None = Field(
        default=None,
        index=True,
    )

    candidate_id: int | None = Field(
        default=None,
        index=True,
    )

    actor: str

    old_standard_minutes: float | None = None

    new_standard_minutes: float | None = None

    old_revision: int | None = None

    new_revision: int | None = None

    old_status: str | None = None

    new_status: str | None = None

    comment: str | None = None

    created_at: datetime = Field(
        default_factory=datetime.now,
        index=True,
    )

class MaterialMaster(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    material_code: str = Field(index=True, unique=True)
    category: str = Field(index=True)
    manufacturer: str | None = None
    model_number: str | None = None
    material_name: str

    unit: str
    unit_price: float

    currency: str = "JPY"

    supplier: str | None = None
    description: str | None = None

    active: bool = True

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class CombinedEstimateRequest(SQLModel):
    material_code: str
    labor_code: str
    cost_code: str

    quantity: float
    correction_factor: float = 1.0

class Estimate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    estimate_number: str = Field(index=True, unique=True)
    project_code: str | None = Field(default=None, index=True)

    customer_name: str
    estimate_title: str

    status: str = Field(default="DRAFT", index=True)

    currency: str = "JPY"

    material_cost_total: float = 0
    labor_cost_total: float = 0
    direct_cost_total: float = 0

    overhead_rate: float = 0
    overhead_amount: float = 0

    profit_rate: float = 0
    profit_amount: float = 0

    estimate_total: float = 0

    description: str | None = None

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class EstimateItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    estimate_id: int = Field(index=True)

    line_number: int

    material_code: str
    labor_code: str
    cost_code: str

    description: str | None = None

    quantity: float
    unit: str

    material_unit_price: float
    material_cost: float

    standard_minutes: float
    correction_factor: float = 1.0
    labor_person_days: float

    labor_unit_price: float
    labor_cost: float

    direct_cost: float

    created_at: datetime = Field(default_factory=datetime.now)

class EstimateCreateRequest(SQLModel):
    estimate_number: str
    project_code: str | None = None

    customer_name: str
    estimate_title: str

    currency: str = "JPY"

    overhead_rate: float = 0
    profit_rate: float = 0

    description: str | None = None

class EstimateItemCreateRequest(SQLModel):
    material_code: str
    labor_code: str
    cost_code: str

    quantity: float
    correction_factor: float = 1.0

    description: str | None = None

class EstimateItemUpdateRequest(SQLModel):
    quantity: float | None = None
    correction_factor: float | None = None
    description: str | None = None

class EstimateStatusUpdateRequest(SQLModel):
    status: str


class UploadedEstimate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    filename: str
    original_filename: str

    uploader: str | None = None
    project_code: str | None = None

    file_path: str

    processed: bool = False
    notes: str | None = None

    uploaded_at: datetime = Field(default_factory=datetime.now)

    