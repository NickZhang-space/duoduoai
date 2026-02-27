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
    AnalysisHistory,
    get_db, User, Order, UsageLog, 
    verify_password, get_password_hash, create_access_token, decode_access_token,
    PLANS, get_plan_info, check_usage_limit, increment_usage
)
from sqlalchemy.orm import Session

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
    allow_origins=["*"],  # 开发阶段允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 速率限制配置
RATE_LIMIT_STORAGE = {}
RATE_LIMIT_WINDOW = 60  # 1分钟
RATE_LIMIT_MAX_REQUESTS = 10

def check_rate_limit(user_id: int) -> bool:
    """检查速率限制（使用Redis）"""
    return rate_limiter.check_limit(
        f"user_{user_id}",
        max_requests=RATE_LIMIT_MAX_REQUESTS,
        window_seconds=RATE_LIMIT_WINDOW
    )

# 支付回调签名密钥
PAYMENT_CALLBACK_SECRET = os.getenv("SECRET_KEY", "")

def verify_payment_signature(order_id: int, signature: str) -> bool:
    """验证支付回调签名"""
    expected = hmac.new(
        PAYMENT_CALLBACK_SECRET.encode(),
        str(order_id).encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

def validate_password_strength(password: str) -> bool:
    """验证密码强度：至少8位，包含字母和数字"""
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
class CompetitorCompareRequest(BaseModel):
    your_price: float
    competitor_prices: List[float]

class CompetitorAnalyzeRequest(BaseModel):
    competitor_url: str
    platform: str

class ExportRequest(BaseModel):
    data_type: str  # select/ads
    data: dict

class DeepAnalyzeRequest(BaseModel):
    platform: str
    data: str
    budget: float
    goal: str  # 降本/放量/提ROI
    category: str = "通用"  # 服饰/食品/美妆/家居/数码/母婴

class PurchaseRequest(BaseModel):
    plan: str
    duration: str  # monthly/yearly
    payment_method: str



class PricingRequest(BaseModel):
    cost: float
    target_profit_margin: float
    platform_fee_rate: float = 0.06
    
# ==================== 认证相关 ====================

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """获取当前登录用户"""
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
        user.select_limit = 3
        user.ads_limit = 3
        db.commit()
    
    return user

# ==================== API 路由 ====================

@app.get("/")
async def root():
    """返回首页"""
    return FileResponse("static/index.html")

@app.post("/api/auth/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        # 验证密码强度
        if not validate_password_strength(user_data.password):
            raise HTTPException(
                status_code=400, 
                detail="密码必须至少8位，且包含字母和数字"
            )
        
        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="邮箱已被注册")
        
        # 检查用户名是否已存在
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="用户名已被使用")
        
        # 创建新用户
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            phone=user_data.phone,
            plan="free",
            select_limit=3,
            ads_limit=3
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"新用户注册成功: {new_user.email}")
        
        # 生成token
        access_token = create_access_token(data={"user_id": new_user.id})
        
        return {
            "success": True,
            "message": "注册成功",
            "token": access_token,
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
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        user = db.query(User).filter(User.email == login_data.email).first()
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="账户已被禁用")
        
        logger.info(f"用户登录: {user.email}")
        
        # 生成token
        access_token = create_access_token(data={"user_id": user.id})
        
        return {
            "success": True,
            "message": "登录成功",
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "plan": user.plan,
                "select_count": user.select_count,
                "select_limit": user.select_limit,
                "ads_count": user.ads_count,
                "ads_limit": user.ads_limit
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="登录失败，请稍后重试")

@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
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
    """获取所有套餐信息"""
    return {
        "success": True,
        "plans": PLANS
    }

