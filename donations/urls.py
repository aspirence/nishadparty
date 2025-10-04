from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    path('', views.donation_home, name='home'),
    path('donate/', views.donate_form, name='donate'),
    path('donate/<int:campaign_id>/', views.donate_form, name='donate_campaign'),
    path('receipt/<uuid:donation_id>/', views.donation_receipt, name='receipt'),
    path('instructions/<uuid:donation_id>/', views.payment_instructions, name='payment_instructions'),
    path('my-donations/', views.my_donations, name='my_donations'),
]