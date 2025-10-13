from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.main_dashboard_view, name='dashboard'),
    path('dashboard/old/', views.dashboard_view, name='dashboard_old'),
    path('about/', views.about_view, name='about'),
    path('leadership/', views.leadership_view, name='leadership'),
    path('vision/', views.vision_view, name='vision'),
    path('manifesto/', views.manifesto_view, name='manifesto'),
    path('photo-gallery/', views.photo_gallery_view, name='photo_gallery'),
    path('video-gallery/', views.video_gallery_view, name='video_gallery'),
    path('news/', views.news_view, name='news'),
    path('policies/', views.policies_view, name='policies'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms/', views.terms_view, name='terms'),
    path('sitemap/', views.sitemap_view, name='sitemap'),
    path('change-language/', views.change_language_view, name='change_language'),
    path('api/kejriwal-videos/', views.kejriwal_videos_api, name='kejriwal_videos_api'),
]