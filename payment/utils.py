import datetime


def is_expired(exp_year, exp_month):
    expiry_date = datetime.date(2000 + exp_year, exp_month, 1)

    if datetime.date.today() > expiry_date:
        return True
    return False
