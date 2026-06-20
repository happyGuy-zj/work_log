"""
Work Log MCP Server
AI 助手通过 MCP 协议直接操作工作记录系统

配置方式（Cursor / Claude Desktop / AnythingLLM 等）：
{
  "mcpServers": {
    "work-log": {
      "command": "python",
      "args": ["D:/work-log/mcp_server.py"],
      "env": {
        "WORK_LOG_USER_ID": "1",
        "WORK_LOG_API_URL": "http://localhost:8000/api"
      }
    }
  }
}
"""
import os
import json
from datetime import date, datetime, timedelta
from typing import Optional

# MCP SDK
from mcp.server.fastmcp import FastMCP

# 项目内部
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import DailyLog, Category, LogTag, User, WeeklyReport, TaskItem, BacklogItem
from app.services.log_service import create_log, get_log_out, query_logs as svc_query_logs
from app.services.report_service import generate_report as svc_generate_report
from app.services.task_service import create_task, update_task, get_task_out, query_tasks as svc_query_tasks, get_task_stats
from app.services.backlog_service import query_backlog as svc_query_backlog
from app.schemas import DailyLogCreate, DailyLogUpdate, ReportGenerate, TaskItemCreate, TaskItemUpdate

mcp = FastMCP("work-log")

API_URL = os.getenv("WORK_LOG_API_URL", "http://localhost:8000/api")
DEFAULT_USER_ID = int(os.getenv("WORK_LOG_USER_ID", "1"))


# ============ 工作记录 ============

