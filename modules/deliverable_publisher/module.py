from core.module_sdk import TRIZModule, ModuleInfo

from modules.deliverable_publisher.page import DeliverablePublisherPage


class DeliverablePublisherModule(TRIZModule):
    def info(self):
        return ModuleInfo(
            id="deliverable_publisher",
            name="Deliverable Publisher",
            category="Drawing Automation",
            version="1.0.0",
            author="Trisler Automation",
            description="Batch plot and publish drawing packages.",
            accent="#22C55E",
        )

    def create_page(self):
        return DeliverablePublisherPage(platform=self.platform)


def create_module(platform=None):
    return DeliverablePublisherModule(platform)