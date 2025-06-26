import os
import json

CONFIG_DIR = "config"
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

def load_config():
    default_format = None

    if not os.path.exists(CONFIG_PATH):
        return {"date_format": default_format}

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    valid_formats = ["dd/mm/yyyy", "mm/dd/yyyy", "yyyy/mm/dd", "yyyy/dd/mm"]
    if config.get("date_format") not in valid_formats:
        config["date_format"] = default_format

    return config

def save_config(date_format):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"date_format": date_format}, f)
