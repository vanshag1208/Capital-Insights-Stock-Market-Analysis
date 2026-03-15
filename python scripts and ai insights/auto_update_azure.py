import pandas as pd
import yfinance as yf
import pyodbc
from datetime import datetime, timedelta
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
# 1️⃣ READ MASTER CSV
# ===============================
master = pd.read_csv("stock_master_full.csv")
yf_symbols = master["YF_SYMBOL"].dropna().tolist()

# ===============================
# 2️⃣ SQL CONNECTION
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

# (Speed improvement – optional but safe)
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
# 4️⃣ GET MAX TRADE DATE
# ===============================
def get_max_trade_date(symbol):
    cursor.execute(
        "SELECT MAX(TradeDate) FROM StockPriceDaily WHERE Symbol = ?",
        symbol
    )
    return cursor.fetchone()[0]

today = datetime.today().date()

# ===============================
# 5️⃣ MAIN LOOP
# ===============================
for yf_sym in yf_symbols:
    symbol = yf_sym.replace(".NS", "")
    print(f"\nProcessing: {symbol}")

    # ---- Get last date from SQL
    try:
        max_date = get_max_trade_date(symbol)
    except Exception as e:
        print("❌ Max date fetch error:", symbol, e)
        continue

    # ---- Decide start date
    if max_date:
        start_date = max_date + timedelta(days=1)
    else:
        start_date = today - timedelta(days=1825)  # fallback: 5 years

    if start_date > today:
        print("✔ Already up to date")
        continue

    print(f"Fetching from {start_date} to {today}")

    # ---- Fetch from Yahoo
    data = yf.download(
        yf_sym,
        start=start_date.strftime("%Y-%m-%d"),
        end=(today + timedelta(days=1)).strftime("%Y-%m-%d"),
        auto_adjust=False,
        progress=True
    )

    if data.empty:
        print("⚠ No Yahoo data")
        continue

    # ---- Reset index
    data.reset_index(inplace=True)

    # ---- FIX: Flatten MultiIndex columns (VERY IMPORTANT)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # ---- Ensure Date column is datetime
    data["Date"] = pd.to_datetime(data["Date"])

    inserted = 0

    # ===============================
    # 6️⃣ INSERT LOOP
    # ===============================
    for _, row in data.iterrows():
        trade_date = None
        try:
            trade_date = pd.to_datetime(row["Date"]).to_pydatetime()

            cursor.execute(
                insert_sql,
                trade_date,
                symbol,
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                float(row["Adj Close"]),
                int(row["Volume"])
            )

            inserted += 1

        except Exception as e:
            # Duplicate / constraint / datatype errors visible
            print("Insert error:", symbol, trade_date, e)

    conn.commit()
    print(f"✅ Inserted {inserted} rows for {symbol}")

# ===============================
# 7️⃣ CLOSE CONNECTION
# ===============================
cursor.close()
conn.close()

print("\n🎯 ALL DATA INSERTED SUCCESSFULLY")
