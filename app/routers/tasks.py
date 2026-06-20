from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_id, get_user
from app.services.task_service import (
    create_task, update_task, delete_task, query_tasks, get_task_stats, get_task_out
)
from app.models import TaskItem
from app.schemas import TaskItemCreate, TaskItemUpdate

router = APIRouter(prefix="/tasks", tags=["任务项"])


@router.post("")
def api_create_task(
    data: TaskItemCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    task = create_task(db, user_id, data)
    return {"code": 0, "message": "success", "data": get_task_out(task)}


@router.get("")
def api_list_tasks(
    status: str | None = None,
    task_category: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    result = query_tasks(
        db, user_id=user_id,
        status=status, task_category=task_category, keyword=keyword,
        page=page, page_size=page_size,
    )
    return {"code": 0, "message": "success", "data": result}


@router.get("/stats")
def api_task_stats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    stats = get_task_stats(db, user_id)
    return {"code": 0, "message": "success", "data": stats}


@router.get("/{task_id}")
def api_get_task(
    task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    task = db.query(TaskItem).filter(TaskItem.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权查看该任务")
    return {"code": 0, "message": "success", "data": get_task_out(task)}


@router.put("/{task_id}")
def api_update_task(
    task_id: int,
    data: TaskItemUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    task = db.query(TaskItem).filter(TaskItem.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权修改该任务")
    task = update_task(db, task, data)
    return {"code": 0, "message": "success", "data": get_task_out(task)}


@router.delete("/{task_id}")
def api_delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    task = db.query(TaskItem).filter(TaskItem.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权删除该任务")
    delete_task(db, task)
    return {"code": 0, "message": "success"}
