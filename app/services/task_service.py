from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.models import TaskItem
from app.schemas import TaskItemCreate, TaskItemUpdate


def get_task_out(task: TaskItem) -> dict:
    """将 ORM 对象转为输出字典，自动计算剩余天数"""
    remaining = None
    if task.deadline:
        remaining = (task.deadline - date.today()).days

    return {
        "id": task.id,
        "user_id": task.user_id,
        "task_title": task.task_title,
        "deadline": task.deadline,
        "task_category": task.task_category,
        "status": task.status,
        "notes": task.notes,
        "remaining_days": remaining,
        "sort_order": task.sort_order,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }

def create_task(db: Session, user_id: int, data: TaskItemCreate) -> TaskItem:
    task = TaskItem(
        user_id=user_id,
        task_title=data.task_title,
        deadline=data.deadline,
        task_category=data.task_category,
        status=data.status,
        notes=data.notes,
        sort_order=data.sort_order,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def update_task(db: Session, task: TaskItem, data: TaskItemUpdate) -> TaskItem:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task: TaskItem):
    db.delete(task)
    db.commit()

def query_tasks(
    db: Session,
    user_id: int,
    status: str | None = None,
    task_category: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    q = db.query(TaskItem).filter(TaskItem.user_id == user_id)

    if status:
        q = q.filter(TaskItem.status == status)
    if task_category:
        q = q.filter(TaskItem.task_category == task_category)
    if keyword:
        q = q.filter(TaskItem.task_title.contains(keyword))

    total = q.count()
    # MySQL 不支持 NULLS LAST，用 CASE WHEN 将 NULL 排到最后
    from sqlalchemy import case
    items = q.order_by(
        TaskItem.status != "未完成",
        case((TaskItem.deadline == None, 1), else_=0),
        TaskItem.deadline.asc(),
        TaskItem.sort_order.asc(),
        TaskItem.id.desc(),
    ).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [get_task_out(item) for item in items],
    }

def get_task_stats(db: Session, user_id: int) -> dict:
    """获取任务统计"""
    base = db.query(TaskItem).filter(TaskItem.user_id == user_id)

    total = base.count()
    by_status = (
        db.query(TaskItem.status, func.count(TaskItem.id))
        .filter(TaskItem.user_id == user_id)
        .group_by(TaskItem.status)
        .all()
    )
    by_category = (
        db.query(TaskItem.task_category, func.count(TaskItem.id))
        .filter(TaskItem.user_id == user_id)
        .group_by(TaskItem.task_category)
        .all()
    )

    # 即将到期（3天内截止的未完成任务）
    today = date.today()
    urgent = (
        db.query(TaskItem)
        .filter(
            TaskItem.user_id == user_id,
            TaskItem.status == "未完成",
            TaskItem.deadline != None,
            TaskItem.deadline <= today + __import__("datetime").timedelta(days=3),
        )
        .count()
    )

    # 待办任务数（仅未完成）
    pending_count = (
        db.query(TaskItem)
        .filter(
            TaskItem.user_id == user_id,
            TaskItem.status == "未完成",
        )
        .count()
    )

    return {
        "total": total,
        "pending_count": pending_count,
        "by_status": {s: c for s, c in by_status},
        "by_category": {c or "未分类": n for c, n in by_category},
        "urgent_count": urgent,
    }
