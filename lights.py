import sys

import easy_requests
from config_reader import ConfigReader

cfg = ConfigReader()


class Lights:
    def __init__(self):
        self.overseer_url = f'http://{cfg.get("overseer")}/'
        self.lights = []
        self.refresh()

    def log(self, msg):
        print(f'[lights] {msg}')

    def refresh(self, data=None):
        if not data:
            data = easy_requests.get(f'{self.overseer_url}lights/info')

        if 'error' in data:
            self.log('error retrieving lights information, does overseer trust this device?')
            sys.exit(-1)

        self.lights = data

    def get_lights(self):
        return self.lights

    def toggle(self, light_id):
        # since IDs are numbers as strings, it's easy to forget to pass a string, ensure we're dealing with a string
        light_id = str(light_id)
        light_name = next(light['name'] for light in self.lights if light['id'] == light_id)

        self.log(f'toggling {light_id} ({light_name})')
        res = easy_requests.get(f'{self.overseer_url}lights/toggle/{light_id}')
        if 'error' in res:
            self.log(f'Error toggling lights: {res["error"]}')
        else:
            self.refresh()
