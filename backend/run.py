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
    reload_dirs = [str(backend_dir / "app")]
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_dirs=reload_dirs,
        reload_excludes=[
            "*.pyc", "*.pyo", "*.pyd", 
            "__pycache__", "*.so", 
            ".venv/**", "venv/**", 
            ".git/**", "*.log",
            "*.pyc", "*.py~", "*.swp"
        ],
        log_level=settings.log_level.lower()
    )

