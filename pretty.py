from datetime import datetime


def pretty_temp(f):
    return "{0:.0f}°".format(f)


def pretty_length(inches):
    if inches == 0:
        return None
    return '{0:0.2f}"'.format(inches)


def pretty_date_str(dt):
    return dt.strftime('%m/%d/%Y %I:%M:%S %p')


def pretty_date_only_str(dt):
    return dt.strftime('%m/%d/%Y')


def pretty_time_str(dt):
    return dt.strftime(f'%I:%M:%S %p')


def pretty_time_str_short(dt):
    return dt.strftime(f'%I %p')


def pretty_weekday(dt):
    return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][dt.weekday()]


def pretty_time_of_day(dt, is_today=False):
    hour = dt.hour
    if hour < 6:
        return 'early this morning' if is_today else 'early morning'
    elif hour < 12:
        return 'this morning' if is_today else 'morning'
    elif hour < 18:
        return 'this afternoon' if is_today else 'afternoon'
    elif hour < 21:
        return 'this evening' if is_today else 'evening'
    else:
        return 'tonight' if is_today else 'night'


def pretty_relative_datetime(dt):
    day_str = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][dt.weekday()]
    if dt.weekday() == datetime.now().weekday():
        return pretty_time_of_day(dt, True)
    return f'{day_str} {pretty_time_of_day(dt)}'
