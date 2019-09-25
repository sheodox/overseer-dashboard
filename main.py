import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QGridLayout, \
    QBoxLayout, QGroupBox, QSizePolicy
from lights import Lights
from weather import Weather


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.lights = Lights()
        self.weather = Weather()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.setObjectName('top-level')

        self.create_lights_ui()
        self.layout.addStretch()
        self.create_weather_ui()

        with open('styles.css', 'r') as file:
            self.setStyleSheet(file.read())

        self.setWindowTitle('Overseer Dashboard')
        self.setMinimumWidth(650)
        self.setMinimumHeight(360)
        self.show()

    def create_lights_ui(self):
        lights_box = QGroupBox('Lights')
        layout = QVBoxLayout()
        lights_box.setLayout(layout)

        def create_light_button(l):
            button = QPushButton(l['name'])
            button.setStyleSheet("""
                background-color: #1a1e26; border: none;
            """)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            button.clicked.connect(lambda: self.lights.toggle(l['id']))
            layout.addWidget(button)

        for light in self.lights.get_lights():
            create_light_button(light)

        self.layout.addWidget(lights_box)

    def create_weather_ui(self):
        max_periods = 5
        weather_box = QGroupBox(f"Weather for {self.weather.get_location_name()}")
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
            print(day)
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
