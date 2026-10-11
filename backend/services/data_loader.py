# - `def load_prices(asset_ids, start, end) -> DataFrame` — цены из БД
# - `def compute_returns(prices) -> DataFrame` — доходности (лог. или простые)
# - `def align_series(prices) -> DataFrame` — выравнивание рядов разной длины (общий период)
# - `def get_expected_returns_and_cov(returns)` — вектор μ и матрица Σ

"""Загрузка данных из локальных CSV (папка data/).
БД и внешние API пока не используются.
TODO (будущее): заменить чтение CSV на API/БД только в этом файле — остальной код не изменится.
"""
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PRICES_DIR = DATA_DIR / "prices"
MIN_MONTHS = 12  # меньше — считаем, что истории недостаточно


def load_catalog() -> pd.DataFrame:
    # ticker читаем как строку, чтобы не потерять "600519" и т.п.
    return pd.read_csv(DATA_DIR / "assets_catalog.csv", dtype={"ticker": str}).fillna("")


def list_assets(query: str = "") -> list[dict]:
    df = load_catalog()
    if query:
        q = query.lower()
        mask = df["name"].str.lower().str.contains(q) | df["ticker"].str.lower().str.contains(q)
        df = df[mask]
    return df[["ticker", "name", "type"]].to_dict("records")


def load_prices(ticker: str) -> pd.Series | None:
    """Цены одного актива (ищем файл <ticker>.csv во всех подпапках prices/)."""
    path = next(PRICES_DIR.glob(f"*/{ticker}.csv"), None)
    if path is None:
        return None
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date")
    return df.set_index("date")["close"].rename(ticker)


def load_price_table(tickers: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Месячные цены выбранных активов на общем периоде + список предупреждений."""
    series, warnings = [], []
    for t in tickers:
        s = load_prices(t)
        if s is None:
            warnings.append(f"{t}: нет файла с ценами — актив пропущен")
            continue
        if len(s.resample("ME").last().dropna()) < MIN_MONTHS:
            warnings.append(f"{t}: данных за прошлое недостаточно — актив пропущен")
            continue
        series.append(s)
    if not series:
        return pd.DataFrame(), warnings
    monthly = pd.concat(series, axis=1).resample("ME").last().dropna()
    return monthly, warnings


def monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna()