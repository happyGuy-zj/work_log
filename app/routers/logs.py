from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.auth import get_current_user_id, get_user, can_view_user
from app.services.permission import get_viewable_user_ids
from app.services.log_service import create_log, update_log, delete_log, query_logs, get_summary
from app.models import DailyLog
from app.schemas import DailyLogCreate, DailyLogUpdate

router = APIRouter(prefix="/logs", tags=["工作记录"])


@router.post("")
def api_create_log(
    data: DailyLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    log = create_log(db, user_id, data)
    from app.services.log_service import get_log_out
    return {"code": 0, "message": "success", "data": get_log_out(log)}


@router.get("")
def api_list_logs(
    log_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    task_item_id: int | None = None,
    status: str | None = None,
    work_type: str | None = None,
    keyword: str | None = None,
    target_user_id: int | None = Query(None, alias="user_id"),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)

    if target_user_id and target_user_id != user_id:
        if not can_view_user(db, user, target_user_id):
            raise HTTPException(status_code=403, detail="无权查看该用户数据")
        user_ids = [target_user_id]
    else:
        user_ids = [user_id]

    result = query_logs(
        db, user_ids=user_ids, log_date=log_date, date_from=date_from, date_to=date_to,
        category_id=category_id, task_item_id=task_item_id, status=status,
        work_type=work_type, keyword=keyword,
        page=page, page_size=page_size,
    )
    return {"code": 0, "message": "success", "data": result}


@router.get("/summary")
def api_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    group_by: str = "date",
    target_user_id: int | None = Query(None, alias="user_id"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)

    if target_user_id and target_user_id != user_id:
        if not can_view_user(db, user, target_user_id):
            raise HTTPException(status_code=403, detail="无权查看该用户数据")
        user_ids = [target_user_id]
    else:
        user_ids = get_viewable_user_ids(db, user)

    result = get_summary(db, user_ids=user_ids, date_from=date_from, date_to=date_to, group_by=group_by)
    return {"code": 0, "message": "success", "data": result}


@router.get("/{log_id}")
def api_get_log(
    log_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="记录不存在")
    if not can_view_user(db, user, log.user_id):
        raise HTTPException(status_code=403, detail="无权查看该记录")
    from app.services.log_service import get_log_out
    return {"code": 0, "message": "success", "data": get_log_out(log)}


@router.put("/{log_id}")
def api_update_log(
    log_id: int,
    data: DailyLogUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="记录不存在")
    if log.user_id != user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改该记录")
    log = update_log(db, log, data)
    from app.services.log_service import get_log_out
    return {"code": 0, "message": "success", "data": get_log_out(log)}


@router.delete("/{log_id}")
def api_delete_log(
    log_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="记录不存在")
    if log.user_id != user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除该记录")
    delete_log(db, log)
    return {"code": 0, "message": "success"}
