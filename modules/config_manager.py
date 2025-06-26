import os
import json

CONFIG_DIR = "config"
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

def load_config():
    default_format = None
    default_theme = "light"

    if not os.path.exists(CONFIG_PATH):
        return {"date_format": default_format, "theme": default_theme}

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    valid_formats = ["dd/mm/yyyy", "mm/dd/yyyy", "yyyy/mm/dd", "yyyy/dd/mm"]
    if config.get("date_format") not in valid_formats:
        config["date_format"] = default_format

    if config.get("theme") not in ["light", "dark"]:
        config["theme"] = default_theme

    return config


def save_config(date_format=None, theme=None):
    os.makedirs(CONFIG_DIR, exist_ok=True)

    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

    if date_format is not None:
        config["date_format"] = date_format
    if theme is not None:
        config["theme"] = theme

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)
