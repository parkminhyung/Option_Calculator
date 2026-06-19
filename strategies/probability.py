import numpy as np
import scipy.stats as stats


def calculate_price_probability(
    current_price,
    target_price,
    days,
    volatility,
    dividend_yield=0,
    risk_free_rate=0,
):
    """
    기초자산 가격이 만기일에 특정 가격보다 높을/낮을 확률 계산
    
    Parameters:
    -----------
    current_price : float
        현재 기초자산 가격
    target_price : float
        목표 기초자산 가격
    days : int
        만기까지 남은 일수
    volatility : float
        연간 변동성 (%)
    dividend_yield : float, optional
        배당수익률 (%)
        
    Returns:
    --------
    tuple
        (상승 확률, 하락 확률)
    """
    if days <= 0 or volatility <= 0:
        return 0.5, 0.5
    
    # 파라미터 변환
    vol = volatility / 100.0
    div = dividend_yield / 100.0
    rf = risk_free_rate / 100.0
    t = days / 252.0  # 거래일 기준으로 변환
    
    # 로그 정규 분포 파라미터 계산
    mu = np.log(current_price) + (rf - div - (vol**2) / 2) * t
    sigma = vol * np.sqrt(t)
    
    # 확률 계산
    z = (np.log(target_price) - mu) / sigma
    prob_above = 1 - stats.norm.cdf(z)
    prob_below = stats.norm.cdf(z)
    
    return prob_above, prob_below


def calculate_expiry_range(
    current_price,
    days,
    volatility,
    confidence=0.68,
    dividend_yield=0,
    risk_free_rate=0,
):
    """
    특정 신뢰도에 따른 만기일의 가격 범위 계산
    
    Parameters:
    -----------
    current_price : float
        현재 기초자산 가격
    days : int
        만기까지 남은 일수
    volatility : float
        연간 변동성 (%)
    confidence : float, optional
        신뢰도 수준 (0.0 ~ 1.0)
    dividend_yield : float, optional
        배당수익률 (%)
        
    Returns:
    --------
    tuple
        (하한가, 상한가)
    """
    if days <= 0 or volatility <= 0:
        return current_price, current_price
    
    # 파라미터 변환
    vol = volatility / 100.0
    div = dividend_yield / 100.0
    rf = risk_free_rate / 100.0
    t = days / 252.0  # 거래일 기준으로 변환
    
    # 로그 정규 분포 파라미터 계산
    mu = np.log(current_price) + (rf - div - (vol**2) / 2) * t
    sigma = vol * np.sqrt(t)
    
    # 신뢰구간 계산
    z_score = stats.norm.ppf((1 + confidence) / 2)
    
    lower_bound = np.exp(mu - z_score * sigma)
    upper_bound = np.exp(mu + z_score * sigma)
    
    return lower_bound, upper_bound


def calculate_itm_probability(
    s,
    k,
    days,
    volatility,
    option_type,
    dividend_yield=0,
    risk_free_rate=0,
):
    """
    만기일에 옵션이 내가격(ITM)이 될 확률 계산
    
    Parameters:
    -----------
    s : float
        현재 기초자산 가격
    k : float
        행사가격
    days : int
        만기까지 남은 일수
    volatility : float
        연간 변동성 (%)
    option_type : str
        'c' (콜) 또는 'p' (풋)
    dividend_yield : float, optional
        배당수익률 (%)
        
    Returns:
    --------
    float
        ITM 확률
    """
    prob_above, prob_below = calculate_price_probability(
        s, k, days, volatility, dividend_yield, risk_free_rate
    )
    
    if option_type.lower() == 'c':
        return prob_above  # 콜옵션이 ITM일 확률 = 기초자산이 행사가격보다 높을 확률
    else:
        return prob_below  # 풋옵션이 ITM일 확률 = 기초자산이 행사가격보다 낮을 확률


