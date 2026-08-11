import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_FILE = BASE_DIR / "triz_platform_settings.json"


def load_config():
    default = {
        "user": "Cody",
        "theme": "dark",
        "startup_page": "Dashboard"
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                default.update(json.load(f))
        except Exception:
            pass

    return default


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
