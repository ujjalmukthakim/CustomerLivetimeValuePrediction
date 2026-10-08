from django.urls import path
from .views import DashboardView, DatasetUploadView, DemoDatasetView, PredictionView, TrainView, CustomerListView, ExportView
urlpatterns = [path("dashboard/", DashboardView.as_view()), path("datasets/upload/", DatasetUploadView.as_view()), path("datasets/demo/", DemoDatasetView.as_view()), path("runs/train/", TrainView.as_view()), path("customers/", CustomerListView.as_view()), path("export/", ExportView.as_view()), path("predict/", PredictionView.as_view())]
