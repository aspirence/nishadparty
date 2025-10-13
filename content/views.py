from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import F
from .models import Photo, Video, Article

def photo_detail(request, slug):
    """Display photo detail page"""
    photo = get_object_or_404(Photo, slug=slug, is_published=True)

    # Increment view count
    Photo.objects.filter(id=photo.id).update(view_count=F('view_count') + 1)

    # Get related photos from same category
    related_photos = Photo.objects.filter(
        category=photo.category,
        is_published=True
    ).exclude(id=photo.id)[:6]

    context = {
        'photo': photo,
        'related_photos': related_photos,
    }
    return render(request, 'content/photo_detail.html', context)

def video_detail(request, slug):
    """Display video detail page"""
    video = get_object_or_404(Video, slug=slug, is_published=True)

    # Increment view count
    Video.objects.filter(id=video.id).update(view_count=F('view_count') + 1)

    # Get related videos from same category
    related_videos = Video.objects.filter(
        category=video.category,
        is_published=True
    ).exclude(id=video.id)[:6]

    context = {
        'video': video,
        'related_videos': related_videos,
    }
    return render(request, 'content/video_detail.html', context)

def article_detail(request, slug):
    """Display article/news detail page"""
    article = get_object_or_404(Article, slug=slug, is_published=True)

    # Increment view count
    Article.objects.filter(id=article.id).update(view_count=F('view_count') + 1)

    # Get related articles from same category
    related_articles = Article.objects.filter(
        category=article.category,
        is_published=True
    ).exclude(id=article.id)[:6]

    context = {
        'article': article,
        'related_articles': related_articles,
    }
    return render(request, 'content/article_detail.html', context)
