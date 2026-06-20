from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_id, get_user
from app.services.project_service import list_projects, get_project, create_project, update_project, delete_project
from app.schemas import ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.get("")
def api_list_projects(
    keyword: str | None = None,
    is_active: int = 1,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_user(db, user_id)
    projects = list_projects(db, keyword=keyword, is_active=is_active)
    return {"code": 0, "message": "success", "data": [
        {
            "id": p.id, "name": p.name, "description": p.description,
            "created_by": p.created_by, "is_active": p.is_active, "created_at": p.created_at,
        }
        for p in projects
    ]}


@router.post("")
def api_create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_user(db, user_id)
    proj = create_project(db, data, user_id)
    return {"code": 0, "message": "success", "data": {
        "id": proj.id, "name": proj.name, "description": proj.description,
        "created_by": proj.created_by, "is_active": proj.is_active, "created_at": proj.created_at,
    }}


@router.put("/{project_id}")
def api_update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    proj = get_project(db, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    proj = update_project(db, proj, data)
    return {"code": 0, "message": "success", "data": {
        "id": proj.id, "name": proj.name, "description": proj.description,
        "created_by": proj.created_by, "is_active": proj.is_active, "created_at": proj.created_at,
    }}


@router.delete("/{project_id}")
def api_delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    proj = get_project(db, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    delete_project(db, proj)
    return {"code": 0, "message": "success"}
