# — Pydantic-схемы запросов/ответов
# - `class InvestRequest` — capital, horizon_years (1–5), risk_level (0–100), country, asset_ids
# - `class InvestResponse` — weights, metrics, forecast, charts_data
# - `class RiskRequest` — percentile (для VaR), scenario (pessimistic/median/optimistic)
# - `class TransactionIn` — asset_id, buy_date, sell_date, quantity или amount
# - `class PortfolioHistoryResponse`
# - `class RebalanceResponse`