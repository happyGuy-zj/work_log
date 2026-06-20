from sqlalchemy.orm import Session
from app.models import User


def get_viewable_user_ids(db: Session, viewer: User) -> list[int]:
    """获取 viewer 能查看的所有用户ID"""
    if viewer.role == "admin":
        users = db.query(User).filter(User.is_active == 1).all()
    elif viewer.role == "leader":
        users = db.query(User).filter(
            User.dept_id == viewer.dept_id, User.is_active == 1
        ).all()
    else:
        users = [viewer]
    return [u.id for u in users]
