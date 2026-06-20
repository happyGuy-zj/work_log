from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date
from app.models import TaskItem


def query_backlog(
    db: Session,
    user_id: int,
    keyword: str | None = None,
    task_category: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """待开发项 = 所有未完成的任务项"""
    q = db.query(TaskItem).filter(
        TaskItem.user_id == user_id,
        TaskItem.status == "未完成",
    )

    if keyword:
        q = q.filter(TaskItem.task_title.contains(keyword))
    if task_category:
        q = q.filter(TaskItem.task_category == task_category)

    total = q.count()

    # 排序：按截止日期（NULL排最后），再按排序字段
    items = q.order_by(
        case((TaskItem.deadline == None, 1), else_=0),
        TaskItem.deadline.asc(),
        TaskItem.sort_order.asc(),
        TaskItem.id.desc(),
    ).offset((page - 1) * page_size).limit(page_size).all()

    item_list = []
    for t in items:
        remaining = None
        if t.deadline:
            remaining = (t.deadline - date.today()).days
        item_list.append({
            "id": t.id,
            "task_title": t.task_title,
            "deadline": t.deadline,
            "remaining_days": remaining,
            "task_category": t.task_category,
            "status": t.status,
            "notes": t.notes,
            "sort_order": t.sort_order,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": item_list,
    }
