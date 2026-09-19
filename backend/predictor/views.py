from rest_framework.response import Response
from rest_framework.views import APIView


class PredictionView(APIView):
    """A transparent baseline CLV model, suitable for replacement by a serialized ML model."""

    def post(self, request):
        fields = ("monthly_spend", "purchase_frequency", "tenure_months", "churn_risk", "acquisition_cost")
        try:
            data = {field: float(request.data[field]) for field in fields}
        except (KeyError, TypeError, ValueError):
            return Response({"detail": "Provide numeric values for all customer metrics."}, status=400)

        if data["monthly_spend"] < 0 or data["purchase_frequency"] < 0 or data["tenure_months"] < 0 or not 0 <= data["churn_risk"] <= 100:
            return Response({"detail": "Values must be positive and churn risk must be between 0 and 100."}, status=400)

        retention = 1 - data["churn_risk"] / 100
        # 24 month prediction horizon; frequency captures recurring order behavior.
        gross_value = data["monthly_spend"] * (0.65 + data["purchase_frequency"] / 4) * 24 * retention
        predicted_clv = max(0, gross_value - data["acquisition_cost"])
        confidence = min(96, round(62 + min(data["tenure_months"], 24) * 1.1 + min(data["purchase_frequency"], 6) * 1.3))
        segment = "High value" if predicted_clv >= 5000 else "Growth potential" if predicted_clv >= 2200 else "Nurture"
        return Response({
            "customer_name": request.data.get("customer_name", "Customer"),
            "predicted_clv": round(predicted_clv, 2), "confidence": confidence,
            "segment": segment, "retention": round(retention * 100),
            "monthly_value": round(predicted_clv / 24, 2),
        })
