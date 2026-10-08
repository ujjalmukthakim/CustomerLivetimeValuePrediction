# AI-Based Customer Value Prediction System

Production-style university final-year project using Django REST, React, Pandas and scikit-learn. It ingests transaction data, creates leakage-safe historical customer features, predicts future monetary value, compares models, creates data-driven segments and exposes dashboard/export APIs.

## Core methodology

For a cutoff `T`, customer features are created exclusively from transactions in the historical feature window ending at `T`. The prediction target is total customer spending in the later forecast horizon `(T, T + horizon]`. This prevents target leakage. Features include recency, frequency, monetary value, average transaction value, average purchase interval and tenure.

The ML pipeline (`backend/predictor/ml/pipeline.py`) cleans duplicate/invalid records, maps common customer/date/amount field names, handles types and outliers, then compares Linear Regression, Random Forest and Gradient Boosting with a fixed customer-level train/test split. MAE, RMSE and R² are stored; the model with lowest test MAE is saved with Joblib. Low/Medium/High segments use 33rd/67th percentile thresholds derived from data.

## Project structure

- `backend/predictor/models.py` — Dataset → ModelRun → CustomerPrediction database schema
- `backend/predictor/ml/` — independently reusable preprocessing/training module
- `backend/predictor/views.py` — validated REST endpoints
- `frontend/` — responsive React dashboard

## Full workflow API

- `POST /api/datasets/demo/` — build and train reproducible demo retail data
- `POST /api/datasets/upload/` — multipart CSV/XLS/XLSX ingestion and mapping validation
- `POST /api/runs/train/` — `{dataset_id, horizon_days, feature_window_days}`
- `GET /api/dashboard/` — KPIs, model metrics and segments
- `GET /api/customers/?search=&segment=` — filterable customer predictions
- `GET /api/export/` — prediction CSV

## Requirements

Use Python **3.11 or 3.12** for the ML environment (Pandas/scikit-learn wheel support) and Node 20+.

Full-stack CLV dashboard built with Django REST Framework, Python and React.

## Run the API

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Run the client

```bash
cd frontend
npm install
npm run dev
```

The React development server proxies `/api` calls to Django at `localhost:8000`.

## API

`POST /api/predict/`

```json
{
  "customer_name": "Ava Mitchell",
  "monthly_spend": 180,
  "purchase_frequency": 3.2,
  "tenure_months": 14,
  "churn_risk": 18,
  "acquisition_cost": 72
}
```
