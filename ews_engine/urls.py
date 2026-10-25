from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.ews_dashboard, name='ews_dashboard'),
    path('analyze/', views.analyze_ews_loan, name='ews_analyze'),
]