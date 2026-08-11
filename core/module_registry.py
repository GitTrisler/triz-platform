from dataclasses import dataclass
from typing import Any

from core.logger import log
from core.module_loader import discover_modules, load_module_instance


@dataclass
class RegisteredModule:
    id: str
    name: str
    category: str
    version: str
    author: str
    description: str
    accent: str
    manifest: dict
    instance: Any = None
    loaded: bool = False
    page: Any = None
    launch_count: int = 0


class ModuleRegistry:
    def __init__(self, platform=None):
        self.platform = platform
        self.modules: list[RegisteredModule] = []

    def scan(self):
        self.modules.clear()

        manifests = discover_modules()

        for manifest in manifests:
            instance = load_module_instance(manifest, platform=self.platform)

            if instance and hasattr(instance, "info"):
                info = instance.info()

                registered = RegisteredModule(
                    id=info.id,
                    name=info.name,
                    category=info.category,
                    version=info.version,
                    author=info.author,
                    description=info.description,
                    accent=info.accent,
                    manifest=manifest,
                    instance=instance,
                    loaded=True,
                )

                self.modules.append(registered)
                log(f"Registered SDK module: {info.name}")

            else:
                registered = RegisteredModule(
                    id=manifest.get("id", "unknown"),
                    name=manifest.get("name", "Unnamed Module"),
                    category=manifest.get("category", "General"),
                    version=manifest.get("version", "1.0.0"),
                    author=manifest.get("author", "Trisler Automation"),
                    description=manifest.get("description", ""),
                    accent=manifest.get("accent", "#38BDF8"),
                    manifest=manifest,
                    instance=instance,
                    loaded=False,
                )

                self.modules.append(registered)
                log(f"Registered legacy module: {registered.name}")

        return self.modules

    def all(self):
        return self.modules

    def by_name(self, name: str):
        for module in self.modules:
            if module.name == name:
                return module
        return None

    def by_category(self):
        grouped = {}

        for module in self.modules:
            grouped.setdefault(module.category, []).append(module)

        return grouped

    def search(self, query: str):
        query = query.lower().strip()

        if not query:
            return []

        results = []

        for module in self.modules:
            haystack = " ".join([
                module.name,
                module.category,
                module.description,
                module.author,
            ]).lower()

            if query in haystack:
                results.append(module)

        return results

    def create_page(self, module_name: str):
        module = self.by_name(module_name)

        if not module:
            return None

        if module.page is not None:
            return module.page

        if module.instance and hasattr(module.instance, "create_page"):
            try:
                if hasattr(module.instance, "on_load"):
                    module.instance.on_load()

                module.page = module.instance.create_page()
                module.launch_count += 1

                log(f"Created page for module: {module.name}")
                return module.page

            except Exception as e:
                log(f"Failed to create page for module {module.name}: {e}")
                return None

        return None
