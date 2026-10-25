from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.risk_dashboard, name='risk_dashboard'),
    path('audit/', views.audit_user_account, name='risk_audit'),
    path('tier/<str:tier>/', views.get_tier_transactions, name='risk_tier_transactions'),
]