import os
import streamlit as st
import pyodbc
import pandas as pd
from dotenv import load_dotenv
from google import genai
import plotly.graph_objects as go
from datetime import date, timedelta

# ---------------------------
# Page Config
# ---------------------------

st.set_page_config(
    page_title="Capital Insights",
    page_icon="📈",
    layout="wide"
)

# ---------------------------
# Load Environment Variables
# ---------------------------

load_dotenv()
 
DB_DRIVER = os.getenv("DB_DRIVER")
SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------------------------
# Gemini Client
# ---------------------------

client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------
# SQL Server Connection
# ---------------------------

conn = pyodbc.connect(
    f"DRIVER={{{DB_DRIVER}}};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"Trusted_Connection=yes;"
)

cursor = conn.cursor()

# ---------------------------
# Title
# ---------------------------

st.title("📊 Capital Insights - AI Stock Analytics")

investment_horizon = None
analyze_horizon = False
analyze_date = False

# ---------------------------
# Tabs
# ---------------------------

tab1, tab2, tab3 = st.tabs([
    "📊 Power BI Dashboard",
    "📈 Symbol + Horizon",
    "📅 Symbol + Date Range"
])

# ---------------------------
# TAB 1 : POWER BI
# ---------------------------

with tab1:

    st.subheader("Power BI Dashboard")

    st.components.v1.iframe(
        "https://app.powerbi.com/reportEmbed?reportId=9d605834-9cb7-4c0e-81d8-26f947ee4187&autoAuth=true&ctid=7088c9fc-7349-4b24-afd1-a7200e6fc029",
        height=800
    )

 
# ---------------------------
# TAB 2 : SYMBOL + HORIZON
# ---------------------------

with tab2:

    st.header("Horizon Filters")

    cursor.execute("SELECT DISTINCT Symbol FROM StockPriceDaily")
    symbols = [row[0] for row in cursor.fetchall()]

    symbol = st.selectbox("Select Stock", symbols)

    investment_horizon = st.selectbox(
        "Investment Horizon",
        ["Short Term", "Medium Term", "Long Term"]
    )

    analyze_horizon = st.button("Analyze Horizon", key="horizon_btn")

    today = date.today()

    if investment_horizon == "Short Term":
        start_date = today - timedelta(days=365)

    elif investment_horizon == "Medium Term":
        start_date = today - timedelta(days=365*3)

    else:
        start_date = today - timedelta(days=365*5)

    end_date = today
