import os
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce_ai.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY 环境变量必须设置！请在 .env 文件中配置")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# ==================== 数据模型 ====================

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    
    # 套餐信息
    plan = Column(String, default="free")  # free, newbie, growth, pro, premium
    plan_expire_date = Column(DateTime, nullable=True)
    
    # 使用次数
    select_count = Column(Integer, default=0)  # 选品次数
    select_limit = Column(Integer, default=30)  # 选品限制
    ads_count = Column(Integer, default=0)  # 投流分析次数
    ads_limit = Column(Integer, default=30)  # 投流分析限制
    
    # 账户信息
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    """订单表"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    plan = Column(String, nullable=False)  # newbie, growth, pro, premium
    duration = Column(String, nullable=False)  # monthly, yearly
    amount = Column(Float, nullable=False)  # 金额
    status = Column(String, default="pending")  # pending, approved, rejected, paid, cancelled
    payment_method = Column(String, nullable=True)  # alipay, wechat
    transaction_id = Column(String, nullable=True)  # 交易单号后4位
    note = Column(String, nullable=True)  # 备注
    reject_reason = Column(String, nullable=True)  # 拒绝原因
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)

class UsageLog(Base):
    """使用记录表"""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)  # select_product, analyze_ads
    details = Column(String, nullable=True)  # JSON格式的详细信息
    created_at = Column(DateTime, default=datetime.utcnow)

class AnalysisHistory(Base):
    """分析历史记录表"""
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    analysis_type = Column(String, nullable=False)  # product, ad
    input_data = Column(Text, nullable=True)  # JSON格式的输入数据
    result_data = Column(Text, nullable=True)  # JSON格式的结果数据
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class UserPromotionData(Base):
    """用户推广数据表"""
    __tablename__ = "user_promotion_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    data_type = Column(String, nullable=False)  # search, allsite, scene
    
    # 推广数据字段
    keyword = Column(String, nullable=True)  # 关键词（搜索推广）
    product_name = Column(String, nullable=True)  # 商品名称
    spend = Column(Float, nullable=False, default=0)  # 花费
    sales = Column(Float, nullable=False, default=0)  # 销售额
    roi = Column(Float, nullable=False, default=0)  # ROI
    clicks = Column(Integer, nullable=False, default=0)  # 点击数
    impressions = Column(Integer, nullable=False, default=0)  # 曝光数
    ctr = Column(Float, nullable=False, default=0)  # 点击率
    conversion_rate = Column(Float, nullable=False, default=0)  # 转化率
    cpc = Column(Float, nullable=False, default=0)  # 平均点击成本
    
    # 时间字段
    data_date = Column(DateTime, nullable=True)  # 数据日期
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Shop(Base):
    """店铺信息表"""
    __tablename__ = "shops"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    shop_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    monthly_revenue = Column(String, nullable=True)
    monthly_ad_spend = Column(String, nullable=True)
    main_products = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Admin(Base):
    """管理员表"""
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Competitor(Base):
    """竞品表"""
    __tablename__ = "competitors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)
    product_url = Column(String, nullable=True)
    category = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    monthly_sales = Column(Integer, nullable=True)
    ad_spend = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CompetitorSnapshot(Base):
    """竞品数据快照表"""
    __tablename__ = "competitor_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, nullable=False, index=True)
    price = Column(Float, nullable=True)
    monthly_sales = Column(Integer, nullable=True)
    ad_spend = Column(Float, nullable=True)
    ranking = Column(Integer, nullable=True)
    snapshot_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)



class Notification(Base):
    """通知表"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # risk, opportunity, report, system
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class NotificationSettings(Base):
    """通知设置表"""
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    notify_risks = Column(Boolean, default=True)  # 风险提醒
    notify_opportunities = Column(Boolean, default=True)  # 机会提醒
    notify_reports = Column(Boolean, default=True)  # 报告提醒
    email_enabled = Column(Boolean, default=False)  # 邮件通知
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ABTest(Base):
    """A/B 测试实验表"""
    __tablename__ = "ab_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="running")  # running, paused, completed
    
    # 实验配置
    variant_a_name = Column(String, default="对照组")
    variant_b_name = Column(String, default="实验组")
    
    # 实验数据
    variant_a_spend = Column(Float, default=0)
    variant_a_sales = Column(Float, default=0)
    variant_a_roi = Column(Float, default=0)
    
    variant_b_spend = Column(Float, default=0)
    variant_b_sales = Column(Float, default=0)
    variant_b_roi = Column(Float, default=0)
    
    # 时间
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 创建所有表
Base.metadata.create_all(bind=engine)

# ==================== 工具函数 ====================

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password[:72], hashed_password)

def get_password_hash(password: str) -> str:
    """加密密码（bcrypt 限制 72 字节）"""
    return pwd_context.hash(password[:72])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """解码JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

# ==================== 套餐配置 ====================

PLANS = {
    "free": {
        "name": "免费版",
        "price_monthly": 0,
        "price_yearly": 0,
        "select_limit": 30,
        "ads_limit": 30,
        "features": ["每日1次选品分析（月30次）", "每日1次投流分析（月30次）", "定价计算器", "新手教程"]
    },
    "basic": {
        "name": "基础版",
        "price_monthly": 49,
        "price_yearly": 499,
        "select_limit": 300,
        "ads_limit": 300,
        "features": ["每日10次选品分析（月300次）", "每日10次投流分析（月300次）", "定价计算器", "新手教程", "竞品分析", "数据导出"]
    },
    "pro": {
        "name": "专业版",
        "price_monthly": 129,
        "price_yearly": 1299,
        "select_limit": 999999,
        "ads_limit": 999999,
        "features": ["无限次选品分析", "无限次投流分析", "定价计算器", "新手教程", "竞品分析", "数据导出", "批量分析", "优先支持"]
    }
}

def get_plan_info(plan: str) -> dict:
    """获取套餐信息"""
    return PLANS.get(plan, PLANS["free"])

def check_usage_limit(user: User, action: str) -> bool:
    """检查使用次数是否超限"""
    if action == "select_product":
        return user.select_count < user.select_limit
    elif action == "analyze_ads":
        return user.ads_count < user.ads_limit
    return False

def increment_usage(db, user: User, action: str):
    """增加使用次数"""
    if action == "select_product":
        user.select_count += 1
    elif action == "analyze_ads":
        user.ads_count += 1
    db.commit()

def reset_monthly_usage(db):
    """重置每月使用次数（定时任务调用）"""
    users = db.query(User).all()
    for user in users:
        user.select_count = 0
        user.ads_count = 0
    db.commit()
