# Mock API responses for course fetching

COURSES = [
    {
        'name': 'Python for Beginners',
        'provider': 'Udemy',
        'rating': 4.5,
        'reviews': 1500,
        'skill': 'Python',
        'url': 'https://www.udemy.com/courses/search/?q=python+for+beginners'
    },
    {
        'name': 'Advanced Django',
        'provider': 'Udemy',
        'rating': 4.7,
        'reviews': 800,
        'skill': 'Django',
        'url': 'https://www.udemy.com/courses/search/?q=advanced+django'
    },
    {
        'name': 'Data Science with Python',
        'provider': 'YouTube',
        'rating': 4.8,
        'reviews': 2500,
        'skill': 'Data Science',
        'url': 'https://www.youtube.com/results?search_query=data+science+with+python'
    },
    {
        'name': 'Machine Learning Basics',
        'provider': 'Coursera',
        'rating': 4.6,
        'reviews': 1200,
        'skill': 'Machine Learning',
        'url': 'https://www.coursera.org/learn/machine-learning'
    },
    {
        'name': 'JavaScript Fundamentals',
        'provider': 'Udemy',
        'rating': 4.4,
        'reviews': 2000,
        'skill': 'JavaScript',
        'url': 'https://www.udemy.com/courses/search/?q=javascript+fundamentals'
    },
    {
        'name': 'React for Beginners',
        'provider': 'YouTube',
        'rating': 4.9,
        'reviews': 1800,
        'skill': 'React',
        'url': 'https://www.youtube.com/results?search_query=react+for+beginners'
    },
    {
        'name': 'SQL for Beginners',
        'provider': 'Udemy',
        'rating': 4.3,
        'reviews': 950,
        'skill': 'SQL',
        'url': 'https://www.udemy.com/courses/search/?q=sql+for+beginners'
    },
    {
        'name': 'Java Programming',
        'provider': 'Udemy',
        'rating': 4.6,
        'reviews': 1400,
        'skill': 'Java',
        'url': 'https://www.udemy.com/courses/search/?q=java+programming'
    },
    {
        'name': 'HTML and CSS Basics',
        'provider': 'YouTube',
        'rating': 4.7,
        'reviews': 2200,
        'skill': 'HTML',
        'url': 'https://www.youtube.com/results?search_query=html+and+css+basics'
    },
    {
        'name': 'C++ Fundamentals',
        'provider': 'Udemy',
        'rating': 4.5,
        'reviews': 1100,
        'skill': 'C++',
        'url': 'https://www.udemy.com/courses/search/?q=cpp+fundamentals'
    },
]

def get_courses():
    return COURSES