@mcp.tool()
def add_log(
    title: str,
    date_str: str = None,
    category_name: str = None,
    task_item_title: str = None,
    detail: str = None,
    reference: str = None,
    work_type: str = None,
    change_type: str = None,
    tcode: str = None,
    program_name: str = None,
    interface_name: str = None,
    enhancement_name: str = None,
    class_name: str = None,
    print_name: str = None,
    time_spent: float = None,
    status: str = "done",
) -> str:
    """
    新增一条工作记录。

    Args:
        title: 任务标题（必填）
        date_str: 日期，格式 YYYY-MM-DD，默认今天
        category_name: 分类名称，如"迭代项"、"运维"，需与分类配置中的名称一致
        task_item_title: 关联任务项的标题，会自动匹配未完成的任务项
        detail: 任务详情/备注
        reference: 参考信息
        work_type: 类型（Bug/Report/功能/增强/接口/学习/培训/打印/问题排查）
        change_type: 新增or修改（新增/修改）
        tcode: SAP事务码
        program_name: SAP程序名
        interface_name: SAP接口名
        enhancement_name: SAP增强名
        class_name: SAP类名
        print_name: SAP打印名
        time_spent: 耗时（小时）
        status: 状态 doing/done/blocked/cancelled，默认done
    """
    db = SessionLocal()
    try:
        user_id = DEFAULT_USER_ID
        log_date = date.fromisoformat(date_str) if date_str else date.today()

        # 解析分类
        category_id = None
        if category_name:
            cat = db.query(Category).filter(
                Category.name == category_name,
                Category.user_id == user_id,
                Category.is_active == 1,
            ).first()
            if cat:
                category_id = cat.id
            else:
                return json.dumps({"code": 400, "message": f"分类 '{category_name}' 不存在，请先在分类配置中添加，或使用 list_categories 查看可用分类"}, ensure_ascii=False)

        # 解析关联任务项（按标题模糊匹配未完成任务）
        task_item_id = None
        if task_item_title:
            task = db.query(TaskItem).filter(
                TaskItem.user_id == user_id,
                TaskItem.status == "未完成",
                TaskItem.task_title.contains(task_item_title),
            ).first()
            if task:
                task_item_id = task.id
                # 如果没指定分类，自动带出任务项的分类
                if not category_id and task.task_category:
                    cat = db.query(Category).filter(
                        Category.name == task.task_category,
                        Category.user_id == user_id,
                        Category.is_active == 1,
                    ).first()
                    if cat:
                        category_id = cat.id
            # 找不到也允许创建，只是不关联

        data = DailyLogCreate(
            log_date=log_date,
            category_id=category_id,
            task_item_id=task_item_id,
            task_title=title,
            task_detail=detail,
            reference=reference,
            work_type=work_type,
            change_type=change_type,
            tcode=tcode,
            program_name=program_name,
            interface_name=interface_name,
            enhancement_name=enhancement_name,
            class_name=class_name,
            print_name=print_name,
            status=status,
            time_spent=time_spent,
        )
        log = create_log(db, user_id, data)
        result = get_log_out(log)
        return json.dumps({"code": 0, "message": "记录成功", "data": result}, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"code": 500, "message": str(e)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def query_logs(
    date_str: str = None,
    date_from: str = None,
    date_to: str = None,
    category_name: str = None,
    work_type: str = None,
    keyword: str = None,
    status: str = None,
) -> str:
    """
    查询工作记录。

    Args:
        date_str: 精确日期 YYYY-MM-DD
        date_from: 起始日期
        date_to: 结束日期
        category_name: 分类名称
        work_type: 工作类型
        keyword: 标题/详情关键词
        status: 状态筛选（doing/done/blocked/cancelled）
    """
    db = SessionLocal()
    try:
        user_id = DEFAULT_USER_ID

        category_id = None
        if category_name:
            cat = db.query(Category).filter(Category.name == category_name, Category.user_id == user_id).first()
            if cat:
                category_id = cat.id

        result = svc_query_logs(
            db,
            user_ids=[user_id],
            log_date=date.fromisoformat(date_str) if date_str else None,
            date_from=date.fromisoformat(date_from) if date_from else None,
            date_to=date.fromisoformat(date_to) if date_to else None,
            category_id=category_id,
            work_type=work_type,
            keyword=keyword,
            status=status,
            page=1,
            page_size=50,
        )
        return json.dumps({"code": 0, "data": result["items"], "total": result["total"]}, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"code": 500, "message": str(e)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def daily_summary(date_str: str = None) -> str:
    """
    获取某天的工作汇总。

    Args:
        date_str: 日期 YYYY-MM-DD，默认今天
    """
    db = SessionLocal()
    try:
        user_id = DEFAULT_USER_ID
        target_date = date.fromisoformat(date_str) if date_str else date.today()

        logs = db.query(DailyLog).filter(
            DailyLog.user_id == user_id, DailyLog.log_date == target_date
        ).all()

        total_hours = sum(float(l.time_spent) if l.time_spent else 0 for l in logs)
        items = []
        for l in logs:
            cat_name = l.category.name if l.category else "未分类"
            wt = f"[{l.work_type}]" if l.work_type else ""
            ct = f"[{l.change_type}]" if l.change_type else ""
            sap = ""
            if l.tcode: sap += f" T:{l.tcode}"
            if l.interface_name: sap += f" I:{l.interface_name}"
            if l.enhancement_name: sap += f" E:{l.enhancement_name}"
            task_info = f" ← {l.task_item.task_title}" if l.task_item else ""
            items.append(f"- {wt}{ct} [{cat_name}] {l.task_title}（{l.time_spent or 0}h）{sap}{task_info}")

        summary = f"📅 {target_date} 工作汇总\n合计：{round(total_hours, 1)}h，{len(logs)}条记录\n\n" + "\n".join(items)
        return summary
    except Exception as e:
        return f"查询失败：{e}"
    finally:
        db.close()


@mcp.tool()
def weekly_summary(date_str: str = None) -> str:
    """
    获取本周工作汇总。

    Args:
        date_str: 周内任意一天 YYYY-MM-DD，默认本周
    """
    db = SessionLocal()
    try:
        user_id = DEFAULT_USER_ID
        target = date.fromisoformat(date_str) if date_str else date.today()
        monday = target - timedelta(days=target.weekday())
        friday = monday + timedelta(days=4)

        logs = db.query(DailyLog).filter(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= monday,
            DailyLog.log_date <= friday,
        ).order_by(DailyLog.log_date).all()

        total_hours = sum(float(l.time_spent) if l.time_spent else 0 for l in logs)

        # 按分类分组
        categories: dict[str, list] = {}
        for l in logs:
            cname = l.category.name if l.category else "未分类"
            if cname not in categories:
                categories[cname] = []
            categories[cname].append(l)

        lines = [f"📊 本周工作汇总（{monday} ~ {friday}）"]
        lines.append(f"合计：{round(total_hours, 1)}h，{len(logs)}条记录\n")

        for cname, cat_logs in categories.items():
            cat_hours = sum(float(l.time_spent) if l.time_spent else 0 for l in cat_logs)
            lines.append(f"【{cname}】{round(cat_hours, 1)}h")
            for l in cat_logs:
                wt = f"[{l.work_type}]" if l.work_type else ""
                lines.append(f"  {l.log_date} | {wt} {l.task_title}（{l.time_spent or 0}h）")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return f"查询失败：{e}"
    finally:
        db.close()


# ============ 任务项 ============

@mcp.tool()
def list_tasks(status: str = None, task_category: str = None) -> str:
    """
    获取任务项列表。

    Args:
        status: 状态筛选（已完成/未完成/挂起/取消）
        task_category: 分类筛选
    """
    db = SessionLocal()
    try:
        result = svc_query_tasks(db, DEFAULT_USER_ID, status=status, task_category=task_category, page_size=50)
        items = []
        for t in result["items"]:
            remaining = t.get("remaining_days")
            if t.get("status") == "已完成":
                remain_str = "✅已完成"
            elif t.get("status") == "取消":
                remain_str = "❌已取消"
            elif remaining is not None and remaining < 0:
                remain_str = f"⚠️逾期{abs(remaining)}天"
            elif remaining is not None and remaining <= 3:
                remain_str = f"⏰剩余{remaining}天"
            elif remaining is not None:
                remain_str = f"剩余{remaining}天"
            else:
                remain_str = "无期限"
            items.append(f"  [{t['status']}] [{t.get('task_category','未分类')}] {t['task_title']} - 截止：{t.get('deadline','无')} {remain_str}")
        return f"任务项（共{result['total']}个）：\n" + "\n".join(items)
    except Exception as e:
        return f"查询失败：{e}"
    finally:
        db.close()


@mcp.tool()
def add_task(
    title: str,
    deadline: str = None,
    task_category: str = None,
    status: str = "未完成",
    notes: str = None,
) -> str:
    """
    新增任务项。

    Args:
        title: 任务标题（必填）
        deadline: 截止日期 YYYY-MM-DD
        task_category: 任务分类，需与分类配置中的名称一致（如"迭代项"、"运维"等）
        status: 状态（已完成/未完成/挂起/取消），默认未完成
        notes: 备注
    """
    db = SessionLocal()
    try:
        data = TaskItemCreate(
            task_title=title,
            deadline=date.fromisoformat(deadline) if deadline else None,
            task_category=task_category,
            status=status,
            notes=notes,
        )
        task = create_task(db, DEFAULT_USER_ID, data)
        return f"任务创建成功：{task.task_title}（ID: {task.id}）"
    except Exception as e:
        db.rollback()
        return f"创建失败：{e}"
    finally:
        db.close()


@mcp.tool()
def update_task(
    task_id: int,
    title: str = None,
    deadline: str = None,
    task_category: str = None,
    status: str = None,
    notes: str = None,
) -> str:
    """
    更新任务项。

    Args:
        task_id: 任务ID（必填）
        title: 新标题
        deadline: 新截止日期 YYYY-MM-DD
        task_category: 新分类
        status: 新状态（已完成/未完成/挂起/取消）
        notes: 新备注
    """
    db = SessionLocal()
    try:
        task = db.query(TaskItem).filter(TaskItem.id == task_id, TaskItem.user_id == DEFAULT_USER_ID).first()
        if not task:
            return f"任务不存在（ID: {task_id}）"

        update_data = {}
        if title is not None:
            update_data["task_title"] = title
        if deadline is not None:
            update_data["deadline"] = date.fromisoformat(deadline)
        if task_category is not None:
            update_data["task_category"] = task_category
        if status is not None:
            update_data["status"] = status
        if notes is not None:
            update_data["notes"] = notes

        if not update_data:
            return "没有需要更新的字段"

        data = TaskItemUpdate(**update_data)
        updated = update_task(db, task, data)
        result = get_task_out(updated)
        return f"任务更新成功：{updated.task_title}（ID: {updated.id}）\n" + json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        db.rollback()
        return f"更新失败：{e}"
    finally:
        db.close()


@mcp.tool()
def complete_task(task_id: int) -> str:
    """
    将任务标记为已完成。

    Args:
        task_id: 任务ID（必填）
    """
    db = SessionLocal()
    try:
        task = db.query(TaskItem).filter(TaskItem.id == task_id, TaskItem.user_id == DEFAULT_USER_ID).first()
        if not task:
            return f"任务不存在（ID: {task_id}）"
        data = TaskItemUpdate(status="已完成")
        updated = update_task(db, task, data)
        return f"任务已完成：{updated.task_title}（ID: {updated.id}）"
    except Exception as e:
        db.rollback()
        return f"操作失败：{e}"
    finally:
        db.close()


@mcp.tool()
def task_stats() -> str:
    """获取任务统计信息（总数、待办数、各状态数量等）。"""
    db = SessionLocal()
    try:
        stats = get_task_stats(db, DEFAULT_USER_ID)
        lines = [
            f"📊 任务统计",
            f"总任务数：{stats['total']}",
            f"待办任务：{stats['pending_count']}",
            f"即将到期（3天内）：{stats['urgent_count']}",
            f"\n按状态：",
        ]
        for s, c in stats.get("by_status", {}).items():
            lines.append(f"  {s}: {c}")
        lines.append("\n按分类：")
        for c, n in stats.get("by_category", {}).items():
            lines.append(f"  {c}: {n}")
        return "\n".join(lines)
    except Exception as e:
        return f"查询失败：{e}"
    finally:
        db.close()


# ============ 分类 ============

@mcp.tool()
def list_categories() -> str:
    """获取当前用户的分类列表（仅启用的）。"""
    db = SessionLocal()
    try:
        cats = db.query(Category).filter(
            Category.user_id == DEFAULT_USER_ID, Category.is_active == 1
        ).order_by(Category.sort_order).all()
        items = [f"  [{c.id}] {c.name}" for c in cats]
        return f"分类列表（共{len(cats)}个）：\n" + "\n".join(items)
    except Exception as e:
        return f"查询失败：{e}"
    finally:
        db.close()


@mcp.tool()
def create_category(name: str, sort_order: int = 0) -> str:
    """
    新增分类。

    Args:
        name: 分类名称
        sort_order: 排序权重
    """
    db = SessionLocal()
    try:
        existing = db.query(Category).filter(
            Category.name == name, Category.user_id == DEFAULT_USER_ID
        ).first()
        if existing:
            return f"分类 '{name}' 已存在（ID: {existing.id}）"
        cat = Category(name=name, user_id=DEFAULT_USER_ID, sort_order=sort_order)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return f"分类创建成功：{cat.name}（ID: {cat.id}）"
    except Exception as e:
        db.rollback()
        return f"创建失败：{e}"
    finally:
        db.close()


# ============ 周报 ============

@mcp.tool()
def generate_report(week_start: str = None) -> str:
    """
    自动生成周报。按分类分组汇总一周工作记录，输出 Markdown 格式。

    Args:
        week_start: 周一日期 YYYY-MM-DD，默认本周一
    """
    db = SessionLocal()
    try:
        if week_start:
            ws = date.fromisoformat(week_start)
        else:
            today = date.today()
            ws = today - timedelta(days=today.weekday())

        report = svc_generate_report(db, DEFAULT_USER_ID, ws)
        return report.content or "无工作记录，无法生成周报"
    except Exception as e:
        return f"生成失败：{e}"
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
