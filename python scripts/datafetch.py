import pandas as pd
import yfinance as yf
import pyodbc

# ===============================
# 1️⃣ READ STOCK MASTER CSV
# ===============================
master = pd.read_csv("C:\\Users\\vansh\\Downloads\\Capital Insights - Stock Market Analysis\\data\\stock_master_full.csv")

yf_symbols = master["YF_SYMBOL"].dropna().tolist()
# yf_symbols = yf_symbols[:1]   


# ===============================
# 2️⃣ SQL SERVER CONNECTION
# ===============================
conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=VANSHPC\SQLEXPRESS02;"
    r"DATABASE=StockMarket;"
    r"Trusted_Connection=yes;"
)
cursor = conn.cursor()


# ===============================
# 3️⃣ INSERT QUERY
# ===============================
insert_sql = """
INSERT INTO StockPriceDaily
(TradeDate, Symbol, OpenPrice, HighPrice, LowPrice, ClosePrice, AdjClose, Volume)
VALUES (?,?,?,?,?,?,?,?)
"""


# ===============================
# 4️⃣ FETCH + INSERT (POSITION BASED)
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

    # Date index → column
    data.reset_index(inplace=True)

    # Add Symbol column at the END
    symbol_value = yf_sym.replace(".NS", "")
    data["Symbol"] = symbol_value

    # Columns order will be:
    # 0 Date | 1 Open | 2 High | 3 Low | 4 Close | 5 Adj Close | 6 Volume | 7 Symbol

    for row in data.itertuples(index=False):
        cursor.execute(
            insert_sql,
            row[0],        # Date
            row[7],        # Symbol  ✅ FIXED
            float(row[1]), # Open
            float(row[2]), # High
            float(row[3]), # Low
            float(row[4]), # Close
            float(row[5]), # Adj Close
            int(row[6])    # Volume
        )

    conn.commit()
    print("Inserted:", yf_sym)


# ===============================
# 5️⃣ CLOSE CONNECTION
# ===============================
cursor.close()
conn.close()

print("✅ ALL DONE SUCCESSFULLY")
