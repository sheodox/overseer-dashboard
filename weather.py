import sys
from copy import copy
from os import path
from urllib.error import HTTPError

from config_reader import ConfigReader
from datetime import datetime
from pretty import pretty_temp, pretty_weekday, pretty_date_str, pretty_length, pretty_relative_datetime, \
    pretty_weekday
import easy_requests

cfg = ConfigReader()


class Weather:
    def __init__(self):
        # get a url to get the forecast based on the coordinates
        self.updated = ''
        self.location_name = ''
        self.forecast_today = {}
        self.coords = {}  # lon and lat, from openweather for checking weather.gov weather alerts
        self.active_alerts = []
        self.periods = []
        self.days = []
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

    def make_alerts_call(self, dt):
        lat = self.coords['lat']
        lon = self.coords['lon']
        alerts = easy_requests.get(f'https://api.weather.gov/alerts/active?point={lat}%2C{lon}')

        self.active_alerts = []
        for alert in list(alert['properties'] for alert in alerts['features']):
            self.active_alerts.append({
                'headline': alert['headline'],
                'description': alert['description']
            })

    def refresh(self):
        today_forecast = self.make_api_call(f'weather?zip={cfg.get("zip-code")}')
        self.coords = today_forecast['coord']
        self.make_alerts_call(datetime.now())
        self.forecast_today = self.collect_weather_information(today_forecast)
        for temp_type in ['temp', 'low', 'high']:
            self.forecast_today[temp_type + '-pretty'] = pretty_temp(self.forecast_today[temp_type])
        self.location_name = today_forecast['name']

        # get forecast for the next few days
        forecast5 = self.make_api_call(f'forecast?zip={cfg.get("zip-code")}')
        self.periods = []
        for period in forecast5['list']:
            self.periods.append(self.collect_weather_information(period))

        def make_pretty(data):
            data['rain'] = f"{pretty_length(data['rain'])} rain" if data['rain'] else None
            data['snow'] = f"{pretty_length(data['snow'])} snow" if data['snow'] else None

            for temp_type in ['temp', 'low', 'high']:
                if temp_type in data:
                    data[temp_type + '-pretty'] = pretty_temp(data[temp_type])
            return data

        # figure out day totals
        self.days = [None] * (1 + max(x['days-from-now'] for x in self.periods))
        self.periods_by_day = copy(self.days)
        for period in self.periods:
            delta = period['days-from-now']
            if not self.days[delta]:
                dt = period['dt'].date()
                self.days[delta] = {
                    "dt": dt,
                    "dt-pretty": pretty_weekday(dt),
                    "rain": 0,
                    "snow": 0,
                    "low": period['low'],
                    "high": period['high'],
                    "weather-mains": []
                }
                self.periods_by_day[delta] = []
            this_day = self.days[delta]
            this_day['low'] = min(this_day['low'], period['low'])
            this_day['high'] = max(this_day['high'], period['high'])
            this_day['rain'] += period['rain']
            this_day['snow'] += period['snow']
            this_day['weather-mains'].append(period['weather-main'])
            self.periods_by_day[delta].append(make_pretty(copy(period)))

        # make everything look pretty, now that we've organized all the data
        for day in self.days:
            if day is not None:
                day = make_pretty(day)
                # get the weather type that's happening the most
                mains = day['weather-mains']
                most_frequent_weather = max(set(mains), key=mains.count)
                day['weather'] = most_frequent_weather
                # pick an icon based on the most main one, eventually this can be more detailed with
                # better daily summaries
                day['weather-icon'] = {
                    'Rain': '10d',
                    'Snow': '13d',
                    'Drizzle': '09d',
                    'Thunderstorm': '11d',
                    'Clear': '01d',
                    'Clouds': '03d'
                }[most_frequent_weather]
                self.cache_icon(day['weather-icon'])

        # see if there are any more extreme low/highs in periods for today
        if self.days[0] is not None:
            fc = self.forecast_today
            today = self.days[0]
            fc['low'] = min(fc['low'], today['low'])
            fc['high'] = max(fc['high'], today['high'])
            self.forecast_today = make_pretty(fc)

    def get_upcoming_precip_message(self):
        now = self.get_todays_forecast()

        def get_precip_message(precip_type, is_currently_precipitating):
            next_precip_dt = next((period['dt'] for period in self.periods if period[precip_type] != 0), None)
            next_clear_dt = next((period['dt'] for period in self.periods if period[precip_type] == 0), None)

            if is_currently_precipitating:
                return f'The {precip_type} should let up {pretty_relative_datetime(next_clear_dt)}.'
            elif next_precip_dt:
                return f'It will {precip_type} {pretty_relative_datetime(next_precip_dt)}.'
            else:
                return None

        return (get_precip_message('rain', now['weather-id'] < 600),
                get_precip_message('snow', 600 <= now['weather-id'] < 700))

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

        self.cache_icon(weather['icon'])

        return {
            "dt": dt,
            "days-from-now": (dt - today).days,
            "dt-pretty": pretty_date_str(dt),
            "temp": temps['temp'],
            # temp_min and temp_max aren't min and max in this time period, it's min and max in the region
            "low": temps['temp'],
            "high": temps['temp'],
            "weather": weather["description"],
            "weather-main": weather["main"],
            "weather-id": weather["id"],
            "weather-icon": weather["icon"],
            # regardless of imperial setting, we get mm as units
            "rain": mm_to_inch(get_precip_amount('rain')),
            "snow": mm_to_inch(get_precip_amount('snow'))
        }

    def get_updated_time(self):
        return self.forecast_today['dt-pretty']

    def get_todays_forecast(self):
        forecast = copy(self.forecast_today)
        if len(self.active_alerts) > 0:
            forecast['alerts'] = copy(self.active_alerts)

        return forecast

    def get_days(self):
        return self.days

    def get_periods_by_day(self, day=None):
        if not day:
           return self.periods_by_day[0]

        for day_, periods in zip(self.days, self.periods_by_day):
            if day_ == day:
                return periods

    def get_location_name(self):
        return self.location_name

    def cache_icon(self, icon_name):
        icon_path = f'cache/{icon_name}.png'
        if not path.exists(icon_path):
            image_data = easy_requests.get(f'http://openweathermap.org/img/wn/{icon_name}@2x.png', 'image/png')
            with open(icon_path, 'wb') as file:
                file.write(image_data)
