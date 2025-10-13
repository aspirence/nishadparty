from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.PhoneLoginView.as_view(), name='phone_login'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend_otp'),
    path('complete-profile/', views.complete_profile_view, name='complete_profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin User Management URLs
    path('admin/users/', views.admin_user_list, name='admin_user_list'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/users/<int:user_id>/change-type/', views.admin_change_user_type, name='admin_change_user_type'),
    path('admin/users/<int:user_id>/toggle-status/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('admin/dashboard-content/', views.dashboard_user_management_content, name='dashboard_user_management_content'),
]