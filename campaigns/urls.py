from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    # Public views
    path('events/', views.events_list, name='events_list'),
    path('calendar/', views.events_calendar, name='calendar'),
    path('event/<slug:event_slug>/', views.event_detail, name='event_detail'),
    path('event/<slug:event_slug>/register/', views.event_register, name='event_register'),
    path('my-events/', views.my_events, name='my_events'),
    
    # Admin views
    path('admin/', views.admin_events_dashboard, name='admin_events_dashboard'),
    path('admin/add/', views.admin_add_event, name='admin_add_event'),
    path('admin/edit/<uuid:event_id>/', views.admin_edit_event, name='admin_edit_event'),
    path('admin/delete/<uuid:event_id>/', views.admin_delete_event, name='admin_delete_event'),
]