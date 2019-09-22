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
        return self.config[name]
