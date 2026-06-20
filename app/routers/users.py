from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_id, get_user, require_role
from app.models import User, Department
from app.services.permission import get_viewable_user_ids

router = APIRouter(prefix="/users", tags=["用户与部门"])


@router.get("/me")
def api_get_me(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    return {"code": 0, "message": "success", "data": {
        "id": user.id, "username": user.username, "display_name": user.display_name,
        "dept_id": user.dept_id, "role": user.role, "is_active": user.is_active,
    }}


@router.get("")
def api_list_users(
    dept_id: int | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    if user.role not in ("admin", "leader"):
        raise HTTPException(status_code=403, detail="权限不足")

    q = db.query(User).filter(User.is_active == 1)
    if user.role == "leader":
        q = q.filter(User.dept_id == user.dept_id)
    if dept_id:
        if user.role == "leader" and dept_id != user.dept_id:
            raise HTTPException(status_code=403, detail="无权查看该部门")
        q = q.filter(User.dept_id == dept_id)

    users = q.all()
    return {"code": 0, "message": "success", "data": [
        {"id": u.id, "username": u.username, "display_name": u.display_name,
         "dept_id": u.dept_id, "role": u.role, "is_active": u.is_active}
        for u in users
    ]}


@router.get("/departments")
def api_list_departments(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_user(db, user_id)
    depts = db.query(Department).all()
    return {"code": 0, "message": "success", "data": [
        {"id": d.id, "name": d.name, "leader_id": d.leader_id}
        for d in depts
    ]}


@router.get("/departments/{dept_id}/members")
def api_dept_members(
    dept_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    if user.role == "admin" or (user.role == "leader" and user.dept_id == dept_id):
        members = db.query(User).filter(User.dept_id == dept_id, User.is_active == 1).all()
        return {"code": 0, "message": "success", "data": [
            {"id": m.id, "username": m.username, "display_name": m.display_name, "role": m.role}
            for m in members
        ]}
    raise HTTPException(status_code=403, detail="无权查看该部门成员")
