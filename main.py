import sys

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QGridLayout, \
    QBoxLayout, QGroupBox, QSizePolicy, QGraphicsBlurEffect, QAction
from datetime import datetime
from lights import Lights
from weather import Weather
from pretty import pretty_weekday, pretty_date_only_str, pretty_time_str


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.lights = Lights()
        self.weather = Weather()
        self.layout = QHBoxLayout()
        self.weather_update_timeout = 1000 * 300  # five minutes, weather reports only update every 10 minutes
        self.setLayout(self.layout)
        self.setObjectName('top-level')

        self.clock_date = None
        self.clock_time = None
        self.light_buttons = {}
        self.create_lights_ui()
        self.layout.addStretch()
        self.weather_box = None
        self.create_weather_ui()

        self.interval(self.rebuild_weather, self.weather_update_timeout)

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

        weather_layout.addWidget(QLabel(f"last updated at {self.weather.get_updated_time()}"))
        today = self.weather.get_todays_forecast()
        weather_layout.addWidget(QLabel(f"Now {today['temp']} {today['weather']} ({today['low']} - {today['high']})"))
        if 'next_rain' in today:
            weather_layout.addWidget(QLabel(today['next_rain']))
        if 'next_snow' in today:
            weather_layout.addWidget(QLabel(today['next_snow']))

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

if __name__ == '__main__':
    app = QApplication([])
    dash = Dashboard()
    sys.exit(app.exec())