# ---------------------------
# Analysis
# ---------------------------

    if analyze_horizon:

        query = """
        SELECT 
        TradeDate,
        Symbol,
        OpenPrice,
        HighPrice,
        LowPrice,
        ClosePrice,
        Volume
        FROM StockPriceDaily
        WHERE Symbol = ?
        AND TradeDate BETWEEN ? AND ?
        ORDER BY TradeDate
        """

        cursor.execute(query, symbol, start_date, end_date)
        rows = cursor.fetchall()


        if not rows:
            st.error("No data available")

        else:

            columns = [column[0] for column in cursor.description]
            df = pd.DataFrame.from_records(rows, columns=columns)

            df["TradeDate"] = pd.to_datetime(df["TradeDate"])

            numeric_cols = [
                "OpenPrice",
                "HighPrice",
                "LowPrice",
                "ClosePrice",
                "Volume"
            ]

            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)

            if investment_horizon == "Short Term":
                lookback = 30
            elif investment_horizon == "Medium Term":
                lookback = 90
            else:
                lookback = 180

            df["MA50"] = df["ClosePrice"].rolling(50).mean()
            df["MA200"] = df["ClosePrice"].rolling(200).mean()

            df["Return"] = df["ClosePrice"].pct_change()

            volatility = df["Return"].std() * (252 ** 0.5)

            support = df["LowPrice"].tail(lookback).min()
            resistance = df["HighPrice"].tail(lookback).max()

            current_price = df["ClosePrice"].iloc[-1]

            delta = df["ClosePrice"].diff()

            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

            rs = gain / loss
            df["RSI"] = 100 - (100 / (1 + rs))

            rsi = df["RSI"].iloc[-1]

            exp1 = df["ClosePrice"].ewm(span=12, adjust=False).mean()
            exp2 = df["ClosePrice"].ewm(span=26, adjust=False).mean()

            df["MACD"] = exp1 - exp2
            df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

            macd = df["MACD"].iloc[-1]

            momentum = df["ClosePrice"].pct_change(10).iloc[-1]

            ma50 = df["MA50"].iloc[-1]
            ma200 = df["MA200"].iloc[-1]

            if ma50 > ma200:
                signal = "BUY"
            elif ma50 < ma200:
                signal = "SELL"
            else:
                signal = "HOLD"

            rating_score = 0

            if ma50 > ma200:
                rating_score += 1
            if current_price <= support * 1.05:
                rating_score += 1
            if volatility < 0.30:
                rating_score += 1

            if rating_score == 3:
                rating = "Strong Buy ⭐⭐⭐⭐"
            elif rating_score == 2:
                rating = "Buy ⭐⭐⭐"
            elif rating_score == 1:
                rating = "Hold ⭐⭐"
            else:
                rating = "Avoid ⭐"

            st.subheader("Key Metrics")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Current Price", round(current_price, 2))
            col2.metric("Support", round(support, 2))
            col3.metric("Resistance", round(resistance, 2))
            col4.metric("Volatility", round(volatility, 4))

            st.subheader("Investment Signals")

            col1, col2, col3 = st.columns(3)

            col1.metric("Signal", signal)
            col2.metric("Rating", rating)
            col3.metric("RSI", round(rsi, 2))

            # ---------------------------
            # Price Chart
            # ---------------------------

            st.subheader("Price Trend")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df["TradeDate"],
                y=df["ClosePrice"],
                mode="lines",
                name="Close Price"
            ))

            fig.add_trace(go.Scatter(
                x=df["TradeDate"],
                y=df["MA50"],
                mode="lines",
                name="50 MA"
            ))

            fig.add_trace(go.Scatter(
                x=df["TradeDate"],
                y=df["MA200"],
                mode="lines",
                name="200 MA"
            ))

            fig.update_layout(
                template="plotly_dark",
                height=500,
                hovermode="x unified"
            )

            st.plotly_chart(fig, use_container_width=True)

            # ---------------------------
            # Volume Chart
            # ---------------------------

            colors = [
                "#00FF9C" if df["ClosePrice"].iloc[i] >= df["OpenPrice"].iloc[i]
                else "#FF4B4B"
                for i in range(len(df))
            ]

            volume = go.Figure()

            volume.add_trace(go.Bar(
                x=df["TradeDate"],
                y=df["Volume"],
                marker_color=colors
            ))

            volume.update_layout(
                template="plotly_dark",
                height=300
            )

            st.plotly_chart(volume, use_container_width=True)

            # ---------------------------
            # AI PROMPTS
            # ---------------------------

            recent_data = df.tail(60)

            stock_text = recent_data[[
                "TradeDate",
                "OpenPrice",
                "HighPrice",
                "LowPrice",
                "ClosePrice",
                "Volume"
            ]].to_string(index=False)


            # Horizon Prompt
            prompt = f"""
    You are a professional quantitative stock analyst and financial advisor.

    Analyze the stock data below and generate a structured investment report.

    The report must be easy to understand for beginner investors and should avoid long paragraphs.

    Use tables wherever possible.

    Also calculate an **AI Buy/Sell Confidence Meter out of 100%** that indicates how attractive the stock currently is.

    The analysis must classify insights into **three investment horizons**:

    • **Short Term → based on the stock performance over the past 1 year**
    • **Medium Term → based on the stock performance over the past 3 years**
    • **Long Term → based on the stock performance over the past 5 years**

    Interpret trends, risks, and opportunities separately for each horizon.

    ---

    STOCK DATA

    Ticker: {symbol}

    Current Price: {current_price}

    Support Level: {support}

    Resistance Level: {resistance}

    Volatility: {volatility}

    Technical Indicators

    RSI: {rsi}

    MACD: {macd}

    50 Day Moving Average: {ma50}

    200 Day Moving Average: {ma200}

    System Signal: {signal}

    Investment Rating: {rating}

    Recent Market Data:
    {stock_text}

    ---

    OUTPUT STRUCTURE

    ---

    # 📊 STOCK SUMMARY

    | Metric        | Value | Meaning |
    | ------------- | ----- | ------- |
    | Current Price |       |         |
    | Support       |       |         |
    | Resistance    |       |         |
    | MA50          |       |         |
    | MA200         |       |         |
    | ATR           |       |         |

    Explain in simple terms if the stock is trending **up, down, or sideways**.

    ---

    # 📈 MULTI-HORIZON TREND ANALYSIS

    Evaluate the stock across three investment horizons.

    | Horizon     | Data Window  | Trend | Explanation |
    | ----------- | ------------ | ----- | ----------- |
    | Short Term  | Past 1 Year  |       |             |
    | Medium Term | Past 3 Years |       |             |
    | Long Term   | Past 5 Years |       |             |

    Explain how the stock behaves differently across these timeframes.

    ---

    # 📉 TECHNICAL INDICATORS

    | Indicator | Value | Signal | Meaning |
    | --------- | ----- | ------ | ------- |
    | RSI       |       |        |         |
    | MACD      |       |        |         |
    | Momentum  |       |        |         |

    Explain whether buyers or sellers currently dominate the market.

    ---

    # ⚠️ RISK ANALYSIS

    | Risk Type           | Risk Level | Explanation |
    | ------------------- | ---------- | ----------- |
    | Downside Risk       |            |             |
    | Volatility Risk     |            |             |
    | Trend Reversal Risk |            |             |

    Explain which investment horizon carries the highest risk.

    ---

    # 🎯 PRICE SCENARIOS

    Provide scenario projections.

    | Scenario     | Target Price | Probability |
    | ------------ | ------------ | ----------- |
    | Bullish Case |              |             |
    | Neutral Case |              |             |
    | Bearish Case |              |             |

    Explain which horizon each scenario is most relevant for.

    ---

    # 📊 STOCK SCORECARD

    Score each factor from **0-10**

    | Factor          | Score |
    | --------------- | ----- |
    | Trend Strength  |       |
    | Momentum        |       |
    | Risk Level      |       |
    | Technical Setup |       |

    Total Score (0-40)

    Interpretation

    0-10 → Strong Sell
    11-20 → Sell
    21-30 → Hold
    31-40 → Buy

    ---

    # 📊 CONFIDENCE CALCULATION MODEL

    Calculate the Buy Confidence using the following weighted scoring model.

    | Factor               | Condition              | Score |
    | -------------------- | ---------------------- | ----- |
    | Trend                | MA50 > MA200           | +20   |
    | Momentum             | RSI between 50 and 70  | +15   |
    | Oversold Opportunity | RSI < 40               | +10   |
    | MACD                 | MACD above signal line | +15   |
    | Price Position       | Price near support     | +15   |
    | Risk                 | Low volatility         | +10   |
    | Resistance Risk      | Price near resistance  | -10   |
    | Overbought Risk      | RSI > 70               | -10   |
    | Downtrend Risk       | MA50 < MA200           | -20   |

    Start from a base score of **50**.

    Final Buy Confidence = base score + total factor scores.

    Clamp the final value between **0 and 100**.

    Sell Pressure = **100 - Buy Confidence**.

    ---

    # 🎯 AI BUY/SELL CONFIDENCE METER

    | Meter          | Percentage | Meaning |
    | -------------- | ---------- | ------- |
    | Buy Confidence |            |         |
    | Sell Pressure  |            |         |

    Interpretation:

    0-30% → Strong Sell Zone
    31-45% → Sell Zone
    46-55% → Neutral Zone
    56-70% → Buy Zone
    71-100% → Strong Buy Zone

    ---

    # 💰 INVESTMENT DECISION

    | Metric               | Result            |
    | -------------------- | ----------------- |
    | AI Signal            |                   |
    | Quant Score          |                   |
    | Buy Confidence       |                   |
    | Risk/Reward          |                   |
    | Final Recommendation | BUY / HOLD / SELL |
    | Confidence Level     | %                 |

    Also explain which **investment horizon (short / medium / long)** the recommendation applies to.

    ---

    # 📊 RECOMMENDED CHARTS

    | Chart                       | Purpose                       |
    | --------------------------- | ----------------------------- |
    | Price vs MA50 & MA200       | Identify trend direction      |
    | RSI Indicator               | Identify overbought/oversold  |
    | Support & Resistance Levels | Identify key price zones      |
    | Volatility Chart            | Understand price fluctuations |
    | AI Confidence Meter         | Show buy/sell probability     |

    ---

    # 🧠 SIMPLE EXPLANATION

    Explain the stock using very simple language.

    Example:

    "This stock is like a car driving on a road. If it stays above its moving averages, the road is going uphill. If it falls below them, the road is going downhill."

    ---

    # 🏁 FINAL VERDICT

    Give the final conclusion in bullet points.

    • Should someone invest now?
    • Which horizon is most attractive? (Short / Medium / Long)
    • Should investors wait for a better entry price?
    """

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            st.subheader("🤖 AI Market Insight")

            st.markdown(response.text)

