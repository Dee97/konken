from datetime import datetime
from django import template

register = template.Library()

"""
    These are filters to be used in the template tags since most of the variables come from JSON Responses.
"""

@register.filter
def convert_str_time(value):
    """
        Formats a parseable string into the 24 hour format.
    """
    try:
        timestamp = datetime.strptime(value, '%H:%M:%S.%f').time()
    except ValueError:
        timestamp = datetime.strptime(value, '%H:%M:%S').time()
    except TypeError:
        return

    time = timestamp.strftime("%H:%M")
    return time

@register.filter
def convert_str_date(value):
    """
        Formats a pareseable string into a Japanese format.
    """
    date = datetime.strptime(value, '%Y-%m-%d').date()
    year = date.strftime('%Y')
    month = date.strftime('%m')
    day = date.strftime('%d')
    return f"{year}年{month}月{day}日"

@register.filter
def times(number):
    """
        Converts a string into a range; Used in ranged for loops iterated in the template itself.
    """
    return range(number)