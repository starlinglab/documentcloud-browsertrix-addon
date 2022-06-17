import os
import json
import time

import requests
from documentcloud.addon import AddOn

SERVER = "https://org1.browsertrix.stg.starlinglab.org"  # No ending slash
SECRETS = json.loads(os.environ["TOKEN"])
USERNAME = SECRETS[0]
PASSWORD = SECRETS[1]
# Archive ID, harcoded based on user account
AID = "7f6f11ac-ce5b-438e-8a5e-86986096e53d"
# Download WACZs into the folder above the workspace
# Workspace folder itself is used up because repo is cloned there
DOWNLOAD_DIR = os.path.normpath(os.path.join(os.environ["GITHUB_WORKSPACE"], ".."))


class Browsertrix(AddOn):
    def main(self):
        # First log in and get access token / JWT
        r = requests.post(
            f"{SERVER}/api/auth/jwt/login",
            data={"username": USERNAME, "password": PASSWORD},
        )
        r.raise_for_status()
        jwt = r.json()["access_token"]
        headers = {"Authorization": "Bearer " + jwt}

        # Add crawl config
        crawl_config = {
            "name": self.id,
            "colls": [],
            "crawlTimeout": 300,
            "scale": 1,
            "schedule": "",
            "runNow": False,
            "config": {
                "seeds": [self.data["site"]],
                "scopeType": "page",
                "depth": -1,
                "limit": 0,
                "extraHops": 0,
                "behaviorTimeout": 60,
                "behaviors": "autoscroll,autoplay,autofetch,siteSpecific",
            },
        }
        r = requests.post(
            f"{SERVER}/api/archives/{AID}/crawlconfigs/",
            json=crawl_config,
            headers=headers,
        )
        r.raise_for_status()
        cid = r.json()["added"]

        # Start crawl
        r = requests.post(
            f"{SERVER}/api/archives/{AID}/crawlconfigs/{cid}/run", headers=headers
        )
        r.raise_for_status()
        crawl_id = r.json()["started"]
        self.set_message("Crawl started")

        # Wait for crawl to finish
        while True:
            r = requests.get(
                f"{SERVER}/api/archives/{AID}/crawls/{crawl_id}.json",
                headers=headers,
            )
            resp = r.json()
            if resp.get("finished"):
                break
            time.sleep(5)

        if resp["state"] == "failed":
            self.set_message("Crawl failed")
            return

        # Download WACZ
        self.set_message("Crawl finished, downloading...")
        download_url = resp["resources"][0]["path"].split("?")[0]
        file_path = os.path.join(DOWNLOAD_DIR, self.id + ".wacz")
        r = requests.get(download_url, stream=True)
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # Delete crawl
        r = requests.post(
            f"{SERVER}/api/archives/{AID}/crawls/delete",
            json={"crawl_ids": [crawl_id]},
            headers=headers,
        )
        r.raise_for_status()

        # Upload WACZ
        self.set_message("Uploading WACZ to DocumentCloud...")
        with open(file_path, "rb") as f:
            self.upload_file(f)

        self.set_message("")


if __name__ == "__main__":
    Browsertrix().main()
