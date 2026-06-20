from sqlalchemy.orm import Session
from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate


def list_projects(db: Session, keyword: str | None = None, is_active: int = 1) -> list[Project]:
    q = db.query(Project)
    if is_active is not None:
        q = q.filter(Project.is_active == is_active)
    if keyword:
        q = q.filter(Project.name.contains(keyword))
    return q.order_by(Project.id).all()


def get_project(db: Session, project_id: int) -> Project | None:
    return db.query(Project).filter(Project.id == project_id).first()


def create_project(db: Session, data: ProjectCreate, user_id: int) -> Project:
    existing = db.query(Project).filter(Project.name == data.name).first()
    if existing:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=f"项目 '{data.name}' 已存在")
    proj = Project(name=data.name, description=data.description, created_by=user_id)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


def update_project(db: Session, project: Project, data: ProjectUpdate) -> Project:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project):
    """软删除：设置 is_active=0"""
    project.is_active = 0
    db.commit()
