import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import logs, categories, users, reports, tasks, backlog
from app.config import settings
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("work-log")

app = FastAPI(
    title="Work Log 工作记录系统",
    version="3.0",
    description="工作记录管理 API，支持多用户、分类配置、任务追踪、待开发项、周报生成",
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.0f}ms)")
    return response

# 跨域支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(logs.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(backlog.router, prefix="/api")


@app.get("/")
def root():
    return {"name": "Work Log API", "version": "3.0", "docs": "/docs"}


@app.get("/health")
def health():
    from app.database import engine
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            db_ok = True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
    return {"status": "ok" if db_ok else "degraded", "db": "connected" if db_ok else "disconnected"}

# 前端页面
@app.get("/app")
def serve_frontend():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
