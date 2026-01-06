"""
URLs pour le dashboard
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('user/', views.UserDashboardView.as_view(), name='user_dashboard'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/users/', views.ManageUsersView.as_view(), name='manage_users'),
    path('admin/users/<int:user_id>/', views.UserDetailView.as_view(), name='user_detail'),
    path('admin/users/<int:user_id>/suspend/', views.SuspendUserView.as_view(), name='suspend_user'),
    path('admin/users/<int:user_id>/reactivate/', views.ReactivateUserView.as_view(), name='reactivate_user'),
]