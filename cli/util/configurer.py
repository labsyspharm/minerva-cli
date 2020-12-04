import os
import pathlib
import stat

class Configurer:
    def __init__(self):
        self.config = {}

    def interactive_config(self):
        config_path = os.path.join(pathlib.Path.home(), ".minerva")
        print("Writing configuration into ", config_path)

        self.config["MINERVA_REGION"] = self.ask_value("AWS Region", "us-east-1")
        self.config["MINERVA_ENDPOINT"] = self.ask_value("Minerva Endpoint")
        self.config["MINERVA_CLIENT_ID"] = self.ask_value("Minerva Client Id")
        self.config["MINERVA_USERNAME"] = self.ask_value("Minerva username", required=False)
        self.config["MINERVA_PASSWORD"] = self.ask_value("Minerva password", required=False)

        with open(config_path, "w") as config_file:
            config_file.write("[Minerva]\n")
            for key, value in self.config.items():
                line = "{} = {}\n".format(key, value)
                config_file.write(line)

        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
        print("Configuration done.")

    def ask_value(self, description, default="", required=True):
        value = None
        while not value:
            value = input(description + " [" + str(default) + "]: ")
            value = value.strip()
            if not value:
                value = default

            if not required:
                break

        return value