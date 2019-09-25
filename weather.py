import sys
from copy import copy
from urllib.error import HTTPError

from config_reader import ConfigReader
from datetime import datetime
import easy_requests

cfg = ConfigReader()


def pretty_temp(f):
    return "{0:.0f}°".format(f)


def pretty_length(inches):
    if inches == 0:
        return None
    return '{0:0.2f}"'.format(inches)


def pretty_date_str(dt):
    return dt.strftime("%m/%d/%Y %I:%M:%S %p")


def pretty_relative_date(dt):
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


class Weather:
    def __init__(self):
        # get a url to get the forecast based on the coordinates
        self.updated = ''
        self.location_name = ''
        self.forecast_today = {}
        self.periods = []
        self.refresh()

    def make_api_call(self, api):
        try:
            return easy_requests.get(
                f'https://api.openweathermap.org/data/2.5/{api}&units=imperial&APPID={cfg.get("weather-api-key")}')
        except HTTPError as err:
            if err.getcode() == 401:
                print('Weather API key was rejected. It\'s either invalid or it hasn\'t been activated yet. Verify it '
                      'is correct or try again later.')
                sys.exit(-1)

    def refresh(self):
        today_forecast = self.make_api_call(f'weather?zip={cfg.get("zip-code")}')
        self.forecast_today = self.collect_weather_information(today_forecast)
        for temp_type in ['temp', 'low', 'high']:
            self.forecast_today[temp_type] = pretty_temp(self.forecast_today[temp_type])
        self.location_name = today_forecast['name']

        # get forecast for the next few days
        forecast5 = self.make_api_call(f'forecast?zip={cfg.get("zip-code")}')
        self.periods = []
        for period in forecast5['list']:
            self.periods.append(self.collect_weather_information(period))

        # figure out day totals
        self.days = [None] * (1 + max(x['days-from-now'] for x in self.periods))
        for period in self.periods:
            delta = period['days-from-now']
            if not self.days[delta]:
                dt = period['dt'].date()
                self.days[delta] = {
                    "dt": dt,
                    "dt-pretty": pretty_relative_date(dt),
                    "rain": 0,
                    "snow": 0,
                    "low": period['low'],
                    "high": period['high']
                }
            this_day = self.days[delta]
            this_day['low'] = min(this_day['low'], period['low'])
            this_day['high'] = max(this_day['high'], period['high'])
            this_day['rain'] += period['rain']
            this_day['snow'] += period['snow']

        # make everything look pretty, now that we've organized all the data
        for day in self.days:
            if day is not None:
                day['low'] = pretty_temp(day['low'])
                day['high'] = pretty_temp(day['high'])
                day['rain'] = pretty_length(day['rain'])
                day['snow'] = pretty_length(day['snow'])

    def collect_weather_information(self, forecast):
        temps = forecast['main']
        weather = forecast['weather'][0]
        dt = datetime.fromtimestamp(forecast['dt'])
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)

        def get_precip_amount(precip_type):
            if precip_type not in forecast:
                return 0

            precip = forecast[precip_type]
            if '3h' in precip:
                return precip['3h']
            elif '1h' in precip:
                return precip['1h']
            else:
                return 0

        def mm_to_inch(mm):
            return 0.0393701 * mm

        return {
            "dt": dt,
            "days-from-now": (dt - today).days,
            "dt-pretty": pretty_date_str(dt),
            "temp": temps['temp'],
            "low": temps['temp_min'],
            "high": temps['temp_max'],
            "weather": weather["main"],
            # regardless of imperial setting, we get mm as units
            "rain": mm_to_inch(get_precip_amount('rain')),
            "snow": mm_to_inch(get_precip_amount('snow'))
        }

    def get_updated_time(self):
        return self.forecast_today['dt-pretty']

    def get_todays_forecast(self):
        forecast = copy(self.forecast_today)

        def get_precip(precip_type):
            precip = next((period['dt'] for period in self.periods if period[precip_type] != 0), None)
            if precip:
                forecast[f'next_{precip_type}'] = f"Next {precip_type} {pretty_relative_datetime(precip)}."

        get_precip('rain')
        get_precip('snow')

        return forecast

    def get_days(self):
        return self.days

    def get_location_name(self):
        return self.location_name
