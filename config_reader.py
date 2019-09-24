import json
import sys


class ConfigReader:
    def __init__(self):
        try:
            with open('config.json') as file:
                self.config = json.load(file)
        except FileNotFoundError:
            print('missing config.json file!')
            sys.exit(-1)

    def get(self, name):
        if name not in self.config:
            print(f'config error - tried to access "{name}" but it couldn\'t be found')
        return self.config[name]