def calculate_win_rate(
    df,
    s,
    bep1,
    bep2=None,
    price_points=100,
    days=30,
    volatility=30,
    dividend_yield=0,
    risk_free_rate=0,
):
    """
    전략의 승률(Win Rate) 계산 - 이익 구간의 확률 합계 / 전체 확률 합계
    
    Parameters:
    -----------
    df : DataFrame
        페이오프 데이터프레임
    s : float
        현재 기초자산 가격
    bep1 : float or None
        첫 번째 손익분기점
    bep2 : float or None, optional
        두 번째 손익분기점
    price_points : int, optional
        가격 포인트 수 (계산 정확도)
        
    Returns:
    --------
    float
        승률 (0.0 ~ 100.0 사이)
    """
    if df is None or df.empty:
        return 0.0
    
    # 이익/손실 구간 결정
    x_vals = df['x'].values
    y_vals = df['y'].values
    
    # 이익 구간과 손실 구간 분리
    profit_indices = np.where(y_vals >= 0)[0]
    loss_indices = np.where(y_vals < 0)[0]
    
    if len(profit_indices) == 0:  # 이익 구간이 없는 경우
        return 0.0
    
    if len(loss_indices) == 0:  # 손실 구간이 없는 경우
        return 100.0
    
    # 구간 확률 계산
    total_prob = 0.0
    profit_prob = 0.0
    
    # 구간 확인 및 확률 계산
    segments = []
    current_type = y_vals[0] >= 0  # True는 이익, False는 손실
    start_idx = 0
    
    # 구간 나누기
    for i in range(1, len(x_vals)):
        is_profit = y_vals[i] >= 0
        if is_profit != current_type:
            segments.append((start_idx, i-1, current_type))
            start_idx = i
            current_type = is_profit
    
    # 마지막 구간 추가
    segments.append((start_idx, len(x_vals)-1, current_type))
    
    # 각 구간별 확률 계산
    for start_idx, end_idx, is_profit in segments:
        start_price = x_vals[start_idx]
        end_price = x_vals[end_idx]
        
        # 시작 가격과 종료 가격 확률 계산
        prob_above_start, _ = calculate_price_probability(
            s, start_price, days, volatility, dividend_yield, risk_free_rate
        )
        prob_above_end, _ = calculate_price_probability(
            s, end_price, days, volatility, dividend_yield, risk_free_rate
        )
        
        # 구간 확률 계산
        segment_prob = abs(prob_above_start - prob_above_end)
        
        if is_profit:
            profit_prob += segment_prob
        
        total_prob += segment_prob
    
    # 확률 합이 0인 경우 처리
    if total_prob <= 0:
        return 0.0
    
    # 승률 계산: 이익 구간 확률 합 / 전체 확률 합
    win_rate = (profit_prob / total_prob) * 100.0
    
    return win_rate


def calculate_probability_curve(
    s, price_range, days, volatility, dividend_yield=0, risk_free_rate=0
):
    """
    가격 범위에 대한 확률 곡선 생성
    
    Parameters:
    -----------
    s : float
        현재 기초자산 가격
    price_range : array-like
        가격 범위
    days : int
        만기까지 남은 일수
    volatility : float
        연간 변동성 (%)
    dividend_yield : float, optional
        배당수익률 (%)
        
    Returns:
    --------
    array
        각 가격 포인트에 대한 확률 밀도
    """
    if days <= 0 or volatility <= 0:
        return np.zeros_like(price_range)
    
    # 파라미터 변환
    vol = volatility / 100.0
    div = dividend_yield / 100.0
    rf = risk_free_rate / 100.0
    t = days / 252.0  # 거래일 기준으로 변환
    
    # 로그 정규 분포 파라미터 계산
    mu = np.log(s) + (rf - div - (vol**2) / 2) * t
    sigma = vol * np.sqrt(t)
    
    # 로그 정규 확률 밀도 함수
    def lognormal_pdf(x):
        return (1 / (x * sigma * np.sqrt(2 * np.pi))) * np.exp(-((np.log(x) - mu) ** 2) / (2 * sigma ** 2))
    
    # 각 가격에 대한 확률 밀도 계산
    pdf_values = np.array([lognormal_pdf(x) for x in price_range])
    
    # 스케일링 (시각적 표현용)
    max_val = np.max(price_range) - np.min(price_range)
    scale_factor = max_val / 20  # 임의 스케일링
    
    return pdf_values * scale_factor
