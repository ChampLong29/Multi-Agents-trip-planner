"""启动脚本"""

import os
import uvicorn
from pathlib import Path
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    # 获取项目根目录
    backend_dir = Path(__file__).parent.absolute()
    
    # 只监控 app 目录，避免监控虚拟环境和其他目录
    app_dir = backend_dir / "app"
    reload_dirs = [str(app_dir)]
    
    # 使用 reload_includes 限制只监控 Python 文件
    reload_includes = ["*.py"]
    
    # 构建完整的排除列表，包括绝对路径
    venv_dir = backend_dir / ".venv"
    data_dir = backend_dir / "data"
    
    reload_excludes = [
        # Python 编译文件
        "**/*.pyc", "**/*.pyo", "**/*.pyd", 
        "**/__pycache__/**", "**/*.so",
        # 虚拟环境（使用多种模式确保匹配）
        "**/.venv/**", ".venv/**", str(venv_dir) + "/**",
        "**/venv/**", "venv/**",
        # Git 和日志
        "**/.git/**", ".git/**", "**/*.log",
        # 编辑器临时文件
        "**/*.py~", "**/*.swp", "**/*.swo", "**/*~",
        # 数据库文件
        "**/*.db", "**/*.sqlite", "**/*.sqlite3",
        "**/data/**", "data/**", str(data_dir) + "/**",
        "**/*.db-journal", "**/*.db-wal", "**/*.db-shm",
        # 锁文件
        "**/uv.lock", "uv.lock", "**/*.lock",
        # 其他
        "**/node_modules/**", "**/.pytest_cache/**"
    ]
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_dirs=reload_dirs,
        reload_includes=reload_includes,
        reload_excludes=reload_excludes,
        log_level=settings.log_level.lower()
    )

