import pandas as pd
import yfinance as yf
import pyodbc
import os
from dotenv import load_dotenv


# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()
 
DB_DRIVER = os.getenv("DB_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_UID = os.getenv("DB_UID")
DB_PWD = os.getenv("DB_PWD")

# ===============================
# 1️⃣ READ CSV
# ===============================
master = pd.read_csv("stock_master_full.csv")
yf_symbols = master["YF_SYMBOL"].dropna().tolist()

# ===============================
# 2️⃣ AZURE SQL CONNECTION
# ===============================
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
cursor.fast_executemany = True

# ===============================
# 3️⃣ INSERT QUERY
# ===============================
insert_sql = """
INSERT INTO StockPriceDaily
(TradeDate, Symbol, OpenPrice, HighPrice, LowPrice, ClosePrice, AdjClose, Volume)
VALUES (?,?,?,?,?,?,?,?)
"""

# ===============================
# 4️⃣ FETCH + BULK INSERT
# ===============================
for yf_sym in yf_symbols:

    print("Fetching:", yf_sym)

    data = yf.download(
        yf_sym,
        period="5y",
        interval="1d",
        auto_adjust=False
    )

    if data.empty:
        print("No data:", yf_sym)
        continue

    data.reset_index(inplace=True)

    symbol = yf_sym.replace(".NS", "")
    data["Symbol"] = symbol

    rows = []

    for row in data.itertuples(index=False):
        rows.append((
            row[0],              # TradeDate
            row[7],              # Symbol
            float(row[1]),       # Open
            float(row[2]),       # High
            float(row[3]),       # Low
            float(row[4]),       # Close
            float(row[5]),       # Adj Close
            int(row[6])          # Volume
        ))

    cursor.executemany(insert_sql, rows)
    conn.commit()

    print("Inserted:", yf_sym)

cursor.close()
conn.close()

print("✅ ALL DONE")