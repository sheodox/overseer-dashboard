import errno
import os
import sys
from datetime import datetime

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QSizePolicy, QMessageBox, \
    QScrollArea, QHBoxLayout, QScroller

from lights import Lights
from pretty import pretty_weekday, pretty_date_only_str, pretty_time_str, pretty_time_str_short
from uibuilder import UIBuilder
from weather import Weather

# icon cache directory
try:
    os.makedirs('cache')
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

with open('styles.css', 'r') as file:
    default_styles = file.read()
forecast_day_template = """
                QPushButton#forecast-day-{i}-details(expanding=true,style=height:150px;)
                    QVBoxLayout
                        QLabel#forecast-day-{i}
                        QLabel#forecast-day-{i}-icon
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

periods_detail_template = """
QGroupBox(detail-group=true)
    QVBoxLayout
        QHBoxLayout
            QLabel#time-{i}
            QLabel#temp-{i}
        QLabel#icon-{i}
        QLabel#conditions-{i}
        QLabel#rain-{i}
        QLabel#snow-{i}
        stretch
"""


def scale_template(template, times):
    temp = ''
    for i in range(times):
        temp += template.replace('{i}', str(i))
    return temp


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
        raw_ui += scale_template(forecast_day_template, 5)
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

        self.setStyleSheet(default_styles)
        self.setWindowTitle('Overseer Dashboard')
        self.show()

        # can be run using 'start_fullscreen.sh' for touch screens
        if 'fullscreen' in sys.argv:
            self.showFullScreen()
        else:
            self.setMinimumWidth(800)
            self.setMinimumHeight(480)

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
            button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)

            button.clicked.connect(on_click)
            layout.addWidget(button)

        lights = self.lights.get_lights()
        if len(lights) is 0:
            self.ui.show('lights-error')
            self.ui.hide('lights-container')
        else:
            self.ui.hide('lights-error')
            self.ui.show('lights-container')

        for light in lights:
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
        self.ui.set_icon('current-icon', today['weather-icon'])
        self.connect_forecast_listener('today-details')

        if 'alerts' in today:
            self.ui.show('today-alert')
            alerts = today['alerts']
            self.ui.set_text('today-alert', f'{len(alerts)} active alert{"s" if len(alerts) > 1 else ""}')
            self.connect_alert_listener('today-alert', alerts)
        else:
            self.ui.hide('today-alert')

        for index, precip_msg in enumerate(self.weather.get_upcoming_precip_message()):
            self.ui.set_text(f'upcoming-{index}', precip_msg)

        # skip the current day
        for i, day in enumerate(self.weather.get_days()[1:]):
            self.ui.set_text(f'forecast-day-{i}', day['dt-pretty'])
            self.ui.set_text(f'forecast-day-{i}-conditions', day['weather'])
            self.connect_forecast_listener(f'forecast-day-{i}-details', day)
            set_temp(f'forecast-day-{i}-low', day, 'low')
            set_temp(f'forecast-day-{i}-high', day, 'high')
            self.ui.set_icon(f'forecast-day-{i}-icon', day['weather-icon'], 50)

            # there might be both types of precip, show one or both, but don't leave a blank line if there's only snow
            precip_num = 0
            for precip in ['rain', 'snow']:
                if day[precip] is not None:
                    self.ui.set_text(f'forecast-day-{i}-precip-{precip_num}', day[precip])
                    precip_num += 1

    def connect_alert_listener(self, id, alerts):
        def show_weather_alert():
            layout = QVBoxLayout()
            for alert in alerts:
                header = QLabel(alert['headline'])
                header.setWordWrap(True)
                header.setProperty('header', True)
                layout.addWidget(header)
                layout.addWidget(QLabel(f"{alert['description']}"))

            box = ScrollMessageBox('Weather Alert', layout)

        self.ui.on_click(id, show_weather_alert)

    def connect_forecast_listener(self, id, day=None):
        def show_forecast():
            periods = self.weather.get_periods_by_day(day)
            # if it's late in the day for the current day, we might not have any more information, show an alert instead
            if periods is None:
                alert = Alert('No more data', "It is late and there is no more available data for today.")
                return

            layout = QHBoxLayout()
            ui = UIBuilder(layout, scale_template(periods_detail_template, len(periods)))

            for i, period in enumerate(periods):
                ui.set_text(f'time-{i}', pretty_time_str_short(period['dt']))
                ui.set_icon(f'icon-{i}', period['weather-icon'], 75)

                temp_id = f'temp-{i}'
                ui.set_text(temp_id, period['temp-pretty'])
                ui.by_id(temp_id).setStyleSheet(get_temp_color_stylesheet(period['temp']))
                ui.set_text(f'conditions-{i}', period['weather'])

                def show_precip(precip_type):
                    precip = period[precip_type]
                    precip_id = f'{precip_type}-{i}'
                    if precip is not None:
                        ui.set_text(precip_id, precip)
                    else:
                        ui.hide(precip_id)

                for precip_type in ['rain', 'snow']:
                    show_precip(precip_type)

            pretty_day = day["dt-pretty"] if day is not None else "Today"
            dlg = ScrollMessageBox(f'Weather for {pretty_day}', layout)

        self.ui.on_click(id, show_forecast)


class Alert(QMessageBox):
    def __init__(self, window_title, window_text):
        QMessageBox.__init__(self)
        self.setWindowTitle(window_title)
        self.setText(window_text)
        self.setObjectName('top-level')
        self.setStyleSheet(default_styles)
        self.exec()


class ScrollMessageBox(QMessageBox):
    def __init__(self, window_title, child_layout):
        QMessageBox.__init__(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        widget = QWidget()
        scroll.setWidget(widget)
        scroll.setMinimumSize(400, 200)
        QScroller.grabGesture(scroll, QScroller.LeftMouseButtonGesture)
        self.scroll_layout = QVBoxLayout()
        widget.setLayout(child_layout)

        self.setObjectName('top-level')
        self.setStyleSheet(default_styles)
        self.setWindowTitle(window_title)
        self.layout().addWidget(scroll, 0, 0, 1, 0)
        self.exec()


if __name__ == '__main__':
    app = QApplication([])
    dash = Dashboard()
    sys.exit(app.exec())
