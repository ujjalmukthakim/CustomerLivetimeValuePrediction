from django.db import models


class Dataset(models.Model):
    name = models.CharField(max_length=150)
    source_file = models.FileField(upload_to="datasets/", blank=True)
    mapping = models.JSONField(default=dict)
    rows_count = models.PositiveIntegerField(default=0)
    customers_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.name


class ModelRun(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="runs")
    horizon_days = models.PositiveIntegerField(default=90)
    feature_window_days = models.PositiveIntegerField(default=180)
    best_model = models.CharField(max_length=100, blank=True)
    metrics = models.JSONField(default=dict)
    model_path = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, default="completed")
    created_at = models.DateTimeField(auto_now_add=True)


class CustomerPrediction(models.Model):
    run = models.ForeignKey(ModelRun, on_delete=models.CASCADE, related_name="predictions")
    customer_id = models.CharField(max_length=120)
    predicted_value = models.FloatField()
    segment = models.CharField(max_length=20)
    features = models.JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=["customer_id"]), models.Index(fields=["segment"])]
