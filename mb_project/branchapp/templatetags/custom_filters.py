from django import template

register = template.Library()

@register.filter
def get_month_name(month_number):
    """Convert month number to month name"""
    months = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    return months.get(month_number, '')

@register.filter
def replace(value, arg):
    """Replace all occurrences of old with new in string"""
    if not value:
        return value
    old, new = arg.split(',')
    return value.replace(old, new)


@register.filter
def add(value, arg):
    """Add two numbers"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value