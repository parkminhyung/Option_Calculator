import numpy as np
import scipy.stats as stats


def option_greeks(s, k, rf, sigma, tau, y):
    """
    옵션 그릭스 계산
    
    Parameters:
    -----------
    s : float
        기초자산 가격
    k : float
        행사가격
    rf : float
        무위험 이자율 (%)
    sigma : float
        변동성 (%)
    tau : int
        만기까지 남은 일수
    y : float
        배당수익률 (%)
        
    Returns:
    --------
    dict
        각종 그릭스 값
    """
    T = 252
    pct = 100

    tau = tau / T
    sigma = sigma / pct
    rf = rf / pct
    y = y / pct

    d1 = (np.log(s / k) + (rf - y + sigma**2 / 2) * tau) / (sigma * np.sqrt(tau))
    d2 = d1 - (sigma * np.sqrt(tau))

    nd1 = (1 / (np.sqrt(2 * np.pi))) * np.exp(-(d1**2 / 2))

    dividend_discount = np.exp(-y * tau)

    call_delta = dividend_discount * stats.norm.cdf(d1)
    put_delta = dividend_discount * (stats.norm.cdf(d1) - 1)

    gamma = dividend_discount * nd1 / (s * sigma * np.sqrt(tau))

    call_theta = (
        -((s * sigma * np.exp(-y * tau)) / (2 * np.sqrt(tau))) * nd1
        - rf * k * np.exp(-rf * tau) * stats.norm.cdf(d2)
        + y * s * np.exp(-y * tau) * stats.norm.cdf(d1)
    ) / T
    put_theta = (
        -((s * sigma * np.exp(-y * tau)) / (2 * np.sqrt(tau))) * nd1
        + rf * k * np.exp(-rf * tau) * stats.norm.cdf(-d2)
        - y * s * np.exp(-y * tau) * stats.norm.cdf(-d1)
    ) / T

    call_rho = (k * tau * np.exp(-rf * tau) * stats.norm.cdf(d2)) / pct
    put_rho = (k * tau * np.exp(-rf * tau) * (stats.norm.cdf(d2) - 1)) / pct

    vega = (s * dividend_discount * np.sqrt(tau) * nd1) / pct
    
    # Vanna calculation - second-order cross Greek (dDelta/dVol or dVega/dSpot)
    vanna = -(np.exp(-y * tau) * d1 / sigma * nd1) / pct
    
    # Charm calculation (delta decay) - rate of change of delta with respect to time
    call_charm = -(
        np.exp(-y * tau) * (
            nd1 * (2 * (rf - y) * tau - d2 * sigma * np.sqrt(tau)) / 
            (2 * tau * sigma * np.sqrt(tau))
        )
    ) / T
    
    put_charm = -(
        np.exp(-y * tau) * (
            nd1 * (2 * (rf - y) * tau - d2 * sigma * np.sqrt(tau)) / 
            (2 * tau * sigma * np.sqrt(tau))
        ) - 
        y * np.exp(-y * tau) * stats.norm.cdf(-d1)
    ) / T

    return {
        "call_delta": call_delta,
        "put_delta": put_delta,
        "gamma": gamma,
        "vega": vega,
        "call_theta": call_theta,
        "put_theta": put_theta,
        "call_rho": call_rho,
        "put_rho": put_rho,
        "vanna": vanna,
        "call_charm": call_charm,
        "put_charm": put_charm,
    }
