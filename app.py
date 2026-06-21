import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from models.bs_model import bs_model, calculate_implied_volatility
from models.heston_model import (
    calibrate_heston_model,
    heston_price,
    heston_price_surface,
    select_calibration_quotes,
)
from plotly.subplots import make_subplots
from strategies.payoff import calculate_payoff_df
from strategies.probability import calculate_itm_probability, calculate_win_rate
from utils.data_fetcher import fetch_data, get_option_chain
from utils.date_utils import calculate_days_to_expiry

# 모듈 임포트
from utils.style import apply_page_styles, apply_parameter_styles
from visualizations.strategy_plot import plot_option_strategy


def bounded_index(index, length):
    if length <= 0:
        return 0
    return max(0, min(index, length - 1))


def render_leg_label(sign, instrument, strike_label=None, quantity=None):
    css_class = "positive" if sign == "+" else "negative"
    qty_text = f"{quantity}x " if quantity else ""
    strike_text = (
        f"<span class='leg-strike'>{strike_label}</span>" if strike_label else ""
    )

    st.markdown(
        f"""
        <div class='option-label'>
            <span class='leg-badge {css_class}'>{sign}</span>
            <span class='leg-name'>{qty_text}{instrument}</span>
            {strike_text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_heston_calibration(
    ticker,
    data,
    s,
    rf,
    y,
    expiry_count=4,
    options_per_expiry=8,
    max_iter=80,
    initial_params=None,
    anchor_expiry=None,
):
    chains = []
    expiry_dates = list(data["expiry_dates"])
    start_idx = 0
    if anchor_expiry in expiry_dates:
        start_idx = expiry_dates.index(anchor_expiry)
    selected_expiries = expiry_dates[start_idx : start_idx + int(expiry_count)]
    for exp_date in selected_expiries:
        days_to_exp = calculate_days_to_expiry(exp_date)
        exp_calls, exp_puts = get_option_chain(ticker, exp_date)
        if exp_calls is not None and exp_puts is not None:
            chains.append((exp_date, days_to_exp, exp_calls, exp_puts))

    quotes = select_calibration_quotes(
        chains,
        s,
        max_options_per_expiry=int(options_per_expiry),
    )
    calibration = calibrate_heston_model(
        quotes,
        s,
        rf,
        y,
        initial_vol=float(data.get("vol", 30.0)),
        max_nfev=int(max_iter),
        initial_params=initial_params,
    )
    calibration["ticker"] = ticker
    calibration["underlying_price"] = s
    calibration["risk_free_rate"] = rf
    calibration["dividend_yield"] = y
    calibration["expiry_count"] = int(expiry_count)
    calibration["anchor_expiry"] = anchor_expiry
    calibration["calibration_expiries"] = selected_expiries
    return calibration


def get_heston_initial_params(data, heston_result=None, ticker=None):
    if (
        heston_result
        and heston_result.get("ticker") == ticker
        and heston_result.get("params")
    ):
        return heston_result["params"]

    initial_vol = max(float(data.get("vol", 30.0)) / 100.0, 0.01)
    initial_var = initial_vol**2
    return {
        "kappa": 1.2,
        "theta": initial_var,
        "sigma_v": 0.6,
        "rho": -0.35,
        "v0": initial_var,
    }


def make_heston_initial_params(kappa, long_run_vol_pct, sigma_v, rho, spot_vol_pct):
    return {
        "kappa": float(kappa),
        "theta": (float(long_run_vol_pct) / 100.0) ** 2,
        "sigma_v": float(sigma_v),
        "rho": float(rho),
        "v0": (float(spot_vol_pct) / 100.0) ** 2,
    }


def main():
    # 페이지 설정
    apply_page_styles()

    # Initialize session state variables for plot storage
    if "plot_fig" not in st.session_state:
        st.session_state.plot_fig = None
    if "strategy_info" not in st.session_state:
        st.session_state.strategy_info = None
    if "df" not in st.session_state:
        st.session_state.df = None
    # Initialize plot parameter storage
    if "plot_side" not in st.session_state:
        st.session_state.plot_side = None
    if "plot_option_type" not in st.session_state:
        st.session_state.plot_option_type = None
    if "plot_strategy" not in st.session_state:
        st.session_state.plot_strategy = None
    if "plot_greeks" not in st.session_state:
        st.session_state.plot_greeks = None
    if "heston_calibration" not in st.session_state:
        st.session_state.heston_calibration = None

    # Sidebar header
    st.sidebar.title("Option Calculator")

    # Ticker input - only fetch on Enter or button click
    ticker = st.sidebar.text_input(
        "Enter Ticker Symbol:", "AAPL", key="ticker_input"
    ).upper()
    fetch_button = st.sidebar.button("Fetch Data")

    # Add JavaScript to detect Enter key in the ticker input
    st.markdown(
        """
    <script>
    const input = document.querySelector('input[data-testid="stTextInput"]');
    if (input) {
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const value = this.value;
                const data = {data: value};
                const jsonData = JSON.stringify(data);
                const xhr = new XMLHttpRequest();
                xhr.open('POST', window.location.href, true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.onload = function() {
                    if (xhr.status === 200) {
                        window.location.reload();
                    }
                };
                xhr.send(jsonData);
            }
        });
    }
    </script>
    """,
        unsafe_allow_html=True,
    )

    # Display company information if data is available
    if "data" in st.session_state:
        data = st.session_state.data

        # Company info and metrics in a clean layout
        with st.container():
            # Company name and sector
            st.markdown(
                f"""
                <h1 style='margin: 0; padding: 0; font-size: 3.5rem; font-weight: 300; 
                            color: #1E88E5; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", 
                            Roboto, Helvetica, Arial, sans-serif; margin-bottom: 0.2rem;'>
                    {data["name"]} <span style='font-size: 1.4rem; color: #666;'>({ticker})</span>
                </h1>
                <div style='font-size: 1.0rem; color: #666; margin-bottom: 0.8rem;'>{data["sector"]}</div>
            """,
                unsafe_allow_html=True,
            )

            # Price and metrics in a modern layout
            change_color = "#1cd4c8" if data["chg"] >= 0 else "#d41c78"
            st.markdown(
                f"""
                <div style='margin-bottom: 1.5rem;'>
                    <div style='display: flex; align-items: baseline; margin-bottom: 0.8rem;'>
                        <span style='font-size: 2.5rem; font-weight: 400;'>${data["underlying_price"]:.2f}</span>
                        <span style='font-size: 1.1rem; color: {change_color}; margin-left: 0.8rem;'>
                            {"+" if data["chg"] > 0 else ""}{data["chg"]:.2f}%
                        </span>
                    </div>
                    <div style='display: flex; flex-wrap: wrap; gap: 0.8rem;'>
                        <div style='background: #f8f9fa; border-radius: 8px; padding: 0.6rem 0.8rem; flex: 1; min-width: 120px;'>
                            <div style='font-size: 0.8rem; color: #6c757d; margin-bottom: 0.2rem;'>
                                <i class='fas fa-door-open' style='margin-right: 0.4rem;'></i>Open
                            </div>
                            <div style='font-size: 1.1rem; font-weight: 500;'>${data["open_price"]:.2f}</div>
                        </div>
                        <div style='background: #f8f9fa; border-radius: 8px; padding: 0.6rem 0.8rem; flex: 1; min-width: 120px;'>
                            <div style='font-size: 0.8rem; color: #6c757d; margin-bottom: 0.2rem;'>
                                <i class='fas fa-arrow-up' style='margin-right: 0.4rem; color: #28a745;'></i>High
                            </div>
                            <div style='font-size: 1.1rem; font-weight: 500; color: #28a745;'>${data["high"]:.2f}</div>
                        </div>
                        <div style='background: #f8f9fa; border-radius: 8px; padding: 0.6rem 0.8rem; flex: 1; min-width: 120px;'>
                            <div style='font-size: 0.8rem; color: #6c757d; margin-bottom: 0.2rem;'>
                                <i class='fas fa-arrow-down' style='margin-right: 0.4rem; color: #dc3545;'></i>Low
                            </div>
                            <div style='font-size: 1.1rem; font-weight: 500; color: #dc3545;'>${data["low"]:.2f}</div>
                        </div>
                        <div style='background: #f8f9fa; border-radius: 8px; padding: 0.6rem 0.8rem; flex: 1; min-width: 120px;'>
                            <div style='font-size: 0.8rem; color: #6c757d; margin-bottom: 0.2rem;'>
                                <i class='fas fa-chart-line' style='margin-right: 0.4rem;'></i>52w Vol
                            </div>
                            <div style='font-size: 1.1rem; font-weight: 500;'>{data["vol"]:.2f}%</div>
                        </div>
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

    # Fetch data if button is clicked
    if fetch_button:
        with st.sidebar:
            with st.spinner("Fetching data..."):
                data = fetch_data(ticker)
                if data:
                    st.session_state.data = data
                    st.success(f"Successfully fetched data for {ticker}")
                    st.rerun()
                else:
                    st.error("Failed to fetch data. Please check the ticker symbol.")

    # Add some space before the tabs
    st.markdown("<br>", unsafe_allow_html=True)

    # Main content tabs
    tab1, tab3, tab2 = st.tabs(
        ["Option Calculator & Strategy", "Option Chain", "About"]
    )
    with tab1:
        if "data" in st.session_state:
            data = st.session_state.data

            st.subheader("Option Parameters")

            apply_parameter_styles()

            pricing_model = st.session_state.get("pricing_model_select", "Black-Scholes")
            heston_result = st.session_state.get("heston_calibration")
            heston_available = (
                heston_result is not None
                and heston_result.get("ticker") == ticker
                and heston_result.get("params")
            )

            param_cols = st.columns(4)

            with param_cols[0]:
                s = st.number_input(
                    "Underlying Price (S)",
                    value=float(data["underlying_price"]),
                    step=0.01,
                    format="%.2f",
                )

                expiry = st.selectbox(
                    "Expiry Date",
                    options=data["expiry_dates"] if "expiry_dates" in data else [],
                    key="expiry_date_select",
                )

                if expiry:
                    tau = calculate_days_to_expiry(expiry)
                    st.number_input(
                        "DTE (days)",
                        value=tau,
                        disabled=True,
                        label_visibility="visible",
                    )
                else:
                    tau = st.number_input(
                        "DTE (days)", value=30, min_value=1, label_visibility="visible"
                    )

                rf = st.number_input(
                    "Risk-free Rate (%)",
                    value=float(data["rf"]),
                    step=0.01,
                    format="%.2f",
                )

                y = st.number_input(
                    "Dividend Yield (%)",
                    value=float(data["dividend_yield"]),
                    step=0.01,
                    format="%.2f",
                )

            with param_cols[1]:
                side = st.selectbox(
                    "Side", options=["LONG", "SHORT"], key="side_select"
                )
                option_type = st.selectbox(
                    "Option Type", options=["CALL", "PUT"], key="option_type_select"
                )

                strategy = st.selectbox(
                    "Strategy",
                    options=[
                        "Single",
                        "Covered",
                        "Protective",
                        "Spread",
                        "Straddle",
                        "Strangle",
                        "Strip",
                        "Strap",
                        "Butterfly",
                        "Ladder",
                        "Jade Lizard",
                        "Reverse Jade Lizard",
                        "Condor",
                    ],
                    key="strategy_select",
                )

                greeks = st.selectbox(
                    "Greeks",
                    options=[
                        "Delta",
                        "Gamma",
                        "Vega",
                        "Theta",
                        "Rho",
                        "Vanna",
                        "Charm",
                    ],
                    key="greeks_select",
                )

                default_vol = float(data["vol"])

                # 내재변동성 계산 (만기일 및 행사가격 선택 시 델타 중립 변동성 사용)
                if expiry:
                    try:
                        calls, puts = get_option_chain(ticker, expiry)

                        if calls is not None and puts is not None:
                            all_strikes = sorted(
                                set(calls["strike"].tolist() + puts["strike"].tolist())
                            )

                            selected_strikes = []
                            if "k1_select_single" in st.session_state:
                                selected_strikes.append(
                                    st.session_state.k1_select_single
                                )
                            elif (
                                "k1_select_strangle_spread" in st.session_state
                                and "k2_select_strangle_spread" in st.session_state
                            ):
                                selected_strikes.append(
                                    st.session_state.k1_select_strangle_spread
                                )
                                selected_strikes.append(
                                    st.session_state.k2_select_strangle_spread
                                )
                            elif (
                                "k1_select_butterfly" in st.session_state
                                and "k2_select_butterfly" in st.session_state
                                and "k3_select_butterfly" in st.session_state
                            ):
                                selected_strikes.append(
                                    st.session_state.k1_select_butterfly
                                )
                                selected_strikes.append(
                                    st.session_state.k2_select_butterfly
                                )
                                selected_strikes.append(
                                    st.session_state.k3_select_butterfly
                                )
                            elif (
                                "k1_select_condor" in st.session_state
                                and "k2_select_condor" in st.session_state
                                and "k3_select_condor" in st.session_state
                                and "k4_select_condor" in st.session_state
                            ):
                                selected_strikes.append(
                                    st.session_state.k1_select_condor
                                )
                                selected_strikes.append(
                                    st.session_state.k2_select_condor
                                )
                                selected_strikes.append(
                                    st.session_state.k3_select_condor
                                )
                                selected_strikes.append(
                                    st.session_state.k4_select_condor
                                )

                            if selected_strikes:
                                atm_strike = all_strikes[len(all_strikes) // 2]

                                if option_type == "CALL":
                                    atm_option = calls[calls["strike"] == atm_strike]
                                    calc_type = "c"
                                else:
                                    atm_option = puts[puts["strike"] == atm_strike]
                                    calc_type = "p"

                                if (
                                    not atm_option.empty
                                    and "lastPrice" in atm_option.columns
                                ):
                                    market_price = atm_option["lastPrice"].iloc[0]

                                    if market_price > 0:
                                        # Newton-Raphson 방식으로 ATM 옵션의 내재변동성 계산
                                        implied_vol = calculate_implied_volatility(
                                            market_price=market_price,
                                            s=s,
                                            k=atm_strike,
                                            rf=rf,
                                            tau=tau,
                                            y=y,
                                            option_type=calc_type,
                                        )

                                        # 계산된 내재변동성이 유효하면 기본값으로 설정
                                        if 5.0 <= implied_vol <= 100.0:
                                            default_vol = implied_vol
                    except Exception as e:
                        st.info(
                            f"Using historical volatility. Delta-neutral IV calculation: {e}"
                        )

                # 변동성 입력 필드 - 계산된 내재변동성 또는 52주 변동성 표시
                sigma = st.number_input(
                    "IV (%)",
                    value=default_vol,
                    step=0.1,
                    format="%.2f",
                    label_visibility="visible",
                    help="Delta-neutral implied volatility calculated from at-the-money options. This is used for pricing all options in multi-leg strategies.",
                )

            with param_cols[2]:
                # 전략 유형에 따른 행사가격 입력 필드 생성
                if strategy in ["Strangle", "Spread"]:
                    if expiry:
                        calls, puts = get_option_chain(ticker, expiry)
                        if calls is not None and puts is not None:
                            all_strikes = sorted(
                                set(calls["strike"].tolist() + puts["strike"].tolist())
                            )

                            k1 = st.selectbox(
                                "Strike Price (k1; Lower)",
                                options=all_strikes,
                                index=bounded_index(
                                    len(all_strikes) // 2 - 1, len(all_strikes)
                                ),
                                key="k1_select_strangle_spread",
                            )
                            k2 = st.selectbox(
                                "Strike Price (k2; Higher)",
                                options=all_strikes,
                                index=bounded_index(
                                    len(all_strikes) // 2 + 1, len(all_strikes)
                                ),
                                key="k2_select_strangle_spread",
                            )
                            k3, k4 = None, None
                        else:
                            k1 = st.number_input(
                                "Strike Price (k1; Lower)",
                                value=s * 0.95,
                                step=0.5,
                                format="%.1f",
                                label_visibility="visible",
                            )
                            k2 = st.number_input(
                                "Strike Price (k2; Higher)",
                                value=s * 1.05,
                                step=0.5,
                                format="%.1f",
                                label_visibility="visible",
                            )
                            k3, k4 = None, None
                    else:
                        k1 = st.number_input(
                            "Strike Price (k1; Lower)",
                            value=s * 0.95,
                            step=0.5,
                            format="%.1f",
                            label_visibility="visible",
                        )
                        k2 = st.number_input(
                            "Strike Price (k2; Higher)",
                            value=s * 1.05,
                            step=0.5,
                            format="%.1f",
                            label_visibility="visible",
                        )
                        k3, k4 = None, None
                elif strategy in [
                    "Butterfly",
                    "Ladder",
                    "Jade Lizard",
                    "Reverse Jade Lizard",
                ]:
                    if expiry:
                        calls, puts = get_option_chain(ticker, expiry)
                        if calls is not None and puts is not None:
                            all_strikes = sorted(
                                set(calls["strike"].tolist() + puts["strike"].tolist())
                            )

                            k1 = st.selectbox(
                                "Strike (k1; Lower)",
                                options=all_strikes,
                                index=bounded_index(
                                    len(all_strikes) // 2 - 2, len(all_strikes)
                                ),
                                key="k1_select_butterfly",
                            )
                            k2 = st.selectbox(
                                "Strike (k2; Middle)",
                                options=all_strikes,
                                index=bounded_index(
                                    len(all_strikes) // 2, len(all_strikes)
                                ),
                                key="k2_select_butterfly",
                            )
                            k3 = st.selectbox(
                                "Strike (k3; Higher)",
                                options=all_strikes,
                                index=bounded_index(
                                    len(all_strikes) // 2 + 2, len(all_strikes)
                                ),
                                key="k3_select_butterfly",
                            )
                            k4 = None
                        else:
                            k1 = st.number_input(
                                "Strike (k1; Lower)",
                                value=s * 0.9,
                                step=0.5,
                                format="%.1f",
                                label_visibility="visible",
                            )
                            k2 = st.number_input(
                                "Strike (k2; Middle)",
                                value=s,
                                step=0.5,
                                format="%.1f",
                                label_visibility="visible",
                            )
                            k3 = st.number_input(
                                "Strike (k3; Higher)",
                                value=s * 1.1,
                                step=0.5,
                                format="%.1f",
                                label_visibility="visible",
                            )
                            k4 = None
                    else:
                        k1 = st.number_input(
                            "Strike (k1; Lower)",
                            value=s * 0.9,
                            step=0.5,
                            format="%.1f",
                            label_visibility="visible",
                        )
                        k2 = st.number_input(
                            "Strike (k2; Middle)",
                            value=s,
                            step=0.5,
                            format="%.1f",
                            label_visibility="visible",
                        )
                        k3 = st.number_input(
                            "Strike (k3; Higher)",
                            value=s * 1.1,
                            step=0.5,
                            format="%.1f",
                            label_visibility="visible",
                        )
                        k4 = None
                elif strategy == "Condor":
                    if expiry:
                        calls, puts = get_option_chain(ticker, expiry)
                        if calls is not None and puts is not None:
                            all_strikes = sorted(
                                set(calls["strike"].tolist() + puts["strike"].tolist())
                            )

                            k1 = st.selectbox(
                                "Strike (k1; Lowest)",
                                options=all_strikes,
                                index=bounded_index(
                                    len(all_strikes) // 2 - 3, len(all_strikes)
                                ),
                                key="k1_select_condor",
                            )
                            k2 = st.selectbox(
                                "Strike (k2; Lower-Mid)",
                                options=all_strikes,
                                index=bounded_index(
                                    len(all_strikes) // 2 - 1, len(all_strikes)
                                ),
                                key="k2_select_condor",
                            )
                            k3 = st.selectbox(
                                "Strike (k3; Upper-Mid)",
                                options=all_strikes,
                                index=bounded_index(
                                    len(all_strikes) // 2 + 1, len(all_strikes)
                                ),
                                key="k3_select_condor",
                            )
                            k4 = st.selectbox(
                                "Strike (k4; Highest)",
                                options=all_strikes,
                                index=bounded_index(
                                    len(all_strikes) // 2 + 3, len(all_strikes)
                                ),
                                key="k4_select_condor",
                            )
                        else:
                            k1 = st.number_input(
                                "Strike (k1; Lowest)",
                                value=s * 0.85,
                                step=0.5,
                                format="%.1f",
                                label_visibility="visible",
                            )
                            k2 = st.number_input(
                                "Strike (k2; Lower-Mid)",
                                value=s * 0.95,
                                step=0.5,
                                format="%.1f",
                                label_visibility="visible",
                            )
                            k3 = st.number_input(
                                "Strike (k3; Upper-Mid)",
                                value=s * 1.05,
                                step=0.5,
                                format="%.1f",
                                label_visibility="visible",
                            )
                            k4 = st.number_input(
                                "Strike (k4; Highest)",
                                value=s * 1.15,
                                step=0.5,
                                format="%.1f",
                                label_visibility="visible",
                            )
                    else:
                        k1 = st.number_input(
                            "Strike (k1; Lowest)",
                            value=s * 0.85,
                            step=0.5,
                            format="%.1f",
                            label_visibility="visible",
                        )
                        k2 = st.number_input(
                            "Strike (k2; Lower-Mid)",
                            value=s * 0.95,
                            step=0.5,
                            format="%.1f",
                            label_visibility="visible",
                        )
                        k3 = st.number_input(
                            "Strike (k3; Upper-Mid)",
                            value=s * 1.05,
                            step=0.5,
                            format="%.1f",
                            label_visibility="visible",
                        )
                        k4 = st.number_input(
                            "Strike (k4; Highest)",
                            value=s * 1.15,
                            step=0.5,
                            format="%.1f",
                            label_visibility="visible",
                        )
                else:
                    if expiry:
                        calls, puts = get_option_chain(ticker, expiry)
                        if calls is not None and puts is not None:
                            all_strikes = sorted(
                                set(calls["strike"].tolist() + puts["strike"].tolist())
                            )
                            k1 = st.selectbox(
                                "Strike Price (k)",
                                options=all_strikes,
                                index=len(all_strikes) // 2,
                                key="k1_select_single",
                            )
                            k2, k3, k4 = k1, None, None
                        else:
                            k1 = st.number_input(
                                "Strike Price (k)",
                                value=s,
                                step=0.5,
                                format="%.1f",
                                label_visibility="visible",
                            )
                            k2, k3, k4 = k1, None, None
                    else:
                        k1 = st.number_input(
                            "Strike Price (k)",
                            value=s,
                            step=0.5,
                            format="%.1f",
                            label_visibility="visible",
                        )
                        k2, k3, k4 = k1, None, None

                size = st.number_input(
                    "Size (@100)", value=1, min_value=1, label_visibility="visible"
                )

            with param_cols[3]:
                heston_available = heston_available and heston_result.get(
                    "anchor_expiry", expiry
                ) == expiry
                st.markdown(
                    "<div class='param-label'>Option Prices</div>",
                    unsafe_allow_html=True,
                    help="Option prices are theoretical values calculated with the selected pricing model.",
                )

                def theoretical_option_price(strike, calc_type):
                    if pricing_model == "Heston (calibrated)" and heston_available:
                        price = heston_price(
                            s,
                            strike,
                            rf,
                            tau,
                            y,
                            heston_result["params"],
                            calc_type,
                        )
                        if np.isfinite(price):
                            return price
                    return bs_model(s, strike, rf, tau, sigma, y, calc_type)

                def price_input(
                    sign, instrument, strike_label, value, key, quantity=None
                ):
                    pricing_key = (
                        "heston"
                        if pricing_model == "Heston (calibrated)" and heston_available
                        else "bs"
                    )
                    dynamic_key = f"{key}_{pricing_key}_{float(value):.4f}"
                    render_leg_label(sign, instrument, strike_label, quantity)
                    return st.number_input(
                        "",
                        value=value,
                        step=0.01,
                        format="%.2f",
                        key=dynamic_key,
                        label_visibility="collapsed",
                    )

                price1, price2, price3, price4 = None, None, None, None

                # 전략별 옵션 가격 입력 필드 생성
                if strategy == "Single":
                    sign = "+" if side == "LONG" else "-"
                    if option_type == "CALL":
                        price1 = price_input(
                            sign,
                            "Call",
                            "k",
                            theoretical_option_price(k1, "c"),
                            "single_call_price",
                        )
                    else:
                        price1 = price_input(
                            sign,
                            "Put",
                            "k",
                            theoretical_option_price(k1, "p"),
                            "single_put_price",
                        )

                elif strategy == "Spread":
                    if option_type == "CALL":
                        sign1 = "+" if side == "LONG" else "-"
                        sign2 = "-" if side == "LONG" else "+"
                        price1 = price_input(
                            sign1,
                            "Call",
                            "k1",
                            theoretical_option_price(k1, "c"),
                            "spread_call_price1",
                        )
                        price2 = price_input(
                            sign2,
                            "Call",
                            "k2",
                            theoretical_option_price(k2, "c"),
                            "spread_call_price2",
                        )
                    else:
                        sign1 = "-" if side == "LONG" else "+"
                        sign2 = "+" if side == "LONG" else "-"
                        price1 = price_input(
                            sign1,
                            "Put",
                            "k1",
                            theoretical_option_price(k1, "p"),
                            "spread_put_price1",
                        )
                        price2 = price_input(
                            sign2,
                            "Put",
                            "k2",
                            theoretical_option_price(k2, "p"),
                            "spread_put_price2",
                        )

                elif strategy == "Straddle":
                    sign = "+" if side == "LONG" else "-"
                    price1 = price_input(
                        sign,
                        "Call",
                        "k",
                        theoretical_option_price(k1, "c"),
                        "straddle_call_price",
                    )
                    price2 = price_input(
                        sign,
                        "Put",
                        "k",
                        theoretical_option_price(k1, "p"),
                        "straddle_put_price",
                    )

                elif strategy == "Strangle":
                    sign = "+" if side == "LONG" else "-"
                    price1 = price_input(
                        sign,
                        "Put",
                        "k1",
                        theoretical_option_price(k1, "p"),
                        "strangle_put_price",
                    )
                    price2 = price_input(
                        sign,
                        "Call",
                        "k2",
                        theoretical_option_price(k2, "c"),
                        "strangle_call_price",
                    )

                elif strategy == "Strip":
                    price1 = price_input(
                        "+",
                        "Put",
                        "k",
                        theoretical_option_price(k1, "p"),
                        "strip_put_price",
                        quantity=2,
                    )
                    price2 = price_input(
                        "+",
                        "Call",
                        "k",
                        theoretical_option_price(k1, "c"),
                        "strip_call_price",
                    )

                elif strategy == "Strap":
                    price1 = price_input(
                        "+",
                        "Put",
                        "k",
                        theoretical_option_price(k1, "p"),
                        "strap_put_price",
                    )
                    price2 = price_input(
                        "+",
                        "Call",
                        "k",
                        theoretical_option_price(k1, "c"),
                        "strap_call_price",
                        quantity=2,
                    )

                elif strategy == "Butterfly":
                    sign1 = "+" if side == "LONG" else "-"
                    sign2 = "-" if side == "LONG" else "+"
                    sign3 = "+" if side == "LONG" else "-"
                    calc_type = "c" if option_type == "CALL" else "p"
                    instrument = "Call" if option_type == "CALL" else "Put"
                    key_prefix = (
                        "butterfly_call" if option_type == "CALL" else "butterfly_put"
                    )
                    price1 = price_input(
                        sign1,
                        instrument,
                        "k1",
                        theoretical_option_price(k1, calc_type),
                        f"{key_prefix}_price1",
                    )
                    price2 = price_input(
                        sign2,
                        instrument,
                        "k2",
                        theoretical_option_price(k2, calc_type),
                        f"{key_prefix}_price2",
                        quantity=2,
                    )
                    price3 = price_input(
                        sign3,
                        instrument,
                        "k3",
                        theoretical_option_price(k3, calc_type),
                        f"{key_prefix}_price3",
                    )

                elif strategy == "Condor":
                    sign1 = "+" if side == "LONG" else "-"
                    sign2 = "-" if side == "LONG" else "+"
                    sign3 = "-" if side == "LONG" else "+"
                    sign4 = "+" if side == "LONG" else "-"
                    calc_type = "c" if option_type == "CALL" else "p"
                    instrument = "Call" if option_type == "CALL" else "Put"
                    key_prefix = (
                        "condor_call" if option_type == "CALL" else "condor_put"
                    )
                    price1 = price_input(
                        sign1,
                        instrument,
                        "k1",
                        theoretical_option_price(k1, calc_type),
                        f"{key_prefix}_price1",
                    )
                    price2 = price_input(
                        sign2,
                        instrument,
                        "k2",
                        theoretical_option_price(k2, calc_type),
                        f"{key_prefix}_price2",
                    )
                    price3 = price_input(
                        sign3,
                        instrument,
                        "k3",
                        theoretical_option_price(k3, calc_type),
                        f"{key_prefix}_price3",
                    )
                    price4 = price_input(
                        sign4,
                        instrument,
                        "k4",
                        theoretical_option_price(k4, calc_type),
                        f"{key_prefix}_price4",
                    )

                elif strategy == "Ladder":
                    if option_type == "CALL":
                        sign1 = "+" if side == "LONG" else "-"
                        sign2 = "-" if side == "LONG" else "+"
                        sign3 = "-" if side == "LONG" else "+"
                        price1 = price_input(
                            sign1,
                            "Call",
                            "k1",
                            theoretical_option_price(k1, "c"),
                            "ladder_call_price1",
                        )
                        price2 = price_input(
                            sign2,
                            "Call",
                            "k2",
                            theoretical_option_price(k2, "c"),
                            "ladder_call_price2",
                        )
                        price3 = price_input(
                            sign3,
                            "Call",
                            "k3",
                            theoretical_option_price(k3, "c"),
                            "ladder_call_price3",
                        )
                    else:
                        sign1 = "-" if side == "LONG" else "+"
                        sign2 = "-" if side == "LONG" else "+"
                        sign3 = "+" if side == "LONG" else "-"
                        price1 = price_input(
                            sign1,
                            "Put",
                            "k1",
                            theoretical_option_price(k1, "p"),
                            "ladder_put_price1",
                        )
                        price2 = price_input(
                            sign2,
                            "Put",
                            "k2",
                            theoretical_option_price(k2, "p"),
                            "ladder_put_price2",
                        )
                        price3 = price_input(
                            sign3,
                            "Put",
                            "k3",
                            theoretical_option_price(k3, "p"),
                            "ladder_put_price3",
                        )

                elif strategy == "Jade Lizard":
                    price1 = price_input(
                        "-",
                        "Put",
                        "k1",
                        theoretical_option_price(k1, "p"),
                        "jade_lizard_put_price",
                    )
                    price2 = price_input(
                        "-",
                        "Call",
                        "k2",
                        theoretical_option_price(k2, "c"),
                        "jade_lizard_call_price1",
                    )
                    price3 = price_input(
                        "+",
                        "Call",
                        "k3",
                        theoretical_option_price(k3, "c"),
                        "jade_lizard_call_price2",
                    )

                elif strategy == "Reverse Jade Lizard":
                    price1 = price_input(
                        "+",
                        "Put",
                        "k1",
                        theoretical_option_price(k1, "p"),
                        "rev_jade_lizard_put_price1",
                    )
                    price2 = price_input(
                        "-",
                        "Put",
                        "k2",
                        theoretical_option_price(k2, "p"),
                        "rev_jade_lizard_put_price2",
                    )
                    price3 = price_input(
                        "-",
                        "Call",
                        "k3",
                        theoretical_option_price(k3, "c"),
                        "rev_jade_lizard_call_price",
                    )

                elif strategy == "Covered":
                    price2 = s
                    if option_type == "CALL":
                        render_leg_label("+", "Stock")
                        price1 = price_input(
                            "-",
                            "Call",
                            "k",
                            theoretical_option_price(k1, "c"),
                            "covered_call_price",
                        )
                    else:
                        render_leg_label("-", "Stock")
                        price1 = price_input(
                            "-",
                            "Put",
                            "k",
                            theoretical_option_price(k1, "p"),
                            "covered_put_price",
                        )

                elif strategy == "Protective":
                    price2 = s
                    if option_type == "CALL":
                        render_leg_label("-", "Stock")
                        price1 = price_input(
                            "+",
                            "Call",
                            "k",
                            theoretical_option_price(k1, "c"),
                            "protective_call_price",
                        )
                    else:
                        render_leg_label("+", "Stock")
                        price1 = price_input(
                            "+",
                            "Put",
                            "k",
                            theoretical_option_price(k1, "p"),
                            "protective_put_price",
                        )

            st.markdown("---")
            st.subheader("Pricing Model")

            pricing_model_cols = st.columns([1, 3])
            with pricing_model_cols[0]:
                pricing_model = st.selectbox(
                    "Pricing Model",
                    options=["Black-Scholes", "Heston (calibrated)"],
                    key="pricing_model_select",
                    help="Heston needs calibrated parameters. You can calibrate here without opening the 3D plot.",
                )

            with pricing_model_cols[1]:
                if pricing_model == "Heston (calibrated)":
                    if heston_available:
                        st.caption(
                            f"Calibrated: {heston_result['quotes_used']} quotes, RMSE ${heston_result['rmse']:.2f}"
                        )
                        calibration_expiries = heston_result.get(
                            "calibration_expiries", []
                        )
                        if calibration_expiries:
                            st.caption(
                                "Calibration expiries: "
                                + ", ".join(calibration_expiries[:4])
                                + ("..." if len(calibration_expiries) > 4 else "")
                            )
                    else:
                        st.caption("No Heston calibration for this ticker yet.")

            if pricing_model == "Heston (calibrated)":
                available_calc_expiries = max(
                    1,
                    min(
                        8,
                        len(data["expiry_dates"]) if "expiry_dates" in data else 1,
                    ),
                )
                st.markdown("**Calibration settings**")
                calc_settings_cols = st.columns(3)
                with calc_settings_cols[0]:
                    calc_heston_expiry_count = st.number_input(
                        "Expiry count",
                        value=min(4, available_calc_expiries),
                        min_value=1,
                        max_value=available_calc_expiries,
                        step=1,
                        key="calc_heston_expiry_count",
                        help="Number of expiries to calibrate, starting from the selected Expiry Date.",
                    )
                with calc_settings_cols[1]:
                    calc_heston_options_per_expiry = st.number_input(
                        "Options per side/expiry",
                        value=8,
                        min_value=4,
                        max_value=20,
                        step=1,
                        key="calc_heston_options_per_expiry",
                    )
                with calc_settings_cols[2]:
                    calc_heston_max_iter = st.number_input(
                        "Max iterations",
                        value=80,
                        min_value=20,
                        max_value=300,
                        step=10,
                        key="calc_heston_max_iter",
                    )

                calc_initial_params = get_heston_initial_params(
                    data, heston_result, ticker
                )
                st.markdown("**Initial Heston parameters**")
                calc_param_cols = st.columns(5)
                with calc_param_cols[0]:
                    calc_heston_kappa = st.number_input(
                        "Kappa",
                        value=float(calc_initial_params["kappa"]),
                        min_value=0.05,
                        max_value=8.0,
                        step=0.05,
                        format="%.2f",
                        key="calc_heston_kappa",
                        help="Mean reversion speed of variance.",
                    )
                with calc_param_cols[1]:
                    calc_heston_long_vol = st.number_input(
                        "Long-run vol (%)",
                        value=float(np.sqrt(calc_initial_params["theta"]) * 100),
                        min_value=1.0,
                        max_value=150.0,
                        step=0.5,
                        format="%.2f",
                        key="calc_heston_long_vol",
                        help="Square of this value is used as theta.",
                    )
                with calc_param_cols[2]:
                    calc_heston_sigma_v = st.number_input(
                        "Vol of vol",
                        value=float(calc_initial_params["sigma_v"]),
                        min_value=0.02,
                        max_value=5.0,
                        step=0.05,
                        format="%.2f",
                        key="calc_heston_sigma_v",
                    )
                with calc_param_cols[3]:
                    calc_heston_rho = st.number_input(
                        "Correlation rho",
                        value=float(calc_initial_params["rho"]),
                        min_value=-0.95,
                        max_value=0.95,
                        step=0.05,
                        format="%.2f",
                        key="calc_heston_rho",
                    )
                with calc_param_cols[4]:
                    calc_heston_spot_vol = st.number_input(
                        "Spot vol (%)",
                        value=float(np.sqrt(calc_initial_params["v0"]) * 100),
                        min_value=1.0,
                        max_value=150.0,
                        step=0.5,
                        format="%.2f",
                        key="calc_heston_spot_vol",
                        help="Square of this value is used as v0.",
                    )

                if st.button("Calibrate Heston Now", key="calc_heston_button"):
                    with st.spinner("Calibrating Heston model..."):
                        try:
                            calc_initial_params = make_heston_initial_params(
                                calc_heston_kappa,
                                calc_heston_long_vol,
                                calc_heston_sigma_v,
                                calc_heston_rho,
                                calc_heston_spot_vol,
                            )
                            calibration = run_heston_calibration(
                                ticker,
                                data,
                                s,
                                rf,
                                y,
                                expiry_count=calc_heston_expiry_count,
                                options_per_expiry=calc_heston_options_per_expiry,
                                max_iter=calc_heston_max_iter,
                                initial_params=calc_initial_params,
                                anchor_expiry=expiry,
                            )
                            st.session_state.heston_calibration = calibration
                            st.success(
                                f"Heston calibrated with {calibration['quotes_used']} quotes."
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Heston calibration failed: {e}")

            st.markdown("---")

            st.subheader("Option Strategy Plot")

            if st.button("Show Plot"):
                with st.spinner("Calculating..."):
                    try:
                        df, strategy_info = calculate_payoff_df(
                            strategy=strategy,
                            side=side,
                            option_type=option_type,
                            s=s,
                            k1=k1,
                            k2=k2,
                            k3=k3,
                            k4=k4,
                            price1=price1,
                            price2=price2,
                            price3=price3,
                            price4=price4,
                            size=size,
                            tau=tau,
                            rf=rf,
                            sigma=sigma,
                            y=y,
                        )

                        # Save calculated data to session state
                        st.session_state.df = df
                        st.session_state.strategy_info = strategy_info

                        # Save current parameters to session state (for display)
                        st.session_state.plot_side = side
                        st.session_state.plot_option_type = option_type
                        st.session_state.plot_strategy = strategy

                        # Generate and save the plot
                        st.session_state.plot_fig = plot_option_strategy(
                            df, s, greeks, strategy_info, tau, sigma, y, rf
                        )
                        st.session_state.plot_greeks = greeks
                    except Exception as e:
                        st.error(f"Error creating plot: {e}")

            if (
                st.session_state.plot_fig is not None
                and st.session_state.df is not None
                and st.session_state.strategy_info is not None
                and st.session_state.plot_greeks != greeks
            ):
                try:
                    st.session_state.plot_fig = plot_option_strategy(
                        st.session_state.df,
                        s,
                        greeks,
                        st.session_state.strategy_info,
                        tau,
                        sigma,
                        y,
                        rf,
                    )
                    st.session_state.plot_greeks = greeks
                except Exception as e:
                    st.error(f"Error updating Greek plot: {e}")

            # Display the saved plot if it exists
            if st.session_state.plot_fig is not None:
                col_info1, col_info2, col_info3 = st.columns(3)
                df = st.session_state.df
                strategy_info = st.session_state.strategy_info

                with col_info1:
                    # Get the saved parameters from session state
                    plot_side = (
                        st.session_state.plot_side
                        if "plot_side" in st.session_state
                        else side
                    )
                    plot_option_type = (
                        st.session_state.plot_option_type
                        if "plot_option_type" in st.session_state
                        else option_type
                    )
                    plot_strategy = (
                        st.session_state.plot_strategy
                        if "plot_strategy" in st.session_state
                        else strategy
                    )

                    # Define strategies that don't need side and/or option_type in their name
                    side_independent_strategies = [
                        "Strip",
                        "Strap",
                        "Jade Lizard",
                        "Reverse Jade Lizard",
                    ]
                    option_type_independent_strategies = [
                        "Straddle",
                        "Strangle",
                        "Strip",
                        "Strap",
                        "Jade Lizard",
                        "Reverse Jade Lizard",
                    ]
                    covered_protective_strategies = [
                        "Covered",
                        "Protective",
                    ]  # These need option_type but not side

                    # Format the strategy title based on strategy type
                    if plot_strategy in side_independent_strategies:
                        # Strategies that don't need side or option_type
                        strategy_title = f"### {plot_strategy}"
                    elif plot_strategy in covered_protective_strategies:
                        # Strategies that need option_type but not side
                        strategy_title = f"### {plot_option_type} {plot_strategy}"
                    elif plot_strategy in option_type_independent_strategies:
                        # Strategies that need side but not option_type
                        strategy_title = f"### {plot_side} {plot_strategy}"
                    else:
                        # Strategies that need both side and option_type
                        strategy_title = (
                            f"### {plot_side} {plot_option_type} {plot_strategy}"
                        )

                    st.markdown(strategy_title)

                    strategy_color = {
                        "Bullish": "#f05f3e",
                        "Bearish": "#34b4eb",
                        "Neutral": "#59d9b5",
                    }.get(strategy_info["strategy_type"], "#808080")

                    risk_color = {
                        "High Risk": "#f03ec6",
                        "Moderate Risk": "#37ad8c",
                        "Low Risk": "#3ebaf0",
                    }.get(strategy_info["risk_level"], "#808080")

                    strategy_text = f"<code style='color:{strategy_color};'>{strategy_info['strategy_type']}</code>"
                    risk_text = f"<code style='color:{risk_color};'>{strategy_info['risk_level']}</code>"

                    st.markdown(
                        f"{strategy_text} | {risk_text}", unsafe_allow_html=True
                    )

                # Display the chart
                st.plotly_chart(st.session_state.plot_fig, use_container_width=True)

                # Calculate Win Rate
                win_rate = calculate_win_rate(
                    df,
                    s,
                    strategy_info["bep1"],
                    strategy_info["bep2"],
                    days=tau,
                    volatility=sigma,
                    dividend_yield=y,
                    risk_free_rate=rf,
                )

                # Calculate ITM probability
                if option_type == "CALL":
                    itm_prob = calculate_itm_probability(s, k1, tau, sigma, "c", y, rf)
                else:
                    itm_prob = calculate_itm_probability(s, k1, tau, sigma, "p", y, rf)

                st.subheader("Strategy Performance")
                max_profit_text = (
                    "+∞"
                    if np.isinf(strategy_info["max_profit"])
                    else f"${strategy_info['max_profit']:.2f}"
                )
                min_profit_text = (
                    "-∞"
                    if np.isinf(strategy_info["min_profit"])
                    else f"${strategy_info['min_profit']:.2f}"
                )
                idx = np.abs(df["x"] - s).argmin()
                current_pl = df["y"].iloc[idx].round(2)

                # Display performance metrics - First row
                col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)

                with col_p1:
                    st.metric("Underlying price", f"${s:.2f}")
                with col_p2:
                    st.metric("Max Profit (@100)", max_profit_text)
                with col_p3:
                    st.metric("Max Loss (@100)", min_profit_text)
                with col_p4:
                    st.metric("Win Rate", f"{win_rate:.2f}%")

                # Second row for Break-Even points
                col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)

                # Display Break-Even points
                if (
                    strategy_info["bep1"] is not None
                    and strategy_info["bep2"] is not None
                ):
                    with col_b1:
                        st.metric("Break-Even ₁", f"${strategy_info['bep1']:.2f}")
                    with col_b2:
                        st.metric("Break-Even ₂", f"${strategy_info['bep2']:.2f}")
                elif strategy_info["bep1"] is not None:
                    with col_b1:
                        st.metric("Break-Even", f"${strategy_info['bep1']:.2f}")
                else:
                    with col_b1:
                        st.metric("Break-Even", "N/A")

                st.markdown("<br>", unsafe_allow_html=True)

                st.subheader("Greeks at Current Price")
                idx = np.abs(df["x"] - s).argmin()

                # Get Greek values
                delta = df["Delta"].iloc[idx]
                gamma = df["Gamma"].iloc[idx]
                vega = df["Vega"].iloc[idx]
                theta = df["Theta"].iloc[idx]
                rho = df["Rho"].iloc[idx]
                vanna = df["Vanna"].iloc[idx]
                charm = df["Charm"].iloc[idx]

                # Define Greek information with symbols
                greeks_info = [
                    {
                        "name": "Δ Delta",
                        "value": delta,
                        "good_high": True
                        if strategy_info.get("option_type", "").upper() == "CALL"
                        else False,
                        "description": "Price sensitivity to underlying asset ($1 change)",
                        "interpretation": "Higher delta means more sensitivity to price changes",
                    },
                    {
                        "name": "Γ Gamma",
                        "value": gamma,
                        "good_high": True,
                        "description": "Rate of change in Delta per $1 move",
                        "interpretation": "Higher gamma means delta changes more rapidly",
                    },
                    {
                        "name": "ν Vega",
                        "value": vega,
                        "good_high": True,
                        "description": "Sensitivity to 1% change in volatility",
                        "interpretation": "Higher vega means more sensitive to volatility changes",
                    },
                    {
                        "name": "Θ Theta",
                        "value": theta,
                        "good_high": False,  # Negative theta is generally bad for option buyers
                        "description": "Daily time decay of option value",
                        "interpretation": "Negative theta means losing value each day",
                    },
                    {
                        "name": "ρ Rho",
                        "value": rho,
                        "good_high": True,
                        "description": "Sensitivity to 1% change in interest rates",
                        "interpretation": "Higher rates generally increase call values, decrease put values",
                    },
                    {
                        "name": "Δν/ΔS Vanna",
                        "value": vanna,
                        "description": "Delta's sensitivity to volatility changes",
                        "interpretation": "Shows how delta changes with volatility",
                    },
                    {
                        "name": "Δδ/Δt Charm",
                        "value": charm,
                        "description": "Delta's sensitivity to time passing",
                        "interpretation": "Shows how delta changes as expiration approaches",
                    },
                ]

                # Display Greeks in a more organized way
                st.markdown(
                    """
                <style>
                .greek-card {
                    background: #f8f9fa;
                    border-radius: 6px;
                    padding: 12px;
                    margin-bottom: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .greek-name {
                    font-weight: 600;
                    font-size: 1.1em;
                    margin-bottom: 5px;
                    font-family: monospace;
                }
                .greek-value {
                    font-size: 1.3em;
                    font-weight: 600;
                    margin: 4px 0;
                }
                .greek-desc {
                    font-size: 0.85em;
                    color: #666;
                    margin-top: 4px;
                }
                .positive {
                    color: #1cd4c8;
                }
                .negative {
                    color: #d41c78;
                }
                </style>
                """,
                    unsafe_allow_html=True,
                )

                # Create two columns for better layout
                col1, col2 = st.columns(2)

                with col1:
                    for greek in greeks_info[:4]:
                        value_color = (
                            "positive"
                            if (greek["value"] >= 0 and greek.get("good_high", True))
                            or (greek["value"] < 0 and not greek.get("good_high", True))
                            else "negative"
                        )

                        st.markdown(
                            f"""
                        <div class='greek-card'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <div>
                                    <div class='greek-name'> {greek["name"]}</div>
                                    <div class='greek-value {value_color}'>{greek["value"]:+.4f}</div>
                                </div>
                                <div style='text-align: right;'>
                                    <div class='greek-desc'>{greek["description"]}</div>
                                    <div style='font-size: 0.8em; color: #888;'>{greek["interpretation"]}</div>
                                </div>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                with col2:
                    for greek in greeks_info[4:]:
                        value_color = (
                            "positive"
                            if (greek["value"] >= 0 and greek.get("good_high", True))
                            or (greek["value"] < 0 and not greek.get("good_high", True))
                            else "negative"
                        )

                        st.markdown(
                            f"""
                        <div class='greek-card'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <div>
                                    <div class='greek-name'> {greek["name"]}</div>
                                    <div class='greek-value {value_color}'>{greek["value"]:+.4f}</div>
                                </div>
                                <div style='text-align: right;'>
                                    <div class='greek-desc'>{greek["description"]}</div>
                                    <div style='font-size: 0.8em; color: #888;'>{greek["interpretation"]}</div>
                                </div>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    # Add a small legend explaining the colors
                    st.markdown(
                        """
                    <div style='margin-top: 15px; font-size: 0.85em; color: #666;'>
                        <div><span style='color: #1cd4c8;'>Green:</span> Desirable direction for this position</div>
                        <div><span style='color: #d41c78;'>Pink:</span> Less desirable direction</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        else:
            st.info("Please enter a ticker symbol and fetch data in the sidebar first.")

    with tab3:
        # 옵션 체인 탭
        st.subheader("Option Chain")

        if "data" in st.session_state:
            data = st.session_state.data

            # 티커 변경 감지 및 볼라틸리티 데이터 캐싱을 위한 session_state 초기화
            if "current_vol_ticker" not in st.session_state:
                st.session_state.current_vol_ticker = None
                st.session_state.vol_data = []
                st.session_state.all_vols_data_call = []
                st.session_state.all_vols_data_put = []

            # 티커가 변경되었는지 확인 또는 데이터가 비어있는지 확인
            ticker_changed = (st.session_state.current_vol_ticker != ticker) or (
                not st.session_state.vol_data
            )

            # Volatility Surface & Smile/Skew 섹션
            st.subheader("Volatility Surface & Smile/Skew")

            # 티커가 변경된 경우에만 데이터 새로 계산
            if ticker_changed:
                with st.spinner("Generating volatility data... "):
                    # 현재 티커 저장
                    st.session_state.current_vol_ticker = ticker

                    # 데이터 수집 초기화
                    all_vols_data_call = []
                    all_vols_data_put = []
                    colors = [
                        "#636EFA",
                        "#EF553B",
                        "#00CC96",
                        "#AB63FA",
                        "#FFA15A",
                        "#19D3F3",
                        "#FF6692",
                    ]
                    vol_data = []

                    # 모든 만기일에 대한 데이터 수집
                    expiry_dates = data["expiry_dates"]

                    # 최대 7개의 만기일만 사용
                    selected_expiries = expiry_dates[: min(7, len(expiry_dates))]

                    for i, exp_date in enumerate(selected_expiries):
                        try:
                            exp_calls, exp_puts = get_option_chain(ticker, exp_date)
                            if exp_calls is not None and exp_puts is not None:
                                # 만기일까지 남은 일수 계산
                                days_to_exp = calculate_days_to_expiry(exp_date)

                                # 만기일이 현재 이후인 경우만 포함
                                if days_to_exp <= 0:
                                    continue

                                # 콜 옵션 내재 변동성 계산
                                exp_calls["implied_volatility"] = exp_calls.apply(
                                    lambda row: calculate_implied_volatility(
                                        row["lastPrice"],
                                        s,
                                        row["strike"],
                                        rf,
                                        days_to_exp,
                                        y,
                                        "c",
                                    ),
                                    axis=1,
                                )

                                # 풋 옵션 내재 변동성 계산
                                exp_puts["implied_volatility"] = exp_puts.apply(
                                    lambda row: calculate_implied_volatility(
                                        row["lastPrice"],
                                        s,
                                        row["strike"],
                                        rf,
                                        days_to_exp,
                                        y,
                                        "p",
                                    ),
                                    axis=1,
                                )

                                # 유효한 값만 선택 (inf 또는 너무 큰 값 제외)
                                valid_calls = exp_calls[
                                    (exp_calls["implied_volatility"] < 200)
                                    & (exp_calls["implied_volatility"] > 1)
                                ]
                                valid_puts = exp_puts[
                                    (exp_puts["implied_volatility"] < 200)
                                    & (exp_puts["implied_volatility"] > 1)
                                ]

                                # 콜과 풋의 내재 변동성 각각 저장
                                if not valid_calls.empty:
                                    exp_color = colors[i % len(colors)]
                                    all_vols_data_call.append(
                                        {
                                            "x": valid_calls["strike"].tolist(),
                                            "y": valid_calls[
                                                "implied_volatility"
                                            ].tolist(),
                                            "name": exp_date,
                                            "color": exp_color,
                                            "days": days_to_exp,
                                        }
                                    )

                                    # 3D 그래프용 콜 데이터 준비
                                    for _, row in valid_calls.iterrows():
                                        vol_data.append(
                                            {
                                                "days": days_to_exp,
                                                "strike": row["strike"],
                                                "iv": row["implied_volatility"],
                                                "type": "Call",
                                                "expiry": exp_date,
                                            }
                                        )

                                if not valid_puts.empty:
                                    exp_color = colors[i % len(colors)]
                                    all_vols_data_put.append(
                                        {
                                            "x": valid_puts["strike"].tolist(),
                                            "y": valid_puts[
                                                "implied_volatility"
                                            ].tolist(),
                                            "name": exp_date,
                                            "color": exp_color,
                                            "days": days_to_exp,
                                        }
                                    )

                                    # 3D 그래프용 풋 데이터 준비
                                    for _, row in valid_puts.iterrows():
                                        vol_data.append(
                                            {
                                                "days": days_to_exp,
                                                "strike": row["strike"],
                                                "iv": row["implied_volatility"],
                                                "type": "Put",
                                                "expiry": exp_date,
                                            }
                                        )
                        except Exception as e:
                            st.warning(f"Error processing expiry date {exp_date}: {e}")
                            continue

                    # 데이터를 session_state에 저장
                    st.session_state.vol_data = vol_data
                    st.session_state.all_vols_data_call = all_vols_data_call
                    st.session_state.all_vols_data_put = all_vols_data_put

            # 2D 그래프용 탭
            vol_tabs = st.tabs(
                [
                    "3D Surface",
                    "Call Volatility Smile/Skew",
                    "Put Volatility Smile/Skew",
                ]
            )

            # 캐시된 데이터 사용
            vol_data = (
                st.session_state.vol_data
                if st.session_state.vol_data is not None
                else []
            )
            all_vols_data_call = (
                st.session_state.all_vols_data_call
                if st.session_state.all_vols_data_call is not None
                else []
            )
            all_vols_data_put = (
                st.session_state.all_vols_data_put
                if st.session_state.all_vols_data_put is not None
                else []
            )

            # 데이터 유효성 확인
            has_vol_data = len(vol_data) > 0
            has_call_data = len(all_vols_data_call) > 0
            has_put_data = len(all_vols_data_put) > 0

            with vol_tabs[0]:  # 3D Surface 탭
                if has_vol_data:
                    try:
                        # 데이터프레임으로 변환
                        vol_df = pd.DataFrame(vol_data)

                        # 콜 옵션 데이터프레임
                        call_df = vol_df[vol_df["type"] == "Call"]
                        # 풋 옵션 데이터프레임
                        put_df = vol_df[vol_df["type"] == "Put"]

                        if len(call_df) <= 1 and len(put_df) <= 1:
                            st.warning(
                                "Not enough data to generate Volatility Surface. Select a more liquid option chain."
                            )
                        else:
                            # 개별 표면 그래프로 변경
                            fig = make_subplots(
                                rows=1,
                                cols=2,
                                specs=[[{"type": "surface"}, {"type": "surface"}]],
                                subplot_titles=(
                                    "Call Options Volatility Surface",
                                    "Put Options Volatility Surface",
                                ),
                            )

                            # 충분한 데이터가 있는 경우에만 표면 추가
                            call_surface_added = False
                            put_surface_added = False

                            if len(call_df) > 1:
                                try:
                                    # 중복 값 및 이상치 제거
                                    call_df = call_df[
                                        (call_df["iv"] > 0) & (call_df["iv"] < 200)
                                    ]

                                    # 최소 필요 데이터 확인
                                    unique_days = call_df["days"].nunique()
                                    unique_strikes = call_df["strike"].nunique()

                                    if unique_days >= 2 and unique_strikes >= 2:
                                        # 콜 옵션 데이터를 표면에 적합하게 그리드화
                                        call_pivoted = (
                                            call_df.pivot_table(
                                                values="iv",
                                                index="days",
                                                columns="strike",
                                                aggfunc="mean",
                                            )
                                            .fillna(method="ffill")
                                            .fillna(method="bfill")
                                        )

                                        # 디버그 메시지 제거

                                        # 데이터가 충분히 있는 경우에만 표면 추가
                                        if (
                                            call_pivoted.shape[0] >= 2
                                            and call_pivoted.shape[1] >= 2
                                        ):
                                            fig.add_trace(
                                                go.Surface(
                                                    z=call_pivoted.values,
                                                    x=call_pivoted.columns.tolist(),  # strike
                                                    y=call_pivoted.index.tolist(),  # days
                                                    colorscale="Reds",  # 콜 옵션은 빨간색 계열로 통일
                                                    opacity=0.8,
                                                    name="Call Options",
                                                    showscale=False,
                                                ),
                                                row=1,
                                                col=1,
                                            )
                                            call_surface_added = True
                                        else:
                                            st.warning(
                                                "Not enough call option data points after pivoting."
                                            )
                                    else:
                                        st.warning(
                                            f"Not enough call option data variety. Need at least 2 different days and strikes. Found: days={unique_days}, strikes={unique_strikes}"
                                        )
                                except Exception as e:
                                    st.warning(f"Error creating call surface: {e}")
                                    st.write("Call data preview:")
                                    st.write(call_df.head())

                            if len(put_df) > 1:
                                try:
                                    # 중복 값 및 이상치 제거
                                    put_df = put_df[
                                        (put_df["iv"] > 0) & (put_df["iv"] < 200)
                                    ]

                                    # 최소 필요 데이터 확인
                                    unique_days = put_df["days"].nunique()
                                    unique_strikes = put_df["strike"].nunique()

                                    if unique_days >= 2 and unique_strikes >= 2:
                                        # 풋 옵션 데이터를 표면에 적합하게 그리드화
                                        put_pivoted = (
                                            put_df.pivot_table(
                                                values="iv",
                                                index="days",
                                                columns="strike",
                                                aggfunc="mean",
                                            )
                                            .fillna(method="ffill")
                                            .fillna(method="bfill")
                                        )

                                        # 디버그 메시지 제거

                                        # 데이터가 충분히 있는 경우에만 표면 추가
                                        if (
                                            put_pivoted.shape[0] >= 2
                                            and put_pivoted.shape[1] >= 2
                                        ):
                                            fig.add_trace(
                                                go.Surface(
                                                    z=put_pivoted.values,
                                                    x=put_pivoted.columns.tolist(),  # strike
                                                    y=put_pivoted.index.tolist(),  # days
                                                    colorscale="Blues",  # 풋 옵션은 파란색 계열로 통일
                                                    opacity=0.8,
                                                    name="Put Options",
                                                    showscale=True,
                                                    colorbar=dict(
                                                        title="IV (%)", x=1.0, y=0.5
                                                    ),
                                                ),
                                                row=1,
                                                col=2,
                                            )
                                            put_surface_added = True
                                        else:
                                            st.warning(
                                                "Not enough put option data points after pivoting."
                                            )
                                    else:
                                        st.warning(
                                            f"Not enough put option data variety. Need at least 2 different days and strikes. Found: days={unique_days}, strikes={unique_strikes}"
                                        )
                                except Exception as e:
                                    st.warning(f"Error creating put surface: {e}")
                                    st.write("Put data preview:")
                                    st.write(put_df.head())

                            # 표면 데이터가 있는 경우에만 그래프 표시
                            if call_surface_added or put_surface_added:
                                # 그래프 레이아웃 업데이트
                                fig.update_layout(
                                    title="Option Volatility Surface",
                                    height=600,
                                    width=800,
                                    scene=dict(
                                        xaxis_title="Strike Price",
                                        yaxis_title="Days to Expiry",
                                        zaxis_title="Implied Volatility (%)",
                                        camera=dict(eye=dict(x=1.5, y=1.5, z=1.0)),
                                    ),
                                    margin=dict(l=65, r=50, b=65, t=90),
                                )

                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning(
                                    "Could not create volatility surface due to insufficient data."
                                )
                    except Exception as e:
                        st.error(f"Error generating volatility surface: {e}")
                        st.write("Original data preview:")
                        if vol_data:
                            df_sample = pd.DataFrame(
                                vol_data[:10]
                            )  # 앞부분 10개만 표시
                            st.write(df_sample)
                        else:
                            st.write("No data available")
                else:
                    st.warning(
                        "No data available to generate volatility surface. Try selecting a different ticker with more liquid options."
                    )

            with vol_tabs[1]:  # Call 옵션 Volatility Smile/Skew 탭
                if has_call_data:
                    try:
                        # 2D smile plot for calls
                        fig = go.Figure()

                        # 각 만기일에 대한 콜 옵션 변동성 스마일 추가
                        for vol_data in all_vols_data_call:
                            fig.add_trace(
                                go.Scatter(
                                    x=vol_data["x"],
                                    y=vol_data["y"],
                                    mode="lines+markers",
                                    name=f"{vol_data['name']} ({vol_data['days']} days)",
                                    line=dict(color=vol_data["color"]),
                                )
                            )

                        # 현재 주가에 수직선 추가
                        fig.add_vline(
                            x=s, line_width=1, line_dash="dash", line_color="green"
                        )

                        fig.update_layout(
                            title="Call Options Volatility Smile/Skew",
                            xaxis_title="Strike Price",
                            yaxis_title="Implied Volatility (%)",
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                            ),
                            width=800,
                            height=500,
                            margin=dict(l=65, r=50, b=65, t=90),
                        )

                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error generating call volatility smile: {e}")
                else:
                    st.warning(
                        "Not enough data to generate call option volatility smile plot. Try selecting a ticker with more liquid options."
                    )

            with vol_tabs[2]:  # Put 옵션 Volatility Smile/Skew 탭
                if has_put_data:
                    try:
                        # 2D smile plot for puts
                        fig = go.Figure()

                        # 각 만기일에 대한 풋 옵션 변동성 스마일 추가
                        for vol_data in all_vols_data_put:
                            fig.add_trace(
                                go.Scatter(
                                    x=vol_data["x"],
                                    y=vol_data["y"],
                                    mode="lines+markers",
                                    name=f"{vol_data['name']} ({vol_data['days']} days)",
                                    line=dict(color=vol_data["color"]),
                                )
                            )

                        # 현재 주가에 수직선 추가
                        fig.add_vline(
                            x=s, line_width=1, line_dash="dash", line_color="green"
                        )

                        fig.update_layout(
                            title="Put Options Volatility Smile/Skew",
                            xaxis_title="Strike Price",
                            yaxis_title="Implied Volatility (%)",
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                            ),
                            width=800,
                            height=500,
                            margin=dict(l=65, r=50, b=65, t=90),
                        )

                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error generating put volatility smile: {e}")
                else:
                    st.warning(
                        "Not enough data to generate put option volatility smile plot. Try selecting a ticker with more liquid options."
                    )

            st.subheader("Heston Calibration 3D")
            st.caption(
                "Optional 3D view of calibrated Heston prices and errors. Heston pricing only needs calibration; the 3D plot is for inspection."
            )

            available_heston_expiries = max(
                1, min(8, len(data["expiry_dates"]) if "expiry_dates" in data else 1)
            )
            heston_cols = st.columns(4)
            with heston_cols[0]:
                heston_expiry_count = st.number_input(
                    "Calibration expiry count",
                    value=min(4, available_heston_expiries),
                    min_value=1,
                    max_value=available_heston_expiries,
                    step=1,
                    help="Number of expiries to calibrate, starting from the selected calculator Expiry Date.",
                )
            with heston_cols[1]:
                heston_options_per_expiry = st.number_input(
                    "Options per side/expiry",
                    value=8,
                    min_value=4,
                    max_value=20,
                    step=1,
                )
            with heston_cols[2]:
                heston_max_iter = st.number_input(
                    "Max iterations",
                    value=80,
                    min_value=20,
                    max_value=300,
                    step=10,
                )
            with heston_cols[3]:
                st.metric("Current ticker", ticker)

            chain_heston_result = st.session_state.get("heston_calibration")
            chain_initial_params = get_heston_initial_params(
                data, chain_heston_result, ticker
            )
            with st.expander("**Initial Heston parameters**", expanded=False):
                chain_param_cols = st.columns(5)
                with chain_param_cols[0]:
                    chain_heston_kappa = st.number_input(
                        "Kappa",
                        value=float(chain_initial_params["kappa"]),
                        min_value=0.05,
                        max_value=8.0,
                        step=0.05,
                        format="%.2f",
                        key="chain_heston_kappa",
                    )
                with chain_param_cols[1]:
                    chain_heston_long_vol = st.number_input(
                        "Long-run vol (%)",
                        value=float(np.sqrt(chain_initial_params["theta"]) * 100),
                        min_value=1.0,
                        max_value=150.0,
                        step=0.5,
                        format="%.2f",
                        key="chain_heston_long_vol",
                    )
                with chain_param_cols[2]:
                    chain_heston_sigma_v = st.number_input(
                        "Vol of vol",
                        value=float(chain_initial_params["sigma_v"]),
                        min_value=0.02,
                        max_value=5.0,
                        step=0.05,
                        format="%.2f",
                        key="chain_heston_sigma_v",
                    )
                with chain_param_cols[3]:
                    chain_heston_rho = st.number_input(
                        "Correlation rho",
                        value=float(chain_initial_params["rho"]),
                        min_value=-0.95,
                        max_value=0.95,
                        step=0.05,
                        format="%.2f",
                        key="chain_heston_rho",
                    )
                with chain_param_cols[4]:
                    chain_heston_spot_vol = st.number_input(
                        "Spot vol (%)",
                        value=float(np.sqrt(chain_initial_params["v0"]) * 100),
                        min_value=1.0,
                        max_value=150.0,
                        step=0.5,
                        format="%.2f",
                        key="chain_heston_spot_vol",
                    )

            if st.button("Calibrate Heston Model"):
                with st.spinner("Calibrating Heston model from option chains..."):
                    try:
                        chain_initial_params = make_heston_initial_params(
                            chain_heston_kappa,
                            chain_heston_long_vol,
                            chain_heston_sigma_v,
                            chain_heston_rho,
                            chain_heston_spot_vol,
                        )
                        calibration = run_heston_calibration(
                            ticker,
                            data,
                            s,
                            rf,
                            y,
                            expiry_count=heston_expiry_count,
                            options_per_expiry=heston_options_per_expiry,
                            max_iter=heston_max_iter,
                            initial_params=chain_initial_params,
                            anchor_expiry=expiry,
                        )
                        st.session_state.heston_calibration = calibration
                        st.success("Heston calibration completed.")
                    except Exception as e:
                        st.error(f"Heston calibration failed: {e}")

            heston_result = st.session_state.get("heston_calibration")
            if heston_result and heston_result.get("ticker") == ticker:
                params = heston_result["params"]
                st.markdown(
                    """
                    <style>
                    .heston-metric-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                        gap: 10px;
                        margin: 8px 0 18px 0;
                    }
                    .heston-metric {
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 6px;
                        padding: 10px 12px;
                        min-width: 0;
                    }
                    .heston-metric-label {
                        color: #6c757d;
                        font-size: 0.78rem;
                        line-height: 1.2;
                        white-space: normal;
                    }
                    .heston-metric-value {
                        color: #212529;
                        font-size: 1.14rem;
                        font-weight: 650;
                        line-height: 1.25;
                        margin-top: 4px;
                        white-space: nowrap;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                heston_metrics = [
                    ("Kappa", f"{params['kappa']:.2f}"),
                    ("Long-run vol", f"{np.sqrt(params['theta']) * 100:.2f}%"),
                    ("Vol of vol", f"{params['sigma_v']:.2f}"),
                    ("Correlation", f"{params['rho']:.2f}"),
                    ("Spot vol", f"{np.sqrt(params['v0']) * 100:.2f}%"),
                    ("RMSE", f"${heston_result['rmse']:.2f}"),
                    ("MAPE", f"{heston_result['mean_abs_pct_error']:.2f}%"),
                ]
                metric_html = "<div class='heston-metric-grid'>"
                for label, value in heston_metrics:
                    metric_html += (
                        "<div class='heston-metric'>"
                        f"<div class='heston-metric-label'>{label}</div>"
                        f"<div class='heston-metric-value'>{value}</div>"
                        "</div>"
                    )
                metric_html += "</div>"
                st.markdown(metric_html, unsafe_allow_html=True)

                fitted_quotes = heston_result.get("fitted_quotes")
                if fitted_quotes is not None and not fitted_quotes.empty:
                    heston_tabs = st.tabs(["Heston Price Surface", "Calibration Error"])

                    with heston_tabs[0]:
                        try:
                            surface_side = st.radio(
                                "Surface option type",
                                options=["Call", "Put"],
                                horizontal=True,
                                key="heston_surface_side",
                            )
                            surface_type = "c" if surface_side == "Call" else "p"
                            strike_min = float(fitted_quotes["strike"].quantile(0.05))
                            strike_max = float(fitted_quotes["strike"].quantile(0.95))
                            day_min = int(max(fitted_quotes["days"].min(), 1))
                            day_max = int(max(fitted_quotes["days"].max(), day_min + 1))
                            strike_grid = np.linspace(strike_min, strike_max, 28)
                            day_grid = np.linspace(day_min, day_max, 16).astype(int)

                            price_surface = heston_price_surface(
                                params, s, rf, y, strike_grid, day_grid, surface_type
                            )
                            quote_overlay = fitted_quotes[
                                fitted_quotes["option_type"] == surface_type
                            ]

                            heston_fig = go.Figure()
                            heston_fig.add_trace(
                                go.Surface(
                                    z=price_surface,
                                    x=strike_grid,
                                    y=day_grid,
                                    colorscale="Reds"
                                    if surface_type == "c"
                                    else "Blues",
                                    opacity=0.82,
                                    colorbar=dict(title="Model price"),
                                    name=f"{surface_side} model surface",
                                    hovertemplate=(
                                        "Strike: %{x:.2f}<br>"
                                        "DTE: %{y}<br>"
                                        "Model price: $%{z:.2f}<extra></extra>"
                                    ),
                                )
                            )
                            if not quote_overlay.empty:
                                heston_fig.add_trace(
                                    go.Scatter3d(
                                        x=quote_overlay["strike"],
                                        y=quote_overlay["days"],
                                        z=quote_overlay["market_price"],
                                        mode="markers",
                                        name=f"{surface_side} market quotes",
                                        marker=dict(
                                            size=4,
                                            color="#111827",
                                            opacity=0.85,
                                        ),
                                        hovertemplate=(
                                            "Expiry: %{text}<br>"
                                            "Strike: %{x:.2f}<br>"
                                            "DTE: %{y}<br>"
                                            "Market price: $%{z:.2f}<extra></extra>"
                                        ),
                                        text=quote_overlay["expiry"],
                                    )
                                )
                            heston_fig.update_layout(
                                title=f"Heston Calibrated {surface_side} Price Surface",
                                height=720,
                                margin=dict(l=20, r=20, b=20, t=65),
                                scene=dict(
                                    xaxis_title="Strike Price",
                                    yaxis_title="Days to Expiry",
                                    zaxis_title="Option Price",
                                    camera=dict(eye=dict(x=1.55, y=1.55, z=1.15)),
                                    aspectmode="cube",
                                ),
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1,
                                ),
                            )
                            st.plotly_chart(heston_fig, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Error creating Heston price surface: {e}")

                    with heston_tabs[1]:
                        error_fig = go.Figure()
                        call_errors = fitted_quotes[
                            fitted_quotes["option_type"] == "c"
                        ]
                        put_errors = fitted_quotes[
                            fitted_quotes["option_type"] == "p"
                        ]
                        if not call_errors.empty:
                            error_fig.add_trace(
                                go.Scatter3d(
                                    x=call_errors["strike"],
                                    y=call_errors["days"],
                                    z=call_errors["pricing_error"],
                                    mode="markers",
                                    name="Call errors",
                                    marker=dict(
                                        size=6,
                                        color=call_errors["pricing_error"],
                                        colorscale="RdBu",
                                        showscale=True,
                                        colorbar=dict(title="Model - Market"),
                                    ),
                                    text=call_errors["expiry"],
                                    hovertemplate=(
                                        "Call<br>"
                                        "Expiry: %{text}<br>"
                                        "Strike: %{x:.2f}<br>"
                                        "DTE: %{y}<br>"
                                        "Error: $%{z:.2f}<extra></extra>"
                                    ),
                                )
                            )
                        if not put_errors.empty:
                            error_fig.add_trace(
                                go.Scatter3d(
                                    x=put_errors["strike"],
                                    y=put_errors["days"],
                                    z=put_errors["pricing_error"],
                                    mode="markers",
                                    name="Put errors",
                                    marker=dict(
                                        size=6,
                                        color=put_errors["pricing_error"],
                                        colorscale="RdBu",
                                        showscale=False,
                                        symbol="diamond",
                                    ),
                                    text=put_errors["expiry"],
                                    hovertemplate=(
                                        "Put<br>"
                                        "Expiry: %{text}<br>"
                                        "Strike: %{x:.2f}<br>"
                                        "DTE: %{y}<br>"
                                        "Error: $%{z:.2f}<extra></extra>"
                                    ),
                                )
                            )
                        zero_x = [
                            fitted_quotes["strike"].min(),
                            fitted_quotes["strike"].max(),
                        ]
                        zero_y = [
                            fitted_quotes["days"].min(),
                            fitted_quotes["days"].max(),
                        ]
                        error_fig.add_trace(
                            go.Surface(
                                x=zero_x,
                                y=zero_y,
                                z=np.zeros((2, 2)),
                                colorscale=[[0, "#6c757d"], [1, "#6c757d"]],
                                opacity=0.18,
                                showscale=False,
                                name="Zero error plane",
                                hoverinfo="skip",
                            )
                        )
                        error_fig.update_layout(
                            title="Heston Calibration Error Surface",
                            height=660,
                            scene=dict(
                                xaxis_title="Strike Price",
                                yaxis_title="Days to Expiry",
                                zaxis_title="Model Price - Market Price",
                                camera=dict(eye=dict(x=1.55, y=1.55, z=1.15)),
                                aspectmode="cube",
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                            ),
                            margin=dict(l=20, r=20, b=20, t=65),
                        )
                        st.plotly_chart(error_fig, use_container_width=True)

                        display_cols = [
                            "expiry",
                            "days",
                            "option_type",
                            "strike",
                            "market_price",
                            "heston_price",
                            "pricing_error",
                        ]
                        st.dataframe(
                            fitted_quotes[display_cols].sort_values(
                                ["days", "strike", "option_type"]
                            ).style.format(
                                {
                                    "strike": "{:.2f}",
                                    "market_price": "{:.2f}",
                                    "heston_price": "{:.2f}",
                                    "pricing_error": "{:.2f}",
                                }
                            ),
                            use_container_width=True,
                        )
            else:
                st.info(
                    "No Heston calibration for this ticker yet. Run calibration above to enable Heston theoretical prices."
                )

            # New section for Call and Put Volume Chart
            st.subheader("Option Volume Chart")

            # 옵션 체인 선택 섹션 - 만기일 선택 후 해당 만기일의 옵션 체인만 업데이트
            st.subheader("Select Option Chain")
            expiry = st.selectbox(
                "Select Expiry Date",
                options=data["expiry_dates"] if "expiry_dates" in data else [],
            )

            if expiry:
                with st.spinner("Fetching option volume data..."):
                    calls, puts = get_option_chain(ticker, expiry)
                    if calls is not None and puts is not None:
                        # Prepare data for volume chart
                        call_strikes = calls["strike"].tolist()
                        put_strikes = puts["strike"].tolist()
                        call_volumes = calls["volume"].tolist()
                        put_volumes = puts["volume"].tolist()

                        # Create volume chart
                        volume_fig = go.Figure()

                        # Add call volume bars - 빨간색으로 통일
                        volume_fig.add_trace(
                            go.Bar(
                                x=call_strikes,
                                y=call_volumes,
                                name="Calls",
                                marker_color="red",
                            )
                        )
                        # Add put volume bars - 파란색으로 통일
                        volume_fig.add_trace(
                            go.Bar(
                                x=put_strikes,
                                y=put_volumes,
                                name="Puts",
                                marker_color="blue",
                            )
                        )

                        volume_fig.update_layout(
                            title="Call and Put Volume by Strike Price",
                            xaxis_title="Strike Price",
                            yaxis_title="Volume",
                            height=400,
                            margin=dict(l=40, r=40, t=40, b=40),
                        )

                        st.plotly_chart(volume_fig, use_container_width=True)
                        # Calculate and display the put-call ratio below the plot
                        if (
                            call_volumes and put_volumes
                        ):  # 리스트가 비어있지 않은지 확인
                            try:
                                # 유효한 숫자만 합산
                                call_volume_total = sum(
                                    v
                                    for v in call_volumes
                                    if isinstance(v, (int, float)) and v >= 0
                                )
                                put_volume_total = sum(
                                    v
                                    for v in put_volumes
                                    if isinstance(v, (int, float)) and v >= 0
                                )

                                # 3개의 열로 나누어 정보 표시
                                vol_cols = st.columns(3)

                                with vol_cols[0]:
                                    st.metric(
                                        "Total Call Volume", f"{call_volume_total:,}"
                                    )

                                with vol_cols[1]:
                                    st.metric(
                                        "Total Put Volume", f"{put_volume_total:,}"
                                    )

                                with vol_cols[2]:
                                    if call_volume_total > 0:
                                        put_call_ratio = (
                                            put_volume_total / call_volume_total
                                        )
                                        st.metric(
                                            "Put-Call Ratio", f"{put_call_ratio:.2f}"
                                        )
                                    else:
                                        st.metric("Put-Call Ratio", "N/A")

                            except Exception as e:
                                st.warning(f"Error calculating Put-Call Ratio: {e}")
                        else:
                            st.warning(
                                "Cannot calculate Put-Call Ratio: Volume data is missing"
                            )

                        # 옵션 체인 데이터 표시
                        st.subheader("Call Option Chain")
                        # 내재 변동성 컬럼 확인 및 표시 형식 변경
                        if "impliedVolatility" in calls.columns:
                            calls["impliedVolatility"] = calls[
                                "impliedVolatility"
                            ].apply(
                                lambda x: (
                                    f"{x * 100:.2f}%"
                                    if isinstance(x, (int, float))
                                    else "N/A"
                                )
                            )
                        elif "implied_volatility" in calls.columns:
                            calls["implied_volatility"] = calls[
                                "implied_volatility"
                            ].apply(
                                lambda x: (
                                    f"{x:.2f}%"
                                    if isinstance(x, (int, float))
                                    else "N/A"
                                )
                            )
                        st.dataframe(calls, use_container_width=True)

                        st.subheader("Put Option Chain")
                        # 내재 변동성 컬럼 확인 및 표시 형식 변경
                        if "impliedVolatility" in puts.columns:
                            puts["impliedVolatility"] = puts["impliedVolatility"].apply(
                                lambda x: (
                                    f"{x * 100:.2f}%"
                                    if isinstance(x, (int, float))
                                    else "N/A"
                                )
                            )
                        elif "implied_volatility" in puts.columns:
                            puts["implied_volatility"] = puts[
                                "implied_volatility"
                            ].apply(
                                lambda x: (
                                    f"{x:.2f}%"
                                    if isinstance(x, (int, float))
                                    else "N/A"
                                )
                            )
                        st.dataframe(puts, use_container_width=True)
                    else:
                        st.warning(
                            "Option chain data not available for the selected expiry date."
                        )
            else:
                st.info("Please select an expiry date to view the option chain.")

    with tab2:
        # About 탭
        st.header("About Option Pricing Models")

        st.markdown(
            r"""
        ### Black-Scholes Model
        
        The theoretical option price was calculated using the **Black-Scholes model**. The Black-Scholes model is the most widely used option pricing model and was developed by Fisher Black and Myron Scholes to derive European option prices based on Einstein's Brownian motion equations.
        
        The formula used is shown below:
        
        $$d_1 = \frac{\ln(S_0/K) + (r_f - y + 0.5 \sigma^2)\tau}{\sigma\sqrt{\tau}}$$
        
        $$d_2 = d_1 - \sigma\sqrt{\tau}$$
        
        **Call price:**
        
        $$C(S_0, \tau) = S_0 N(d_1)e^{-y\tau} - K e^{-r_f\tau}N(d_2)$$
        
        
        **Put price:**
        
        $$P(S_0, \tau) = K e^{-r_f\tau}N(-d_2) - S_0 N(-d_1)e^{-y\tau}$$
        
        *where,*
        - $S_0$ : Underlying Price
        - $K$ : Strike Price
        - $r_f$ : Risk-free rate
        - $y$ : Dividend yield
        - $τ$ : Time to maturity
        - $N(x)$ : Standard normal cumulative distribution function
        """
        )

        st.markdown(
            r"""
        ### Heston Model

        The app also supports a calibrated **Heston stochastic volatility model**. Unlike Black-Scholes, which assumes a single constant volatility until expiration, the Heston model treats variance itself as a random process. This makes it better suited for markets where options with different strikes and expirations trade at different implied volatilities.

        Under the Heston model, the underlying price and variance evolve together:

        $$dS_t = (r_f-y)S_tdt + \sqrt{v_t}S_tdW_t^S$$

        $$dv_t = \kappa(\theta - v_t)dt + \sigma_v\sqrt{v_t}dW_t^v$$

        $$dW_t^S dW_t^v = \rho dt$$

        *where,*
        - $S_t$ : Underlying price
        - $v_t$ : Instantaneous variance
        - $r_f$ : Risk-free rate
        - $y$ : Dividend yield
        - $\kappa$ : Speed of mean reversion in variance
        - $\theta$ : Long-run variance level
        - $\sigma_v$ : Volatility of volatility
        - $\rho$ : Correlation between price shocks and variance shocks
        - $v_0$ : Current variance

        **Why Heston can be more realistic**

        Black-Scholes assumes one volatility input, so it cannot naturally explain volatility smiles or skews. Heston allows volatility to move over time and allows price returns and volatility changes to be correlated. A negative $\rho$, which is common in equity markets, can produce the left-skew often seen in index and stock option surfaces.

        **How this app uses Heston**

        Select **Heston (calibrated)** in the calculator tab and use **Calibrate Heston Now** to estimate the five Heston parameters from liquid option-chain quotes. The selected **Expiry Date** is used as the calibration anchor, and **Expiry count** controls how many expirations starting from that anchor are included. Once calibration is complete, the option prices in **Option Prices** use the calibrated Heston model instead of Black-Scholes.

        The **Heston Calibration 3D** section in the Option Chain tab is optional. It visualizes the fitted Heston theoretical price surface and the model error against market quotes, but the 3D plot is not required for pricing.

        **Important limitations**

        Heston prices are only as good as the calibration data. Wide bid/ask spreads, stale last prices, low volume, low open interest, very short-dated options, or sparse strike coverage can produce unstable parameters. A lower RMSE or MAPE generally indicates a better fit to the selected quotes, but it does not guarantee predictive accuracy.

        In practice, Heston should be viewed as a richer theoretical pricing framework, not as a guaranteed fair value. It is most useful when compared with market prices, implied volatility surfaces, and liquidity conditions.
        """
        )

        st.markdown(
            r"""
        ### Option Greeks
        
        Option Greeks are key measures that assess an option's price sensitivity to factors like volatility and the price of the underlying asset. They are crucial for analyzing options portfolios and are widely used by investors to make informed trading decisions.
        
        **Delta:**
        
        Delta measures how much an option's price will change for every 1 dollar movement in the underlying asset. A Delta of 0.40 means the option price will move 0.40 dollar for each $1 change, and suggests a 40% chance the option will expire in the money (ITM).
        
        Call options have a Delta between 0.00 and 1.00, with at-the-money options near 0.50, increasing toward 1.00 as they move deeper ITM or approach expiration, and decreasing toward 0.00 if they are out-of-the-money.
        
        Put options have a Delta between 0.00 and –1.00, with at-the-money options near –0.50, decreasing toward –1.00 as they move deeper ITM or approach expiration, and approaching 0.00 if they are out-of-the-money.
        
        $$\text{Call: } \Delta_c = e^{-y\tau}N(d_1)$$
        
        $$\text{Put: } \Delta_p = e^{-y\tau}[N(d_1)-1]$$
        
        **Gamma:**
        
        Gamma measures the rate of change in an option's Delta for every $1 move in the underlying asset, much like acceleration compared to speed. As Delta increases with a stock price move, Gamma reflects how much Delta shifts.
        
        $$\Gamma = \frac{e^{-y\tau}}{S_0\sigma\sqrt{\tau}}N'(d_1)$$
        
        **Vega:**
        
        Vega measures the change in an option's price for a one-percentage-point change in the implied volatility of the underlying asset.
        
        $$\nu = S_0e^{-y\tau}N'(d_1)\sqrt{\tau}$$
        
        **Theta:**
        
        Theta measures the daily decrease in an option's price as it approaches expiration, reflecting time decay.
        
        $$\text{Call: } \theta_c = \frac{1}{T}\left(-\frac{S_0\sigma e^{-y\tau}}{2\sqrt{\tau}}N'(d_1) - r_fKe^{-r_f\tau}N(d_2) + yS_0e^{-y\tau}N(d_1)\right)$$
        
        $$\text{Put: } \theta_p = \frac{1}{T}\left(-\frac{S_0\sigma e^{-y\tau}}{2\sqrt{\tau}}N'(d_1) + r_fKe^{-r_f\tau}N(-d_2) - yS_0e^{-y\tau}N(-d_1)\right)$$
        
        **Rho:**
        
        Rho measures the change in an option's price for a one-percentage-point shift in interest rates.
        
        $$\text{Call: } \rho_c = K\tau e^{-r_f\tau}N(d_2)$$
        
        $$\text{Put: } \rho_p = -K\tau e^{-r_f\tau}N(-d_2)$$
        
        **Vanna:**
        
        Vanna (also known as DvegaDspot or DdeltaDvol) measures the rate of change of delta with respect to a change in volatility, or equivalently, the rate of change of vega with respect to a change in the underlying price. Vanna is a second-order Greek that helps traders understand how their delta hedges will change when volatility changes.
        
        $$\text{Vanna} = -e^{-y\tau}\frac{d_1}{\sigma}N'(d_1)$$
        
        Vanna is highest for at-the-money options with moderate time to expiration. Positive vanna means that as volatility increases, delta increases (becomes more positive). Vanna is the same for both calls and puts with the same strike and expiration.
        
        **Charm:**
        
        Charm (also known as delta decay) measures the instantaneous rate of change of delta over the passage of time. It tells option traders how much delta will change each day if all other factors remain constant. Charm helps traders maintain delta-neutral positions as time passes.
        
        $$\text{Call Charm} = -e^{-y\tau}\frac{N'(d_1)(2(r_f-y)\tau-d_2\sigma\sqrt{\tau})}{2\tau\sigma\sqrt{\tau}}$$
        
        $$\text{Put Charm} = -e^{-y\tau}\frac{N'(d_1)(2(r_f-y)\tau-d_2\sigma\sqrt{\tau})}{2\tau\sigma\sqrt{\tau}} - ye^{-y\tau}N(-d_1)$$
        
        Charm can be particularly significant for options close to expiration, helping traders understand how quickly delta changes as time runs out.
        """
        )

        st.markdown(
            """
        ### Option Strategies
        
        This calculator supports several option strategies:
        
        - **Single**: A basic long or short position in a call or put option.
        - **Covered**: Covered call (long stock + short call) or covered put (short stock + short put).
        - **Protective**: Protective put (long stock + long put) or protective call (short stock + long call).
        - **Spread**: Bull/bear spread using calls or puts with different strike prices.
        - **Straddle**: Long/short position in both a call and put with the same strike and expiration.
        - **Strangle**: Long/short position in both a call and put with different strikes but same expiration.
        - **Strip**: Long 1 call and 2 puts at the same strike (bearish strategy).
        - **Strap**: Long 2 calls and 1 put at the same strike (bullish strategy).
        - **Butterfly**: A three-leg strategy with limited risk and reward.
        - **Ladder**: A multi-leg strategy with strike prices at regular intervals.
        - **Jade Lizard**: Short put + short call spread (bullish strategy).
        - **Reverse Jade Lizard**: Long put spread + short call (bearish strategy).
        - **Condor**: A four-leg strategy with limited risk and reward.

        If you have any questions or suggestions, please contact: pmh621@naver.com 
        """
        )


if __name__ == "__main__":
    main()
