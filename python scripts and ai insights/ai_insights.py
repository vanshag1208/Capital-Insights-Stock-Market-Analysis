import os
import pyodbc
import pandas as pd
from dotenv import load_dotenv
from google import genai


# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()
 
DB_DRIVER = os.getenv("DB_DRIVER")
SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
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
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"Trusted_Connection=yes;"
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