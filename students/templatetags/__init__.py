from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows template to access dict[key] safely."""
    return dictionary.get(key)
