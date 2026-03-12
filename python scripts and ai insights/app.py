import streamlit as st
import pyodbc
import pandas as pd
from google import genai

# ---------------------------
# 1. Gemini Client
# ---------------------------
client = genai.Client(api_key="YOUR_API_KEY_HERE")

# ---------------------------
# 2. SQL Server Connection
# ---------------------------
conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=VANSHPC\SQLEXPRESS02;"
    r"DATABASE=StockMarket;"
    r"Trusted_Connection=yes;"
)

cursor = conn.cursor()

st.title("AI Stock Market Analyzer")

# ---------------------------
# 3. Fetch Symbols
# ---------------------------
cursor.execute("SELECT DISTINCT Symbol FROM StockPriceDaily")
symbols = [row[0] for row in cursor.fetchall()]

# ---------------------------
# 4. Selectbox for User Input
# ---------------------------
symbol = st.selectbox("Select Stock Symbol", symbols)

# ---------------------------
# 5. Analyze Button
# ---------------------------
if st.button("Analyze Stock"):

    query = """
    SELECT TOP 10
    TradeDate,
    Symbol,
    OpenPrice,
    HighPrice,
    LowPrice,
    ClosePrice,
    Volume
    FROM StockPriceDaily
    WHERE Symbol = ?
    ORDER BY TradeDate DESC
    """

    cursor.execute(query, symbol)
    rows = cursor.fetchall()

    if not rows:
        st.error("Stock not found in database")

    else:
        columns = [column[0] for column in cursor.description]
        df = pd.DataFrame.from_records(rows, columns=columns)

        st.subheader("Stock Data")
        st.dataframe(df)

        stock_text = df.to_string(index=False)

        prompt = f"""
        You are a financial analyst.

        Analyze the following stock OHLCV data.

        Provide:
        1. Trend
        2. Volatility
        3. Short insight

        Stock Data:
        {stock_text}
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        st.subheader("AI Market Insight")
        st.write(response.text)