import sys
from datetime import datetime

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QGroupBox, QSizePolicy

from lights import Lights
from pretty import pretty_weekday, pretty_date_only_str, pretty_time_str
from weather import Weather
from uibuilder import UIBuilder

forecast_day = """
                 QGroupBox#forecast-day-{i}
                    QVBoxLayout
                        QHBoxLayout
                            QLabel#forecast-day-{i}-low.temperature
                            QLabel -
                            QLabel#forecast-day-{i}-high.temperature
                            stretch
                        QLabel#forecast-day-{i}-conditions
                        //like the upcoming precip for today, we could have one or both types of precip, don't leave a gap
                        QLabel#forecast-day-{i}-precip-0
                        QLabel#forecast-day-{i}-precip-1
                        stretch
"""


def get_temperature_color(degrees):
    if degrees > 100:
        return 'cc006c'
    elif degrees > 90:
        return 'fe3300'
    elif degrees > 80:
        return 'fe6601'
    elif degrees > 70:
        return 'fe8a33'
    elif degrees > 60:
        return 'ffbf00'
    elif degrees > 50:
        return 'fdff00'
    elif degrees > 40:
        return '3fff6e'
    elif degrees > 30:
        return '34cbc6'
    elif degrees > 20:
        return '35cbcb'
    elif degrees > 10:
        return '009afe'
    elif degrees > 0:
        return '2f34c9'
    elif degrees > -10:
        return '6a00ce'
    elif degrees > -20:
        return '9901f6'
    elif degrees > -30:
        return 'cd98fe'
    else:
        return 'e3e1ed'


def get_temp_color_stylesheet(temp):
    return f'color: #{get_temperature_color(temp)};'


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.lights = Lights()
        self.weather = Weather()
        self.setObjectName('top-level')
        with open('ui.txt') as file:
            raw_ui = file.read()
        for day_num in range(5):
            raw_ui += forecast_day.replace('{i}', str(day_num))
        self.ui = UIBuilder(self, raw_ui)

        self.update_time()  # set the time immediately
        self.light_buttons = {}
        self.create_lights_ui()
        self.weather_box = None
        self.update_weather_ui()

        self.weather_update_timeout = 1000 * 300  # five minutes, weather reports only update every 10 minutes
        self.light_refresh_timeout = 1000 * 10
        self.interval(self.update_time, 1000)
        self.interval(self.rebuild_weather, self.weather_update_timeout)
        # poll every so often just in case the lights are changed elsewhere
        self.interval(self.refresh_lights, self.light_refresh_timeout)

        with open('styles.css', 'r') as file:
            self.setStyleSheet(file.read())

        self.setWindowTitle('Overseer Dashboard')
        self.setMinimumWidth(650)
        self.setMinimumHeight(360)
        self.show()

        # can be run using 'start_fullscreen.sh' for touch screens
        if 'fullscreen' in sys.argv:
            self.showFullScreen()

    def refresh_lights(self):
        self.lights.refresh()
        self.set_light_on_status()

    def update_time(self):
        now = datetime.now()
        self.ui.set_text('clock-date', f'{pretty_weekday(now)} {pretty_date_only_str(now)}')
        self.ui.set_text('clock-time', pretty_time_str(now))

    def interval(self, fn, ms):
        timer = QTimer(self)
        timer.timeout.connect(fn)
        timer.start(ms)

    def rebuild_weather(self):
        self.weather.refresh()
        self.update_weather_ui()

    def create_lights_ui(self):
        layout = self.ui.by_id('lights-box')

        def create_light_button(l):
            def on_click():
                self.lights.toggle(l['id'])
                self.set_light_on_status()

            button = QPushButton(l['name'])
            self.light_buttons[l['id']] = button
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            button.clicked.connect(on_click)
            layout.addWidget(button)

        for light in self.lights.get_lights():
            create_light_button(light)

        self.set_light_on_status()

    def set_light_on_status(self):
        for light in self.lights.get_lights():
            button = self.light_buttons[light['id']]
            button.setProperty('light-on', light['on'])
            self.update_widget(button)

    def update_widget(self, widget):
        self.style().unpolish(widget)
        self.style().polish(widget)

    def update_weather_ui(self):
        def set_temp(id, weather_data, temp_attr):
            self.ui.set_text(id, weather_data[f'{temp_attr}-pretty'])
            self.ui.set_stylesheet(id, get_temp_color_stylesheet(weather_data[temp_attr]))

        self.ui.set_text('weather-box', f"Weather for {self.weather.get_location_name()}")

        today = self.weather.get_todays_forecast()
        self.ui.set_text('updated-time', f"last updated at {self.weather.get_updated_time()}")

        set_temp('current-temperature', today, 'temp')
        set_temp('today-low', today, 'low')
        set_temp('today-high', today, 'high')
        self.ui.set_text('current-conditions', f"{today['weather']}")

        for index, precip_msg in enumerate(self.weather.get_upcoming_precip_message()):
            self.ui.set_text(f'upcoming-{index}', precip_msg)

        # skip the current day
        for i, day in enumerate(self.weather.get_days()[1:]):
            self.ui.set_text(f'forecast-day-{i}', day['dt-pretty'])
            self.ui.set_text(f'forecast-day-{i}-conditions', day['weather'])
            set_temp(f'forecast-day-{i}-low', day, 'low')
            set_temp(f'forecast-day-{i}-high', day, 'high')

            # there might be both types of precip, show one or both, but don't leave a blank line if there's only snow
            precip_num = 0
            for precip in ['rain', 'snow']:
                if day[precip] is not None:
                    self.ui.set_text(f'forecast-day-{i}-precip-{precip_num}', day[precip])
                    precip_num += 1


if __name__ == '__main__':
    app = QApplication([])
    dash = Dashboard()
    sys.exit(app.exec())
