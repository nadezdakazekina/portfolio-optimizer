# - `def portfolio_performance(weights, mu, cov, rf)` — доход, волатильность, Шарп
# - `def min_variance_portfolio(mu, cov)`
# - `def max_sharpe_portfolio(mu, cov, rf)`
# - `def efficient_frontier(mu, cov, n_points=50)` — точки границы
# - `def portfolio_for_risk_level(risk_level, frontier)` — выбор точки на границе по ползунку 0–100%
# - `def optimize_portfolio(...)` — главная функция (ограничения: веса ≥ 0, сумма = 1)

"""Модель Марковица: минимальная дисперсия, максимальный Шарп, эффективная граница."""
import numpy as np
from scipy.optimize import minimize


def _solve(fun, n, extra=()):
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}, *extra]
    res = minimize(fun, np.full(n, 1 / n), method="SLSQP",
                   bounds=[(0, 1)] * n, constraints=cons)  # без шортов: веса от 0 до 1
    return res.x


def min_variance(mu, cov):
    return _solve(lambda w: w @ cov @ w, len(mu))


def max_sharpe(mu, cov, rf):
    return _solve(lambda w: -(w @ mu - rf) / np.sqrt(w @ cov @ w + 1e-12), len(mu))


def efficient_frontier(mu, cov, n_points=30):
    lo = float(min_variance(mu, cov) @ mu)
    points = []
    for target in np.linspace(lo, float(mu.max()), n_points):
        w = _solve(lambda w: w @ cov @ w, len(mu),
                   [{"type": "eq", "fun": lambda w, t=target: w @ mu - t}])
        points.append({"ret": float(w @ mu), "vol": float(np.sqrt(w @ cov @ w)), "weights": w.tolist()})
    return points


def pick_for_risk(frontier, risk_level):
    """risk_level 0..100: 0 — самый консервативный портфель границы, 100 — самый доходный."""
    return frontier[round(risk_level / 100 * (len(frontier) - 1))]