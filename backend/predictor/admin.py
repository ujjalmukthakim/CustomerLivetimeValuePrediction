from django.contrib import admin
from .models import CustomerPrediction, Dataset, ModelRun
admin.site.register([Dataset, ModelRun, CustomerPrediction])
