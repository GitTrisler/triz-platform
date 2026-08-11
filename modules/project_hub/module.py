from core.module_sdk import TRIZModule, ModuleInfo

from modules.project_hub.page import ProjectHubPage


class ProjectHubModule(TRIZModule):
    def info(self):
        return ModuleInfo(
            id="project_hub",
            name="Project Hub",
            category="Drawing Automation",
            version="0.1.0",
            author="Trisler Automation",
            description="Index a project folder and search every drawing, tag, "
                        "revision, and deliverable from one place.",
            accent="#38BDF8",
        )

    def create_page(self):
        return ProjectHubPage(platform=self.platform)


def create_module(platform=None):
    return ProjectHubModule(platform)
