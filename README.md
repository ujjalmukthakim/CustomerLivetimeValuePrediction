# LumenCLV — Customer Lifetime Value Prediction

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
