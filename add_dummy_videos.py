#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to the Python path
sys.path.append('/Users/vinaydubey/Documents/Vinay/Projects/Django/nishadparty')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nishadparty.settings')
django.setup()

from core.models import YouTubeVideo
from accounts.models import User

# Create dummy YouTube videos
dummy_videos = [
    {
        'title': 'निषाद पार्टी - मत्स्यजीवी समुदाय के लिए न्याय',
        'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'description': 'निषाद पार्टी के संस्थापक द्वारा मत्स्यजीवी समुदाय के अधिकारों और न्याय के लिए एक प्रेरणादायक भाषण।',
        'is_featured': True,
        'display_order': 1
    },
    {
        'title': 'Community Rally - Voice of the Fishermen',
        'youtube_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
        'description': 'A massive rally showcasing the strength and unity of the fishing community. Thousands gathered to support Nishad Party\'s vision.',
        'is_featured': True,
        'display_order': 2
    },
    {
        'title': 'Nishad Party Manifesto Launch',
        'youtube_url': 'https://www.youtube.com/watch?v=ScMzIvxBSi4',
        'description': 'The official launch of Nishad Party\'s manifesto focusing on fishermen welfare, economic empowerment, and social justice.',
        'is_featured': False,
        'display_order': 3
    },
    {
        'title': 'समुदायिक विकास कार्यक्रम',
        'youtube_url': 'https://www.youtube.com/watch?v=astISOttCQ0',
        'description': 'निषाद पार्टी द्वारा चलाए जा रहे विभिन्न सामुदायिक विकास कार्यक्रमों की जानकारी और उनके सकारात्मक प्रभाव।',
        'is_featured': False,
        'display_order': 4
    },
    {
        'title': 'Youth Empowerment Initiative',
        'youtube_url': 'https://www.youtube.com/watch?v=fJ9rUzIMcZQ',
        'description': 'Nishad Party\'s initiatives to empower youth from fishing communities through education, skill development, and job opportunities.',
        'is_featured': False,
        'display_order': 5
    },
    {
        'title': 'Women in Leadership - नारी शक्ति',
        'youtube_url': 'https://www.youtube.com/watch?v=QH2-TGUlwu4',
        'description': 'Celebrating the role of women in Nishad Party and how they are leading change in their communities. Empowering women for a better tomorrow.',
        'is_featured': False,
        'display_order': 6
    }
]

print("Adding dummy YouTube videos...")

# Try to get the first admin user, or create a generic one
try:
    admin_user = User.objects.filter(user_type='ADMINISTRATOR').first()
    if not admin_user:
        admin_user = User.objects.filter(is_superuser=True).first()
except:
    admin_user = None

for video_data in dummy_videos:
    # Check if video already exists
    if not YouTubeVideo.objects.filter(title=video_data['title']).exists():
        video = YouTubeVideo.objects.create(
            title=video_data['title'],
            youtube_url=video_data['youtube_url'],
            description=video_data['description'],
            is_featured=video_data['is_featured'],
            is_active=True,
            display_order=video_data['display_order'],
            created_by=admin_user
        )
        print(f"✓ Created: {video.title}")
    else:
        print(f"- Skipped (exists): {video_data['title']}")

total_videos = YouTubeVideo.objects.filter(is_active=True).count()
print(f"\n🎬 Total active videos: {total_videos}")
print("✅ Dummy videos added successfully!")
print("\nYou can now visit the homepage to see the YouTube videos section.")