# — таблицы (SQLAlchemy)
# - `class Asset` — id, ticker, name, type (stock/bond/gold/future/etf), currency, country, description
# - `class Price` — asset_id, date, close
# - `class TaxRate` — country, year, rate_type (dividend/capital_gain/coupon), rate
# - `class CommissionRate` — country, broker_name, rate_percent, min_fee
# - `class InflationRate` — country, year, rate
# - `class DepositRate` — country, year, rate
# - `class UserPortfolio` — id, name, country, created_at (сохранённый расчёт)
# - `class Transaction` — portfolio_id, asset_id, buy_date, sell_date (nullable), quantity, price, amount