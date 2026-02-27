import logging
from dotenv import load_dotenv
load_dotenv()
import hmac
import hashlib
import re
import time
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
import uvicorn
from datetime import datetime, timedelta
import os
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入功能模块
from product_selector import ProductSelector
from ad_optimizer import AdOptimizer
from advanced_ad_optimizer import AdvancedAdOptimizer
from pricing_calculator import PricingCalculator
from advanced_tools import CompetitorAnalyzer, DataExporter, BatchAnalyzer
from database import (
    get_db, User, Order, UsageLog, AnalysisHistory,
    verify_password, get_password_hash, create_access_token, decode_access_token,
    PLANS, get_plan_info, check_usage_limit, increment_usage
)
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

# 导入新模块
from payment import payment_manager
from email_service import email_service
from visualization import visualizer
from redis_service import redis_service, rate_limiter, cache_service
from batch_analysis import BatchAnalysisService

app = FastAPI(title="多多AI优化师", description="拼多多商家智能推广优化助手")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 速率限制配置
RATE_LIMIT_STORAGE = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 10

def check_rate_limit(user_id: int) -> bool:
    return rate_limiter.check_limit(
        f"user_{user_id}",
        max_requests=RATE_LIMIT_MAX_REQUESTS,
        window_seconds=RATE_LIMIT_WINDOW
    )

# 支付回调签名密钥
PAYMENT_CALLBACK_SECRET = os.getenv("SECRET_KEY", "")

