from django.urls import path
from . import views

app_name = 'gatepass'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('create/', views.create_gatepass, name='create'),
    path('list/', views.list_gatepasses, name='list'),
    path('<int:pk>/', views.gatepass_detail, name='detail'),
    path('<int:pk>/approve/', views.approve_gatepass, name='approve'),
    path('<int:pk>/print/', views.print_gatepass, name='print'),
    path('permissions/', views.manage_permissions, name='manage_permissions'),
    path('permissions/toggle/<int:user_id>/', views.toggle_permission, name='toggle_permission'),
]