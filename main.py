import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QGridLayout
from lights import Lights
from weather import Weather


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.lights = Lights()
        self.weather = Weather()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_lights_ui()
        self.create_weather_ui()

        self.setWindowTitle('Overseer Dashboard')
        self.show()

    def create_lights_ui(self):
        self.layout.addWidget(QLabel('Lights'))

        def create_light_button(l):
            button = QPushButton(l['name'])

            button.clicked.connect(lambda: self.lights.toggle(l['id']))
            self.layout.addWidget(button)

        for light in self.lights.get_lights():
            create_light_button(light)

    def create_weather_ui(self):
        max_periods = 5
        weather_layout = QGridLayout()

        self.layout.addWidget(QLabel(f"Weather for {self.weather.get_location_name()}"))
        self.layout.addWidget(QLabel(f"last updated at {self.weather.get_updated_time()}"))
        self.layout.addLayout(weather_layout)
        today = self.weather.get_todays_forecast()
        self.layout.addWidget(QLabel(f"Now {today['temp']} {today['weather']} ({today['low']} - {today['high']})"))

        # skip the current day
        for day in self.weather.get_days()[1:]:
            print(day)
            self.layout.addWidget(QLabel(f'{day["dt-pretty"]} {day["low"]}-{day["high"]}'))


if __name__ == '__main__':
    app = QApplication([])
    dash = Dashboard()
    sys.exit(app.exec())
