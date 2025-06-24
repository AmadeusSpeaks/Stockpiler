import os
import json

CONFIG_DIR = "config"
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

def load_config():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    if not os.path.exists(CONFIG_PATH):
        return {"date_format": ""}

    with open(CONFIG_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"date_format": ""}

def save_config(date_format):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"date_format": date_format}, f)