# ---------------------------
# TAB 3 : DATE RANGE
# ---------------------------

with tab3:

    st.header("Date Range Filters")

    cursor.execute("SELECT DISTINCT Symbol FROM StockPriceDaily")
    symbols = [row[0] for row in cursor.fetchall()]

    symbol = st.selectbox("Select Stock ", symbols)

    today = date.today()

    default_start = today - timedelta(days=365)

    start_date = st.date_input("Start Date", default_start)
    end_date = st.date_input("End Date", today)

    analyze_date = st.button("Analyze Date Range", key="date_btn")

    # ---------------------------
    # Analysis
    # ---------------------------

    if analyze_date:

        query = """
        SELECT 
        TradeDate,
        Symbol,
        OpenPrice,
        HighPrice,
        LowPrice,
        ClosePrice,
        Volume
        FROM StockPriceDaily
        WHERE Symbol = ?
        AND TradeDate BETWEEN ? AND ?
        ORDER BY TradeDate
        """

        cursor.execute(query, symbol, start_date, end_date)
        rows = cursor.fetchall()


        if not rows:
            st.error("No data available")

        else:

            columns = [column[0] for column in cursor.description]
            df = pd.DataFrame.from_records(rows, columns=columns)

            df["TradeDate"] = pd.to_datetime(df["TradeDate"])

            numeric_cols = [
                "OpenPrice",
                "HighPrice",
                "LowPrice",
                "ClosePrice",
                "Volume"
            ]

            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)

            if investment_horizon == "Short Term":
                lookback = 30
            elif investment_horizon == "Medium Term":
                lookback = 90
            else:
                lookback = 180

            df["MA50"] = df["ClosePrice"].rolling(50).mean()
            df["MA200"] = df["ClosePrice"].rolling(200).mean()

            df["Return"] = df["ClosePrice"].pct_change()

            volatility = df["Return"].std() * (252 ** 0.5)

            support = df["LowPrice"].tail(lookback).min()
            resistance = df["HighPrice"].tail(lookback).max()

            current_price = df["ClosePrice"].iloc[-1]

            delta = df["ClosePrice"].diff()

            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

            rs = gain / loss
            df["RSI"] = 100 - (100 / (1 + rs))

            rsi = df["RSI"].iloc[-1]

            exp1 = df["ClosePrice"].ewm(span=12, adjust=False).mean()
            exp2 = df["ClosePrice"].ewm(span=26, adjust=False).mean()

            df["MACD"] = exp1 - exp2
            df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

            macd = df["MACD"].iloc[-1]

            momentum = df["ClosePrice"].pct_change(10).iloc[-1]

            ma50 = df["MA50"].iloc[-1]
            ma200 = df["MA200"].iloc[-1]

            if ma50 > ma200:
                signal = "BUY"
            elif ma50 < ma200:
                signal = "SELL"
            else:
                signal = "HOLD"

            rating_score = 0

            if ma50 > ma200:
                rating_score += 1
            if current_price <= support * 1.05:
                rating_score += 1
            if volatility < 0.30:
                rating_score += 1

            if rating_score == 3:
                rating = "Strong Buy ⭐⭐⭐⭐"
            elif rating_score == 2:
                rating = "Buy ⭐⭐⭐"
            elif rating_score == 1:
                rating = "Hold ⭐⭐"
            else:
                rating = "Avoid ⭐"

            st.subheader("Key Metrics")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Current Price", round(current_price, 2))
            col2.metric("Support", round(support, 2))
            col3.metric("Resistance", round(resistance, 2))
            col4.metric("Volatility", round(volatility, 4))

            st.subheader("Investment Signals")

            col1, col2, col3 = st.columns(3)

            col1.metric("Signal", signal)
            col2.metric("Rating", rating)
            col3.metric("RSI", round(rsi, 2))

            # ---------------------------
            # Price Chart
            # ---------------------------

            st.subheader("Price Trend")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df["TradeDate"],
                y=df["ClosePrice"],
                mode="lines",
                name="Close Price"
            ))

            fig.add_trace(go.Scatter(
                x=df["TradeDate"],
                y=df["MA50"],
                mode="lines",
                name="50 MA"
            ))

            fig.add_trace(go.Scatter(
                x=df["TradeDate"],
                y=df["MA200"],
                mode="lines",
                name="200 MA"
            ))

            fig.update_layout(
                template="plotly_dark",
                height=500,
                hovermode="x unified"
            )

            st.plotly_chart(fig, use_container_width=True)

            # ---------------------------
            # Volume Chart
            # ---------------------------

            colors = [
                "#00FF9C" if df["ClosePrice"].iloc[i] >= df["OpenPrice"].iloc[i]
                else "#FF4B4B"
                for i in range(len(df))
            ]

            volume = go.Figure()

            volume.add_trace(go.Bar(
                x=df["TradeDate"],
                y=df["Volume"],
                marker_color=colors
            ))

            volume.update_layout(
                template="plotly_dark",
                height=300
            )

            st.plotly_chart(volume, use_container_width=True)

            # ---------------------------
            # AI PROMPTS
            # ---------------------------

            recent_data = df.tail(60)

            stock_text = recent_data[[
                "TradeDate",
                "OpenPrice",
                "HighPrice",
                "LowPrice",
                "ClosePrice",
                "Volume"
            ]].to_string(index=False)

            
            # Date Range Prompt
            prompt = f"""
    You are a professional quantitative stock analyst and financial advisor.

    Analyze the stock data below and generate a structured investment report.

    The report must be easy to understand for beginner investors and should avoid long paragraphs.

    Use tables wherever possible.

    Also calculate an **AI Buy/Sell Confidence Meter out of 100%** that indicates how attractive the stock currently is.

    ---

    STOCK DATA

    Ticker: {symbol}

    Current Price: {current_price}

    Support Level: {support}

    Resistance Level: {resistance}

    Volatility: {volatility}

    Technical Indicators

    RSI: {rsi}

    MACD: {macd}

    50 Day Moving Average: {ma50}

    200 Day Moving Average: {ma200}

    System Signal: {signal}

    Investment Rating: {rating}

    Recent Market Data:
    {stock_text}

    ---

    OUTPUT STRUCTURE

    ---

    # 📊 STOCK SUMMARY

    | Metric        | Value | Meaning |
    | ------------- | ----- | ------- |
    | Current Price |       |         |
    | Support       |       |         |
    | Resistance    |       |         |
    | MA50          |       |         |
    | MA200         |       |         |
    | ATR           |       |         |

    Explain in simple terms if the stock is trending **up, down, or sideways**.

    ---

    # 📈 TREND ANALYSIS

    | Trend Direction | Explanation |
    | --------------- | ----------- |
    | Overall Trend   |             |

    Explain whether the stock is trading **above or below its moving averages** and what this indicates about the market trend.

    ---

    # 📉 TECHNICAL INDICATORS

    | Indicator | Value | Signal | Meaning |
    | --------- | ----- | ------ | ------- |
    | RSI       |       |        |         |
    | MACD      |       |        |         |
    | Momentum  |       |        |         |

    Explain whether buyers or sellers currently dominate the market.

    ---

    # ⚠️ RISK ANALYSIS

    | Risk Type           | Risk Level | Explanation |
    | ------------------- | ---------- | ----------- |
    | Downside Risk       |            |             |
    | Volatility Risk     |            |             |
    | Trend Reversal Risk |            |             |

    ---

    # 🎯 PRICE SCENARIOS

    | Scenario     | Target Price | Probability |
    | ------------ | ------------ | ----------- |
    | Bullish Case |              |             |
    | Neutral Case |              |             |
    | Bearish Case |              |             |

    ---

    # 📊 STOCK SCORECARD

    Score each factor from **0-10**

    | Factor          | Score |
    | --------------- | ----- |
    | Trend Strength  |       |
    | Momentum        |       |
    | Risk Level      |       |
    | Technical Setup |       |

    Total Score (0-40)

    Interpretation

    0-10 → Strong Sell
    11-20 → Sell
    21-30 → Hold
    31-40 → Buy

    ---

    # 📊 CONFIDENCE CALCULATION MODEL

    Calculate the Buy Confidence using the following weighted scoring model.

    | Factor               | Condition              | Score |
    | -------------------- | ---------------------- | ----- |
    | Trend                | MA50 > MA200           | +20   |
    | Momentum             | RSI between 50 and 70  | +15   |
    | Oversold Opportunity | RSI < 40               | +10   |
    | MACD                 | MACD above signal line | +15   |
    | Price Position       | Price near support     | +15   |
    | Risk                 | Low volatility         | +10   |
    | Resistance Risk      | Price near resistance  | -10   |
    | Overbought Risk      | RSI > 70               | -10   |
    | Downtrend Risk       | MA50 < MA200           | -20   |

    Start from a base score of **50**.

    Final Buy Confidence = base score + total factor scores.

    Clamp the final value between **0 and 100**.

    Sell Pressure = **100 - Buy Confidence**.

    ---

    # 🎯 AI BUY/SELL CONFIDENCE METER

    | Meter          | Percentage | Meaning |
    | -------------- | ---------- | ------- |
    | Buy Confidence |            |         |
    | Sell Pressure  |            |         |

    Interpretation:

    0-30% → Strong Sell Zone
    31-45% → Sell Zone
    46-55% → Neutral Zone
    56-70% → Buy Zone
    71-100% → Strong Buy Zone

    ---

    # 💰 INVESTMENT DECISION

    | Metric               | Result            |
    | -------------------- | ----------------- |
    | AI Signal            |                   |
    | Quant Score          |                   |
    | Buy Confidence       |                   |
    | Risk/Reward          |                   |
    | Final Recommendation | BUY / HOLD / SELL |
    | Confidence Level     | %                 |

    ---

    # 📊 RECOMMENDED CHARTS

    | Chart                       | Purpose                       |
    | --------------------------- | ----------------------------- |
    | Price vs MA50 & MA200       | Identify trend direction      |
    | RSI Indicator               | Identify overbought/oversold  |
    | Support & Resistance Levels | Identify key price zones      |
    | Volatility Chart            | Understand price fluctuations |
    | AI Confidence Meter         | Show buy/sell probability     |

    ---

    # 🧠 SIMPLE EXPLANATION

    Explain the stock using very simple language.

    Example:

    "This stock is like a car driving on a road. If it stays above its moving averages, the road is going uphill. If it falls below them, the road is going downhill."

    ---

    # 🏁 FINAL VERDICT

    Give the final conclusion in bullet points.

    • Should someone invest now?
    • Should they wait for a better entry?
    • What price level might be safer to buy?




    ye hh long term short term wala hatake normal jaisa hame cchaiye tha uska prompt
    """

            
        
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            st.subheader("🤖 AI Market Insight")

            st.markdown(response.text)



