import sys
from datetime import datetime

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QGroupBox, QSizePolicy

from lights import Lights
from pretty import pretty_weekday, pretty_date_only_str, pretty_time_str
from weather import Weather


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.lights = Lights()
        self.weather = Weather()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.setObjectName('top-level')

        self.clock_date = None
        self.clock_time = None
        self.light_buttons = {}
        self.create_lights_ui()
        self.layout.addStretch()
        self.weather_box = None
        self.create_weather_ui()

        self.weather_update_timeout = 1000 * 300  # five minutes, weather reports only update every 10 minutes
        self.light_refresh_timeout = 1000 * 10
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

    def create_clock(self, layout):
        self.clock_time = QLabel('')
        self.clock_date = QLabel('')
        self.clock_date.setAlignment(Qt.AlignRight)
        self.clock_time.setObjectName('clock-time')
        self.clock_date.setObjectName('clock-date')
        layout.addWidget(self.clock_time)
        layout.addWidget(self.clock_date)
        self.interval(self.update_time, 1000)
        self.update_time()  # set the time immediately

    def refresh_lights(self):
        self.lights.refresh()
        self.set_light_on_status()

    def update_time(self):
        now = datetime.now()
        self.clock_date.setText(f'{pretty_weekday(now)} {pretty_date_only_str(now)}')
        self.clock_time.setText(pretty_time_str(now))

    def interval(self, fn, ms):
        timer = QTimer(self)
        timer.timeout.connect(fn)
        timer.start(ms)

    def rebuild_weather(self):
        self.weather.refresh()
        self.create_weather_ui()

    def create_lights_ui(self):
        column = QVBoxLayout()
        self.create_clock(column)
        lights_box = QGroupBox('Lights')
        column.addWidget(lights_box)
        layout = QVBoxLayout()
        lights_box.setLayout(layout)

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
        self.layout.addLayout(column)

    def set_light_on_status(self):
        for light in self.lights.get_lights():
            button = self.light_buttons[light['id']]
            button.setProperty('light-on', light['on'])
            self.update_widget(button)

    def update_widget(self, widget):
        self.style().unpolish(widget)
        self.style().polish(widget)

    def create_weather_ui(self):
        if self.weather_box != None:
            self.layout.removeWidget(self.weather_box)
            self.weather_box.deleteLater()
        weather_box = QGroupBox(f"Weather for {self.weather.get_location_name()}")
        self.weather_box = weather_box
        weather_layout = QVBoxLayout()
        weather_box.setLayout(weather_layout)

        today = self.weather.get_todays_forecast()
        today_row_layout = QHBoxLayout()
        weather_layout.addLayout(today_row_layout)
        today_left = QVBoxLayout()
        today_right = QVBoxLayout()

        today_left.addWidget(QLabel(f"last updated at {self.weather.get_updated_time()}"))
        today_row_layout.addLayout(today_left)
        today_row_layout.addStretch()
        today_row_layout.addLayout(today_right)
        current_temp = QLabel(today['temp-pretty'])
        current_temp.setObjectName('current-temperature')
        self.set_temp_color(current_temp, today['temp'])
        today_right.addWidget(current_temp)
        low_label = QLabel(today['low-pretty'])
        self.set_temp_color(low_label, today['low'])
        high_label = QLabel(today['high-pretty'])
        self.set_temp_color(high_label, today['high'])
        self.in_h_layout(today_right, low_label, QLabel('-'), high_label)
        today_right.addWidget(QLabel(f"{today['weather']}"))

        if 'next_rain' in today:
            today_left.addWidget(QLabel(today['next_rain']))
        if 'next_snow' in today:
            today_left.addWidget(QLabel(today['next_snow']))
        today_left.addStretch()
        today_right.addStretch()

        weather_layout.addStretch()
        days_layout = QHBoxLayout()
        days_layout.classes = 'forecast-days'
        # skip the current day
        for day in self.weather.get_days()[1:]:
            label = lambda text: day_layout.addWidget(QLabel(text))
            day_box = QGroupBox(day['dt-pretty'])
            day_layout = QVBoxLayout()
            label(f"{day['low']} - {day['high']}")
            if day['rain'] is not None:
                label(f"{day['rain']} rain")
            if day['snow'] is not None:
                label(f"{day['snow']} snow")
            day_layout.addStretch()
            day_box.setLayout(day_layout)
            days_layout.addWidget(day_box)

        weather_layout.addLayout(days_layout)
        self.layout.addWidget(weather_box)

    def in_v_layout(self, parent, *widgets):
        layout = QVBoxLayout()
        for widget in widgets:
            layout.addWidget(widget)
        parent.addLayout(layout)

    def in_h_layout(self, parent, *widgets):
        layout = QHBoxLayout()
        for widget in widgets:
            layout.addWidget(widget)
        parent.addLayout(layout)

    def set_temp_color(self, widget, temp):
        widget.setStyleSheet(f'color: #{self.get_temperature_color(temp)}')

    def get_temperature_color(self, degrees):
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



if __name__ == '__main__':
    app = QApplication([])
    dash = Dashboard()
    sys.exit(app.exec())
