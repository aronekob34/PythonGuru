from calendar import monthrange, month_name
from datetime import date

from django import template

register = template.Library()


@register.simple_tag
def format_timespan(month, year):

    if date.today().month == int(month) and date.today().year == int(year):

        return '{} 1 - {} {}, {}'.format(
            month_name[int(month)], month_name[int(month)], date.today().day, year
        )

    return '{} 1 - {} {}, {}'.format(
        month_name[int(month)], month_name[int(month)], monthrange(int(year), int(month))[1], year
    )


@register.filter
def modulo_10(value):

    return int(value) % 10


@register.filter
def div_10(value):

    return (int(value) / 10) + 1


@register.filter
def is_current_month(month, year):

    if (date.today().month == int(month) and date.today().year == int(year)) or (date.today().year == int(year) and date.today().month == int(month) + 1 and date.today().day < 8):
        return True

    return False
