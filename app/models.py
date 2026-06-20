from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Date, DateTime,
    Numeric, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


class Department(Base):
    __tablename__ = "department"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="部门名称")
    leader_id = Column(Integer, ForeignKey("user.id"), comment="部门主管ID")
    created_at = Column(DateTime, default=lambda: datetime.now(), comment="创建时间")

    leader = relationship("User", foreign_keys=[leader_id], backref="led_department")
    members = relationship("User", foreign_keys="User.dept_id", backref="department")


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, comment="登录名")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    dept_id = Column(Integer, ForeignKey("department.id"), comment="所属部门")
    role = Column(String(20), default="member", comment="角色：member/leader/admin")
    password_hash = Column(String(255), comment="密码哈希")
    is_active = Column(Integer, default=1, comment="是否启用")
    created_at = Column(DateTime, default=lambda: datetime.now(), comment="创建时间")


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="分类名称")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="所属用户")
    sort_order = Column(Integer, default=0, comment="排序权重")
    is_active = Column(Integer, default=1, comment="是否启用")
    created_at = Column(DateTime, default=lambda: datetime.now(), comment="创建时间")

    user = relationship("User")
    __table_args__ = (UniqueConstraint("name", "user_id", name="uk_category_user"),)


class DailyLog(Base):
    __tablename__ = "daily_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="记录人")
    log_date = Column(Date, nullable=False, comment="记录日期")
    category_id = Column(Integer, ForeignKey("category.id"), comment="分类ID")
    task_item_id = Column(BigInteger, ForeignKey("task_item.id"), comment="关联任务项ID")
    task_title = Column(String(200), nullable=False, comment="任务标题")
    task_detail = Column(Text, comment="任务详情/备注")
    reference = Column(String(500), comment="参考")
    # SAP 开发专属字段
    work_type = Column(String(20), comment="类型：Bug/Report/功能/增强/接口/学习/培训/打印/问题排查")
    change_type = Column(String(10), comment="新增or修改：新增/修改")
    tcode = Column(String(30), comment="事务码")
    program_name = Column(String(50), comment="程序名")
    interface_name = Column(String(200), comment="接口")
    enhancement_name = Column(String(200), comment="增强")
    class_name = Column(String(50), comment="类")
    print_name = Column(String(50), comment="打印")
    # 通用字段
    status = Column(String(20), default="done", comment="状态：doing/done/blocked/cancelled")
    time_spent = Column(Numeric(4, 1), comment="耗时(小时)")
    priority = Column(String(10), default="normal", comment="优先级：low/normal/high/urgent")
    created_at = Column(DateTime, default=lambda: datetime.now(), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now(), comment="更新时间")

    user = relationship("User")
    category = relationship("Category")
    task_item = relationship("TaskItem")
    tags = relationship("LogTag", back_populates="log", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_user_date", "user_id", "log_date"),
        Index("idx_task_item", "task_item_id"),
        Index("idx_category", "category_id"),
        Index("idx_status", "status"),
        Index("idx_work_type", "work_type"),
    )


class LogTag(Base):
    __tablename__ = "log_tag"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(BigInteger, ForeignKey("daily_log.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String(50), nullable=False, comment="标签名")

    log = relationship("DailyLog", back_populates="tags")

    __table_args__ = (
        Index("idx_tag_log_id", "log_id"),
        Index("idx_tag_name", "tag"),
    )


class TaskItem(Base):
    """任务项 - 对应 Excel「任务项」sheet"""
    __tablename__ = "task_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="所属用户")
    task_title = Column(String(300), nullable=False, comment="任务标题")
    deadline = Column(Date, comment="截止日期")
    task_category = Column(String(30), comment="任务分类")
    status = Column(String(20), default="未完成", comment="状态：已完成/未完成/挂起/取消")
    notes = Column(Text, comment="备注")
    sort_order = Column(Integer, default=0, comment="排序权重")
    created_at = Column(DateTime, default=lambda: datetime.now(), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now(), comment="更新时间")

    user = relationship("User")

    __table_args__ = (
        Index("idx_task_user", "user_id"),
        Index("idx_task_status", "status"),
        Index("idx_task_category", "task_category"),
        Index("idx_task_deadline", "deadline"),
    )


class BacklogItem(Base):
    """待开发项 - 对应 Excel「待开发项」sheet（已改为任务项的只读视图，此表保留但不使用）"""
    __tablename__ = "backlog_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="所属用户")
    task_title = Column(String(500), nullable=False, comment="任务标题")
    deadline = Column(Date, comment="截止日期")
    pending_count = Column(Integer, comment="待完成任务数")
    notes = Column(Text, comment="备注")
    sort_order = Column(Integer, default=0, comment="排序权重")
    created_at = Column(DateTime, default=lambda: datetime.now(), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now(), comment="更新时间")

    user = relationship("User")

    __table_args__ = (
        Index("idx_backlog_user", "user_id"),
        Index("idx_backlog_deadline", "deadline"),
    )


class WeeklyReport(Base):
    __tablename__ = "weekly_report"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="所属用户")
    week_start = Column(Date, nullable=False, comment="周一日期")
    week_end = Column(Date, nullable=False, comment="周五日期")
    content = Column(Text, comment="周报正文(Markdown)")
    generated_at = Column(DateTime, comment="AI生成时间")
    edited_at = Column(DateTime, comment="人工修改时间")
    status = Column(String(20), default="draft", comment="状态：draft/submitted/approved")
    created_at = Column(DateTime, default=lambda: datetime.now(), comment="创建时间")

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uk_user_week"),
    )


# 保留 Project 模型定义（数据库表可能仍存在），但不再使用
class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="项目名称")
    description = Column(String(500), comment="项目描述")
    created_by = Column(Integer, ForeignKey("user.id"), comment="创建人")
    is_active = Column(Integer, default=1, comment="是否活跃")
    created_at = Column(DateTime, default=lambda: datetime.now(), comment="创建时间")

    creator = relationship("User", foreign_keys=[created_by])
