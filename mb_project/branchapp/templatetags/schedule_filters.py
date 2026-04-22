from django import template
from datetime import date
from django.utils import timezone

register = template.Library()

@register.filter
def filter_by_status(queryset, status):
    """Filter schedules by status"""
    if hasattr(queryset, 'filter'):
        return queryset.filter(status=status)
    return [item for item in queryset if getattr(item, 'status', None) == status]

@register.filter
def filter_current(queryset, is_current=True):
    """Filter current schedules"""
    today = date.today()
    result = []
    for schedule in queryset:
        if schedule.start_date <= today <= schedule.end_date:
            result.append(schedule)
    return result if is_current else [s for s in queryset if s not in result]

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide value by argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0