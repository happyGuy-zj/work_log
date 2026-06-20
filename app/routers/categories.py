from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_id, get_user
from app.models import Category
from app.schemas import CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["分类配置"])


@router.get("")
def api_list_categories(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    cats = db.query(Category).filter(
        Category.user_id == user_id, Category.is_active == 1
    ).order_by(Category.sort_order).all()
    return {"code": 0, "message": "success", "data": [
        {"id": c.id, "name": c.name, "user_id": c.user_id, "sort_order": c.sort_order, "is_active": c.is_active}
        for c in cats
    ]}


@router.post("")
def api_create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_user(db, user_id)
    existing = db.query(Category).filter(Category.name == data.name, Category.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"分类 '{data.name}' 已存在")
    cat = Category(name=data.name, user_id=user_id, sort_order=data.sort_order)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {"code": 0, "message": "success", "data": {
        "id": cat.id, "name": cat.name, "user_id": cat.user_id, "sort_order": cat.sort_order, "is_active": cat.is_active
    }}


@router.put("/{category_id}")
def api_update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_user(db, user_id)
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    if cat.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权修改该分类")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return {"code": 0, "message": "success", "data": {
        "id": cat.id, "name": cat.name, "user_id": cat.user_id, "sort_order": cat.sort_order, "is_active": cat.is_active
    }}


@router.delete("/{category_id}")
def api_delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_user(db, user_id)
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    if cat.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权删除该分类")
    # 软删除
    cat.is_active = 0
    db.commit()
    return {"code": 0, "message": "success"}
