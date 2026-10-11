# - `def expected_return(returns, weights)`
# - `def volatility(returns, weights)`
# - `def sharpe_ratio(ret, vol, rf)`
# - `def drawdown_series(values)` — ряд просадок (для drawdown chart)
# - `def max_drawdown(values)`
# - `def recovery_period(values)` — сколько дней/месяцев восстанавливались после максимальной просадки


# growth_of_100(...)
"""Метрики портфеля: доходность, волатильность, Шарп, просадка, период восстановления."""
import numpy as np
import pandas as pd

PERIODS = 12  # месячные данные -> годовые значения


def annual_stats(returns: pd.DataFrame):
    return returns.mean() * PERIODS, returns.cov() * PERIODS


def portfolio_stats(w, mu, cov, rf=0.0):
    ret = float(w @ mu)
    vol = float(np.sqrt(w @ cov @ w))
    sharpe = (ret - rf) / vol if vol > 0 else 0.0
    return ret, vol, sharpe


def drawdown_series(values: pd.Series) -> pd.Series:
    return values / values.cummax() - 1


def max_drawdown(values: pd.Series) -> float:
    return float(drawdown_series(values).min())


def recovery_months(values: pd.Series):
    """Сколько месяцев от дна максимальной просадки до возврата на прежний максимум (None — не восстановился)."""
    dd = drawdown_series(values)
    trough = dd.idxmin()
    peak_value = values[:trough].max()
    after = values[trough:]
    back = after[after >= peak_value]
    if back.empty:
        return None
    return int(round((back.index[0] - trough).days / 30.4))