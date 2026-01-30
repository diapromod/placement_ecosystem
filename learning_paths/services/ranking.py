def score_courses(courses, skill_priorities=None):
    """
    Score courses using the mandatory algorithm.
    Normalized Rating = rating / 5
    Normalized Popularity = reviews / max_reviews
    Course Score = 0.5 × Normalized Rating + 0.3 × Normalized Popularity + 0.2 × Skill Priority
    """
    if not courses:
        return []

    max_reviews = max(c['reviews'] for c in courses)
    if max_reviews == 0:
        max_reviews = 1

    for course in courses:
        course['normalized_rating'] = course['rating'] / 5.0
        course['normalized_popularity'] = course['reviews'] / max_reviews
        skill_priority = skill_priorities.get(course.get('skill'), 1) if skill_priorities else 1
        course['score'] = 0.5 * course['normalized_rating'] + 0.3 * course['normalized_popularity'] + 0.2 * skill_priority

    return sorted(courses, key=lambda x: x['score'], reverse=True)