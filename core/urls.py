from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('about/', views.about_view, name='about'),
    path('policies/', views.policies_view, name='policies'),
    path('contact/', views.contact_view, name='contact'),
    path('change-language/', views.change_language_view, name='change_language'),
    path('api/kejriwal-videos/', views.kejriwal_videos_api, name='kejriwal_videos_api'),
]