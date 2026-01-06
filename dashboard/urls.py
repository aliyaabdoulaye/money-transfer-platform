"""
URLs pour le dashboard (temporaire - sera complété dans la phase suivante)
"""
from django.urls import path
from django.views.generic import TemplateView

app_name = 'dashboard'

urlpatterns = [
    path('user/', TemplateView.as_view(template_name='dashboard/user_dashboard.html'), name='user_dashboard'),
    path('admin/', TemplateView.as_view(template_name='dashboard/admin_dashboard.html'), name='admin_dashboard'),
]