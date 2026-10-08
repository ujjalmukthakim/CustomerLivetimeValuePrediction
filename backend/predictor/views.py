import logging
from django.conf import settings
from django.http import HttpResponse
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CustomerPrediction, Dataset, ModelRun
logger = logging.getLogger(__name__)

def latest_run(): return ModelRun.objects.order_by("-created_at").first()
def persist_run(dataset, tx, horizon=90, window=180):
    from .ml.pipeline import train
    run=ModelRun.objects.create(dataset=dataset,horizon_days=horizon,feature_window_days=window,status="training")
    data,best,metrics,path,cutoff,thresholds=train(tx,settings.MEDIA_ROOT/"models"/str(run.id),horizon,window)
    run.best_model,run.metrics,run.model_path,run.status=best,{"models":metrics,"cutoff_date":cutoff,"segment_thresholds":thresholds},path,"completed";run.save()
    CustomerPrediction.objects.bulk_create([CustomerPrediction(run=run,customer_id=r.customer_id,predicted_value=float(r.predicted_value),segment=r.segment,features={k:float(r[k]) for k in ["recency_days","frequency","monetary","avg_transaction_value","purchase_interval_days","tenure_days"]}) for _,r in data.iterrows()])
    return run

class DemoDatasetView(APIView):
 def post(self,request):
    from .ml.pipeline import demo_transactions
    tx=demo_transactions();d=Dataset.objects.create(name="Built-in retail demo",mapping={"customer_id":"customer_id","date":"transaction_date","amount":"amount"},rows_count=len(tx),customers_count=tx.customer_id.nunique());run=persist_run(d,tx);return Response({"dataset_id":d.id,"run_id":run.id,"message":"Demo data trained."},201)

class DatasetUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        file = request.FILES.get("file")
        if not file: return Response({"detail": "Upload a CSV or Excel file."}, 400)
        try:
            import pandas as pd
            from .ml.pipeline import clean_transactions, infer_mapping
            raw = pd.read_csv(file) if file.name.lower().endswith(".csv") else pd.read_excel(file)
            mapping = infer_mapping(raw.columns); tx, mapping = clean_transactions(raw, mapping)
            d = Dataset.objects.create(name=file.name, source_file=file, mapping=mapping, rows_count=len(tx), customers_count=tx.customer_id.nunique())
            return Response({"dataset_id": d.id, "rows": len(tx), "customers": tx.customer_id.nunique(), "mapping": mapping}, 201)
        except Exception as exc: return Response({"detail": str(exc)}, 400)

class TrainView(APIView):
 def post(self,request):
  try:
   import pandas as pd
   from .ml.pipeline import clean_transactions
   d=Dataset.objects.get(pk=request.data.get("dataset_id"));h=int(request.data.get("horizon_days",90));w=int(request.data.get("feature_window_days",180))
   if h<30 or w<=h:return Response({"detail":"Feature window must exceed horizon; horizon must be at least 30 days."},400)
   raw=pd.read_csv(d.source_file.path) if d.source_file.name.lower().endswith(".csv") else pd.read_excel(d.source_file.path);tx,_=clean_transactions(raw,d.mapping);run=persist_run(d,tx,h,w)
   return Response({"run_id":run.id,"best_model":run.best_model,"metrics":run.metrics},201)
  except Dataset.DoesNotExist:return Response({"detail":"Dataset not found."},404)
  except Exception as exc:logger.exception("Training failed");return Response({"detail":str(exc)},400)

class DashboardView(APIView):
 def get(self,request):
  run=latest_run()
  if not run:return Response({"ready":False,"message":"Load demo data or upload a dataset to begin."})
  qs=run.predictions.all();values=[p.predicted_value for p in qs]
  return Response({"ready":True,"run_id":run.id,"dataset":run.dataset.name,"best_model":run.best_model,"metrics":run.metrics,"total_customers":len(values),"total_predicted_value":round(sum(values),2),"average_predicted_value":round(sum(values)/max(len(values),1),2),"segments":{s:qs.filter(segment=s).count() for s in ["Low","Medium","High"]}})

class CustomerListView(APIView):
 def get(self,request):
  run=latest_run()
  if not run:return Response([])
  qs=run.predictions.all().order_by("-predicted_value");search=request.GET.get("search","");seg=request.GET.get("segment")
  if search:qs=qs.filter(customer_id__icontains=search)
  if seg in ["Low","Medium","High"]:qs=qs.filter(segment=seg)
  return Response([{"customer_id":p.customer_id,"predicted_value":p.predicted_value,"segment":p.segment,"features":p.features} for p in qs[:200]])

class ExportView(APIView):
 def get(self,request):
  run=latest_run()
  if not run:return Response({"detail":"No predictions available."},404)
  text="customer_id,predicted_future_value,segment\n"+"\n".join(f"{p.customer_id},{p.predicted_value:.2f},{p.segment}" for p in run.predictions.all())
  res=HttpResponse(text,content_type="text/csv");res["Content-Disposition"]='attachment; filename="customer-value-predictions.csv"';return res

class PredictionView(APIView):
 def post(self,request):return Response({"detail":"Use the dataset training workflow for leakage-safe predictions."},400)
