"""认证服务模块"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..models.database import User, get_db
from ..config import get_settings

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """加密密码"""
    # 将密码编码为字节
    password_bytes = password.encode('utf-8')
    # 生成盐并加密
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # 返回字符串格式的哈希值
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        # 将密码和哈希值都转换为字节
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        # 验证密码
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        print(f"⚠️ JWT验证失败: {str(e)}")
        return None
    except Exception as e:
        print(f"⚠️ Token验证异常: {str(e)}")
        return None


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """从token获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        print("⚠️ 未提供 token")
        raise credentials_exception
    
    print(f"🔍 验证 token: {token[:20]}...")
    payload = verify_token(token)
    if payload is None:
        print("⚠️ Token 验证失败")
        raise credentials_exception
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        print("⚠️ Token 中未找到用户ID")
        raise credentials_exception
    
    # sub 是字符串，需要转换为整数
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        print(f"⚠️ 无效的用户ID格式: {user_id_str}")
        raise credentials_exception
    
    print(f"🔍 查找用户 ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print(f"⚠️ 用户 ID {user_id} 不存在")
        raise credentials_exception
    
    print(f"✅ 用户验证成功: {user.username}")
    return user


def get_current_user_optional(
    request: "Request",
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选，用于未登录用户）"""
    from fastapi import Request
    
    # 从请求头中获取 token
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization[7:]
    
    try:
        payload = verify_token(token)
        if payload is None:
            return None
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        
        # sub 是字符串，需要转换为整数
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None

