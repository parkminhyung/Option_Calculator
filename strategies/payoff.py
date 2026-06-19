import numpy as np
import pandas as pd
from models.greeks import option_greeks


def calculate_call_payoff(spot_price, strike, premium):
    """콜 옵션 페이오프 계산"""
    return np.where(spot_price <= strike, -premium, (spot_price - strike) - premium)


def calculate_put_payoff(spot_price, strike, premium):
    """풋 옵션 페이오프 계산"""
    return np.where(spot_price <= strike, (strike - spot_price) - premium, -premium)


def calculate_payoff_df(
    strategy,
    side,
    option_type,
    s,
    k1,
    k2=None,
    k3=None,
    k4=None,
    price1=None,
    price2=None,
    price3=None,
    price4=None,
    size=1,
    tau=30,
    rf=3.95,
    sigma=30,
    y=0,
    option_chain=None,
):
    """
    옵션 전략에 따른 손익 및 그릭스 계산
    
    Parameters:
    -----------
    strategy : str
        옵션 전략 이름
    side : str
        'LONG' 또는 'SHORT'
    option_type : str
        'CALL' 또는 'PUT'
    s : float
        기초자산 가격
    k1, k2, k3, k4 : float
        각 포지션의 행사가격
    price1, price2, price3, price4 : float
        각 포지션의 옵션 가격
    size : int
        포지션 크기
    tau : int
        만기까지 남은 일수
    rf : float
        무위험 이자율 (%)
    sigma : float
        변동성 (%)
    y : float
        배당수익률 (%)
    option_chain : DataFrame, optional
        옵션 체인 데이터
        
    Returns:
    --------
    tuple
        (페이오프 데이터프레임, 전략 정보 딕셔너리)
    """
    if strategy in ["Straddle", "Strip", "Strap"] and k2 is None:
        k2 = k1

    k_values = [k for k in [k1, k2, k3, k4] if k is not None]
    if not k_values:
        return None

    k_min, k_max = min(k_values), max(k_values)
    price_range_min = max(0.1, s * 0.7, k_min * 0.7)
    price_range_max = max(s * 1.3, k_max * 1.3)

    x = np.arange(price_range_min, price_range_max, 0.1)
    df = pd.DataFrame({"x": x})

    # 그릭스 벡터 초기화
    call_delta1, call_delta2, call_delta3, call_delta4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))
    put_delta1, put_delta2, put_delta3, put_delta4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))
    gamma1, gamma2, gamma3, gamma4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))
    vega1, vega2, vega3, vega4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))
    call_theta1, call_theta2, call_theta3, call_theta4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))
    put_theta1, put_theta2, put_theta3, put_theta4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))
    call_rho1, call_rho2, call_rho3, call_rho4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))
    put_rho1, put_rho2, put_rho3, put_rho4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))
    # Initialize Vanna and Charm vectors
    vanna1, vanna2, vanna3, vanna4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))
    call_charm1, call_charm2, call_charm3, call_charm4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))
    put_charm1, put_charm2, put_charm3, put_charm4 = np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x)), np.zeros(len(x))

    # 각 행사가격에 대한 그릭스 계산
    if k1 is not None:
        greeks1 = [option_greeks(price, k1, rf, sigma, tau, y) for price in x]
        call_delta1 = np.array([g["call_delta"] for g in greeks1])
        put_delta1 = np.array([g["put_delta"] for g in greeks1])
        gamma1 = np.array([g["gamma"] for g in greeks1])
        vega1 = np.array([g["vega"] for g in greeks1])
        call_theta1 = np.array([g["call_theta"] for g in greeks1])
        put_theta1 = np.array([g["put_theta"] for g in greeks1])
        call_rho1 = np.array([g["call_rho"] for g in greeks1])
        put_rho1 = np.array([g["put_rho"] for g in greeks1])
        vanna1 = np.array([g["vanna"] for g in greeks1])
        call_charm1 = np.array([g["call_charm"] for g in greeks1])
        put_charm1 = np.array([g["put_charm"] for g in greeks1])

    if k2 is not None:
        greeks2 = [option_greeks(price, k2, rf, sigma, tau, y) for price in x]
        call_delta2 = np.array([g["call_delta"] for g in greeks2])
        put_delta2 = np.array([g["put_delta"] for g in greeks2])
        gamma2 = np.array([g["gamma"] for g in greeks2])
        vega2 = np.array([g["vega"] for g in greeks2])
        call_theta2 = np.array([g["call_theta"] for g in greeks2])
        put_theta2 = np.array([g["put_theta"] for g in greeks2])
        call_rho2 = np.array([g["call_rho"] for g in greeks2])
        put_rho2 = np.array([g["put_rho"] for g in greeks2])
        vanna2 = np.array([g["vanna"] for g in greeks2])
        call_charm2 = np.array([g["call_charm"] for g in greeks2])
        put_charm2 = np.array([g["put_charm"] for g in greeks2])

    if k3 is not None:
        greeks3 = [option_greeks(price, k3, rf, sigma, tau, y) for price in x]
        call_delta3 = np.array([g["call_delta"] for g in greeks3])
        put_delta3 = np.array([g["put_delta"] for g in greeks3])
        gamma3 = np.array([g["gamma"] for g in greeks3])
        vega3 = np.array([g["vega"] for g in greeks3])
        call_theta3 = np.array([g["call_theta"] for g in greeks3])
        put_theta3 = np.array([g["put_theta"] for g in greeks3])
        call_rho3 = np.array([g["call_rho"] for g in greeks3])
        put_rho3 = np.array([g["put_rho"] for g in greeks3])
        vanna3 = np.array([g["vanna"] for g in greeks3])
        call_charm3 = np.array([g["call_charm"] for g in greeks3])
        put_charm3 = np.array([g["put_charm"] for g in greeks3])

    if k4 is not None:
        greeks4 = [option_greeks(price, k4, rf, sigma, tau, y) for price in x]
        call_delta4 = np.array([g["call_delta"] for g in greeks4])
        put_delta4 = np.array([g["put_delta"] for g in greeks4])
        gamma4 = np.array([g["gamma"] for g in greeks4])
        vega4 = np.array([g["vega"] for g in greeks4])
        call_theta4 = np.array([g["call_theta"] for g in greeks4])
        put_theta4 = np.array([g["put_theta"] for g in greeks4])
        call_rho4 = np.array([g["call_rho"] for g in greeks4])
        put_rho4 = np.array([g["put_rho"] for g in greeks4])
        vanna4 = np.array([g["vanna"] for g in greeks4])
        call_charm4 = np.array([g["call_charm"] for g in greeks4])
        put_charm4 = np.array([g["put_charm"] for g in greeks4])

    # 각 행사가격에 대한 페이오프 계산
    c1 = calculate_call_payoff(x, k1, price1) if k1 is not None and price1 is not None else 0
    p1 = calculate_put_payoff(x, k1, price1) if k1 is not None and price1 is not None else 0

    c2 = calculate_call_payoff(x, k2, price2) if k2 is not None and price2 is not None else 0
    p2 = calculate_put_payoff(x, k2, price2) if k2 is not None and price2 is not None else 0

    c3 = calculate_call_payoff(x, k3, price3) if k3 is not None and price3 is not None else 0
    p3 = calculate_put_payoff(x, k3, price3) if k3 is not None and price3 is not None else 0

    c4 = calculate_call_payoff(x, k4, price4) if k4 is not None and price4 is not None else 0
    p4 = calculate_put_payoff(x, k4, price4) if k4 is not None and price4 is not None else 0

    # 전략별 손익 및 그릭스 계산
    if strategy == "Single":
        if side == "LONG" and option_type == "CALL":
            y_values = c1
            delta = call_delta1
            gamma = gamma1
            vega = vega1
            theta = call_theta1
            rho = call_rho1
            vanna = vanna1
            charm = call_charm1
            strategy_type = "Bullish"
            risk_level = "Moderate Risk"
        elif side == "SHORT" and option_type == "CALL":
            y_values = -c1
            delta = -call_delta1
            gamma = -gamma1
            vega = -vega1
            theta = -call_theta1
            rho = -call_rho1
            vanna = -vanna1
            charm = -call_charm1
            strategy_type = "Bearish"
            risk_level = "High Risk"
        elif side == "LONG" and option_type == "PUT":
            y_values = p1
            delta = put_delta1
            gamma = gamma1
            vega = vega1
            theta = put_theta1
            rho = put_rho1
            vanna = vanna1
            charm = put_charm1
            strategy_type = "Bearish"
            risk_level = "Moderate Risk"
        elif side == "SHORT" and option_type == "PUT":
            y_values = -p1
            delta = -put_delta1
            gamma = -gamma1
            vega = -vega1
            theta = -put_theta1
            rho = -put_rho1
            vanna = -vanna1
            charm = -put_charm1
            strategy_type = "Bullish"
            risk_level = "High Risk"

    elif strategy == "Straddle":
        if side == "LONG":
            y_values = c1 + p2
            delta = call_delta1 + put_delta2
            gamma = gamma1 + gamma2
            vega = vega1 + vega2
            theta = call_theta1 + put_theta2
            rho = call_rho1 + put_rho2
            vanna = vanna1 + vanna2
            charm = call_charm1 + put_charm2
            strategy_type = "Neutral"
            risk_level = "High Risk"
        elif side == "SHORT":
            y_values = -(c1 + p2)
            delta = -(call_delta1 + put_delta2)
            gamma = -(gamma1 + gamma2)
            vega = -(vega1 + vega2)
            theta = -(call_theta1 + put_theta2)
            rho = -(call_rho1 + put_rho2)
            vanna = -(vanna1 + vanna2)
            charm = -(call_charm1 + put_charm2)
            strategy_type = "Neutral"
            risk_level = "High Risk"

    elif strategy == "Strangle":
        if side == "LONG":
            y_values = p1 + c2
            delta = put_delta1 + call_delta2
            gamma = gamma1 + gamma2
            vega = vega1 + vega2
            theta = put_theta1 + call_theta2
            rho = put_rho1 + call_rho2
            vanna = vanna1 + vanna2
            charm = put_charm1 + call_charm2
            strategy_type = "Neutral"
            risk_level = "High Risk"
        elif side == "SHORT":
            y_values = -(p1 + c2)
            delta = -(put_delta1 + call_delta2)
            gamma = -(gamma1 + gamma2)
            vega = -(vega1 + vega2)
            theta = -(put_theta1 + call_theta2)
            rho = -(put_rho1 + call_rho2)
            vanna = -(vanna1 + vanna2)
            charm = -(put_charm1 + call_charm2)
            strategy_type = "Neutral"
            risk_level = "High Risk"

    elif strategy == "Spread":
        if side == "LONG" and option_type == "CALL":
            y_values = c1 - c2
            delta = call_delta1 - call_delta2
            gamma = gamma1 - gamma2
            vega = vega1 - vega2
            theta = call_theta1 - call_theta2
            rho = call_rho1 - call_rho2
            vanna = vanna1 - vanna2
            charm = call_charm1 - call_charm2
            strategy_type = "Bullish"
            risk_level = "Moderate Risk"
        elif side == "SHORT" and option_type == "CALL":
            y_values = -(c1 - c2)
            delta = -(call_delta1 - call_delta2)
            gamma = -(gamma1 - gamma2)
            vega = -(vega1 - vega2)
            theta = -(call_theta1 - call_theta2)
            rho = -(call_rho1 - call_rho2)
            vanna = -(vanna1 - vanna2)
            charm = -(call_charm1 - call_charm2)
            strategy_type = "Bearish"
            risk_level = "Moderate Risk"
        elif side == "SHORT" and option_type == "PUT":
            y_values = p1 - p2
            delta = put_delta1 - put_delta2
            gamma = gamma1 - gamma2
            vega = vega1 - vega2
            theta = put_theta1 - put_theta2
            rho = put_rho1 - put_rho2
            vanna = vanna1 - vanna2
            charm = put_charm1 - put_charm2
            strategy_type = "Bullish"
            risk_level = "Moderate Risk"
        elif side == "LONG" and option_type == "PUT":
            y_values = -(p1 - p2)
            delta = -(put_delta1 - put_delta2)
            gamma = -(gamma1 - gamma2)
            vega = -(vega1 - vega2)
            theta = -(put_theta1 - put_theta2)
            rho = -(put_rho1 - put_rho2)
            vanna = -(vanna1 - vanna2)
            charm = -(put_charm1 - put_charm2)
            strategy_type = "Bearish"
            risk_level = "Moderate Risk"

    elif strategy == "Covered" and option_type == "PUT":
        y_values = (s - x) - p1
        delta = -1 + put_delta1
        gamma = gamma1
        vega = vega1
        theta = -put_theta1
        rho = -put_rho1
        vanna = vanna1
        charm = put_charm1
        strategy_type = "Bearish"
        risk_level = "Moderate Risk"

    elif strategy == "Covered" and option_type == "CALL":
        y_values = (x - s) - c1
        delta = 1 - call_delta1
        gamma = -gamma1
        vega = -vega1
        theta = -call_theta1
        rho = -call_rho1
        vanna = -vanna1
        charm = -call_charm1
        strategy_type = "Bullish"
        risk_level = "Low Risk"

    elif strategy == "Protective" and option_type == "PUT":
        y_values = (x - s) + p1
        delta = 1 + put_delta1
        gamma = gamma1
        vega = vega1
        theta = put_theta1
        rho = put_rho1
        vanna = vanna1
        charm = put_charm1
        strategy_type = "Bullish"
        risk_level = "Moderate Risk"

    elif strategy == "Protective" and option_type == "CALL":
        y_values = (s - x) + c1
        delta = -1 + call_delta1
        gamma = gamma1
        vega = vega1
        theta = call_theta1
        rho = call_rho1
        vanna = vanna1
        charm = call_charm1
        strategy_type = "Bearish"
        risk_level = "Low Risk"

    elif strategy == "Strip":
        y_values = c2 + 2 * p1
        delta = call_delta2 + 2 * put_delta1
        gamma = gamma2 + 2 * gamma1
        vega = vega2 + 2 * vega1
        theta = call_theta2 + 2 * put_theta1
        rho = call_rho2 + 2 * put_rho1
        vanna = vanna2 + 2 * vanna1
        charm = call_charm2 + 2 * put_charm1
        strategy_type = "Bearish"
        risk_level = "High Risk"

    elif strategy == "Strap":
        y_values = 2 * c2 + p1
        delta = 2 * call_delta2 + put_delta1
        gamma = 2 * gamma2 + gamma1
        vega = 2 * vega2 + vega1
        theta = 2 * call_theta2 + put_theta1
        rho = 2 * call_rho2 + put_rho1
        vanna = 2 * vanna2 + vanna1
        charm = 2 * call_charm2 + put_charm1
        strategy_type = "Bullish"
        risk_level = "High Risk"

    elif strategy == "Butterfly":
        if side == "LONG" and option_type == "CALL":
            y_values = c1 - 2 * c2 + c3
            delta = call_delta1 - 2 * call_delta2 + call_delta3
            gamma = gamma1 - 2 * gamma2 + gamma3
            vega = vega1 - 2 * vega2 + vega3
            theta = call_theta1 - 2 * call_theta2 + call_theta3
            rho = call_rho1 - 2 * call_rho2 + call_rho3
            vanna = vanna1 - 2 * vanna2 + vanna3
            charm = call_charm1 - 2 * call_charm2 + call_charm3
            strategy_type = "Neutral"
            risk_level = "Low Risk"
        elif side == "SHORT" and option_type == "CALL":
            y_values = -(c1 - 2 * c2 + c3)
            delta = -(call_delta1 - 2 * call_delta2 + call_delta3)
            gamma = -(gamma1 - 2 * gamma2 + gamma3)
            vega = -(vega1 - 2 * vega2 + vega3)
            theta = -(call_theta1 - 2 * call_theta2 + call_theta3)
            rho = -(call_rho1 - 2 * call_rho2 + call_rho3)
            vanna = -(vanna1 - 2 * vanna2 + vanna3)
            charm = -(call_charm1 - 2 * call_charm2 + call_charm3)
            strategy_type = "Neutral"
            risk_level = "Low Risk"
        elif side == "LONG" and option_type == "PUT":
            y_values = p1 - 2 * p2 + p3
            delta = put_delta1 - 2 * put_delta2 + put_delta3
            gamma = gamma1 - 2 * gamma2 + gamma3
            vega = vega1 - 2 * vega2 + vega3
            theta = put_theta1 - 2 * put_theta2 + put_theta3
            rho = put_rho1 - 2 * put_rho2 + put_rho3
            vanna = vanna1 - 2 * vanna2 + vanna3
            charm = put_charm1 - 2 * put_charm2 + put_charm3
            strategy_type = "Neutral"
            risk_level = "Low Risk"
        elif side == "SHORT" and option_type == "PUT":
            y_values = -(p1 - 2 * p2 + p3)
            delta = -(put_delta1 - 2 * put_delta2 + put_delta3)
            gamma = -(gamma1 - 2 * gamma2 + gamma3)
            vega = -(vega1 - 2 * vega2 + vega3)
            theta = -(put_theta1 - 2 * put_theta2 + put_theta3)
            rho = -(put_rho1 - 2 * put_rho2 + put_rho3)
            vanna = -(vanna1 - 2 * vanna2 + vanna3)
            charm = -(put_charm1 - 2 * put_charm2 + put_charm3)
            strategy_type = "Neutral"
            risk_level = "Low Risk"

    elif strategy == "Ladder":
        if side == "LONG" and option_type == "CALL":
            y_values = c1 - c2 - c3
            delta = call_delta1 - call_delta2 - call_delta3
            gamma = gamma1 - gamma2 - gamma3
            vega = vega1 - vega2 - vega3
            theta = call_theta1 - call_theta2 - call_theta3
            rho = call_rho1 - call_rho2 - call_rho3
            vanna = vanna1 - vanna2 - vanna3
            charm = call_charm1 - call_charm2 - call_charm3
            strategy_type = "Bullish"
            risk_level = "High Risk"
        elif side == "SHORT" and option_type == "CALL":
            y_values = -(c1 - c2 - c3)
            delta = -(call_delta1 - call_delta2 - call_delta3)
            gamma = -(gamma1 - gamma2 - gamma3)
            vega = -(vega1 - vega2 - vega3)
            theta = -(call_theta1 - call_theta2 - call_theta3)
            rho = -(call_rho1 - call_rho2 - call_rho3)
            vanna = -(vanna1 - vanna2 - vanna3)
            charm = -(call_charm1 - call_charm2 - call_charm3)
            strategy_type = "Bearish"
            risk_level = "High Risk"
        elif side == "SHORT" and option_type == "PUT":
            y_values = p1 + p2 - p3
            delta = put_delta1 + put_delta2 - put_delta3
            gamma = gamma1 + gamma2 - gamma3
            vega = vega1 + vega2 - vega3
            theta = put_theta1 + put_theta2 - put_theta3
            rho = put_rho1 + put_rho2 - put_rho3
            vanna = vanna1 + vanna2 - vanna3
            charm = put_charm1 + put_charm2 - put_charm3
            strategy_type = "Bullish"
            risk_level = "High Risk"
        elif side == "LONG" and option_type == "PUT":
            y_values = -(p1 + p2 - p3)
            delta = -(put_delta1 + put_delta2 - put_delta3)
            gamma = -(gamma1 + gamma2 - gamma3)
            vega = -(vega1 + vega2 - vega3)
            theta = -(put_theta1 + put_theta2 - put_theta3)
            rho = -(put_rho1 + put_rho2 - put_rho3)
            vanna = -(vanna1 + vanna2 - vanna3)
            charm = -(put_charm1 + put_charm2 - put_charm3)
            strategy_type = "Bearish"
            risk_level = "High Risk"

    elif strategy == "Jade Lizard":
        y_values = -p1 - c2 + c3
        delta = -put_delta1 - call_delta2 + call_delta3
        gamma = -gamma1 - gamma2 + gamma3
        vega = -vega1 - vega2 + vega3
        theta = -put_theta1 - call_theta2 + call_theta3
        rho = -put_rho1 - call_rho2 + call_rho3
        vanna = -vanna1 - vanna2 + vanna3
        charm = -put_charm1 - call_charm2 + call_charm3
        strategy_type = "Bullish"
        risk_level = "Moderate Risk"

    elif strategy == "Reverse Jade Lizard":
        y_values = p1 - p2 - c3
        delta = put_delta1 - put_delta2 - call_delta3
        gamma = gamma1 - gamma2 - gamma3
        vega = vega1 - vega2 - vega3
        theta = put_theta1 - put_theta2 - call_theta3
        rho = put_rho1 - put_rho2 - call_rho3
        vanna = vanna1 - vanna2 - vanna3
        charm = put_charm1 - put_charm2 - call_charm3
        strategy_type = "Bearish"
        risk_level = "Moderate Risk"

    elif strategy == "Condor":
        if side == "LONG" and option_type == "CALL":
            y_values = c1 - c2 - c3 + c4
            delta = call_delta1 - call_delta2 - call_delta3 + call_delta4
            gamma = gamma1 - gamma2 - gamma3 + gamma4
            vega = vega1 - vega2 - vega3 + vega4
            theta = call_theta1 - call_theta2 - call_theta3 + call_theta4
            rho = call_rho1 - call_rho2 - call_rho3 + call_rho4
            vanna = vanna1 - vanna2 - vanna3 + vanna4
            charm = call_charm1 - call_charm2 - call_charm3 + call_charm4
            strategy_type = "Neutral"
            risk_level = "Low Risk"
        elif side == "SHORT" and option_type == "CALL":
            y_values = -(c1 - c2 - c3 + c4)
            delta = -(call_delta1 - call_delta2 - call_delta3 + call_delta4)
            gamma = -(gamma1 - gamma2 - gamma3 + gamma4)
            vega = -(vega1 - vega2 - vega3 + vega4)
            theta = -(call_theta1 - call_theta2 - call_theta3 + call_theta4)
            rho = -(call_rho1 - call_rho2 - call_rho3 + call_rho4)
            vanna = -(vanna1 - vanna2 - vanna3 + vanna4)
            charm = -(call_charm1 - call_charm2 - call_charm3 + call_charm4)
            strategy_type = "Neutral"
            risk_level = "Low Risk"
        elif side == "LONG" and option_type == "PUT":
            y_values = p1 - p2 - p3 + p4
            delta = put_delta1 - put_delta2 - put_delta3 + put_delta4
            gamma = gamma1 - gamma2 - gamma3 + gamma4
            vega = vega1 - vega2 - vega3 + vega4
            theta = put_theta1 - put_theta2 - put_theta3 + put_theta4
            rho = put_rho1 - put_rho2 - put_rho3 + put_rho4
            vanna = vanna1 - vanna2 - vanna3 + vanna4
            charm = put_charm1 - put_charm2 - put_charm3 + put_charm4
            strategy_type = "Neutral"
            risk_level = "Low Risk"
        elif side == "SHORT" and option_type == "PUT":
            y_values = -(p1 - p2 - p3 + p4)
            delta = -(put_delta1 - put_delta2 - put_delta3 + put_delta4)
            gamma = -(gamma1 - gamma2 - gamma3 + gamma4)
            vega = -(vega1 - vega2 - vega3 + vega4)
            theta = -(put_theta1 - put_theta2 - put_theta3 + put_theta4)
            rho = -(put_rho1 - put_rho2 - put_rho3 + put_rho4)
            vanna = -(vanna1 - vanna2 - vanna3 + vanna4)
            charm = -(put_charm1 - put_charm2 - put_charm3 + put_charm4)
            strategy_type = "Neutral"
            risk_level = "Low Risk"

    else:
        y_values = np.zeros(len(x))
        delta = np.zeros(len(x))
        gamma = np.zeros(len(x))
        vega = np.zeros(len(x))
        theta = np.zeros(len(x))
        rho = np.zeros(len(x))
        vanna = np.zeros(len(x))
        charm = np.zeros(len(x))
        strategy_type = "Unknown"
        risk_level = "Unknown"

    # 포지션 크기 적용
    y_values = y_values * size
    delta = delta * size
    gamma = gamma * size
    vega = vega * size
    theta = theta * size
    rho = rho * size
    vanna = vanna * size
    charm = charm * size

    # 손익 데이터 저장
    df["y"] = y_values
    df["profit"] = np.where(y_values >= 0, y_values, np.nan)
    df["loss"] = np.where(y_values < 0, y_values, np.nan)
    df["Delta"] = delta
    df["Gamma"] = gamma
    df["Vega"] = vega
    df["Theta"] = theta
    df["Rho"] = rho
    df["Vanna"] = vanna
    df["Charm"] = charm

    # 손익 계산
    calculated_max_profit = np.max(y_values)
    calculated_min_profit = np.min(y_values)

    # 손익분기점 계산
    sign_changes = np.where(np.diff(np.signbit(y_values)))[0]
    bep1 = x[sign_changes[0]] if len(sign_changes) > 0 else None
    bep2 = x[sign_changes[1]] if len(sign_changes) > 1 else None

    premium1 = price1 or 0
    premium2 = price2 or 0
    premium3 = price3 or 0
    def scaled(value):
        return value * size

    # 각 전략별 최대/최소 손익 계산 (무한대 손익 적절하게 처리)
    if strategy == "Single":
        if side == "LONG" and option_type == "CALL":
            max_profit = float("inf")  # 콜 매수: 무제한 이익
            min_profit = scaled(-premium1)  # 최대 손실은 프리미엄
        elif side == "SHORT" and option_type == "CALL":
            max_profit = scaled(premium1)  # 최대 이익은 프리미엄
            min_profit = float("-inf")  # 콜 매도: 무제한 손실
        elif side == "LONG" and option_type == "PUT":
            max_profit = scaled(k1 - premium1)  # 풋 매수 최대 이익은 기초자산 0 도달 시
            min_profit = scaled(-premium1)  # 최대 손실은 프리미엄
        elif side == "SHORT" and option_type == "PUT":
            max_profit = scaled(premium1)  # 최대 이익은 프리미엄
            min_profit = scaled(premium1 - k1)  # 풋 매도 최대 손실은 기초자산 0 도달 시

    elif strategy == "Straddle":
        if side == "LONG":
            max_profit = float("inf")  # 스트래들 매수: 무제한 이익 가능
            min_profit = scaled(-(premium1 + premium2))  # 최대 손실은 양쪽 프리미엄 합계
        elif side == "SHORT":
            max_profit = scaled(premium1 + premium2)  # 최대 이익은 양쪽 프리미엄 합계
            min_profit = float("-inf")  # 스트래들 매도: 무제한 손실 가능

    elif strategy == "Strangle":
        if side == "LONG":
            max_profit = float("inf")  # 스트랭글 매수: 무제한 이익 가능
            min_profit = scaled(-(premium1 + premium2))  # 최대 손실은 양쪽 프리미엄 합계
        elif side == "SHORT":
            max_profit = scaled(premium1 + premium2)  # 최대 이익은 양쪽 프리미엄 합계
            min_profit = float("-inf")  # 스트랭글 매도: 무제한 손실 가능

    elif strategy == "Spread":
        if option_type == "CALL":
            if side == "LONG":  # 불 콜 스프레드
                max_profit = calculated_max_profit  # 최대 이익은 스프레드 차이에서 프리미엄 차감
                min_profit = calculated_min_profit  # 최대 손실은 지불한 순 프리미엄
            else:  # 베어 콜 스프레드
                max_profit = calculated_max_profit  # 최대 이익은 수취한 순 프리미엄
                min_profit = calculated_min_profit  # 최대 손실은 스프레드 차이에서 프리미엄 가산
        else:  # option_type == "PUT"
            if side == "LONG":  # 베어 풋 스프레드
                max_profit = calculated_max_profit  # 최대 이익은 스프레드 차이에서 프리미엄 차감
                min_profit = calculated_min_profit  # 최대 손실은 지불한 순 프리미엄
            else:  # 불 풋 스프레드
                max_profit = calculated_max_profit  # 최대 이익은 수취한 순 프리미엄
                min_profit = calculated_min_profit  # 최대 손실은 스프레드 차이에서 프리미엄 가산

    elif strategy == "Butterfly":
        # 버터플라이는 양쪽이 제한됨
        max_profit = calculated_max_profit
        min_profit = calculated_min_profit

    elif strategy == "Condor":
        # 콘도르도 양쪽이 제한됨
        max_profit = calculated_max_profit
        min_profit = calculated_min_profit

    elif strategy == "Covered" and option_type == "CALL":
        max_profit = scaled(k1 - s + premium1)  # 최대 이익은 행사가격에서 매수가 차감 + 프리미엄
        min_profit = scaled(-s + premium1)  # 기초자산은 0 아래로 내려가지 않음

    elif strategy == "Covered" and option_type == "PUT":
        max_profit = scaled(s - k1 + premium1)  # 숏 주식 + 숏 풋은 하방에서 수익이 제한됨
        min_profit = float("-inf")  # 기초자산 상승에 따른 숏 주식 손실은 무제한

    elif strategy == "Protective" and option_type == "PUT":
        max_profit = float("inf")  # 기초자산 상승에 따른 이익은 이론상 무제한
        min_profit = scaled(k1 - s - premium1)  # 최대 손실은 프리미엄 + 행사가격과 현재가격 차이

    elif strategy == "Protective" and option_type == "CALL":
        max_profit = scaled(s - premium1)  # 기초자산이 0에 도달할 때 최대
        min_profit = scaled(s - k1 - premium1)  # 상승 구간에서는 손익이 이 값으로 제한됨

    elif strategy == "Strip":
        max_profit = float("inf")  # 콜 보유로 상방 이익은 무제한
        min_profit = scaled(-(premium2 + 2 * premium1))  # 최대 손실은 전체 프리미엄

    elif strategy == "Strap":
        max_profit = float("inf")  # 상방 움직임에서 이익은 이론상 무제한 (콜 2개)
        min_profit = scaled(-(2 * premium2 + premium1))  # 최대 손실은 프리미엄 합계

    elif strategy == "Ladder":
        if option_type == "CALL":
            if side == "LONG":
                max_profit = calculated_max_profit  # 최대 이익은 프리미엄 차액
                min_profit = float("-inf")  # 상방 극단 움직임에서 손실은 무제한
            else:  # SHORT
                max_profit = float("inf")  # 상방 극단 움직임에서 이익은 무제한
                min_profit = calculated_min_profit  # 최대 손실은 프리미엄 차액
        else:  # option_type == "PUT"
            if side == "LONG":
                max_profit = calculated_max_profit  # 최대 이익은 제한적
                min_profit = calculated_min_profit  # 풋 래더는 양쪽 손익이 제한됨
            else:  # SHORT
                max_profit = calculated_max_profit  # 풋 래더는 양쪽 손익이 제한됨
                min_profit = calculated_min_profit  # 최대 손실은 제한적

    elif strategy == "Jade Lizard":
        net_credit = premium1 + premium2 - premium3
        upside_result = net_credit - max(k3 - k2, 0)
        downside_result = net_credit - k1
        max_profit = scaled(net_credit)  # 최대 이익은 받은 순 프리미엄
        min_profit = scaled(min(upside_result, downside_result))  # 양쪽 손실 모두 제한됨

    elif strategy == "Reverse Jade Lizard":
        max_profit = calculated_max_profit  # 최대 이익은 제한적
        min_profit = float("-inf")  # 최대 손실은 상방 극단 움직임에서 무제한

    else:
        # 기타 전략은 계산된 값 사용
        max_profit = calculated_max_profit
        min_profit = calculated_min_profit

    # 전략 정보 반환
    strategy_info = {
        "strategy_type": strategy_type,
        "risk_level": risk_level,
        "side": side,
        "option_type": option_type,
        "bep1": bep1,
        "bep2": bep2,
        "max_profit": max_profit,
        "min_profit": min_profit,
    }

    return df, strategy_info
