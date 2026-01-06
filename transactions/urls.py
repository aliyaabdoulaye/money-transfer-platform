"""
URLs pour les transactions
"""
from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('deposit/', views.DepositView.as_view(), name='deposit'),
    path('transfer/', views.TransferView.as_view(), name='transfer'),
    path('withdrawal/request/', views.WithdrawalRequestView.as_view(), name='withdrawal_request'),
    path('withdrawal/verify/', views.WithdrawalVerifyView.as_view(), name='withdrawal_verify'),
    path('withdrawal/resend-otp/', views.ResendWithdrawalOTPView.as_view(), name='resend_withdrawal_otp'),
    path('history/', views.TransactionHistoryView.as_view(), name='history'),
]