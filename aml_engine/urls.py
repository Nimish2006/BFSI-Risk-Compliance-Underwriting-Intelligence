from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.aml_dashboard, name='aml_dashboard'),
    path('analyze/', views.analyze_aml_transaction, name='aml_analyze'),
]