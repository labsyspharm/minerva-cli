import os
import sys
import pathlib
import stat
from getpass import getpass

class Configurer:
    DEFAULT_REGION = "us-east-1"
    DEFAULT_CLIENT_ID = "2amp6q8t55a0usvo63cqu5vj11"

    def __init__(self):
        self.config = {}

    def interactive_config(self):
        config_path = os.path.join(pathlib.Path.home(), ".minerva")
        print("Writing configuration into ", config_path)

        self.config["MINERVA_REGION"] = self.ask_value("AWS Region", Configurer.DEFAULT_REGION)
        self.config["MINERVA_ENDPOINT"] = self.ask_endpoint()
        self.config["MINERVA_CLIENT_ID"] = self.ask_value("Minerva Client Id", Configurer.DEFAULT_CLIENT_ID)
        self.config["MINERVA_USERNAME"] = self.ask_value("Minerva username", required=False)
        self.config["MINERVA_PASSWORD"] = self.ask_password()

        with open(config_path, "w") as config_file:
            config_file.write("[Minerva]\n")
            for key, value in self.config.items():
                line = "{} = {}\n".format(key, value)
                config_file.write(line)

        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
        print("Configuration done.")

    def ask_value(self, description, default="", required=True):
        value = None
        tries = 0
        while not value:
            if tries > 3:
                print("Aborting configuration")
                sys.exit(-1)

            value = input(description + " [" + str(default) + "]: ")
            value = value.strip()
            if not value:
                value = default

            if not required:
                break

            tries += 1

        return value

    def ask_endpoint(self):
        endpoint = self.ask_value("Minerva Endpoint")
        if not endpoint.startswith("https://"):
            endpoint = "https://" + endpoint
        return endpoint

    def ask_password(self):
        return getpass(prompt='Minerva password: ')
