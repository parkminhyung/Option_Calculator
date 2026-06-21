from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.special import roots_laguerre


TRADING_DAYS = 252


@dataclass
class HestonParams:
    kappa: float
    theta: float
    sigma_v: float
    rho: float
    v0: float


_LAGUERRE_NODES, _LAGUERRE_WEIGHTS = roots_laguerre(48)


def _year_fraction(days):
    return max(float(days) / TRADING_DAYS, 1e-6)


def _heston_cf(u, s, t, rf, y, params):
    i = 1j
    kappa = params.kappa
    theta = params.theta
    sigma_v = max(params.sigma_v, 1e-8)
    rho = np.clip(params.rho, -0.999, 0.999)
    v0 = max(params.v0, 1e-10)

    r = rf / 100.0
    q = y / 100.0
    x = np.log(s)

    d = np.sqrt((rho * sigma_v * i * u - kappa) ** 2 + sigma_v**2 * (i * u + u**2))
    g = (kappa - rho * sigma_v * i * u - d) / (
        kappa - rho * sigma_v * i * u + d
    )

    exp_dt = np.exp(-d * t)
    log_term = np.log((1 - g * exp_dt) / (1 - g))

    c = i * u * ((r - q) * t + x) + (kappa * theta / sigma_v**2) * (
        (kappa - rho * sigma_v * i * u - d) * t - 2 * log_term
    )
    d_term = ((kappa - rho * sigma_v * i * u - d) / sigma_v**2) * (
        (1 - exp_dt) / (1 - g * exp_dt)
    )
    return np.exp(c + d_term * v0)


def heston_price(s, k, rf, tau, y, params, option_type="c"):
    """
    Heston stochastic volatility European option price.

    Parameters use the app's convention: rates in %, tau in trading days.
    Variance parameters are decimal variance units, e.g. theta=0.04 means 20% vol.
    """
    if not isinstance(params, HestonParams):
        params = HestonParams(**params)

    s = float(s)
    k = float(k)
    t = _year_fraction(tau)
    r = rf / 100.0
    q = y / 100.0

    if s <= 0 or k <= 0:
        return 0.0

    u = _LAGUERRE_NODES
    weights = _LAGUERRE_WEIGHTS
    iu = 1j * u

    phi_minus_i = _heston_cf(-1j, s, t, rf, y, params)
    phi_u = _heston_cf(u, s, t, rf, y, params)
    phi_shifted = _heston_cf(u - 1j, s, t, rf, y, params)

    exp_term = np.exp(-iu * np.log(k))
    p1_integrand = np.real(exp_term * phi_shifted / (iu * phi_minus_i))
    p2_integrand = np.real(exp_term * phi_u / iu)

    # Gauss-Laguerre integrates int_0^inf e^-x g(x) dx. Our integrand has no e^-x.
    p1 = 0.5 + np.sum(weights * np.exp(u) * p1_integrand) / np.pi
    p2 = 0.5 + np.sum(weights * np.exp(u) * p2_integrand) / np.pi

    call_price = s * np.exp(-q * t) * p1 - k * np.exp(-r * t) * p2
    put_price = call_price - s * np.exp(-q * t) + k * np.exp(-r * t)
    price = call_price if option_type.lower().startswith("c") else put_price

    if not np.isfinite(price):
        return np.nan
    return float(max(price, 0.0))


def heston_price_surface(params, s, rf, y, strikes, days, option_type="c"):
    z = []
    for day in days:
        row = [
            heston_price(s, strike, rf, day, y, params, option_type)
            for strike in strikes
        ]
        z.append(row)
    return np.array(z)


def _quote_price(row):
    bid = row.get("bid", np.nan)
    ask = row.get("ask", np.nan)
    last = row.get("lastPrice", np.nan)

    if pd.notna(bid) and pd.notna(ask) and bid > 0 and ask >= bid:
        return float((bid + ask) / 2)
    if pd.notna(last) and last > 0:
        return float(last)
    return np.nan


