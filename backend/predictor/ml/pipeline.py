"""Leakage-safe customer value training pipeline.

Features use only transactions on/before the cutoff. The target is spending after
the cutoff in the defined forecast horizon.
"""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ALIASES = {
    "customer_id": ["customer_id", "customer", "customerid", "client_id", "user_id"],
    "date": ["transaction_date", "date", "order_date", "purchase_date", "invoice_date"],
    "amount": ["amount", "revenue", "sales", "total", "transaction_amount", "value"],
}
FEATURES = ["recency_days", "frequency", "monetary", "avg_transaction_value", "purchase_interval_days", "tenure_days"]


def infer_mapping(columns):
    normalized = {str(c).strip().lower().replace(" ", "_"): c for c in columns}
    mapping = {}
    for canonical, aliases in ALIASES.items():
        mapping[canonical] = next((normalized[a] for a in aliases if a in normalized), None)
    return mapping


def clean_transactions(frame, mapping=None):
    mapping = mapping or infer_mapping(frame.columns)
    missing = [key for key in ("customer_id", "date", "amount") if not mapping.get(key)]
    if missing: raise ValueError(f"Could not map required columns: {', '.join(missing)}. Map customer ID, transaction date, and amount.")
    tx = frame[[mapping["customer_id"], mapping["date"], mapping["amount"]].copy()
    tx.columns = ["customer_id", "date", "amount"]
    tx["customer_id"] = tx.customer_id.astype(str).str.strip()
    tx["date"] = pd.to_datetime(tx.date, errors="coerce")
    tx["amount"] = pd.to_numeric(tx.amount, errors="coerce")
    tx = tx.dropna().drop_duplicates()
    tx = tx[(tx.customer_id != "") & (tx.amount >= 0)]
    # Clip extreme values rather than silently deleting valid high-value customers.
    if len(tx) >= 10:
        lo, hi = tx.amount.quantile([.01, .99]); tx["amount"] = tx.amount.clip(lo, hi)
    return tx.sort_values("date"), mapping


def make_customer_dataset(tx, horizon_days=90, feature_window_days=180):
    cutoff = tx.date.max().normalize() - pd.Timedelta(days=horizon_days)
    history = tx[(tx.date <= cutoff) & (tx.date > cutoff - pd.Timedelta(days=feature_window_days))]
    future = tx[(tx.date > cutoff) & (tx.date <= cutoff + pd.Timedelta(days=horizon_days))]
    if history.empty or future.empty: raise ValueError("Dataset needs transactions both before and after the forecast cutoff.")
    grouped = history.groupby("customer_id")
    table = grouped.amount.agg(frequency="count", monetary="sum", avg_transaction_value="mean")
    table["last_purchase"] = grouped.date.max()
    table["first_purchase"] = grouped.date.min()
    intervals = grouped.date.apply(lambda d: d.sort_values().diff().dt.days.mean())
    table["purchase_interval_days"] = intervals.fillna(feature_window_days)
    table["recency_days"] = (cutoff - table.last_purchase).dt.days
    table["tenure_days"] = (cutoff - table.first_purchase).dt.days
    target = future.groupby("customer_id").amount.sum().rename("future_value")
    table = table.join(target, how="left").fillna({"future_value": 0}).reset_index()
    return table, cutoff


def train(tx, artifact_dir, horizon_days=90, feature_window_days=180):
    data, cutoff = make_customer_dataset(tx, horizon_days, feature_window_days)
    if len(data) < 8: raise ValueError("At least 8 customers with historical activity are required to train a model.")
    x, y = data[FEATURES], data.future_value
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=.25, random_state=42)
    candidates = {"Linear Regression": LinearRegression(), "Random Forest": RandomForestRegressor(n_estimators=200, min_samples_leaf=2, random_state=42), "Gradient Boosting": GradientBoostingRegressor(random_state=42)}
    metrics, fitted = {}, {}
    for name, estimator in candidates.items():
        pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("model", estimator)])
        pipe.fit(x_train, y_train); pred = np.maximum(0, pipe.predict(x_test)); fitted[name] = pipe
        metrics[name] = {"mae": round(mean_absolute_error(y_test, pred), 2), "rmse": round(mean_squared_error(y_test, pred) ** .5, 2), "r2": round(r2_score(y_test, pred), 3)}
    best = min(metrics, key=lambda name: metrics[name]["mae"])
    thresholds = data.future_value.quantile([.33, .67]).tolist()
    data["predicted_value"] = np.maximum(0, fitted[best].predict(x))
    data["segment"] = pd.cut(data.predicted_value, [-1, thresholds[0], thresholds[1], np.inf], labels=["Low", "Medium", "High"]).astype(str)
    path = Path(artifact_dir); path.mkdir(parents=True, exist_ok=True); model_file = path / "clv_model.joblib"
    joblib.dump({"model": fitted[best], "features": FEATURES, "thresholds": thresholds, "cutoff": str(cutoff.date())}, model_file)
    return data, best, metrics, str(model_file), str(cutoff.date()), thresholds


def demo_transactions():
    rng = np.random.default_rng(12); rows=[]; start=pd.Timestamp("2024-01-01")
    for customer in range(1, 81):
        base=rng.uniform(25, 250); n=rng.integers(4, 16)
        for _ in range(n): rows.append({"customer_id": f"C{customer:03}", "transaction_date": start + pd.Timedelta(days=int(rng.integers(0, 540))), "amount": round(max(5, rng.normal(base, base*.25)), 2)})
    return pd.DataFrame(rows)
