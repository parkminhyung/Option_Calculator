import numpy as np
import scipy.stats as stats


def bs_model(s, k, rf, tau, sigma, y, option_type="c"):
    """
    블랙숄즈 옵션 가격 모델
    
    Parameters:
    -----------
    s : float
        기초자산 가격
    k : float
        행사가격
    rf : float
        무위험 이자율 (%)
    tau : int
        만기까지 남은 일수
    sigma : float
        변동성 (%)
    y : float
        배당수익률 (%)
    option_type : str
        옵션 타입 ('c' for call, 'p' for put)
        
    Returns:
    --------
    float or dict
        옵션 가격(들)
    """
    T = 252
    pct = 100
    tau = tau / T
    sigma = sigma / pct  # 변동성을 소수점으로 변환 (예: 30% -> 0.3)
    rf = rf / pct
    y = y / pct

    d1 = (np.log(s / k) + (rf - y + 0.5 * sigma**2) * tau) / (sigma * np.sqrt(tau))
    d2 = d1 - sigma * np.sqrt(tau)

    call_price = s * np.exp(-y * tau) * stats.norm.cdf(d1) - k * np.exp(
        -rf * tau
    ) * stats.norm.cdf(d2)
    put_price = k * np.exp(-rf * tau) * stats.norm.cdf(-d2) - s * np.exp(
        -y * tau
    ) * stats.norm.cdf(-d1)

    if option_type == "c":
        return call_price
    elif option_type == "p":
        return put_price
    else:
        return {"call_price": call_price, "put_price": put_price}


def calculate_implied_volatility(
    market_price, s, k, rf, tau, y, option_type="c", max_iter=100, tolerance=1e-5
):
    """
    Newton-Raphson 방법을 사용하여 implied volatility 계산
    
    Parameters:
    -----------
    market_price : float
        시장에서 관측된 옵션 가격
    s, k, rf, tau, y, option_type : 
        bs_model과 동일
    max_iter : int
        최대 반복 횟수
    tolerance : float
        허용 오차
    
    Returns:
    --------
    float
        추정된 내재 변동성 (%)
    """
    # 초기 추정값 (30%)
    sigma = 0.3  # 이미 소수점 형태로 시작

    # 시장 가격이 0이거나 음수인 경우 처리
    if market_price <= 0:
        return 30.0  # 기본값 반환

    for i in range(max_iter):
        # 현재 sigma로 옵션 가격 계산 (sigma는 이미 소수점 형태)
        price = bs_model(s, k, rf, tau, sigma * 100, y, option_type)

        # 가격 차이 계산
        diff = price - market_price

        # 차이가 허용 오차보다 작으면 종료
        if abs(diff) < tolerance:
            return sigma * 100  # 퍼센트로 변환하여 반환

        # vega 계산 (가격의 sigma에 대한 도함수)
        T = 252
        pct = 100
        tau_scaled = tau / T
        sigma_scaled = sigma  # 이미 소수점 형태
        rf_scaled = rf / pct
        y_scaled = y / pct

        # Black-Scholes 모델의 vega 계산
        d1 = (
            np.log(s / k) + (rf_scaled - y_scaled + 0.5 * sigma_scaled**2) * tau_scaled
        ) / (sigma_scaled * np.sqrt(tau_scaled))
        vega = (
            s
            * np.exp(-y_scaled * tau_scaled)
            * np.sqrt(tau_scaled)
            * (1 / np.sqrt(2 * np.pi))
            * np.exp(-(d1**2) / 2)
        )

        # vega가 0에 가까운 경우 처리
        if abs(vega) < 1e-10:
            sigma = sigma * 1.5  # sigma를 증가시켜 다시 시도
            continue

        # Newton-Raphson 업데이트
        sigma = sigma - diff / vega

        # 음수 방지
        sigma = max(sigma, 0.0001)

        # sigma가 너무 큰 경우 처리
        if sigma > 5.0:  # 500% 이상의 변동성은 비현실적
            return 30.0  # 기본값 반환

    # 최대 반복 횟수에 도달하면 현재 sigma 반환
    return sigma * 100  # 퍼센트로 변환하여 반환
