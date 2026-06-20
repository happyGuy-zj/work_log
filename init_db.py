"""
数据库初始化脚本
运行方式：python init_db.py
功能：创建所有表 + 插入初始数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import Department, User, Category, Project, TaskItem, BacklogItem
from dotenv import load_dotenv

load_dotenv()


def init():
    # 创建所有表
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("表创建完成！")

    db = SessionLocal()
    try:
        # 检查是否已有初始数据
        if db.query(Department).count() > 0:
            print("初始数据已存在，跳过。")
            return

        # 创建默认部门
        dept = Department(name="IT部")
        db.add(dept)
        db.flush()

        # 创建管理员用户
        admin = User(
            username="zhengjie",
            display_name="郑杰",
            dept_id=dept.id,
            role="admin",
        )
        db.add(admin)
        db.flush()

        # 设置部门主管
        dept.leader_id = admin.id

        # 创建默认分类（对应 Excel 中的「任务分类」）
        default_categories = [
            "运维工单", "Bug工单", "临时任务", "迭代项",
            "SRM项目", "培训", "紧急插入临时任务",
            "按需采购", "年度任务", "绩效", "STO项目",
            "开发", "会议", "学习", "沟通", "其他",
        ]
        for i, cat_name in enumerate(default_categories, 1):
            cat = Category(name=cat_name, user_id=admin.id, sort_order=i)
            db.add(cat)

        db.commit()
        print("初始数据插入完成！")
        print(f"  部门：{dept.name}（ID: {dept.id}）")
        print(f"  管理员：{admin.username}（ID: {admin.id}）")
        print(f"  默认分类：{', '.join(default_categories)}")
    except Exception as e:
        db.rollback()
        print(f"初始化失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init()
