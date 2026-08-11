import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
SETTINGS_DIR = BASE_DIR / "settings"
SETTINGS_DIR.mkdir(exist_ok=True)


class ModuleSettings:
    def __init__(self, module_id: str, defaults: dict | None = None):
        self.module_id = module_id
        self.defaults = defaults or {}
        self.path = SETTINGS_DIR / f"{module_id}.json"
        self.data = self.load()

    def load(self) -> dict:
        data = dict(self.defaults)

        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                data.update(saved)
            except Exception:
                pass

        return data

    def save(self):
        self.path.write_text(
            json.dumps(self.data, indent=4),
            encoding="utf-8"
        )

    def get(self, key: str, default: Any = None):
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()

    def update(self, values: dict):
        self.data.update(values)
        self.save()