def select_calibration_quotes(chains, s, max_options_per_expiry=14):
    """
    Build a compact calibration set from yfinance option chains.

    chains: iterable of (expiry, days_to_expiry, calls_df, puts_df)
    """
    rows = []

    for expiry, days, calls, puts in chains:
        if days <= 3:
            continue

        for option_type, options in (("c", calls), ("p", puts)):
            if options is None or options.empty or "strike" not in options:
                continue

            frame = options.copy()
            frame["market_price"] = frame.apply(_quote_price, axis=1)
            frame["moneyness_distance"] = np.abs(np.log(frame["strike"] / s))
            if "volume" not in frame:
                frame["volume"] = 0
            if "openInterest" not in frame:
                frame["openInterest"] = 0

            frame = frame[
                (frame["market_price"] > 0.05)
                & (frame["strike"] > s * 0.55)
                & (frame["strike"] < s * 1.55)
            ]
            if frame.empty:
                continue

            frame["liquidity"] = frame["volume"].fillna(0) + frame[
                "openInterest"
            ].fillna(0)
            frame = frame.sort_values(
                ["moneyness_distance", "liquidity"], ascending=[True, False]
            ).head(max_options_per_expiry)

            for _, row in frame.iterrows():
                rows.append(
                    {
                        "expiry": expiry,
                        "days": int(days),
                        "strike": float(row["strike"]),
                        "option_type": option_type,
                        "market_price": float(row["market_price"]),
                        "weight": 1.0 / max(float(row["market_price"]), 1.0),
                    }
                )

    return pd.DataFrame(rows)


def calibrate_heston_model(
    quotes, s, rf, y, initial_vol=30.0, max_nfev=80, initial_params=None
):
    if quotes is None or quotes.empty or len(quotes) < 6:
        raise ValueError("Need at least 6 liquid option quotes for Heston calibration.")

    lower = np.array([0.05, 0.0001, 0.02, -0.95, 0.0001])
    upper = np.array([8.0, 2.0, 5.0, 0.95, 2.0])
    initial_var = max((float(initial_vol) / 100.0) ** 2, 0.0001)
    if initial_params is None:
        x0 = np.array([1.2, initial_var, 0.6, -0.35, initial_var])
    else:
        x0 = np.array(
            [
                initial_params.get("kappa", 1.2),
                initial_params.get("theta", initial_var),
                initial_params.get("sigma_v", 0.6),
                initial_params.get("rho", -0.35),
                initial_params.get("v0", initial_var),
            ],
            dtype=float,
        )
        x0 = np.clip(x0, lower + 1e-8, upper - 1e-8)

    strikes = quotes["strike"].to_numpy(float)
    days = quotes["days"].to_numpy(float)
    market_prices = quotes["market_price"].to_numpy(float)
    option_types = quotes["option_type"].to_numpy(str)
    weights = quotes["weight"].to_numpy(float)

    def residuals(x):
        params = HestonParams(*x)
        errors = []
        for strike, day, market_price, option_type, weight in zip(
            strikes, days, market_prices, option_types, weights
        ):
            model_price = heston_price(s, strike, rf, day, y, params, option_type)
            if not np.isfinite(model_price):
                errors.append(10.0)
            else:
                errors.append((model_price - market_price) * weight)
        return np.array(errors)

    result = least_squares(
        residuals,
        x0,
        bounds=(lower, upper),
        max_nfev=int(max_nfev),
        xtol=1e-4,
        ftol=1e-4,
        gtol=1e-4,
    )
    params = HestonParams(*result.x)

    fitted_prices = np.array(
        [
            heston_price(s, strike, rf, day, y, params, option_type)
            for strike, day, option_type in zip(strikes, days, option_types)
        ]
    )
    price_errors = fitted_prices - market_prices
    rmse = float(np.sqrt(np.mean(price_errors**2)))
    mean_abs_pct_error = float(
        np.mean(np.abs(price_errors) / np.maximum(market_prices, 1.0)) * 100
    )

    fitted = quotes.copy()
    fitted["heston_price"] = fitted_prices
    fitted["pricing_error"] = price_errors

    return {
        "params": asdict(params),
        "rmse": rmse,
        "mean_abs_pct_error": mean_abs_pct_error,
        "quotes_used": int(len(quotes)),
        "success": bool(result.success),
        "message": result.message,
        "fitted_quotes": fitted,
    }
