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


def pretty_weekday(dt):
    return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][dt.weekday()]


def pretty_relative_datetime(dt):
    day_str = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][dt.weekday()]
    hour = dt.hour
    if hour < 6:
        hour_str = 'early morning'
    elif hour < 12:
        hour_str = 'morning'
    elif hour < 18:
        hour_str = 'afternoon'
    elif hour < 21:
        hour_str = 'evening'
    else:
        hour_str = 'night'
    return f'{day_str} {hour_str}'
