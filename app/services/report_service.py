from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import DailyLog, WeeklyReport, Project


def get_week_range(week_start) -> tuple:
    """返回 (周一, 周五) 日期"""
    week_end = week_start + timedelta(days=4)
    return week_start, week_end


def generate_report(db: Session, user_id: int, week_start) -> WeeklyReport:
    """根据一周工作记录自动生成周报"""
    week_end = week_start + timedelta(days=4)

    # 查询该周的工作记录
    logs = (
        db.query(DailyLog)
        .filter(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= week_start,
            DailyLog.log_date <= week_end,
        )
        .order_by(DailyLog.log_date, DailyLog.id)
        .all()
    )

    # 按分类分组
    category_groups: dict[str, list] = {}
    total_hours = 0.0

    for log in logs:
        hours = float(log.time_spent) if log.time_spent else 0
        total_hours += hours
        entry = {
            "title": log.task_title,
            "detail": log.task_detail or "",
            "date": str(log.log_date),
            "hours": hours,
            "status": log.status,
        }
        if log.category:
            cname = log.category.name
        else:
            cname = "其他"
        if cname not in category_groups:
            category_groups[cname] = []
        category_groups[cname].append(entry)

    # 生成周报内容（匹配用户习惯格式）
    lines = []

    for cname, entries in category_groups.items():
        lines.append(cname)
        for idx, e in enumerate(entries, 1):
            # 拼接：序号. 任务标题
            item = f"{idx}. {e['title']}"
            # 拼接详情/进展
            detail_parts = []
            if e["detail"]:
                detail_parts.append(e["detail"])
            # 状态用中文补充
            status_text = ""
            if e["status"] == "done":
                status_text = "已完成"
            elif e["status"] == "doing":
                status_text = "进行中"
            elif e["status"] == "blocked":
                status_text = "阻塞"
            # 如果详情中已经包含了状态描述，就不重复追加
            if status_text and detail_parts and status_text not in detail_parts[0]:
                detail_parts[0] = detail_parts[0].rstrip("。；;,；") + "，" + status_text
            elif status_text and not detail_parts:
                detail_parts.append(status_text)
            # 耗时
            if e["hours"] > 0:
                detail_parts.append(f"耗时{e['hours']}h")

            if detail_parts:
                item += "（" + "；".join(detail_parts) + "）"
            item += "；"
            lines.append(item)
        lines.append("")

    # 如果没有任何记录
    if not lines:
        lines.append("本周暂无工作记录")

    content = "\n".join(lines)

    # 存入或更新周报
    existing = db.query(WeeklyReport).filter(
        WeeklyReport.user_id == user_id, WeeklyReport.week_start == week_start
    ).first()

    now = datetime.now()
    if existing:
        existing.content = content
        existing.generated_at = now
        existing.week_end = week_end
        db.commit()
        db.refresh(existing)
        return existing
    else:
        report = WeeklyReport(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            content=content,
            generated_at=now,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report


def list_reports(db: Session, user_ids: list[int], week_start=None) -> list[WeeklyReport]:
    q = db.query(WeeklyReport).filter(WeeklyReport.user_id.in_(user_ids))
    if week_start:
        q = q.filter(WeeklyReport.week_start == week_start)
    return q.order_by(WeeklyReport.week_start.desc()).all()


def get_report(db: Session, report_id: int) -> WeeklyReport | None:
    return db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()


def update_report(db: Session, report: WeeklyReport, content: str | None = None, status: str | None = None) -> WeeklyReport:
    from datetime import datetime
    if content is not None:
        report.content = content
        report.edited_at = datetime.now()
    if status is not None:
        report.status = status
    db.commit()
    db.refresh(report)
    return report
