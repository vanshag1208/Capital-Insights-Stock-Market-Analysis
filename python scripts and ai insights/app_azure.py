import os
import streamlit as st
import pyodbc
import pandas as pd
from dotenv import load_dotenv
from google import genai

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()
 
DB_DRIVER = os.getenv("DB_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_UID = os.getenv("DB_UID")
DB_PWD = os.getenv("DB_PWD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ---------------------------
# 1. Gemini Client
# ---------------------------

client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------
# 2. SQL Server Connection
# ---------------------------

conn = pyodbc.connect(
    f"DRIVER={{{DB_DRIVER}}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_DATABASE};"
    f"UID={DB_UID};"
    f"PWD={DB_PWD};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
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