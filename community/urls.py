from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.community_home, name='home'),
    # Community URLs will be added here
]