import logging
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from collections import defaultdict

logger = logging.getLogger(__name__)

# 토큰 사용량 저장을 위한 임시 저장소 (실제로는 DB 사용 필요)
token_usage = defaultdict(list)

async def log_token_usage(room: str, tokens_used: int, timestamp: datetime, task: str = "chat"):
    """토큰 사용량을 기록합니다"""
    try:
        # 토큰 사용량 기록
        token_usage[room].append({
            'tokens': tokens_used,
            'timestamp': timestamp,
            'task': task
        })
        logger.info(f"토큰 사용 기록: {room}, {tokens_used} tokens, {task}")
    except Exception as e:
        logger.error(f"토큰 사용량 기록 중 오류: {str(e)}")

async def get_monthly_usage():
    """이번 달 토큰 사용량을 반환합니다"""
    try:
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total_tokens = 0
        for room in token_usage:
            for usage in token_usage[room]:
                if usage['timestamp'] >= month_start:
                    total_tokens += usage['tokens']
        
        return f"{total_tokens:,} 토큰"
    except Exception as e:
        logger.error(f"토큰 사용량 조회 중 오류: {str(e)}")
        return "조회 중 오류 발생"

async def predict_monthly_usage():
    """이번 달 예상 토큰 사용량을 선형회귀로 계산합니다"""
    try:
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 일별 사용량 집계
        daily_usage = defaultdict(int)
        for room in token_usage:
            for usage in token_usage[room]:
                if usage['timestamp'] >= month_start:
                    day = usage['timestamp'].date()
                    daily_usage[day] += usage['tokens']
        
        if not daily_usage:
            return "데이터가 충분하지 않습니다"
        
        # 선형회귀를 위한 데이터 준비
        days = [(date - month_start.date()).days for date in daily_usage.keys()]
        tokens = list(daily_usage.values())
        
        X = np.array(days).reshape(-1, 1)
        y = np.array(tokens)
        
        # 선형회귀 모델 학습
        model = LinearRegression()
        model.fit(X, y)
        
        # 이번 달 마지막 날까지 예측
        last_day = (month_start.replace(month=month_start.month + 1) - timedelta(days=1)).date()
        total_days = (last_day - month_start.date()).days + 1
        
        # 전체 예측값 계산
        predicted_total = int(model.predict([[total_days - 1]])[0] * total_days / len(days))
        
        return f"예상 사용량: {predicted_total:,} 토큰"
        
    except Exception as e:
        logger.error(f"토큰 사용량 예측 중 오류: {str(e)}")
        return "예측 중 오류 발생" 