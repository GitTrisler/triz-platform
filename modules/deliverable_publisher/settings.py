from core.module_settings import ModuleSettings


DEFAULTS = {
    "drawing_folder": "",
    "output_folder": "",
    "page_setup": "Deliverable Publisher",
    "overwrite_pdfs": True,
    "close_drawings_after_publish": True,
    "write_csv_log": True,
    "recurse": True,
    "template_dwg": "",
    "layout_mode": "model",
    "layout_filter": "ISO",
    "merge_folder": "",
    "merge_name": "Merged.pdf",
    "merge_recurse": False,
    "merge_archive_sources": False,
}


def get_settings():
    return ModuleSettings(
        "deliverable_publisher",
        defaults=DEFAULTS
    )