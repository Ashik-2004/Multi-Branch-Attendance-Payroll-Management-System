from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def percentage(value, total=100):
    """Calculate percentage"""
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def duration_bar_width(shift):
    """Calculate duration bar width as percentage of 8 hours"""
    try:
        duration = float(shift.duration_hours)
        width = (duration / 8) * 100
        return min(width, 100)  # Cap at 100%
    except (AttributeError, ValueError):
        return 0