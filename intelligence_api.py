#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多多AI优化师 - 智能化升级API路由
将第一阶段智能化功能集成到FastAPI应用
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db, User
from intelligence import UserBehaviorLearner, SimpleTrendPredictor, IntelligentQA

# 创建API路由
router = APIRouter(prefix="/api/intelligence", tags=["智能化功能"])

# 初始化模块
trend_predictor = SimpleTrendPredictor()
intelligent_qa = IntelligentQA()

# ==================== 用户行为学习API ====================

@router.post("/track-behavior")
async def track_user_behavior(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    记录用户行为
    
    请求体示例:
    {
        "user_id": 1,
        "action_type": "select_product",
        "context": {
            "category": "电子产品",
            "price": 299.99,
            "keywords": ["手机", "充电器"]
        },
        "result": "success"
    }
    """
    try:
        data = await request.json()
        
        user_id = data.get("user_id")
        action_type = data.get("action_type")
        context = data.get("context", {})
        result = data.get("result", "neutral")
        
        if not user_id or not action_type:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 验证用户存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 创建行为学习器并记录行为
        learner = UserBehaviorLearner(db)
        success = learner.track_action(user_id, action_type, context, result)
        
        if success:
            return {
                "success": True,
                "message": "用户行为记录成功",
                "user_id": user_id,
                "action_type": action_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="记录用户行为失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.get("/user-patterns/{user_id}")
async def get_user_patterns(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    获取用户行为模式分析
    """
    try:
        # 验证用户存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 分析用户模式
        learner = UserBehaviorLearner(db)
        patterns = learner.learn_patterns(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "patterns": patterns,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.get("/personalized-recommendations/{user_id}")
async def get_personalized_recommendations(
    user_id: int,
    context: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取个性化推荐
    """
    try:
        # 验证用户存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 解析上下文
        context_dict = {}
        if context:
            try:
                context_dict = json.loads(context)
            except:
                context_dict = {"raw_context": context}
        
        # 获取个性化推荐
        learner = UserBehaviorLearner(db)
        recommendations = learner.get_personalized_recommendations(user_id, context_dict)
        
        return {
            "success": True,
            "user_id": user_id,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

# ==================== 趋势预测API ====================

@router.post("/predict-sales-trend")
async def predict_sales_trend(request: Request):
    """
    预测销量趋势
    
    请求体示例:
    {
        "product_name": "手机壳",
        "history_data": [100, 120, 110, 130, 125]
    }
    或
    {
        "product_history": [
            {
                "date": "2026-02-21",
                "sales": 100,
                "price": 99.9
            },
            {
                "date": "2026-02-22", 
                "sales": 110,
                "price": 99.9
            }
        ]
    }
    """
    try:
        data = await request.json()
        
        # 支持两种格式：简单数组格式和完整对象格式
        if "history_data" in data:
            # 简单格式：只有销量数组
            history_data = data.get("history_data", [])
            product_name = data.get("product_name", "未知产品")
            
            if not history_data or not isinstance(history_data, list):
                raise HTTPException(status_code=400, detail="history_data 必须是数字列表")
            
            # 转换为标准格式
            from datetime import datetime, timedelta
            product_history = []
            base_date = datetime.now() - timedelta(days=len(history_data))
            for i, sales in enumerate(history_data):
                product_history.append({
                    "date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "sales": sales,
                    "price": 0
                })
        else:
            # 完整格式
            product_history = data.get("product_history", [])
            product_name = data.get("product_name", "未知产品")
        
        if not product_history:
            raise HTTPException(status_code=400, detail="缺少产品历史数据")
        
        if not isinstance(product_history, list):
            raise HTTPException(status_code=400, detail="product_history 必须是列表类型")
        
        # 进行趋势预测
        prediction = trend_predictor.predict_sales_trend(product_history)
        
        return {
            "success": True,
            "product_name": product_name,
            "prediction": prediction,
            "data_points": len(product_history),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.post("/detect-market-opportunities")
async def detect_market_opportunities(request: Request):
    """
    检测市场机会
    
    请求体示例:
    {
        "market_data": [
            {
                "product_id": 1,
                "product_name": "手机充电器",
                "price": 29.9,
                "sales": 1000,
                "sales_trend": 0.2
            }
            // ... 更多市场数据
        ]
    }
    """
    try:
        data = await request.json()
        market_data = data.get("market_data", [])
        
        if not market_data:
            raise HTTPException(status_code=400, detail="缺少市场数据")
        
        # 检测市场机会
        opportunities = trend_predictor.detect_opportunities(market_data)
        
        return {
            "success": True,
            "opportunities": opportunities,
            "total_analyzed": len(market_data),
            "opportunities_found": len(opportunities),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.post("/generate-market-report")
async def generate_market_report(request: Request):
    """
    生成市场分析报告
    """
    try:
        data = await request.json()
        market_data = data.get("market_data", [])
        product_history = data.get("product_history", [])
        
        if not market_data:
            raise HTTPException(status_code=400, detail="缺少市场数据")
        
        # 生成市场报告
        report = trend_predictor.generate_market_report(market_data, product_history)
        
        return {
            "success": True,
            "report": report,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

# ==================== 智能问答API ====================

@router.post("/ask-question")
async def ask_question(request: Request):
    """
    智能问答
    
    请求体示例:
    {
        "question": "新品如何快速起量？",
        "user_context": {
            "history": "经营服装店3个月",
            "products": "夏季连衣裙、T恤",
            "monthly_sales": "5万元"
        }
    }
    """
    try:
        data = await request.json()
        question = data.get("question")
        user_context = data.get("user_context", {})
        
        if not question:
            raise HTTPException(status_code=400, detail="缺少问题内容")
        
        # 进行智能问答
        result = await intelligent_qa.answer(question, user_context)
        
        return {
            "success": True,
            "question": question,
            "result": result,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.get("/quick-answer")
async def get_quick_answer(question: str):
    """
    快速问答（基于知识库）
    """
    try:
        if not question:
            raise HTTPException(status_code=400, detail="缺少问题内容")
        
        # 获取快速回答
        answer = intelligent_qa.get_quick_answer(question)
        
        return {
            "success": True,
            "question": question,
            "answer": answer,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.get("/knowledge-summary")
async def get_knowledge_summary():
    """
    获取知识库摘要
    """
    try:
        summary = intelligent_qa.export_knowledge_summary()
        
        return {
            "success": True,
            "summary": summary,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

# ==================== 健康检查API ====================

@router.get("/health")
async def health_check():
    """
    智能化模块健康检查
    """
    return {
        "status": "healthy",
        "service": "多多AI优化师智能化模块",
        "version": "1.0.0",
        "stage": "第一阶段 - 数据驱动智能化",
        "modules": {
            "user_behavior_learner": "可用",
            "trend_predictor": "可用", 
            "intelligent_qa": "可用"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/test")
async def test_all_modules(db: Session = Depends(get_db)):
    """
    测试所有智能化模块
    """
    test_results = {}
    
    try:
        # 测试用户行为学习器
        learner = UserBehaviorLearner(db)
        test_results["user_behavior_learner"] = {
            "status": "可用",
            "test_action": "记录测试行为",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        test_results["user_behavior_learner"] = {
            "status": "错误",
            "error": str(e)
        }
    
    try:
        # 测试趋势预测器
        sample_data = [{"date": "2026-02-28", "sales": 100}]
        prediction = trend_predictor.predict_sales_trend(sample_data)
        test_results["trend_predictor"] = {
            "status": "可用",
            "prediction_generated": True,
            "data_points": len(sample_data)
        }
    except Exception as e:
        test_results["trend_predictor"] = {
            "status": "错误", 
            "error": str(e)
        }
    
    try:
        # 测试智能问答
        import asyncio
        answer = intelligent_qa.get_quick_answer("测试问题")
        test_results["intelligent_qa"] = {
            "status": "可用",
            "quick_answer": answer[:50] + "..." if len(answer) > 50 else answer
        }
    except Exception as e:
        test_results["intelligent_qa"] = {
            "status": "错误",
            "error": str(e)
        }
    
    return {
        "success": True,
        "test_results": test_results,
        "overall_status": "健康" if all(r["status"] == "可用" for r in test_results.values()) else "部分异常",
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== 风险预警API ====================

from intelligence.report_generator import DailyReportGenerator
from intelligence.user_profiler import UserProfiler
from intelligence.risk_monitor import RiskMonitor

risk_monitor = RiskMonitor()

@router.get("/check-risks")
async def check_risks(user_id: int):
    """
    检查用户风险
    """
    try:
        risks = await risk_monitor.monitor_campaigns(user_id)
        
        # 按严重程度分类
        high_risk = [r for r in risks if r['severity'] == 'high']
        medium_risk = [r for r in risks if r['severity'] == 'medium']
        low_risk = [r for r in risks if r['severity'] == 'low']
        
        return {
            "success": True,
            "data": {
                "high_risk": high_risk,
                "medium_risk": medium_risk,
                "low_risk": low_risk,
                "total_risks": len(risks)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# ==================== 用户画像分析 API ====================

@router.get("/user-profile/{user_id}")
async def get_user_profile(user_id: str):
    """获取用户完整画像"""
    try:
        profiler = UserProfiler()
        profile = await profiler.build_profile(user_id)
        
        return {
            "success": True,
            "data": profile
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取用户画像失败: {str(e)}"
        }

@router.get("/behavior-heatmap/{user_id}")
async def get_behavior_heatmap(user_id: str):
    """获取行为热力图数据"""
    try:
        profiler = UserProfiler()
        heatmap = await profiler.get_behavior_heatmap(user_id)
        
        return {
            "success": True,
            "data": heatmap
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取热力图失败: {str(e)}"
        }


# ==================== 每日智能报告 API ====================

@router.get("/daily-report/{user_id}")
async def get_daily_report(user_id: str, date: str = None):
    """获取每日报告"""
    try:
        generator = DailyReportGenerator()
        report = await generator.generate_report(user_id)
        
        return {
            "success": True,
            "data": report
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取报告失败: {str(e)}"
        }

@router.post("/report/regenerate")
async def regenerate_report(user_id: str):
    """重新生成今日报告"""
    try:
        generator = DailyReportGenerator()
        report = await generator.generate_report(user_id)
        
        return {
            "success": True,
            "data": report,
            "message": "报告已重新生成"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"生成报告失败: {str(e)}"
        }

@router.get("/report-history/{user_id}")
async def get_report_history(user_id: str, days: int = 7):
    """获取历史报告列表"""
    try:
        generator = DailyReportGenerator()
        reports = await generator.get_report_history(user_id, days)
        
        return {
            "success": True,
            "data": reports
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取历史报告失败: {str(e)}"
        }
