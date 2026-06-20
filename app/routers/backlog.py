from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_id, get_user
from app.services.backlog_service import query_backlog

router = APIRouter(prefix="/backlog", tags=["待开发项"])


@router.get("")
def api_list_backlog(
    keyword: str | None = None,
    task_category: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """待开发项 = 所有未完成的任务项（只读视图，不允许手动新增/编辑/删除）"""
    user = get_user(db, user_id)
    result = query_backlog(
        db, user_id=user_id,
        keyword=keyword, task_category=task_category,
        page=page, page_size=page_size,
    )
    return {"code": 0, "message": "success", "data": result}
