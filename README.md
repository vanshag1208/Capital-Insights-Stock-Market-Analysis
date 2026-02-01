# 📈 Capital Insights – Stock Market Analysis Platform

Capital Insights is an **end-to-end stock market analytics project designed to analyze, process, and visualize large-scale historical stock data.  
The project focuses on transforming raw market data into actionable investment insights using Python, SQL Server, and Power BI.


## 🧠 Project Objective
- Analyze historical stock market data at scale  
- Track price movements, returns, volume, and trends  
- Build interactive dashboards for investment insights  
- Implement efficient data ingestion and optimized querying  
- Simulate a real-world analytics pipeline used in finance teams  



## 🛠️ Tech Stack
- Python – Data ingestion & automation (Yahoo Finance API)
- SQL Server – Data storage, indexing & performance optimization
- Power BI – Interactive dashboards & reporting
- DAX – Financial calculations & measures
- Excel – Data validation & preprocessing
- Git & GitHub – Version control


## 📊 Dataset Details
- Processed 2M+ OHLCV records
- Automated daily incremental data refresh
- Covers multiple stocks with historical price data



## 🔄 Data Pipeline Architecture
1. Fetch daily stock data using Yahoo Finance API
2. Clean and preprocess data using Python
3. Store structured data in SQL Server.
4. Apply SQL indexing on `Symbol` and `TradeDate`
5. Load data into Power BI
6. Create interactive dashboards using DAX measures


## 📈 Dashboard Features
- 📌 Stock price trends (Open, High, Low, Close)
- 📌 Daily & percentage returns
- 📌 Moving averages
- 📌 Volume analysis
- 📌 Time-frame analysis (5D, 1M, 3M, YTD)
- 📌 Stock-wise comparison



## ⚡ Performance Optimizations
- Implemented **SQL indexing** on critical columns, reducing dashboard load time by ~30%
- Designed **incremental data ingestion logic**, reducing redundant data loads by ~40%
- Optimized Power BI data model for faster query execution


