import os
import json

from documentcloud.addon import AddOn

SERVER = "https://org1.browsertrix.stg.starlinglab.org"  # No ending slash
SECRETS = json.loads(os.environ["TOKEN"])
USERNAME = SECRETS[0]
PASSWORD = SECRETS[1]


class Browsertrix(AddOn):
    def main(self):
        pass


if __name__ == "__main__":
    Browsertrix().main()
