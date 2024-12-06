from django import template

register = template.Library()

@register.filter
def in_list(value, arg):
    """Check if the value is in a comma-separated string."""
    if value is None:  # Handle NoneType gracefully
        return False
    return value in arg.split(',')

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')
