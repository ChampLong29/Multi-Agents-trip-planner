"""FastAPI主应用"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..config import get_settings, validate_config, print_config
from .routes import trip, poi, map as map_routes, auth, history

# 获取配置
settings = get_settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="智能旅行规划系统API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trip.router, prefix="/api")
app.include_router(poi.router, prefix="/api")
app.include_router(map_routes.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(history.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("\n" + "="*60)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("="*60)
    
    # 初始化数据库
    from ..models.database import init_db
    init_db()
    
    # 打印配置信息
    print_config()
    
    # 验证配置
    try:
        validate_config()
        print("\n✅ 配置验证通过")
    except ValueError as e:
        print(f"\n❌ 配置验证失败:\n{e}")
        print("\n请检查.env文件并确保所有必要的配置项都已设置")
        raise
    
    print("\n" + "="*60)
    print("📚 API文档: http://localhost:8000/docs")
    print("📖 ReDoc文档: http://localhost:8000/redoc")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("\n" + "="*60)
    print("👋 应用正在关闭...")
    print("="*60 + "\n")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    from pathlib import Path
    
    # 获取项目根目录
    backend_dir = Path(__file__).parent.parent.parent.absolute()
    app_dir = backend_dir / "app"
    venv_dir = backend_dir / ".venv"
    data_dir = backend_dir / "data"
    
    reload_dirs = [str(app_dir)]
    reload_includes = ["*.py"]
    
    reload_excludes = [
        "**/*.pyc", "**/*.pyo", "**/*.pyd", 
        "**/__pycache__/**", "**/*.so", 
        "**/.venv/**", "**/venv/**", ".venv/**", "venv/**", str(venv_dir) + "/**",
        "**/.git/**", ".git/**", "**/*.log",
        "**/*.py~", "**/*.swp",
        "**/*.db", "**/*.sqlite", "**/*.sqlite3",
        "**/data/**", "data/**", str(data_dir) + "/**",
        "**/*.db-journal", "**/*.db-wal", "**/*.db-shm",
        "**/uv.lock", "uv.lock", "**/*.lock"
    ]
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_dirs=reload_dirs,
        reload_includes=reload_includes,
        reload_excludes=reload_excludes
    )

