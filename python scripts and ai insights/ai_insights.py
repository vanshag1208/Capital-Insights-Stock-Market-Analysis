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

# ---------------------------
# 2. Show Available Symbols
# ---------------------------
cursor.execute("SELECT DISTINCT Symbol FROM StockPriceDaily")

symbols = [row[0] for row in cursor.fetchall()]

print("\nAvailable Stocks:")
print(symbols[:30])

symbol = input("\nEnter Stock Symbol: ").upper().strip()

# ---------------------------
# 3. Query Stock Data
# ---------------------------
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
WHERE Symbol LIKE ?
ORDER BY TradeDate DESC
"""

cursor.execute(query, f"%{symbol}%")

rows = cursor.fetchall()

if not rows:
    print("Stock not found in database")
    exit()

# column names extract
columns = [column[0] for column in cursor.description]

# dataframe create
df = pd.DataFrame.from_records(rows, columns=columns)

stock_text = df.to_string(index=False)

# ---------------------------
# 4. Prompt
# ---------------------------
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

# ---------------------------
# 5. Gemini API Call
# ---------------------------
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

print("\nAI Market Insight:\n")
print(response.text)