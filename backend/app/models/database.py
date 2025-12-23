"""数据库模型和配置"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# 数据库URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/trip_planner.db")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


# 用户模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 对话历史模型
class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# 旅行历史模型
class TripHistory(Base):
    __tablename__ = "trip_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    city = Column(String, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    travel_days = Column(Integer, nullable=True)  # 允许为空，兼容旧数据
    request_data = Column(JSON)  # 存储TripRequest的JSON数据
    plan_data = Column(JSON)  # 存储TripPlan的JSON数据
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 用户偏好模型
class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    preferences_json = Column(JSON)  # 存储用户偏好的JSON数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 数据库依赖注入
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 初始化数据库
def init_db():
    """初始化数据库，创建所有表"""
    # 确保数据目录存在
    if "sqlite" in DATABASE_URL:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 执行数据库迁移（添加缺失的列）
    _migrate_database()
    
    print("✅ 数据库初始化完成")


def _migrate_database():
    """执行数据库迁移，添加缺失的列"""
    from sqlalchemy import inspect, text
    
    inspector = inspect(engine)
    
    # 定义需要迁移的表和列
    table_migrations = {
        "trip_history": [
            ("travel_days", "INTEGER"),
            ("updated_at", "DATETIME")
        ],
        "user_preferences": [
            ("created_at", "DATETIME"),
            ("updated_at", "DATETIME")
        ],
        "users": [
            ("created_at", "DATETIME"),
            ("updated_at", "DATETIME")
        ],
        "conversation_history": [
            # 这个表应该已经有 created_at，检查即可
        ]
    }
    
    # 遍历所有需要迁移的表
    for table_name, required_columns in table_migrations.items():
        if table_name not in inspector.get_table_names():
            continue
        
        # 获取现有列
        existing_columns = [col["name"] for col in inspector.get_columns(table_name)]
        print(f"🔍 {table_name} 表现有列: {existing_columns}")
        
        # 需要添加的列列表
        columns_to_add = []
        for col_name, col_type in required_columns:
            if col_name not in existing_columns:
                columns_to_add.append((col_name, col_type))
        
        # 批量添加缺失的列
        if columns_to_add:
            print(f"🔄 正在更新 {table_name} 表，添加 {len(columns_to_add)} 个列...")
            with engine.connect() as conn:
                for col_name, col_type in columns_to_add:
                    try:
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                        print(f"  ✅ 已添加列: {table_name}.{col_name}")
                    except Exception as e:
                        print(f"  ⚠️ 添加列 {table_name}.{col_name} 时出错: {str(e)}")
                conn.commit()
    
    print("✅ 数据库迁移完成")

