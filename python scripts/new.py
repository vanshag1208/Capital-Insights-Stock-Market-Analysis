import yfinance as yf

print(
    yf.download(
        "PAYTM.NS",
        start="2025-12-16",
        end="2026-01-02"
    )
)
