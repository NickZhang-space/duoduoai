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

from report_generator import report_generator
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
    Shop, Competitor, CompetitorSnapshot,
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

from intelligence.ab_test_engine import ABTestEngine
from intelligence.dynamic_pricing import DynamicPricingEngine
# 导入智能化模块
from intelligence_api import router as intelligence_router
app = FastAPI(title="多多AI优化师", description="拼多多商家智能推广优化助手")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加智能化路由

# 初始化智能化引擎
ab_test_engine = ABTestEngine()
pricing_engine = DynamicPricingEngine()
app.include_router(intelligence_router)
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
        
        # 获取店铺信息用于个性化分析
        shop = db.query(Shop).filter(Shop.user_id == current_user.id).first()
        shop_context = ""
        if shop:
            shop_context = f"店铺信息：{shop.shop_name}，主营品类：{shop.category or '未设置'}，月营收：{shop.monthly_revenue or '未设置'}，月推广费：{shop.monthly_ad_spend or '未设置'}。"
        result = product_selector.select(
            shop_context=shop_context,
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
        
        # 获取店铺信息用于个性化分析
        shop = db.query(Shop).filter(Shop.user_id == current_user.id).first()
        shop_context = ""
        if shop:
            shop_context = f"店铺信息：{shop.shop_name}，主营品类：{shop.category or '未设置'}，月营收：{shop.monthly_revenue or '未设置'}，月推广费：{shop.monthly_ad_spend or '未设置'}。"
        result = await ad_optimizer.analyze(
            platform=request.platform,
            data=request.data,
            analysis_type=request.analysis_type,
            category=request.category,
            shop_context=shop_context
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


@app.post("/api/payment/manual-submit")
async def manual_submit_payment(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        plan = request.get("plan", "")
        duration = request.get("duration", "monthly")
        payment_method = request.get("payment_method", "alipay")
        
        if plan not in PLANS or plan == "free":
            raise HTTPException(status_code=400, detail="无效的套餐")
        
        plan_info = PLANS[plan]
        if duration == "yearly":
            amount = plan_info["price_yearly"]
        else:
            amount = plan_info["price_monthly"]
        
        order = Order(
            user_id=current_user.id,
            plan=plan,
            duration=duration,
            amount=amount,
            payment_method=payment_method,
            status="pending"
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        return {
            "success": True,
            "message": "支付信息已提交，等待管理员审核",
            "order_id": order.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="提交支付失败")

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
        
        # 统计数据
        from datetime import datetime, timedelta
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        pending_count = sum(1 for o in orders if o.status == "pending")
        today_count = sum(1 for o in orders if o.created_at >= today_start)
        today_revenue = sum(o.amount for o in orders if o.status == "approved" and o.paid_at and o.paid_at >= today_start)
        user_count = db.query(User).count()
        
        stats = {
            "pending": pending_count,
            "today": today_count,
            "revenue": today_revenue,
            "users": user_count
        }
        
        return {"success": True, "orders": result, "stats": stats}
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


# ==================== 报告生成 API ====================

@app.post("/api/report/generate")
async def generate_report(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        history_id = request.get('history_id')
        if not history_id:
            raise HTTPException(status_code=400, detail="缺少 history_id 参数")
        
        history = db.query(AnalysisHistory).filter(
            AnalysisHistory.id == history_id,
            AnalysisHistory.user_id == current_user.id
        ).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        history_data = {
            'id': history.id,
            'analysis_type': history.analysis_type,
            'input_data': history.input_data,
            'result_data': history.result_data,
            'created_at': history.created_at
        }
        
        report_html = report_generator.generate_html_report(history_data)
        
        return {
            "success": True,
            "report_html": report_html
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="生成报告失败")

@app.get("/api/report/{history_id}")
async def get_report_html(
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
        
        history_data = {
            'id': history.id,
            'analysis_type': history.analysis_type,
            'input_data': history.input_data,
            'result_data': history.result_data,
            'created_at': history.created_at
        }
        
        report_html = report_generator.generate_html_report(history_data)
        
        return HTMLResponse(content=report_html)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取报告失败")

# ==================== 店铺信息管理 API ====================

class ShopRequest(BaseModel):
    shop_name: str
    category: Optional[str] = None
    monthly_revenue: Optional[str] = None
    monthly_ad_spend: Optional[str] = None
    main_products: Optional[str] = None
    notes: Optional[str] = None

@app.post("/api/shop")
async def create_or_update_shop(
    request: ShopRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 查找用户是否已有店铺
        shop = db.query(Shop).filter(Shop.user_id == current_user.id).first()
        
        if shop:
            # 更新现有店铺
            shop.shop_name = request.shop_name
            shop.category = request.category
            shop.monthly_revenue = request.monthly_revenue
            shop.monthly_ad_spend = request.monthly_ad_spend
            shop.main_products = request.main_products
            shop.notes = request.notes
            shop.updated_at = datetime.utcnow()
        else:
            # 创建新店铺
            shop = Shop(
                user_id=current_user.id,
                shop_name=request.shop_name,
                category=request.category,
                monthly_revenue=request.monthly_revenue,
                monthly_ad_spend=request.monthly_ad_spend,
                main_products=request.main_products,
                notes=request.notes
            )
            db.add(shop)
        
        db.commit()
        db.refresh(shop)
        
        return {
            "success": True,
            "message": "店铺信息保存成功",
            "shop": {
                "id": shop.id,
                "shop_name": shop.shop_name,
                "category": shop.category,
                "monthly_revenue": shop.monthly_revenue,
                "monthly_ad_spend": shop.monthly_ad_spend,
                "main_products": shop.main_products,
                "notes": shop.notes,
                "created_at": shop.created_at.isoformat(),
                "updated_at": shop.updated_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"保存店铺信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="保存失败")

@app.get("/api/shop")
async def get_shop(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        shop = db.query(Shop).filter(Shop.user_id == current_user.id).first()
        
        if not shop:
            return {
                "success": True,
                "shop": None
            }
        
        return {
            "success": True,
            "shop": {
                "id": shop.id,
                "shop_name": shop.shop_name,
                "category": shop.category,
                "monthly_revenue": shop.monthly_revenue,
                "monthly_ad_spend": shop.monthly_ad_spend,
                "main_products": shop.main_products,
                "notes": shop.notes,
                "created_at": shop.created_at.isoformat(),
                "updated_at": shop.updated_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"获取店铺信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取失败")

@app.delete("/api/shop/{shop_id}")
async def delete_shop(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        shop = db.query(Shop).filter(
            Shop.id == shop_id,
            Shop.user_id == current_user.id
        ).first()
        
        if not shop:
            raise HTTPException(status_code=404, detail="店铺不存在")
        
        db.delete(shop)
        db.commit()
        
        return {
            "success": True,
            "message": "店铺删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除店铺失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除失败")



# ==================== 竞品跟踪 API ====================

class CompetitorRequest(BaseModel):
    name: str
    product_url: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    monthly_sales: Optional[int] = None
    ad_spend: Optional[float] = None
    notes: Optional[str] = None

class CompetitorSnapshotRequest(BaseModel):
    price: Optional[float] = None
    monthly_sales: Optional[int] = None
    ad_spend: Optional[float] = None
    ranking: Optional[int] = None

@app.post("/api/competitors")
async def add_competitor(
    request: CompetitorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加竞品"""
    try:
        # 检查竞品数量限制
        competitor_count = db.query(Competitor).filter(Competitor.user_id == current_user.id).count()
        
        # 根据套餐限制竞品数量
        if current_user.plan == "free":
            max_competitors = 2
        elif current_user.plan == "basic":
            max_competitors = 5
        else:  # pro, premium
            max_competitors = 999999
        
        if competitor_count >= max_competitors:
            raise HTTPException(
                status_code=403,
                detail=f"您的套餐最多支持 {max_competitors} 个竞品，请升级套餐"
            )
        
        # 创建竞品
        competitor = Competitor(
            user_id=current_user.id,
            name=request.name,
            product_url=request.product_url,
            category=request.category,
            price=request.price,
            monthly_sales=request.monthly_sales,
            ad_spend=request.ad_spend,
            notes=request.notes
        )
        db.add(competitor)
        db.commit()
        db.refresh(competitor)
        
        # 创建初始快照
        if request.price or request.monthly_sales or request.ad_spend:
            snapshot = CompetitorSnapshot(
                competitor_id=competitor.id,
                price=request.price,
                monthly_sales=request.monthly_sales,
                ad_spend=request.ad_spend
            )
            db.add(snapshot)
            db.commit()
        
        return {
            "success": True,
            "message": "竞品添加成功",
            "competitor": {
                "id": competitor.id,
                "name": competitor.name,
                "product_url": competitor.product_url,
                "category": competitor.category,
                "price": competitor.price,
                "monthly_sales": competitor.monthly_sales,
                "ad_spend": competitor.ad_spend,
                "notes": competitor.notes,
                "created_at": competitor.created_at.isoformat(),
                "updated_at": competitor.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加竞品失败: {str(e)}")
        raise HTTPException(status_code=500, detail="添加失败")

@app.get("/api/competitors")
async def get_competitors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的竞品列表"""
    try:
        competitors = db.query(Competitor).filter(
            Competitor.user_id == current_user.id
        ).order_by(Competitor.created_at.desc()).all()
        
        result = []
        for comp in competitors:
            # 获取最新快照
            latest_snapshot = db.query(CompetitorSnapshot).filter(
                CompetitorSnapshot.competitor_id == comp.id
            ).order_by(CompetitorSnapshot.snapshot_date.desc()).first()
            
            result.append({
                "id": comp.id,
                "name": comp.name,
                "product_url": comp.product_url,
                "category": comp.category,
                "price": comp.price,
                "monthly_sales": comp.monthly_sales,
                "ad_spend": comp.ad_spend,
                "notes": comp.notes,
                "created_at": comp.created_at.isoformat(),
                "updated_at": comp.updated_at.isoformat(),
                "latest_snapshot": {
                    "price": latest_snapshot.price if latest_snapshot else None,
                    "monthly_sales": latest_snapshot.monthly_sales if latest_snapshot else None,
                    "ad_spend": latest_snapshot.ad_spend if latest_snapshot else None,
                    "ranking": latest_snapshot.ranking if latest_snapshot else None,
                    "snapshot_date": latest_snapshot.snapshot_date.isoformat() if latest_snapshot else None
                } if latest_snapshot else None
            })
        
        return {
            "success": True,
            "competitors": result
        }
    except Exception as e:
        logger.error(f"获取竞品列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取失败")

@app.put("/api/competitors/{competitor_id}")
async def update_competitor(
    competitor_id: int,
    request: CompetitorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新竞品信息（同时创建快照）"""
    try:
        competitor = db.query(Competitor).filter(
            Competitor.id == competitor_id,
            Competitor.user_id == current_user.id
        ).first()
        
        if not competitor:
            raise HTTPException(status_code=404, detail="竞品不存在")
        
        # 检查数据是否变化，如果变化则创建快照
        data_changed = (
            (request.price and request.price != competitor.price) or
            (request.monthly_sales and request.monthly_sales != competitor.monthly_sales) or
            (request.ad_spend and request.ad_spend != competitor.ad_spend)
        )
        
        # 更新竞品信息
        competitor.name = request.name
        competitor.product_url = request.product_url
        competitor.category = request.category
        competitor.price = request.price
        competitor.monthly_sales = request.monthly_sales
        competitor.ad_spend = request.ad_spend
        competitor.notes = request.notes
        competitor.updated_at = datetime.utcnow()
        
        db.commit()
        
        # 如果数据变化，创建快照
        if data_changed:
            snapshot = CompetitorSnapshot(
                competitor_id=competitor.id,
                price=request.price,
                monthly_sales=request.monthly_sales,
                ad_spend=request.ad_spend
            )
            db.add(snapshot)
            db.commit()
        
        return {
            "success": True,
            "message": "竞品更新成功",
            "competitor": {
                "id": competitor.id,
                "name": competitor.name,
                "product_url": competitor.product_url,
                "category": competitor.category,
                "price": competitor.price,
                "monthly_sales": competitor.monthly_sales,
                "ad_spend": competitor.ad_spend,
                "notes": competitor.notes,
                "created_at": competitor.created_at.isoformat(),
                "updated_at": competitor.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新竞品失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新失败")

@app.delete("/api/competitors/{competitor_id}")
async def delete_competitor(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除竞品"""
    try:
        competitor = db.query(Competitor).filter(
            Competitor.id == competitor_id,
            Competitor.user_id == current_user.id
        ).first()
        
        if not competitor:
            raise HTTPException(status_code=404, detail="竞品不存在")
        
        # 删除所有快照
        db.query(CompetitorSnapshot).filter(
            CompetitorSnapshot.competitor_id == competitor_id
        ).delete()
        
        # 删除竞品
        db.delete(competitor)
        db.commit()
        
        return {
            "success": True,
            "message": "竞品删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除竞品失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除失败")

@app.post("/api/competitors/{competitor_id}/snapshot")
async def add_competitor_snapshot(
    competitor_id: int,
    request: CompetitorSnapshotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动添加竞品数据快照"""
    try:
        competitor = db.query(Competitor).filter(
            Competitor.id == competitor_id,
            Competitor.user_id == current_user.id
        ).first()
        
        if not competitor:
            raise HTTPException(status_code=404, detail="竞品不存在")
        
        # 创建快照
        snapshot = CompetitorSnapshot(
            competitor_id=competitor_id,
            price=request.price,
            monthly_sales=request.monthly_sales,
            ad_spend=request.ad_spend,
            ranking=request.ranking
        )
        db.add(snapshot)
        
        # 更新竞品主表数据
        if request.price:
            competitor.price = request.price
        if request.monthly_sales:
            competitor.monthly_sales = request.monthly_sales
        if request.ad_spend:
            competitor.ad_spend = request.ad_spend
        competitor.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(snapshot)
        
        return {
            "success": True,
            "message": "快照添加成功",
            "snapshot": {
                "id": snapshot.id,
                "competitor_id": snapshot.competitor_id,
                "price": snapshot.price,
                "monthly_sales": snapshot.monthly_sales,
                "ad_spend": snapshot.ad_spend,
                "ranking": snapshot.ranking,
                "snapshot_date": snapshot.snapshot_date.isoformat(),
                "created_at": snapshot.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加快照失败: {str(e)}")
        raise HTTPException(status_code=500, detail="添加失败")

@app.get("/api/competitors/{competitor_id}/history")
async def get_competitor_history(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取竞品历史快照"""
    try:
        competitor = db.query(Competitor).filter(
            Competitor.id == competitor_id,
            Competitor.user_id == current_user.id
        ).first()
        
        if not competitor:
            raise HTTPException(status_code=404, detail="竞品不存在")
        
        snapshots = db.query(CompetitorSnapshot).filter(
            CompetitorSnapshot.competitor_id == competitor_id
        ).order_by(CompetitorSnapshot.snapshot_date.asc()).all()
        
        return {
            "success": True,
            "competitor": {
                "id": competitor.id,
                "name": competitor.name
            },
            "history": [
                {
                    "id": snap.id,
                    "price": snap.price,
                    "monthly_sales": snap.monthly_sales,
                    "ad_spend": snap.ad_spend,
                    "ranking": snap.ranking,
                    "snapshot_date": snap.snapshot_date.isoformat()
                }
                for snap in snapshots
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取失败")

class CompetitorAnalyzeRequest(BaseModel):
    competitor_ids: List[int]

@app.post("/api/competitors/analyze")
async def analyze_competitors(
    request: CompetitorAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI 对比分析竞品"""
    try:
        if not request.competitor_ids:
            raise HTTPException(status_code=400, detail="请选择要分析的竞品")
        
        # 获取用户店铺信息
        shop = db.query(Shop).filter(Shop.user_id == current_user.id).first()
        
        # 获取竞品信息
        competitors = db.query(Competitor).filter(
            Competitor.id.in_(request.competitor_ids),
            Competitor.user_id == current_user.id
        ).all()
        
        if not competitors:
            raise HTTPException(status_code=404, detail="未找到竞品")
        
        # 构建分析提示词
        shop_info = ""
        if shop:
            shop_info = f"""
我的店铺信息：
- 店铺名称：{shop.shop_name}
- 类目：{shop.category or '未设置'}
- 月营收：{shop.monthly_revenue or '未设置'}
- 月广告支出：{shop.monthly_ad_spend or '未设置'}
- 主营产品：{shop.main_products or '未设置'}
"""
        
        competitor_info = "\n\n".join([
            f"""竞品 {i+1}：{comp.name}
- 类目：{comp.category or '未知'}
- 价格：{comp.price or '未知'}
- 月销量：{comp.monthly_sales or '未知'}
- 广告支出：{comp.ad_spend or '未知'}
- 备注：{comp.notes or '无'}"""
            for i, comp in enumerate(competitors)
        ])
        
        prompt = f"""作为拼多多电商运营专家，请分析以下竞品数据，并给出专业建议。

{shop_info}

竞品信息：
{competitor_info}

请从以下角度进行分析：
1. 定价策略对比
2. 销量表现分析
3. 广告投入效率
4. 竞争优势与劣势
5. 具体优化建议

请给出详细、可执行的建议。"""
        
        # 调用 DeepSeek API
        import httpx
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            raise HTTPException(status_code=500, detail="DeepSeek API 未配置")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {deepseek_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "你是一位专业的拼多多电商运营专家，擅长竞品分析和数据洞察。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI 分析失败")
            
            result = response.json()
            analysis = result["choices"][0]["message"]["content"]
        
        return {
            "success": True,
            "analysis": analysis,
            "competitors": [
                {
                    "id": comp.id,
                    "name": comp.name,
                    "price": comp.price,
                    "monthly_sales": comp.monthly_sales,
                    "ad_spend": comp.ad_spend
                }
                for comp in competitors
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"竞品分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.get("/")
async def root():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

# ==================== 手动支付提交 ====================

@app.post("/api/payment/manual-submit")
async def manual_payment_submit(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        plan = request.get("plan")
        duration = request.get("duration", "monthly")
        payment_method = request.get("payment_method", "alipay")
        amount = request.get("amount", 0)
        transaction_id = request.get("transaction_id", "")
        note = request.get("note", "")

        if plan not in PLANS or plan == "free":
            raise HTTPException(status_code=400, detail="无效的套餐")

        order = Order(
            user_id=current_user.id,
            plan=plan,
            duration=duration,
            amount=float(amount),
            status="paid"
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        return {"success": True, "message": "支付信息已提交，等待审核", "order_id": order.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动支付提交失败: {str(e)}")
        raise HTTPException(status_code=500, detail="提交失败")

@app.post("/api/ab-test/create")
async def create_ab_test(request: dict):
    """创建A/B测试"""
    try:
        experiment = ab_test_engine.create_experiment(
            name=request['name'],
            variants=request['variants'],
            metrics=request['metrics'],
            traffic_split=request.get('traffic_split'),
            user_id=request.get('user_id', '1')
        )
        
        return {
            "success": True,
            "data": experiment
        }
    except Exception as e:
        logger.error(f"创建A/B测试失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/ab-test/list")
async def list_experiments(user_id: str = "1"):
    """获取实验列表"""
    try:
        experiments = ab_test_engine.list_experiments(user_id)
        return {
            "success": True,
            "data": experiments
        }
    except Exception as e:
        logger.error(f"获取实验列表失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/ab-test/results/{experiment_id}")
async def get_ab_test_results(experiment_id: str):
    """获取实验结果"""
    try:
        results = ab_test_engine.analyze_results(experiment_id)
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        logger.error(f"获取实验结果失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ab-test/track")
async def track_conversion(request: dict):
    """记录转化数据"""
    try:
        conversion = ab_test_engine.track_conversion(
            user_id=request['user_id'],
            experiment_id=request['experiment_id'],
            metrics_data=request['metrics']
        )
        
        return {
            "success": True,
            "data": conversion
        }
    except Exception as e:
        logger.error(f"记录转化失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ab-test/stop/{experiment_id}")
async def stop_experiment(experiment_id: str):
    """停止实验"""
    try:
        ab_test_engine.stop_experiment(experiment_id)
        return {
            "success": True,
            "message": "实验已停止"
        }
    except Exception as e:
        logger.error(f"停止实验失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }



# ==================== 动态定价 API ====================

@app.post("/api/pricing/suggest")
async def suggest_pricing(request: dict):
    """智能定价建议"""
    try:
        from intelligence.dynamic_pricing import DynamicPricingEngine
        engine = DynamicPricingEngine()
        
        product = request['product']
        market_data = request.get('market_data', {})
        user_goal = request.get('goal', 'balanced')
        
        suggestion = await engine.suggest_price(product, market_data, user_goal)
        
        return {
            "success": True,
            "data": suggestion
        }
    except Exception as e:
        logger.error(f"智能定价失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/pricing/simulate")
async def simulate_pricing(request: dict):
    """价格模拟"""
    try:
        from intelligence.dynamic_pricing import DynamicPricingEngine
        engine = DynamicPricingEngine()
        
        product = request['product']
        price = request['price']
        market_data = request.get('market_data', {})
        
        prediction = await engine.simulate_price(product, price, market_data)
        
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        logger.error(f"价格模拟失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }



# ==================== 自动化优化 API ====================

@app.post("/api/automation/configure")
async def configure_automation(request: dict):
    """配置自动化设置"""
    try:
        from intelligence.auto_optimizer import AutoOptimizer
        global auto_optimizer
        if "auto_optimizer" not in globals():
            auto_optimizer = AutoOptimizer()
        optimizer = auto_optimizer
        
        user_id = request['user_id']
        settings = request['settings']
        
        optimizer.save_settings(user_id, settings)
        
        return {
            "success": True,
            "message": "自动化设置已保存"
        }
    except Exception as e:
        logger.error(f"配置自动化失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/automation/settings/{user_id}")
async def get_automation_settings(user_id: str):
    """获取自动化设置"""
    try:
        from intelligence.auto_optimizer import AutoOptimizer
        global auto_optimizer
        if "auto_optimizer" not in globals():
            auto_optimizer = AutoOptimizer()
        optimizer = auto_optimizer
        
        settings = optimizer.get_settings(user_id)
        
        return {
            "success": True,
            "data": settings
        }
    except Exception as e:
        logger.error(f"获取设置失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/automation/run")
async def run_automation(request: dict):
    """手动触发一轮自动优化"""
    try:
        from intelligence.auto_optimizer import AutoOptimizer
        global auto_optimizer
        if "auto_optimizer" not in globals():
            auto_optimizer = AutoOptimizer()
        optimizer = auto_optimizer
        
        user_id = request.get('user_id', '1')
        result = await optimizer.run_optimization_cycle(user_id)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"运行自动化失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/automation/logs/{user_id}")
async def get_automation_logs(user_id: str, limit: int = 50):
    """获取自动化操作日志"""
    try:
        from intelligence.auto_optimizer import AutoOptimizer
        global auto_optimizer
        if "auto_optimizer" not in globals():
            auto_optimizer = AutoOptimizer()
        optimizer = auto_optimizer
        
        logs = optimizer.get_logs(user_id, limit)
        
        return {
            "success": True,
            "data": logs
        }
    except Exception as e:
        logger.error(f"获取日志失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/automation/pause")
async def pause_automation(request: dict):
    """暂停自动化"""
    try:
        from intelligence.auto_optimizer import AutoOptimizer
        global auto_optimizer
        if "auto_optimizer" not in globals():
            auto_optimizer = AutoOptimizer()
        optimizer = auto_optimizer
        
        user_id = request.get('user_id', '1')
        settings = optimizer.get_settings(user_id)
        settings['enabled'] = False
        optimizer.save_settings(user_id, settings)
        
        return {
            "success": True,
            "message": "自动化已暂停"
        }
    except Exception as e:
        logger.error(f"暂停自动化失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }



# ==================== 通知系统 API ====================
# 内存存储通知数据
notifications_store = []
notification_id_counter = 1

@app.get("/api/notifications")
async def get_notifications(user_id: str = "1", limit: int = 50):
    """获取通知列表"""
    try:
        user_notifications = [n for n in notifications_store if n.get("user_id") == user_id]
        user_notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {
            "success": True,
            "data": user_notifications[:limit]
        }
    except Exception as e:
        logger.error(f"获取通知失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/notifications/read")
async def mark_notification_read(request: dict):
    """标记通知已读"""
    try:
        notification_id = request.get("notification_id")
        if not notification_id:
            return {"success": False, "error": "缺少notification_id"}
        
        for notif in notifications_store:
            if notif.get("id") == notification_id:
                notif["read"] = True
                break
        
        return {
            "success": True,
            "message": "已标记为已读"
        }
    except Exception as e:
        logger.error(f"标记已读失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/notifications/unread-count")
async def get_unread_count(user_id: str = "1"):
    """获取未读通知数量"""
    try:
        unread = [n for n in notifications_store if n.get("user_id") == user_id and not n.get("read", False)]
        return {
            "success": True,
            "data": {
                "count": len(unread)
            }
        }
    except Exception as e:
        logger.error(f"获取未读数量失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def init_sample_notifications():
    """初始化一些示例通知"""
    global notification_id_counter, notifications_store
    from datetime import datetime, timedelta
    
    sample_notifications = [
        {
            "id": notification_id_counter,
            "user_id": "1",
            "type": "analysis_complete",
            "title": "分析完成",
            "message": "您的产品分析报告已生成",
            "icon": "📊",
            "read": False,
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "id": notification_id_counter + 1,
            "user_id": "1",
            "type": "risk_warning",
            "title": "风险预警",
            "message": "广告点击率下降15%，建议优化创意",
            "icon": "⚠️",
            "read": False,
            "created_at": (datetime.now() - timedelta(hours=5)).isoformat()
        },
        {
            "id": notification_id_counter + 2,
            "user_id": "1",
            "type": "price_change",
            "title": "价格变动",
            "message": "竞品降价提醒：手机壳降价至¥19.9",
            "icon": "💰",
            "read": True,
            "created_at": (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            "id": notification_id_counter + 3,
            "user_id": "1",
            "type": "system_message",
            "title": "系统消息",
            "message": "每日智能报告已生成，点击查看",
            "icon": "🔔",
            "read": False,
            "created_at": datetime.now().isoformat()
        }
    ]
    
    notifications_store.extend(sample_notifications)
    notification_id_counter += len(sample_notifications)


if __name__ == "__main__":
    init_sample_notifications()
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
