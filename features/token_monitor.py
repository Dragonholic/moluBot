import json
import os
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Tuple
from sklearn.linear_model import LinearRegression

TOKEN_USAGE_FILE = "data/token_usage.json"
os.makedirs("data", exist_ok=True)

# 토큰 사용량 저장 파일 초기화
if not os.path.exists(TOKEN_USAGE_FILE):
    with open(TOKEN_USAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump({"usage": []}, f)

async def log_token_usage(input_tokens: int, output_tokens: int):
    """토큰 사용량 기록"""
    try:
        with open(TOKEN_USAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 비용 계산
        input_cost = input_tokens * 0.0000037  # $3/MTok
        output_cost = output_tokens * 0.000015  # $15/MTok
        total_cost = input_cost + output_cost
        
        # 현재 날짜와 토큰 사용량 기록
        usage = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }
        
        data["usage"].append(usage)
        
        with open(TOKEN_USAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"토큰 사용량 기록 중 오류: {str(e)}")

async def get_monthly_usage() -> Dict:
    """현재 달의 토큰 사용량 조회"""
    try:
        with open(TOKEN_USAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        current_month = datetime.now().strftime("%Y-%m")
        monthly_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "input_cost": 0,
            "output_cost": 0,
            "total_cost": 0
        }
        
        for usage in data["usage"]:
            usage_date = datetime.strptime(usage["date"], "%Y-%m-%d")
            if usage_date.strftime("%Y-%m") == current_month:
                monthly_usage["input_tokens"] += usage["input_tokens"]
                monthly_usage["output_tokens"] += usage["output_tokens"]
                monthly_usage["total_tokens"] += usage["total_tokens"]
                monthly_usage["input_cost"] += usage["input_cost"]
                monthly_usage["output_cost"] += usage["output_cost"]
                monthly_usage["total_cost"] += usage["total_cost"]
        
        return monthly_usage
    
    except Exception as e:
        return {"error": str(e)}

async def predict_monthly_usage() -> Dict:
    """선형 회귀를 사용한 월간 사용량 예측"""
    try:
        with open(TOKEN_USAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if len(data["usage"]) < 7:  # 최소 7일의 데이터 필요
            return {"error": "예측을 위한 충분한 데이터가 없습니다."}
        
        # 데이터 준비
        dates = []
        daily_totals = []
        
        for usage in data["usage"]:
            dates.append(datetime.strptime(usage["date"], "%Y-%m-%d").timestamp())
            daily_totals.append(usage["total_tokens"])
        
        # 선형 회귀 수행
        X = np.array(dates).reshape(-1, 1)
        y = np.array(daily_totals)
        model = LinearRegression()
        model.fit(X, y)
        
        # 한 달 후 예측
        future_date = datetime.now() + timedelta(days=30)
        future_prediction = model.predict([[future_date.timestamp()]])[0]
        
        # 월간 예상 사용량 및 비용
        predicted_monthly = future_prediction * 30
        predicted_cost = predicted_monthly * 0.000015  # 평균 토큰 비용 사용
        
        return {
            "predicted_monthly_tokens": int(predicted_monthly),
            "predicted_monthly_cost": round(predicted_cost, 2),
            "confidence": round(model.score(X, y) * 100, 2)  # 예측 신뢰도
        }
        
    except Exception as e:
        return {"error": str(e)} 