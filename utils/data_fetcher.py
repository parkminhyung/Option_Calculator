import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime


def fetch_data(ticker):
    """주식 정보 및 옵션 체인 가져오기"""
    try:
        stock = yf.Ticker(ticker)
        stock_info = stock.info

        underlying_price = stock_info.get("currentPrice", None)
        if underlying_price is None:
            underlying_price = stock_info.get("regularMarketPrice", None)

        try:
            rf = round(yf.Ticker("^TNX").history(period="1d").iloc[0, 3], 2)
        except:
            rf = 3.95

        raw_dividend_yield = stock_info.get("dividendYield", 0.0) or 0.0
        dividend_yield = (
            raw_dividend_yield * 100
            if abs(raw_dividend_yield) <= 1
            else raw_dividend_yield
        )

        open_price = stock_info.get("open", None)
        high = stock_info.get("dayHigh", None)
        low = stock_info.get("dayLow", None)

        previous_close = stock_info.get("previousClose", None)
        if previous_close and underlying_price:
            chg = round(((underlying_price / previous_close) - 1) * 100, 3)
        else:
            chg = 0.0

        name = stock_info.get("shortName", "N/A")
        sector = stock_info.get("sector", "N/A")

        expiry_dates = stock.options

        try:
            stock_data = yf.download(ticker, period="1y", progress=False)
            close_col = "Close"
            stock_data["Returns"] = np.log(
                stock_data[close_col] / stock_data[close_col].shift(1)
            )
            stock_data.dropna(inplace=True)
            daily_volatility = stock_data["Returns"].std()
            annual_volatility = daily_volatility * np.sqrt(252)
            vol = round(annual_volatility * 100, 2)
        except Exception as e:
            st.warning(f"Volatility calculation warning: {e}")
            vol = 30.0

        return {
            "underlying_price": underlying_price,
            "rf": rf,
            "dividend_yield": dividend_yield,
            "expiry_dates": expiry_dates,
            "open_price": open_price,
            "high": high,
            "low": low,
            "chg": chg,
            "name": name,
            "sector": sector,
            "vol": vol,
        }
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None


def get_option_chain(ticker, expiry_date):
    """특정 만기일에 대한 옵션 체인 가져오기"""
    try:
        stock = yf.Ticker(ticker)
        calls = stock.option_chain(expiry_date).calls
        puts = stock.option_chain(expiry_date).puts

        calls["type"] = "CALL"
        puts["type"] = "PUT"

        return calls, puts
    except Exception as e:
        st.error(f"Error fetching option chain: {e}")
        return None, None
