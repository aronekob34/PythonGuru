from datetime import date


def get_time_frame(month_string):

    year, month = month_string.split('-')
    return int(year), int(month)


def is_current_month(month_string):

    year, month = month_string.split('-')

    if date.today().month == int(month) and date.today().year == int(year):
        return True

    return False
