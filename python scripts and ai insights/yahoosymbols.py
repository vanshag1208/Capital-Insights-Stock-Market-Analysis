import pandas as pd

# Step 1: NSE master list load
url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
df = pd.read_csv(url)

# Step 2: .NS Yahoo format column add
df["YF_SYMBOL"] = df["SYMBOL"] + ".NS"

# Step 3: Save full file including all details + .NS column
df.to_csv("stock_master_full.csv", index=False)

print(df.head(10))
