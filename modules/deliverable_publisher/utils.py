import shutil
from datetime import datetime
from pathlib import Path

from modules.deliverable_publisher.models import PublishConfig


ACC_TEMP_ROOT = Path(
    r"E:\Cody TEST\Isometric\QED\ProdIsos\Drawings\DeliverablePublisher_ACC"
)


def is_acc_cache_path(path: Path) -> bool:
    text = str(path).lower()
    return "collaborationcache" in text or "collaboration cache" in text


def create_working_copy(path: Path, temp_root: Path, ui_logger):
    if not is_acc_cache_path(path):
        return path, False

    ui_logger("  [WARN] ACC CollaborationCache detected - creating working copy...")

    temp_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    temp_name = f"{path.stem}_{timestamp}{path.suffix}"
    temp_path = temp_root / temp_name

    shutil.copy2(path, temp_path)

    ui_logger(f"  [OK] Working copy: {temp_path.name}")

    return temp_path, True


def cleanup_temp_file(path: Path, ui_logger) -> None:
    try:
        if path and path.exists():
            path.unlink()
            ui_logger(f"  [OK] Cleaned up temp file: {path.name}")
    except Exception as e:
        ui_logger(f"  [WARN] Could not delete temp file: {e}")


def select_layouts(all_layouts: list[str], mode: str, filter_text: str = "") -> list[str]:
    selected = []

    if mode == "model":
        for name in all_layouts:
            if name.lower() == "model":
                selected.append(name)

    elif mode == "all":
        for name in all_layouts:
            if name.lower() != "model":
                selected.append(name)

    elif mode == "filter":
        filter_lower = filter_text.lower()

        for name in all_layouts:
            if name.lower() != "model" and filter_lower in name.lower():
                selected.append(name)

    return selected


def generate_pdf_path(
    dwg_path: Path,
    layout_name: str,
    config: PublishConfig
) -> Path:
    safe_layout = (
        layout_name
        .replace(" ", "_")
        .replace("/", "-")
        .replace("\\", "-")
    )

    if layout_name.lower() == "model":
        pdf_name = f"{dwg_path.stem}.pdf"
    else:
        pdf_name = f"{dwg_path.stem}_{safe_layout}.pdf"

    if config.selection_mode == "files" or config.folder_mode == "flat":
        return config.output_root / pdf_name

    try:
        rel_path = dwg_path.parent.relative_to(config.input_root)
    except ValueError:
        rel_path = Path()

    return config.output_root / rel_path / pdf_name