@app.post("/api/purchase")
async def purchase(
    purchase_data: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """购买套餐"""
    try:
        plan = purchase_data.plan
        duration = purchase_data.duration
        
        if plan not in PLANS or plan == "free":
            raise HTTPException(status_code=400, detail="无效的套餐")
        
        plan_info = PLANS[plan]
        amount = plan_info[f"price_{duration}"]
        
        # 创建订单
        order = Order(
            user_id=current_user.id,
            plan=plan,
            duration=duration,
            amount=amount,
            status="pending"
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        logger.info(f"订单创建: user_id={current_user.id}, order_id={order.id}, plan={plan}")
        
        return {
            "success": True,
            "message": "订单创建成功",
            "order_id": order.id,
            "amount": amount,
            "payment_url": f"/payment/{order.id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建订单失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建订单失败，请稍后重试")

@app.post("/api/payment/callback/{order_id}")
async def payment_callback(order_id: int, signature: str = Header(None), db: Session = Depends(get_db)):
    """支付回调（带签名验证）"""
    try:
        # 验证签名
        if not signature or not verify_payment_signature(order_id, signature):
            logger.warning(f"支付回调签名验证失败: order_id={order_id}")
            raise HTTPException(status_code=403, detail="签名验证失败")
        
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        if order.status == "paid":
            return {"success": True, "message": "订单已支付"}
        
        # 更新订单状态
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        
        # 更新用户套餐
        user = db.query(User).filter(User.id == order.user_id).first()
        user.plan = order.plan
        
        plan_info = PLANS[order.plan]
        user.select_limit = plan_info["select_limit"]
        user.ads_limit = plan_info["ads_limit"]
        
        # 设置过期时间
        if order.duration == "monthly":
            user.plan_expire_date = datetime.utcnow() + timedelta(days=30)
        else:  # yearly
            user.plan_expire_date = datetime.utcnow() + timedelta(days=365)
        
        db.commit()
        
        logger.info(f"支付成功: order_id={order_id}, user_id={user.id}")
        
        return {
            "success": True,
            "message": "支付成功，套餐已激活"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"支付回调处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail="支付处理失败，请联系客服")

@app.post("/api/select-products")
async def select_products(
    request: ProductSelectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """智能选品"""
    try:
        # 速率限制
        if not check_rate_limit(current_user.id):
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        
        # 检查使用次数
        if not check_usage_limit(current_user, "select_product"):
            raise HTTPException(
                status_code=403,
                detail=f"本月选品次数已用完（{current_user.select_count}/{current_user.select_limit}），请升级套餐"
            )
        
        result = await product_selector.analyze(
            budget=request.budget,
            category=request.category,
            experience=request.experience,
            platform=request.platform
        )
        
        # 增加使用次数
        increment_usage(db, current_user, "select_product")
        
        # 记录使用日志
        log = UsageLog(
            user_id=current_user.id,
            action="select_product",
            details=json.dumps({
                "platform": request.platform,
                "category": request.category,
                "budget": request.budget
            })
        )
        db.add(log)
        db.commit()
        # 存储分析历史
        analysis_history = AnalysisHistory(
            user_id=current_user.id,
            analysis_type="product",
            input_data=json.dumps({
                "platform": request.platform,
                "category": request.category,
                "budget": request.budget,
                "experience": request.experience
            }),
            result_data=json.dumps(result, ensure_ascii=False)
        )
        db.add(analysis_history)
        
        logger.info(f"选品分析: user_id={current_user.id}, platform={request.platform}")
        
        # 添加剩余次数信息
        result["usage"] = {
            "used": current_user.select_count,
            "limit": current_user.select_limit,
            "remaining": current_user.select_limit - current_user.select_count
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"选品分析失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(status_code=500, detail="分析失败，请稍后重试")

@app.post("/api/analyze-ads")
async def analyze_ads(
    request: AdAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """投流数据分析"""
    try:
        # 速率限制
        if not check_rate_limit(current_user.id):
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        
        # 检查使用次数
        if not check_usage_limit(current_user, "analyze_ads"):
            raise HTTPException(
                status_code=403,
                detail=f"本月投流分析次数已用完（{current_user.ads_count}/{current_user.ads_limit}），请升级套餐"
            )
        
        result = await ad_optimizer.analyze(
            platform=request.platform,
            data=request.data,
            analysis_type=request.analysis_type,
            category=request.category
        )
        
        # 增加使用次数
        increment_usage(db, current_user, "analyze_ads")
        
        # 记录使用日志
        log = UsageLog(
            user_id=current_user.id,
            action="analyze_ads",
            details=json.dumps({
                "platform": request.platform,
                "analysis_type": request.analysis_type
            })
        )
        db.add(log)
        db.commit()
        
        # 存储分析历史
        analysis_history = AnalysisHistory(
            user_id=current_user.id,
            analysis_type="ad",
            input_data=json.dumps({
                "platform": request.platform,
                "analysis_type": request.analysis_type,
                "category": request.category
            }),
            result_data=json.dumps(result, ensure_ascii=False)
        )
        db.add(analysis_history)
        logger.info(f"投流分析: user_id={current_user.id}, platform={request.platform}")
        
        # 添加剩余次数信息
        result["usage"] = {
            "used": current_user.ads_count,
            "limit": current_user.ads_limit,
            "remaining": current_user.ads_limit - current_user.ads_count
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"投流分析失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(status_code=500, detail="分析失败，请稍后重试")

@app.get("/api/usage-history")
async def get_usage_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取使用记录"""
    logs = db.query(UsageLog).filter(
        UsageLog.user_id == current_user.id
    ).order_by(UsageLog.created_at.desc()).limit(50).all()
    
    return {
        "success": True,
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "details": json.loads(log.details) if log.details else {},
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }

@app.post("/api/pricing/calculate")
async def calculate_pricing(request: PricingRequest):
    """定价计算器"""
    result = pricing_calculator.calculate_price(
        cost=request.cost,
        target_margin=request.target_margin,
        shipping=request.shipping
    )
    return result

@app.post("/api/pricing/compare")
async def compare_pricing(request: CompetitorCompareRequest):
    """竞品价格对比"""
    result = pricing_calculator.compare_with_competitors(
        your_price=request.your_price,
        competitor_prices=request.competitor_prices
    )
    return result

@app.get("/api/tutorials")
async def get_tutorials():
    """获取新手教程列表"""
    tutorials = [
        {"id": 1, "title": "拼多多开店完整流程", "category": "开店"},
        {"id": 2, "title": "拼多多店铺基础设置", "category": "开店"},
        {"id": 3, "title": "如何选品（新手必看）", "category": "选品"},
        {"id": 4, "title": "拼多多商品定价策略", "category": "定价"},
        {"id": 5, "title": "拼多多推广通入门", "category": "投流"},
        {"id": 6, "title": "全站推广 vs 标准推广怎么选", "category": "投流"},
        {"id": 7, "title": "如何提高转化率", "category": "运营"},
        {"id": 8, "title": "新手常见错误（避坑指南）", "category": "避坑"},
        {"id": 9, "title": "如何看懂推广数据", "category": "数据"},
        {"id": 10, "title": "月销0到1万的完整路径", "category": "进阶"}
    ]
    return {"success": True, "tutorials": tutorials}

@app.post("/api/competitor/analyze")
async def analyze_competitor(
    request: CompetitorAnalyzeRequest,
    current_user: User = Depends(get_current_user)
):
    """竞品分析"""
    try:
        result = competitor_analyzer.analyze_competitor(
            competitor_url=request.competitor_url,
            platform=request.platform
        )
        return result
    except Exception as e:
        logger.error(f"竞品分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail="分析失败，请稍后重试")

@app.post("/api/export")
async def export_data(
    request: ExportRequest,
    current_user: User = Depends(get_current_user)
):
    """导出数据"""
    try:
        if request.data_type in ["select", "ads"]:
            result = data_exporter.export_analysis_report(
                analysis_data=request.data,
                report_type=request.data_type
            )
            return result
        else:
            return {"success": False, "message": "不支持的导出类型"}
    except Exception as e:
        logger.error(f"数据导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导出失败，请稍后重试")

@app.post("/api/ads/deep-analyze")
async def deep_analyze_ads(
    request: DeepAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """深度投流分析 - 优化师级别"""
    try:
        # 速率限制
        if not check_rate_limit(current_user.id):
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        
        # 检查使用次数
        if not check_usage_limit(current_user, "analyze_ads"):
            raise HTTPException(
                status_code=403,
                detail=f"本月投流分析次数已用完（{current_user.ads_count}/{current_user.ads_limit}），请升级套餐"
            )
        
        # 解析数据
        parsed_data = ad_optimizer._parse_pdd_data(request.data)
        
        if not parsed_data:
            return {
                "success": False,
                "message": "数据格式错误"
            }
        
        # 深度分析
        result = await advanced_ad_optimizer.deep_analyze(
            platform=request.platform,
            data=parsed_data,
            budget=request.budget,
            goal=request.goal,
            category=request.category
        )
        
        # 增加使用次数
        increment_usage(db, current_user, "analyze_ads")
        
        # 记录使用日志
        log = UsageLog(
            user_id=current_user.id,
            action="deep_analyze_ads",
            details=json.dumps({
                "platform": request.platform,
                "goal": request.goal,
                "budget": request.budget
            })
        )
        db.add(log)
        db.commit()
        
        logger.info(f"深度投流分析: user_id={current_user.id}, goal={request.goal}")
        
        # 添加剩余次数信息
        result["usage"] = {
            "used": current_user.ads_count,
            "limit": current_user.ads_limit,
            "remaining": current_user.ads_limit - current_user.ads_count
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"深度投流分析失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(status_code=500, detail="分析失败，请稍后重试")

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0"
    }

# ==================== 新增功能接口 ====================

@app.post("/api/payment/create")
async def create_payment(
    request: PurchaseRequest,
    payment_method: str = "alipay",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建支付订单"""
    try:
        plan_info = PLANS.get(request.plan)
        if not plan_info:
            raise HTTPException(status_code=400, detail="无效的套餐")
        
        # 计算金额
        if request.duration == "yearly":
            amount = plan_info["yearly_price"]
        else:
            amount = plan_info["monthly_price"]
        
        # 创建订单
        order = Order(
            user_id=current_user.id,
            plan=request.plan,
            amount=amount,
            duration=request.duration,
            status="pending"
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # 创建支付
        payment_result = payment_manager.create_payment(
            payment_method=payment_method,
            order_id=order.id,
            amount=amount,
            subject=f"多多AI优化师 - {plan_info['name']}"
        )
        
        logger.info(f"创建支付订单: user_id={current_user.id}, order_id={order.id}, amount={data.amount}")
        
        return {
            "success": True,
            "order_id": order.id,
            "payment": payment_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建支付订单失败: {e}")
        raise HTTPException(status_code=500, detail="创建订单失败")

@app.post("/api/payment/callback")
async def payment_callback(request: Request, db: Session = Depends(get_db)):
    """支付回调"""
    try:
        params = await request.json()
        order_id = params.get("order_id")
        payment_method = params.get("payment_method", "alipay")
        
        # 验证签名
        if not payment_manager.verify_payment_callback(payment_method, params):
            raise HTTPException(status_code=400, detail="签名验证失败")
        
        # 更新订单状态
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        if order.status == "paid":
            return {"success": True, "message": "订单已支付"}
        
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        
        # 更新用户套餐
        user = db.query(User).filter(User.id == order.user_id).first()
        user.plan = order.plan
        
        plan_info = PLANS.get(order.plan)
        user.select_limit = plan_info["select_limit"]
        user.ads_limit = plan_info["ads_limit"]
        
        if order.duration == "yearly":
            user.plan_expire_date = datetime.utcnow() + timedelta(days=365)
        else:
            user.plan_expire_date = datetime.utcnow() + timedelta(days=30)
        
        db.commit()
        
        logger.info(f"支付成功: order_id={order_id}, user_id={user.id}")
        
        return {"success": True, "message": "支付成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"支付回调处理失败: {e}")
        raise HTTPException(status_code=500, detail="处理失败")

@app.post("/api/email/send-verification")
async def send_verification_code(email: EmailStr):
    """发送验证码"""
    try:
        code = email_service.send_verification_code(email)
        if code:
            return {"success": True, "message": "验证码已发送"}
        else:
            raise HTTPException(status_code=500, detail="发送失败")
    except Exception as e:
        logger.error(f"发送验证码失败: {e}")
        raise HTTPException(status_code=500, detail="发送失败")

@app.post("/api/email/verify-code")
async def verify_email_code(email: EmailStr, code: str):
    """验证邮箱验证码"""
    if email_service.verify_code(email, code):
        return {"success": True, "message": "验证成功"}
    else:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

@app.post("/api/password/reset-request")
async def request_password_reset(email: EmailStr, db: Session = Depends(get_db)):
    """请求重置密码"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # 为了安全，不透露用户是否存在
            return {"success": True, "message": "如果邮箱存在，重置链接已发送"}
        
        token = email_service.send_password_reset_email(email, user.username)
        if token:
            return {"success": True, "message": "重置链接已发送到您的邮箱"}
        else:
            raise HTTPException(status_code=500, detail="发送失败")
    except Exception as e:
        logger.error(f"请求重置密码失败: {e}")
        raise HTTPException(status_code=500, detail="发送失败")

@app.post("/api/password/reset")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """重置密码"""
    try:
        if not validate_password_strength(new_password):
            raise HTTPException(status_code=400, detail="密码必须至少8位，且包含字母和数字")
        
        email = email_service.verify_reset_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="重置链接无效或已过期")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        
        logger.info(f"密码重置成功: {email}")
        
        return {"success": True, "message": "密码重置成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置密码失败: {e}")
        raise HTTPException(status_code=500, detail="重置失败")

@app.post("/api/visualization/roi-chart")
async def create_roi_chart(data: List[Dict], current_user: User = Depends(get_current_user)):
    """生成ROI趋势图"""
    try:
        chart_json = visualizer.create_roi_chart(data)
        return {"success": True, "chart": chart_json}
    except Exception as e:
        logger.error(f"生成图表失败: {e}")
        raise HTTPException(status_code=500, detail="生成失败")

@app.post("/api/visualization/keyword-chart")
async def create_keyword_chart(keywords: List[Dict], current_user: User = Depends(get_current_user)):
    """生成关键词性能图"""
    try:
        chart_json = visualizer.create_keyword_performance_chart(keywords)
        return {"success": True, "chart": chart_json}
    except Exception as e:
        logger.error(f"生成图表失败: {e}")
        raise HTTPException(status_code=500, detail="生成失败")

@app.post("/api/batch/product-analysis")
async def batch_product_analysis(
    requests: List[Dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量商品分析"""
    try:
        # 检查套餐限制
        if current_user.plan == "free":
            raise HTTPException(status_code=403, detail="免费版不支持批量分析")
        
        if len(requests) > 10:
            raise HTTPException(status_code=400, detail="单次最多分析10个")
        
        results = await batch_analysis_service.batch_product_analysis(requests)
        
        logger.info(f"批量商品分析: user_id={current_user.id}, count={len(requests)}")
        
        return {"success": True, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量分析失败: {e}")
        raise HTTPException(status_code=500, detail="分析失败")

@app.post("/api/batch/ad-analysis")
async def batch_ad_analysis(
    requests: List[Dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量投流分析"""
    try:
        # 检查套餐限制
        if current_user.plan == "free":
            raise HTTPException(status_code=403, detail="免费版不支持批量分析")
        
        if len(requests) > 10:
            raise HTTPException(status_code=400, detail="单次最多分析10个")
        
        results = await batch_analysis_service.batch_ad_analysis(requests)
        
        logger.info(f"批量投流分析: user_id={current_user.id}, count={len(requests)}")
        
        return {"success": True, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量分析失败: {e}")
        raise HTTPException(status_code=500, detail="分析失败")

@app.post("/api/export/results")
async def export_results(
    results: List[Dict],
    format: str = "json",
    current_user: User = Depends(get_current_user)
):
    """导出分析结果"""
    try:
        exported = batch_analysis_service.batch_export(results, format)
        
        return {
            "success": True,
            "format": format,
            "data": exported
        }
    except Exception as e:
        logger.error(f"导出失败: {e}")
        raise HTTPException(status_code=500, detail="导出失败")

# ==================== 手动支付接口 ====================

class ManualPaymentRequest(BaseModel):
    plan: str
    duration: str
    payment_method: str
    amount: float
    transaction_id: str
    note: Optional[str] = None

@app.post("/api/payment/manual-submit")
async def manual_payment_submit(
    data: ManualPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户提交手动支付信息"""
    try:
        # 创建订单
        order = Order(
            user_id=current_user.id,
            plan=data.plan,
            duration=data.duration,
            amount=data.amount,
            payment_method=data.payment_method,
            transaction_id=data.transaction_id,
            note=data.note,
            status="pending"
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        logger.info(f"用户提交支付: user_id={current_user.id}, order_id={order.id}, amount={data.amount}")
        
        return {
            "success": True,
            "message": "提交成功，请等待审核",
            "order_id": order.id
        }
    except Exception as e:
        logger.error(f"提交支付失败: {e}")
        raise HTTPException(status_code=500, detail="提交失败")

# ==================== 管理员接口 ====================

from database import Admin

class AdminLogin(BaseModel):
    username: str
    password: str

@app.post("/api/admin/login")
async def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    """管理员登录"""
    try:
        admin = db.query(Admin).filter(Admin.username == data.username).first()
        
        if not admin or not verify_password(data.password, admin.hashed_password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        if not admin.is_active:
            raise HTTPException(status_code=403, detail="账户已被禁用")
        
        # 生成token
        token = create_access_token(data={"admin_id": admin.id, "type": "admin"})
        
        logger.info(f"管理员登录: {admin.username}")
        
        return {
            "success": True,
            "token": token
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"管理员登录失败: {e}")
        raise HTTPException(status_code=500, detail="登录失败")

def get_current_admin(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Admin:
    """获取当前管理员"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    
    if not payload or payload.get("type") != "admin":
        raise HTTPException(status_code=401, detail="Token无效")
    
    admin_id = payload.get("admin_id")
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="管理员不存在或已禁用")
    
    return admin


@app.get("/api/analysis-history")
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取分析历史记录"""
    try:
        query = db.query(AnalysisHistory).filter(
            AnalysisHistory.user_id == current_user.id
        )
        
        if type:
            query = query.filter(AnalysisHistory.analysis_type == type)
        
        total = query.count()
        
        history = query.order_by(
            AnalysisHistory.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "total": total,
            "history": [
                {
                    "id": h.id,
                    "type": h.analysis_type,
                    "summary": (json.loads(h.result_data).get("result", {}).get("summary", "")[:100] if h.result_data else ""),
                    "created_at": h.created_at.isoformat()
                }
                for h in history
            ]
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
    """获取单条分析详情"""
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

@app.get("/api/admin/orders")
async def get_admin_orders(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取所有订单"""
    try:
        orders = db.query(Order).order_by(Order.created_at.desc()).all()
        
        # 获取用户信息
        order_list = []
        for order in orders:
            user = db.query(User).filter(User.id == order.user_id).first()
            order_list.append({
                "id": order.id,
                "user_email": user.email if user else "未知",
                "plan_name": PLANS.get(order.plan, {}).get("name", order.plan),
                "amount": order.amount,
                "payment_method": order.payment_method,
                "transaction_id": order.transaction_id,
                "note": order.note,
                "status": order.status,
                "created_at": order.created_at.isoformat()
            })
        
        # 统计数据
        today = datetime.utcnow().date()
        pending_count = len([o for o in orders if o.status == "pending"])
        today_count = len([o for o in orders if o.created_at.date() == today])
        today_revenue = sum([o.amount for o in orders if o.created_at.date() == today and o.status == "approved"])
        user_count = db.query(User).count()
        
        return {
            "success": True,
            "orders": order_list,
            "stats": {
                "pending": pending_count,
                "today": today_count,
                "revenue": today_revenue,
                "users": user_count
            }
        }
    except Exception as e:
        logger.error(f"获取订单失败: {e}")
        raise HTTPException(status_code=500, detail="获取失败")

@app.post("/api/admin/orders/{order_id}/approve")
async def approve_order(
    order_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """通过订单"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        if order.status != "pending":
            raise HTTPException(status_code=400, detail="订单状态不正确")
        
        # 更新订单状态
        order.status = "approved"
        order.approved_at = datetime.utcnow()
        
        # 更新用户套餐
        user = db.query(User).filter(User.id == order.user_id).first()
        if user:
            user.plan = order.plan
            plan_info = PLANS.get(order.plan, {})
            user.select_limit = plan_info.get("select_limit", 3)
            user.ads_limit = plan_info.get("ads_limit", 3)
            
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
        logger.error(f"通过订单失败: {e}")
        raise HTTPException(status_code=500, detail="操作失败")

@app.post("/api/admin/orders/{order_id}/reject")
async def reject_order(
    order_id: int,
    reason: str,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """拒绝订单"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        if order.status != "pending":
            raise HTTPException(status_code=400, detail="订单状态不正确")
        
        order.status = "rejected"
        order.reject_reason = reason
        db.commit()
        
        logger.info(f"订单已拒绝: order_id={order_id}, reason={reason}")
        
        return {"success": True, "message": "订单已拒绝"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"拒绝订单失败: {e}")
        raise HTTPException(status_code=500, detail="操作失败")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
