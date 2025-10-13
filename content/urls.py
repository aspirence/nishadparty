from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('photo/<slug:slug>/', views.photo_detail, name='photo_detail'),
    path('video/<slug:slug>/', views.video_detail, name='video_detail'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
]