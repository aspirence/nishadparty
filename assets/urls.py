from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    # Dashboard
    path('', views.asset_dashboard, name='dashboard'),
    
    # Asset Management
    path('list/', views.asset_list, name='list'),
    path('add/', views.add_asset, name='add'),
    path('edit/<uuid:asset_id>/', views.edit_asset, name='edit'),
    path('delete/<uuid:asset_id>/', views.delete_asset, name='delete'),
    path('assign/', views.assign_asset, name='assign'),
    path('history/<uuid:asset_id>/', views.asset_history, name='history'),
    
    # Assignment Actions
    path('accept/<uuid:assignment_id>/', views.accept_assignment, name='accept'),
    path('reject/<uuid:assignment_id>/', views.reject_assignment, name='reject'),
    path('return/<uuid:assignment_id>/', views.return_asset, name='return'),
]