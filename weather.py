from config_reader import ConfigReader
from datetime import datetime
import easy_requests

cfg = ConfigReader()


def pretty_date_str(iso_date):
    return datetime.fromisoformat(iso_date).astimezone().strftime("%m/%d/%Y %I:%M:%S %p")


class Weather:
    def __init__(self):
        # get a url to get the forecast based on the coordinates
        point_res = easy_requests.get(f'https://api.weather.gov/points/{cfg.get("latitude")},{cfg.get("longitude")}')
        self.forecast_url = point_res['properties']['forecast']
        self.updated = ''
        rel_loc = point_res['properties']['relativeLocation']['properties']
        self.location_name = f'{rel_loc["city"]}, {rel_loc["state"]}'
        self.periods = []
        self.refresh()

    def refresh(self):
        forecast = easy_requests.get(self.forecast_url)['properties']
        self.updated = pretty_date_str(forecast['updated'])
        self.periods = forecast['periods']
        print(self.updated)

    def get_updated_time(self):
        return self.updated

    def get_periods(self):
        return self.periods

    def get_location_name(self):
        return self.location_name
