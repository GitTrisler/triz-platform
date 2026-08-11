import json
import importlib.util
from pathlib import Path

from core.logger import log


BASE_DIR = Path(__file__).resolve().parents[1]
MODULES_DIR = BASE_DIR / "modules"


def discover_modules():
    modules = []

    for folder in MODULES_DIR.iterdir():
        if not folder.is_dir():
            continue

        manifest_path = folder / "manifest.json"

        if not manifest_path.exists():
            continue

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["path"] = str(folder)
            modules.append(manifest)
            log(f"Discovered module manifest: {manifest.get('name', folder.name)}")

        except Exception as e:
            log(f"Failed to load module manifest: {manifest_path} | {e}")

    return modules


def load_module_instance(module_manifest, platform=None):
    try:
        module_path = Path(module_manifest["path"])
        entry_file = module_path / module_manifest.get("entry", "ui.py")

        if not entry_file.exists():
            log(f"Module entry file missing: {entry_file}")
            return None

        module_name = f"triz_module_{module_manifest.get('id', entry_file.stem)}"

        spec = importlib.util.spec_from_file_location(module_name, entry_file)
        imported = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(imported)

        if hasattr(imported, "create_module"):
            module = imported.create_module(platform)
            log(f"Loaded SDK module: {module.info().name}")
            return module

        if hasattr(imported, "create_page"):
            log(f"Loaded legacy module page: {module_manifest.get('name')}")
            return imported

        log(f"Module has no create_module or create_page: {module_manifest.get('name')}")
        return None

    except Exception as e:
        log(f"Failed to load module {module_manifest.get('name')}: {e}")
        return None
