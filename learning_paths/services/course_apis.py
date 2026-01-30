import requests

def fetch_courses(skill):
    """
    Fetch courses for a given skill from external APIs.
    Uses Udemy and YouTube APIs (requires API keys).
    Falls back to mock data if APIs fail.
    """
    courses = []
    
    # Udemy API (requires API key)
    udemy_courses = fetch_udemy_courses(skill)
    courses.extend(udemy_courses)
    
    # YouTube API (requires API key)
    youtube_courses = fetch_youtube_courses(skill)
    courses.extend(youtube_courses)
    
    # If no real courses, fall back to mock
    if not courses:
        from .mock_api import get_courses
        all_mock = get_courses()
        courses = [c for c in all_mock if c['skill'].lower() == skill.lower()]
    
    return courses

import requests
from django.conf import settings

def fetch_udemy_courses(skill):
    """
    Fetch courses from Udemy API.
    """
    url = 'https://www.udemy.com/api-2.0/courses/'
    params = {
        'search': skill,
        'page_size': 5,  # Limit to 5
    }
    headers = {
        'Authorization': f'Basic {settings.UDEMY_CLIENT_ID}:{settings.UDEMY_CLIENT_SECRET}'
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            courses = []
            for item in data.get('results', []):
                courses.append({
                    'name': item['title'],
                    'provider': 'Udemy',
                    'rating': item.get('avg_rating', 0),
                    'reviews': item.get('num_reviews', 0),
                    'skill': skill,
                    'url': f"https://www.udemy.com{item['url']}"
                })
            return courses
    except Exception as e:
        print(f"Udemy API error: {e}")
    return []

def fetch_youtube_courses(skill):
    """
    Fetch videos/playlists from YouTube Data API.
    """
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': f'{skill} tutorial',
        'type': 'video',
        'maxResults': 5,
        'key': settings.YOUTUBE_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            courses = []
            for item in data.get('items', []):
                courses.append({
                    'name': item['snippet']['title'],
                    'provider': 'YouTube',
                    'rating': 4.5,  # YouTube doesn't provide ratings easily
                    'reviews': item['snippet'].get('viewCount', 0),  # Use view count as proxy
                    'skill': skill,
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                })
            return courses
    except Exception as e:
        print(f"YouTube API error: {e}")
    return []