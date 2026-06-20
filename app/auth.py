from fastapi import Header, HTTPException
from sqlalchemy.orm import Session
from app.models import User


def get_current_user_id(x_user_id: int = Header(..., alias="X-User-Id")) -> int:
    """从请求头获取当前用户ID"""
    return x_user_id


def get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id, User.is_active == 1).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    return user


def require_role(user: User, *roles: str):
    """检查用户角色"""
    if user.role not in roles:
        raise HTTPException(status_code=403, detail="权限不足")


def can_view_user(db: Session, viewer: User, target_user_id: int) -> bool:
    """判断 viewer 是否能查看 target_user 的数据"""
    if viewer.role == "admin":
        return True
    if viewer.id == target_user_id:
        return True
    if viewer.role == "leader":
        target = db.query(User).filter(User.id == target_user_id).first()
        if target and target.dept_id == viewer.dept_id:
            return True
    return False


def get_viewable_user_ids(db: Session, viewer: User) -> list[int]:
    """获取 viewer 能查看的所有用户ID列表"""
    if viewer.role == "admin":
        users = db.query(User).filter(User.is_active == 1).all()
    elif viewer.role == "leader":
        users = db.query(User).filter(
            User.dept_id == viewer.dept_id, User.is_active == 1
        ).all()
    else:
        users = [viewer]
    return [u.id for u in users]
