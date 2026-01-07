create database StockMarket

use StockMarket

CREATE TABLE StockPriceDaily (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    TradeDate DATE,
    Symbol VARCHAR(50),
    OpenPrice DECIMAL(18,2),
    HighPrice DECIMAL(18,2),
    LowPrice DECIMAL(18,2),
    ClosePrice DECIMAL(18,2),
    AdjClose DECIMAL(18,2),
    Volume BIGINT
);

select * from StockPriceDaily;

TRUNCATE TABLE StockPriceDaily;

select * from StockPriceDaily where Symbol='PAYTM' order by TradeDate DESC;

  
CREATE UNIQUE INDEX UX_StockPriceDaily_Symbol_Date
ON StockPriceDaily(Symbol, TradeDate);

SELECT MAX(TradeDate)
FROM StockPriceDaily
WHERE Symbol = 'ZUARIIND';

