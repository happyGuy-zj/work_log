from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.models import DailyLog, LogTag, Category, TaskItem
from app.schemas import DailyLogCreate, DailyLogUpdate


def get_log_out(log: DailyLog) -> dict:
    """将 ORM 对象转为输出字典"""
    return {
        "id": log.id,
        "user_id": log.user_id,
        "log_date": log.log_date,
        "category": {"id": log.category.id, "name": log.category.name, "user_id": log.category.user_id, "sort_order": log.category.sort_order, "is_active": log.category.is_active} if log.category else None,
        "task_item": {
            "id": log.task_item.id,
            "task_title": log.task_item.task_title,
            "task_category": log.task_item.task_category,
            "status": log.task_item.status,
            "notes": log.task_item.notes,
        } if log.task_item else None,
        "task_title": log.task_title,
        "task_detail": log.task_detail,
        "reference": log.reference,
        "work_type": log.work_type,
        "change_type": log.change_type,
        "tcode": log.tcode,
        "program_name": log.program_name,
        "interface_name": log.interface_name,
        "enhancement_name": log.enhancement_name,
        "class_name": log.class_name,
        "print_name": log.print_name,
        "status": log.status,
        "time_spent": float(log.time_spent) if log.time_spent else None,
        "priority": log.priority,
        "tags": [t.tag for t in log.tags],
        "created_at": log.created_at,
        "updated_at": log.updated_at,
    }


def create_log(db: Session, user_id: int, data: DailyLogCreate) -> DailyLog:
    log = DailyLog(
        user_id=user_id,
        log_date=data.log_date,
        category_id=data.category_id,
        task_item_id=data.task_item_id,
        task_title=data.task_title,
        task_detail=data.task_detail,
        reference=data.reference,
        work_type=data.work_type,
        change_type=data.change_type,
        tcode=data.tcode,
        program_name=data.program_name,
        interface_name=data.interface_name,
        enhancement_name=data.enhancement_name,
        class_name=data.class_name,
        print_name=data.print_name,
        status=data.status,
        time_spent=data.time_spent,
        priority=data.priority,
    )
    db.add(log)
    db.flush()

    if data.tags:
        for tag_name in data.tags:
            db.add(LogTag(log_id=log.id, tag=tag_name))
        db.flush()

    db.commit()
    db.refresh(log)
    return log


def update_log(db: Session, log: DailyLog, data: DailyLogUpdate) -> DailyLog:
    update_data = data.model_dump(exclude_unset=True, exclude={"tags"})
    for field, value in update_data.items():
        setattr(log, field, value)

    if data.tags is not None:
        db.query(LogTag).filter(LogTag.log_id == log.id).delete()
        for tag_name in data.tags:
            db.add(LogTag(log_id=log.id, tag=tag_name))

    db.commit()
    db.refresh(log)
    return log


def delete_log(db: Session, log: DailyLog):
    db.delete(log)
    db.commit()


def query_logs(
    db: Session,
    user_ids: list[int],
    log_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    task_item_id: int | None = None,
    status: str | None = None,
    work_type: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    q = db.query(DailyLog).filter(DailyLog.user_id.in_(user_ids))

    if log_date:
        q = q.filter(DailyLog.log_date == log_date)
    if date_from:
        q = q.filter(DailyLog.log_date >= date_from)
    if date_to:
        q = q.filter(DailyLog.log_date <= date_to)
    if category_id:
        q = q.filter(DailyLog.category_id == category_id)
    if task_item_id:
        q = q.filter(DailyLog.task_item_id == task_item_id)
    if status:
        q = q.filter(DailyLog.status == status)
    if work_type:
        q = q.filter(DailyLog.work_type == work_type)
    if keyword:
        q = q.filter(
            (DailyLog.task_title.contains(keyword)) | (DailyLog.task_detail.contains(keyword))
        )

    total = q.count()
    items = q.order_by(DailyLog.log_date.desc(), DailyLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [get_log_out(item) for item in items],
    }


def get_summary(
    db: Session,
    user_ids: list[int],
    date_from: date | None = None,
    date_to: date | None = None,
    group_by: str = "date",
) -> dict:
    q = db.query(DailyLog).filter(DailyLog.user_id.in_(user_ids))

    if date_from:
        q = q.filter(DailyLog.log_date >= date_from)
    if date_to:
        q = q.filter(DailyLog.log_date <= date_to)

    total_row = db.query(
        func.count(DailyLog.id),
        func.coalesce(func.sum(DailyLog.time_spent), 0),
    ).filter(DailyLog.user_id.in_(user_ids))

    if date_from:
        total_row = total_row.filter(DailyLog.log_date >= date_from)
    if date_to:
        total_row = total_row.filter(DailyLog.log_date <= date_to)

    total_records, total_hours_val = total_row.first()
    total_hours = float(total_hours_val or 0)

    if group_by == "category":
        group_col = Category.name
    elif group_by == "work_type":
        group_col = DailyLog.work_type
    else:
        group_col = DailyLog.log_date

    group_q = (
        db.query(
            group_col.label("key"),
            func.count(DailyLog.id).label("record_count"),
            func.coalesce(func.sum(DailyLog.time_spent), 0).label("total_hours"),
        )
        .outerjoin(Category, DailyLog.category_id == Category.id)
        .filter(DailyLog.user_id.in_(user_ids))
    )

    if date_from:
        group_q = group_q.filter(DailyLog.log_date >= date_from)
    if date_to:
        group_q = group_q.filter(DailyLog.log_date <= date_to)

    group_results = group_q.group_by(group_col).order_by(group_col).all()

    groups = []
    for row in group_results:
        key = row.key if row.key is not None else "未分类"

        cat_q = (
            db.query(
                func.coalesce(Category.name, "未分类").label("cat_name"),
                func.coalesce(func.sum(DailyLog.time_spent), 0).label("cat_hours"),
            )
            .outerjoin(Category, DailyLog.category_id == Category.id)
            .filter(DailyLog.user_id.in_(user_ids))
        )

        if group_by == "category":
            cat_q = cat_q.filter(Category.name == row.key)
        else:
            cat_q = cat_q.filter(DailyLog.log_date == row.key)

        if date_from:
            cat_q = cat_q.filter(DailyLog.log_date >= date_from)
        if date_to:
            cat_q = cat_q.filter(DailyLog.log_date <= date_to)

        cat_results = cat_q.group_by(func.coalesce(Category.name, "未分类")).all()
        categories = {cr.cat_name: round(float(cr.cat_hours or 0), 1) for cr in cat_results}

        groups.append({
            "key": str(key),
            "record_count": row.record_count,
            "total_hours": round(float(row.total_hours or 0), 1),
            "categories": categories,
        })

    return {
        "total_records": total_records,
        "total_hours": round(total_hours, 1),
        "groups": groups,
    }
