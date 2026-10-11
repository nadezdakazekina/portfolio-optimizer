# - Создаёт `app = FastAPI()`
# - Подключает роутеры (`assets`, `invest`, `portfolio`, `taxes`, `inflation`)
# - Раздаёт папку `frontend/` как статику: `app.mount("/static", ...)`
# - `def serve_index()` — отдаёт `frontend/index.html` по адресу `/`
# - `def on_startup()` — создаёт таблицы в БД

# **Связи:** импортирует `routers/*`, `database.py`; отдаёт `frontend/index.html`.

"""Точка входа. Запуск: uvicorn backend.main:app --reload"""
from pathlib import Path
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.services import data_loader, markowitz, metrics

FRONT = Path(__file__).resolve().parents[1] / "frontend"
app = FastAPI(title="Investment analyzer")
app.mount("/static", StaticFiles(directory=FRONT), name="static")


class InvestRequest(BaseModel):
    capital: float = Field(gt=0)
    horizon_years: int = Field(1, ge=1, le=5)
    risk_level: int = Field(50, ge=0, le=100)
    tickers: list[str]
    risk_free: float = 0.03


@app.get("/")
def index():
    return FileResponse(FRONT / "index.html")


@app.get("/api/assets")
def assets(q: str = ""):
    return data_loader.list_assets(q)


@app.post("/api/invest/optimize")
def optimize(req: InvestRequest):
    prices, warnings = data_loader.load_price_table(req.tickers)
    if prices.shape[1] < 2:
        raise HTTPException(400, {"msg": "Нужно минимум 2 актива с достаточной историей", "warnings": warnings})
    returns = data_loader.monthly_returns(prices)
    if len(returns) < 12:
        raise HTTPException(400, {"msg": "Общий период данных меньше 12 месяцев", "warnings": warnings})

    mu, cov = metrics.annual_stats(returns)
    m, c = mu.values, cov.values
    frontier = markowitz.efficient_frontier(m, c)
    chosen = markowitz.pick_for_risk(frontier, req.risk_level)
    best = markowitz.max_sharpe(m, c, req.risk_free)

    w = np.array(chosen["weights"])
    ret, vol, sharpe = metrics.portfolio_stats(w, m, c, req.risk_free)
    # историческая стоимость портфеля с постоянными весами -> просадка и восстановление
    value = pd.Series((1 + returns.values @ w).cumprod() * req.capital, index=returns.index)
    b_ret, b_vol, _ = metrics.portfolio_stats(best, m, c, req.risk_free)

    return {
        "warnings": warnings,
        "period": [str(returns.index[0].date()), str(returns.index[-1].date())],
        "allocation": [{"ticker": t, "weight": float(x), "amount": float(x * req.capital)}
                       for t, x in zip(prices.columns, w) if x > 0.005],
        "metrics": {
            "expected_return": ret, "volatility": vol, "sharpe": sharpe,
            "max_drawdown": metrics.max_drawdown(value),
            "recovery_months": metrics.recovery_months(value),
            "expected_value": req.capital * (1 + ret) ** req.horizon_years,
        },
        "frontier": [{"ret": p["ret"], "vol": p["vol"]} for p in frontier],
        "chosen": {"ret": ret, "vol": vol},
        "max_sharpe": {"ret": b_ret, "vol": b_vol},
    }