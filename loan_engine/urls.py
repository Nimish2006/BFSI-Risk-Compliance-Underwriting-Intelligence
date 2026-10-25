from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.loan_dashboard, name='loan_dashboard'),
    path('evaluate/', views.evaluate_loan_risk, name='loan_evaluate'),
    path('tier/<str:tier>/', views.get_loan_tier_applications, name='loan_tier_applications'),
]