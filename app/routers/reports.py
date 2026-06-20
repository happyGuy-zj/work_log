from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_id, get_user, can_view_user
from app.schemas import ReportGenerate, ReportUpdate
from app.services.report_service import generate_report, list_reports, get_report, update_report

router = APIRouter(prefix="/reports", tags=["周报"])


@router.post("/generate")
def api_generate_report(
    data: ReportGenerate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_user(db, user_id)
    report = generate_report(db, user_id, data.week_start)
    return {"code": 0, "message": "success", "data": {
        "id": report.id, "user_id": report.user_id,
        "week_start": report.week_start, "week_end": report.week_end,
        "content": report.content, "status": report.status,
        "generated_at": report.generated_at, "edited_at": report.edited_at,
    }}


@router.get("")
def api_list_reports(
    week_start: date | None = None,
    target_user_id: int | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    if target_user_id and target_user_id != user_id:
        if not can_view_user(db, user, target_user_id):
            raise HTTPException(status_code=403, detail="无权查看该用户周报")
        user_ids = [target_user_id]
    else:
        from app.services.permission import get_viewable_user_ids
        user_ids = get_viewable_user_ids(db, user)

    reports = list_reports(db, user_ids, week_start)
    return {"code": 0, "message": "success", "data": [
        {
            "id": r.id, "user_id": r.user_id,
            "week_start": r.week_start, "week_end": r.week_end,
            "status": r.status, "generated_at": r.generated_at,
        }
        for r in reports
    ]}


@router.get("/{report_id}")
def api_get_report(
    report_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    report = get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="周报不存在")
    if not can_view_user(db, user, report.user_id):
        raise HTTPException(status_code=403, detail="无权查看该周报")
    return {"code": 0, "message": "success", "data": {
        "id": report.id, "user_id": report.user_id,
        "week_start": report.week_start, "week_end": report.week_end,
        "content": report.content, "status": report.status,
        "generated_at": report.generated_at, "edited_at": report.edited_at,
    }}


@router.put("/{report_id}")
def api_update_report(
    report_id: int,
    data: ReportUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = get_user(db, user_id)
    report = get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="周报不存在")
    if report.user_id != user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改该周报")
    report = update_report(db, report, content=data.content, status=data.status)
    return {"code": 0, "message": "success", "data": {
        "id": report.id, "user_id": report.user_id,
        "week_start": report.week_start, "week_end": report.week_end,
        "content": report.content, "status": report.status,
        "generated_at": report.generated_at, "edited_at": report.edited_at,
    }}