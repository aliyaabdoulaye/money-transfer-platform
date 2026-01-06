"""
URLs pour l'authentification
"""
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend_otp'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]