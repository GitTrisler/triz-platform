from core.module_settings import ModuleSettings


DEFAULTS = {
    "drawing_folder": "",
    "output_folder": "",
    "page_setup": "Deliverable Publisher",
    "overwrite_pdfs": True,
    "close_drawings_after_publish": True,
}


def get_settings():
    return ModuleSettings(
        "deliverable_publisher",
        defaults=DEFAULTS
    )