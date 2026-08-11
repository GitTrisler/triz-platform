from core.module_sdk import TRIZModule, ModuleInfo

from modules.title_block_manager.page import TitleBlockManagerPage


class TitleBlockManagerModule(TRIZModule):
    def info(self):
        return ModuleInfo(
            id="title_block_manager",
            name="Title Block Manager",
            category="Drawing Automation",
            version="1.0.0",
            author="Trisler Automation",
            description="Update AutoCAD title block attributes from Excel data.",
            accent="#A78BFA",
        )

    def create_page(self):
        return TitleBlockManagerPage(platform=self.platform)


def create_module(platform=None):
    return TitleBlockManagerModule(platform)