from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total=100):
    """Calculate percentage"""
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def duration_width(shift):
    """Calculate duration bar width"""
    try:
        if hasattr(shift, 'duration_hours'):
            width = (shift.duration_hours / 8) * 100
            return min(width, 100)
    except:
        pass
    return 0

@register.filter
def bar_class(shift):
    """Get CSS class for duration bar"""
    try:
        if hasattr(shift, 'duration_hours'):
            if shift.duration_hours > 8:
                return "danger"
            elif shift.duration_hours > 6:
                return "warning"
            else:
                return "normal"
    except:
        pass
    return "normal"