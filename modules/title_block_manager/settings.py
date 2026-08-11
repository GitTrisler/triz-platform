from core.module_settings import ModuleSettings


DEFAULTS = {
    "excel_file": "",
    "drawing_folder": "",
    "worksheet": "",
    "key_column": "CADFILE",
    "block_name": "TITLEBLOCK",
    "dry_run": True,
    "replace_fields": False,
    "write_blank_values": False,
    "include_subfolders": True,
}


def get_settings():
    return ModuleSettings(
        "title_block_manager",
        defaults=DEFAULTS
    )