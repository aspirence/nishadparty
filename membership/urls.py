from django.urls import path
from . import views

app_name = 'membership'

urlpatterns = [
    path('', views.membership_home, name='home'),
    path('apply/<int:tier_id>/', views.apply_membership, name='apply'),
    path('apply/', views.apply_membership_with_payment, name='apply_with_payment'),
    path('payment/<uuid:membership_id>/', views.payment_page, name='payment'),
    path('payment/complete/<uuid:membership_id>/', views.payment_complete, name='payment_complete'),
    path('status/<uuid:membership_id>/', views.application_status, name='application_status'),
    path('card/', views.membership_card, name='card'),
    path('dashboard-content/', views.dashboard_membership_content, name='dashboard_content'),
]