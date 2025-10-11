from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely get a value from a dictionary in templates."""
    return dictionary.get(key)
    