def verify_payment_signature(order_id: int, signature: str) -> bool:
    expected = hmac.new(
        PAYMENT_CALLBACK_SECRET.encode(),
        str(order_id).encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

def validate_password_strength(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r'[a-zA-Z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True

# 初始化模块
product_selector = ProductSelector()
ad_optimizer = AdOptimizer()
advanced_ad_optimizer = AdvancedAdOptimizer()
pricing_calculator = PricingCalculator()
competitor_analyzer = CompetitorAnalyzer()
data_exporter = DataExporter()
batch_analyzer = BatchAnalyzer()
batch_analysis_service = BatchAnalysisService(product_selector, ad_optimizer)

# ==================== 数据模型 ====================

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProductSelectionRequest(BaseModel):
    budget: int
    category: str
    experience: str
    platform: str

class AdAnalysisRequest(BaseModel):
    platform: str
    data: str
    analysis_type: str
    category: str = "通用"

class PurchaseRequest(BaseModel):
    plan: str
    duration: str

class PricingRequest(BaseModel):
    cost: float
    target_margin: float
    shipping: float = 0

class CompetitorCompareRequest(BaseModel):
    your_price: float
    competitor_prices: List[float]

class CompetitorAnalyzeRequest(BaseModel):
    competitor_url: str
    platform: str

class ExportRequest(BaseModel):
    data_type: str
    data: dict

class DeepAnalyzeRequest(BaseModel):
    platform: str
    data: str
    budget: float
    goal: str
    category: str = "通用"

# ==================== 认证相关 ====================

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效")
    
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")
    
    # 检查套餐是否过期
    if user.plan != "free" and user.plan_expire_date and user.plan_expire_date < datetime.utcnow():
        user.plan = "free"
        user.select_limit = PLANS["free"]["select_limit"]
        user.ads_limit = PLANS["free"]["ads_limit"]
        db.commit()
    
    return user

# ==================== 用户注册登录 ====================

@app.post("/api/auth/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    try:
        if not validate_password_strength(user_data.password):
            raise HTTPException(status_code=400, detail="密码至少8位，需包含字母和数字")
        
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="邮箱已注册")
        
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            phone=user_data.phone,
            plan="free",
            select_limit=PLANS["free"]["select_limit"],
            ads_limit=PLANS["free"]["ads_limit"]
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        token = create_access_token(data={"user_id": new_user.id})
        
        return {
            "success": True,
            "message": "注册成功",
            "token": token,
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "plan": new_user.plan
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试")

@app.post("/api/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == user_data.email).first()
        if not user or not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="账户已被禁用")
        
        token = create_access_token(data={"user_id": user.id})
        
        return {
            "success": True,
            "message": "登录成功",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "plan": user.plan
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="登录失败，请稍后重试")

@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    plan_info = get_plan_info(current_user.plan)
    
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "plan": current_user.plan,
            "plan_name": plan_info["name"],
            "plan_expire": current_user.plan_expire_date.isoformat() if current_user.plan_expire_date else None,
            "select_count": current_user.select_count,
            "select_limit": current_user.select_limit,
            "ads_count": current_user.ads_count,
            "ads_limit": current_user.ads_limit,
            "created_at": current_user.created_at.isoformat()
        },
        "stats": {
            "product_used": current_user.select_count,
            "product_limit": current_user.select_limit,
            "ad_used": current_user.ads_count,
            "ad_limit": current_user.ads_limit
        }
    }

@app.get("/api/plans")
async def get_plans():
    return {"success": True, "plans": PLANS}

# ==================== 核心业务 API ====================

@app.post("/api/select-products")
async def select_products(
    request: ProductSelectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not check_usage_limit(current_user, "select_product"):
            raise HTTPException(status_code=403, detail="本月选品次数已用完，请升级套餐")
        
        if not check_rate_limit(current_user.id):
            raise HTTPException(status_code=429, detail="请求太频繁，请稍后再试")
        
        result = product_selector.select(
            platform=request.platform,
            category=request.category,
            budget=request.budget,
            experience=request.experience
        )
        
        increment_usage(db, current_user, "select_product")
        
        # 记录使用日志
        usage_log = UsageLog(
            user_id=current_user.id,
            action="select_product",
            details=json.dumps({"platform": request.platform, "category": request.category})
        )
        db.add(usage_log)
        
        # 保存分析历史
        analysis_history = AnalysisHistory(
            user_id=current_user.id,
            analysis_type="product",
            input_data=json.dumps({
                "platform": request.platform,
                "category": request.category,
                "budget": request.budget,
                "experience": request.experience
            }),
            result_data=json.dumps(result)
        )
        db.add(analysis_history)
        db.commit()
        
        logger.info(f"选品分析: user_id={current_user.id}, platform={request.platform}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"选品分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail="分析失败，请稍后重试")

@app.post("/api/analyze-ads")
async def analyze_ads(
    request: AdAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not check_usage_limit(current_user, "analyze_ads"):
            raise HTTPException(status_code=403, detail="本月投流分析次数已用完，请升级套餐")
        
        if not check_rate_limit(current_user.id):
            raise HTTPException(status_code=429, detail="请求太频繁，请稍后再试")
        
        result = await ad_optimizer.analyze(
            platform=request.platform,
            data=request.data,
            analysis_type=request.analysis_type,
            category=request.category
        )
        
        if result.get("success"):
            increment_usage(db, current_user, "analyze_ads")
            
            usage_log = UsageLog(
                user_id=current_user.id,
                action="analyze_ads",
                details=json.dumps({"platform": request.platform, "analysis_type": request.analysis_type})
            )
            db.add(usage_log)
            
            # 保存分析历史
            analysis_history = AnalysisHistory(
                user_id=current_user.id,
                analysis_type="ad",
                input_data=json.dumps({
                    "platform": request.platform,
                    "analysis_type": request.analysis_type,
                    "category": request.category
                }),
                result_data=json.dumps(result)
            )
            db.add(analysis_history)
            db.commit()
            
            logger.info(f"投流分析: user_id={current_user.id}, platform={request.platform}")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"投流分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail="分析失败，请稍后重试")

@app.post("/api/deep-analyze")
async def deep_analyze(
    request: DeepAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user.plan == "free":
            raise HTTPException(status_code=403, detail="深度分析需要付费套餐")
        
        result = await advanced_ad_optimizer.deep_analyze(
            platform=request.platform,
            data=request.data,
            budget=request.budget,
            goal=request.goal,
            category=request.category
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"深度分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail="分析失败，请稍后重试")

@app.post("/api/pricing/calculate")
async def calculate_pricing(request: PricingRequest):
    try:
        result = pricing_calculator.calculate_price(
            cost=request.cost,
            target_margin=request.target_margin,
            shipping=request.shipping
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pricing/compare")
async def compare_pricing(request: CompetitorCompareRequest):
    try:
        result = pricing_calculator.compare_with_competitors(
            your_price=request.your_price,
            competitor_prices=request.competitor_prices
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 订单 & 支付 ====================

@app.post("/api/orders/create")
async def create_order(
    request: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if request.plan not in PLANS or request.plan == "free":
            raise HTTPException(status_code=400, detail="无效的套餐")
        
        plan_info = PLANS[request.plan]
        if request.duration == "yearly":
            amount = plan_info["price_yearly"]
        else:
            amount = plan_info["price_monthly"]
        
        order = Order(
            user_id=current_user.id,
            plan=request.plan,
            duration=request.duration,
            amount=amount,
            status="pending"
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        return {
            "success": True,
            "order": {
                "id": order.id,
                "plan": order.plan,
                "duration": order.duration,
                "amount": order.amount,
                "status": order.status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建订单失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建订单失败")

@app.post("/api/orders/{order_id}/confirm")
async def confirm_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        if order.status != "pending":
            raise HTTPException(status_code=400, detail="订单状态不正确")
        
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        db.commit()
        
        return {"success": True, "message": "订单已确认，等待审核"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认订单失败: {str(e)}")
        raise HTTPException(status_code=500, detail="确认订单失败")

@app.get("/api/orders")
async def get_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        orders = db.query(Order).filter(
            Order.user_id == current_user.id
        ).order_by(Order.created_at.desc()).all()
        
        return {
            "success": True,
            "orders": [{
                "id": o.id,
                "plan": o.plan,
                "duration": o.duration,
                "amount": o.amount,
                "status": o.status,
                "created_at": o.created_at.isoformat(),
                "paid_at": o.paid_at.isoformat() if o.paid_at else None
            } for o in orders]
        }
    except Exception as e:
        logger.error(f"获取订单失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取订单失败")

# ==================== 竞品 & 导出 ====================

@app.post("/api/competitor/analyze")
async def analyze_competitor(
    request: CompetitorAnalyzeRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        if current_user.plan == "free":
            raise HTTPException(status_code=403, detail="竞品分析需要付费套餐")
        result = competitor_analyzer.analyze(request.competitor_url, request.platform)
        return {"success": True, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export")
async def export_data(
    request: ExportRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        if current_user.plan == "free":
            raise HTTPException(status_code=403, detail="数据导出需要付费套餐")
        result = data_exporter.export(request.data_type, request.data)
        return {"success": True, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 分析历史 ====================

@app.get("/api/analysis-history")
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(AnalysisHistory).filter(
            AnalysisHistory.user_id == current_user.id
        )
        
        if type:
            query = query.filter(AnalysisHistory.analysis_type == type)
        
        total = query.count()
        records = query.order_by(
            AnalysisHistory.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "total": total,
            "records": [{
                "id": r.id,
                "type": r.analysis_type,
                "summary": (json.loads(r.result_data) if r.result_data else {}).get("summary", "")[:100] if r.result_data else "",
                "created_at": r.created_at.isoformat()
            } for r in records]
        }
    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取失败")

@app.get("/api/analysis-history/{history_id}")
async def get_analysis_detail(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        history = db.query(AnalysisHistory).filter(
            AnalysisHistory.id == history_id,
            AnalysisHistory.user_id == current_user.id
        ).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        return {
            "success": True,
            "history": {
                "id": history.id,
                "type": history.analysis_type,
                "input_data": json.loads(history.input_data) if history.input_data else {},
                "result_data": json.loads(history.result_data) if history.result_data else {},
                "created_at": history.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取失败")

# ==================== P3: 趋势数据 & 仪表盘 ====================

@app.get("/api/analysis-trends")
async def get_analysis_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from datetime import date
        today = date.today()
        start_date = today - timedelta(days=30)

        records = db.query(AnalysisHistory).filter(
            AnalysisHistory.user_id == current_user.id,
            AnalysisHistory.created_at >= datetime.combine(start_date, datetime.min.time())
        ).all()

        date_map = {}
        for i in range(31):
            d = (start_date + timedelta(days=i)).isoformat()
            date_map[d] = {"product": 0, "ad": 0}

        for r in records:
            d = r.created_at.date().isoformat()
            if d in date_map:
                if r.analysis_type == "product":
                    date_map[d]["product"] += 1
                else:
                    date_map[d]["ad"] += 1

        dates = sorted(date_map.keys())
        return {
            "success": True,
            "dates": dates,
            "product_counts": [date_map[d]["product"] for d in dates],
            "ad_counts": [date_map[d]["ad"] for d in dates]
        }
    except Exception as e:
        logger.error(f"获取趋势数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取失败")

@app.get("/api/dashboard-stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from datetime import date
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        total_count = db.query(AnalysisHistory).filter(
            AnalysisHistory.user_id == current_user.id
        ).count()

        week_count = db.query(AnalysisHistory).filter(
            AnalysisHistory.user_id == current_user.id,
            AnalysisHistory.created_at >= datetime.combine(week_start, datetime.min.time())
        ).count()

        last_analysis = db.query(AnalysisHistory).filter(
            AnalysisHistory.user_id == current_user.id
        ).order_by(AnalysisHistory.created_at.desc()).first()

        last_time = last_analysis.created_at.isoformat() if last_analysis else None

        all_dates = db.query(
            sa_func.date(AnalysisHistory.created_at)
        ).filter(
            AnalysisHistory.user_id == current_user.id
        ).distinct().order_by(
            sa_func.date(AnalysisHistory.created_at).desc()
        ).all()

        streak = 0
        check_date = today
        date_set = {str(d[0]) for d in all_dates}
        while check_date.isoformat() in date_set:
            streak += 1
            check_date -= timedelta(days=1)

        return {
            "success": True,
            "total_count": total_count,
            "week_count": week_count,
            "last_analysis_time": last_time,
            "streak_days": streak
        }
    except Exception as e:
        logger.error(f"获取仪表盘统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取失败")

# ==================== 管理员 API ====================

from database import Admin

def get_admin_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效")
    
    admin_id = payload.get("admin_id")
    if not admin_id:
        raise HTTPException(status_code=403, detail="非管理员")
    
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=403, detail="管理员不存在或已禁用")
    
    return admin

@app.post("/api/admin/login")
async def admin_login(request: dict, db: Session = Depends(get_db)):
    try:
        username = request.get("username")
        password = request.get("password")
        
        admin = db.query(Admin).filter(Admin.username == username).first()
        if not admin or not verify_password(password, admin.hashed_password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        token = create_access_token(data={"admin_id": admin.id})
        return {"success": True, "token": token}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="登录失败")

@app.get("/api/admin/orders")
async def admin_get_orders(
    status: Optional[str] = None,
    admin: Admin = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Order)
        if status:
            query = query.filter(Order.status == status)
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        result = []
        for o in orders:
            user = db.query(User).filter(User.id == o.user_id).first()
            plan_info = PLANS.get(o.plan, {})
            result.append({
                "id": o.id,
                "user_id": o.user_id,
                "username": user.username if user else "未知",
                "email": user.email if user else "未知",
                "plan": o.plan,
                "plan_name": plan_info.get("name", o.plan),
                "duration": o.duration,
                "amount": o.amount,
                "status": o.status,
                "payment_method": o.payment_method,
                "transaction_id": o.transaction_id,
                "note": o.note,
                "reject_reason": o.reject_reason,
                "created_at": o.created_at.isoformat(),
                "paid_at": o.paid_at.isoformat() if o.paid_at else None
            })
        
        return {"success": True, "orders": result}
    except Exception as e:
        logger.error(f"获取订单列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取失败")

@app.post("/api/admin/orders/{order_id}/approve")
async def admin_approve_order(
    order_id: int,
    admin: Admin = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        order.status = "approved"
        order.approved_at = datetime.utcnow()
        
        # 升级用户套餐
        user = db.query(User).filter(User.id == order.user_id).first()
        if user:
            plan_info = PLANS.get(order.plan, PLANS["free"])
            user.plan = order.plan
            user.select_limit = plan_info["select_limit"]
            user.ads_limit = plan_info["ads_limit"]
            
            if order.duration == "yearly":
                user.plan_expire_date = datetime.utcnow() + timedelta(days=365)
            else:
                user.plan_expire_date = datetime.utcnow() + timedelta(days=30)
        
        db.commit()
        logger.info(f"订单已通过: order_id={order_id}, user_id={order.user_id}")
        return {"success": True, "message": "订单已通过"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"审核订单失败: {str(e)}")
        raise HTTPException(status_code=500, detail="审核失败")

@app.post("/api/admin/orders/{order_id}/reject")
async def admin_reject_order(
    order_id: int,
    request: dict,
    admin: Admin = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        order.status = "rejected"
        order.reject_reason = request.get("reason", "")
        db.commit()
        
        return {"success": True, "message": "订单已拒绝"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="操作失败")

@app.get("/api/admin/users")
async def admin_get_users(
    admin: Admin = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return {
            "success": True,
            "users": [{
                "id": u.id,
                "email": u.email,
                "username": u.username,
                "plan": u.plan,
                "plan_name": get_plan_info(u.plan)["name"],
                "select_count": u.select_count,
                "ads_count": u.ads_count,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat()
            } for u in users]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取失败")

@app.get("/api/admin/stats")
async def admin_get_stats(
    admin: Admin = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        total_users = db.query(User).count()
        paid_users = db.query(User).filter(User.plan != "free").count()
        total_orders = db.query(Order).count()
        pending_orders = db.query(Order).filter(Order.status == "pending").count()
        
        return {
            "success": True,
            "stats": {
                "total_users": total_users,
                "paid_users": paid_users,
                "total_orders": total_orders,
                "pending_orders": pending_orders
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取失败")

# ==================== 静态文件 & 启动 ====================

@app.get("/")
async def root():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
