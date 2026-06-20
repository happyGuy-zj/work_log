from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import DailyLog, WeeklyReport


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

    # 按分类 + 任务合并（同一任务多天记录合并为一条）
    # 合并key：优先用 task_item_id，否则用 task_title
    category_groups: dict[str, dict[str, dict]] = {}
    total_hours = 0.0

    for log in logs:
        hours = float(log.time_spent) if log.time_spent else 0
        total_hours += hours

        if log.category:
            cname = log.category.name
        else:
            cname = "其他"

        if cname not in category_groups:
            category_groups[cname] = {}

        # 合并key：关联同一任务项 或 标题完全相同
        merge_key = str(log.task_item_id) if log.task_item_id else log.task_title

        if merge_key in category_groups[cname]:
            # 合并到已有条目
            existing = category_groups[cname][merge_key]
            existing["hours"] += hours
            existing["days"].add(str(log.log_date))
            # 合并详情：直接收集，输出时统一做片段级去重
            if log.task_detail:
                existing["details"].append(log.task_detail)
            # 状态取最新的（done优先于doing，doing优先于blocked）
            status_priority = {"done": 3, "doing": 2, "blocked": 1, "cancelled": 0}
            if status_priority.get(log.status, 0) > status_priority.get(existing["status"], 0):
                existing["status"] = log.status
            # 合并work_type（去重）
            if log.work_type and log.work_type not in existing["work_types"]:
                existing["work_types"].append(log.work_type)
            # 合并change_type
            if log.change_type and log.change_type not in existing["change_types"]:
                existing["change_types"].append(log.change_type)
        else:
            category_groups[cname][merge_key] = {
                "title": log.task_title,
                "details": [log.task_detail] if log.task_detail else [],
                "days": {str(log.log_date)},
                "hours": hours,
                "status": log.status,
                "work_types": [log.work_type] if log.work_type else [],
                "change_types": [log.change_type] if log.change_type else [],
            }

    # 生成周报内容
    lines = []

    for cname, tasks in category_groups.items():
        lines.append(cname)
        for idx, (merge_key, e) in enumerate(tasks.items(), 1):
            # 标题
            item = f"{idx}. {e['title']}"
            detail_parts = []

            # 详情合并：拆成小片段去重后重新组合
            if e["details"]:
                # 把每条备注按中文逗号、顿号、分号拆成小片段
                all_fragments = []
                for d in e["details"]:
                    # 按常见分隔符拆分
                    import re
                    parts = re.split(r'[,，、；;]\s*', d.strip())
                    all_fragments.extend(p for p in parts if p)
                # 去重（保持首次出现顺序）
                seen = set()
                unique_fragments = []
                for f in all_fragments:
                    if f not in seen:
                        seen.add(f)
                        unique_fragments.append(f)
                merged_detail = "，".join(unique_fragments)
                item += "（" + merged_detail + "）"
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
