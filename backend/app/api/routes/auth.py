"""认证API路由"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...models.database import User, get_db
from ...models.schemas import (
    UserRegister, UserLogin, Token, UserInfo, UserResponse
)
from ...services.auth_service import (
    hash_password, verify_password, create_access_token, get_current_user
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )
    
    # 创建新用户
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        success=True,
        message="注册成功",
        data=UserInfo(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            created_at=new_user.created_at.isoformat()
        )
    )


@router.post("/login", response_model=Token, summary="用户登录")
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户（支持用户名或邮箱登录）
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌（sub 必须是字符串）
    access_token = create_access_token(data={"sub": str(user.id)})
    
    print(f"✅ 用户 {user.username} (ID: {user.id}) 登录成功")
    print(f"🔑 生成的 token: {access_token[:30]}...")
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserResponse(
        success=True,
        message="获取成功",
        data=UserInfo(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            created_at=current_user.created_at.isoformat()
        )
    )

