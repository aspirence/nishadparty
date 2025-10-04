from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def community_home(request):
    """Community home page placeholder"""
    return render(request, 'community/home.html')
