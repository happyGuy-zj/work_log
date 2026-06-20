from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============ 枚举常量 ============

WORK_TYPES = Literal[
    "Bug", "Report", "功能", "增强", "接口",
    "学习", "培训", "打印", "问题排查"
]

CHANGE_TYPES = Literal["新增", "修改"]

TASK_CATEGORIES = Literal[
    "运维工单", "Bug工单", "临时任务", "迭代项",
    "SRM项目", "培训", "紧急插入临时任务",
    "按需采购", "年度任务", "绩效", "STO项目"
]

TASK_STATUSES = Literal["已完成", "未完成", "挂起", "取消"]

LOG_STATUSES = Literal["doing", "done", "blocked", "cancelled"]

PRIORITIES = Literal["low", "normal", "high", "urgent"]


# ============ 通用 ============

class ResponseBase(BaseModel):
    code: int = 0
    message: str = "success"


# ============ 部门 ============

class DepartmentOut(BaseModel):
    id: int
    name: str
    leader_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    name: str
    leader_id: Optional[int] = None


# ============ 用户 ============

class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    dept_id: Optional[int] = None
    role: str = "member"
    is_active: int = 1
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    display_name: str
    dept_id: Optional[int] = None
    role: str = "member"
    password: Optional[str] = None


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    dept_id: Optional[int] = None
    role: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[int] = None


# ============ 分类 ============

class CategoryOut(BaseModel):
    id: int
    name: str
    user_id: int
    sort_order: int = 0
    is_active: int = 1

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[int] = None


# ============ 标签 ============

class TagOut(BaseModel):
    id: int
    tag: str

    model_config = {"from_attributes": True}


# ============ 任务项（简要，用于工作记录下拉） ============

class TaskItemBrief(BaseModel):
    id: int
    task_title: str
    task_category: Optional[str] = None
    status: str = "未完成"
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


# ============ 工作记录 ============

class DailyLogCreate(BaseModel):
    log_date: date
    category_id: Optional[int] = None
    task_item_id: Optional[int] = None
    task_title: str
    task_detail: Optional[str] = None
    reference: Optional[str] = None
    # SAP 开发专属字段
    work_type: Optional[WORK_TYPES] = None
    change_type: Optional[CHANGE_TYPES] = None
    tcode: Optional[str] = None
    program_name: Optional[str] = None
    interface_name: Optional[str] = None
    enhancement_name: Optional[str] = None
    class_name: Optional[str] = None
    print_name: Optional[str] = None
    # 通用字段
    status: LOG_STATUSES = "done"
    time_spent: Optional[float] = Field(None, ge=0)
    priority: PRIORITIES = "normal"
    tags: Optional[list[str]] = None


class DailyLogUpdate(BaseModel):
    log_date: Optional[date] = None
    category_id: Optional[int] = None
    task_item_id: Optional[int] = None
    task_title: Optional[str] = None
    task_detail: Optional[str] = None
    reference: Optional[str] = None
    work_type: Optional[WORK_TYPES] = None
    change_type: Optional[CHANGE_TYPES] = None
    tcode: Optional[str] = None
    program_name: Optional[str] = None
    interface_name: Optional[str] = None
    enhancement_name: Optional[str] = None
    class_name: Optional[str] = None
    print_name: Optional[str] = None
    status: Optional[LOG_STATUSES] = None
    time_spent: Optional[float] = Field(None, ge=0)
    priority: Optional[PRIORITIES] = None
    tags: Optional[list[str]] = None


class DailyLogOut(BaseModel):
    id: int
    user_id: int
    log_date: date
    category: Optional[CategoryOut] = None
    task_item: Optional[TaskItemBrief] = None
    task_title: str
    task_detail: Optional[str] = None
    reference: Optional[str] = None
    work_type: Optional[str] = None
    change_type: Optional[str] = None
    tcode: Optional[str] = None
    program_name: Optional[str] = None
    interface_name: Optional[str] = None
    enhancement_name: Optional[str] = None
    class_name: Optional[str] = None
    print_name: Optional[str] = None
    status: str
    time_spent: Optional[float] = None
    priority: str
    tags: list[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DailyLogListOut(ResponseBase):
    data: dict = Field(default_factory=dict)


# ============ 任务项 ============

class TaskItemCreate(BaseModel):
    task_title: str
    deadline: Optional[date] = None
    task_category: Optional[TASK_CATEGORIES] = None
    status: TASK_STATUSES = "未完成"
    notes: Optional[str] = None
    sort_order: int = 0


class TaskItemUpdate(BaseModel):
    task_title: Optional[str] = None
    deadline: Optional[date] = None
    task_category: Optional[TASK_CATEGORIES] = None
    status: Optional[TASK_STATUSES] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None


class TaskItemOut(BaseModel):
    id: int
    user_id: int
    task_title: str
    deadline: Optional[date] = None
    task_category: Optional[str] = None
    status: str
    notes: Optional[str] = None
    remaining_days: Optional[int] = None
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ============ 待开发项 ============

class BacklogItemCreate(BaseModel):
    task_title: str
    deadline: Optional[date] = None
    pending_count: Optional[int] = None
    notes: Optional[str] = None
    sort_order: int = 0


class BacklogItemUpdate(BaseModel):
    task_title: Optional[str] = None
    deadline: Optional[date] = None
    pending_count: Optional[int] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None


class BacklogItemOut(BaseModel):
    id: int
    user_id: int
    task_title: str
    deadline: Optional[date] = None
    remaining_days: Optional[int] = None
    pending_count: Optional[int] = None
    notes: Optional[str] = None
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ============ 统计汇总 ============

class SummaryGroup(BaseModel):
    key: str
    record_count: int
    total_hours: float
    categories: dict[str, float] = {}


class SummaryOut(ResponseBase):
    data: dict = Field(default_factory=dict)


# ============ 周报 ============

class ReportGenerate(BaseModel):
    week_start: date


class ReportOut(BaseModel):
    id: int
    user_id: int
    week_start: date
    week_end: date
    content: Optional[str] = None
    generated_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    status: str = "draft"
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None
