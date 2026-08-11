from PySide6.QtWidgets import QFileDialog, QSizePolicy

from ui.triz_widgets import TRIZCard, FormField


class SetupPanel(TRIZCard):
    def __init__(self):
        super().__init__("Set Up", step=1, color="#38BDF8")

        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.drawing_folder = FormField(
            label="Drawing Folder",
            placeholder="Select drawing folder...",
            browse_text="Browse",
            browse_callback=self.browse_drawing_folder,
        )

        self.output_folder = FormField(
            label="Output Folder",
            placeholder="Select output folder...",
            browse_text="Browse",
            browse_callback=self.browse_output_folder,
        )

        self.page_setup = FormField(
            label="Page Setup",
            placeholder="Page setup name...",
        )

        self.template_dwg = FormField(
            label="Template DWG",
            placeholder="Optional template DWG containing page setup...",
            browse_text="Browse",
            browse_callback=self.browse_template_dwg,
        )

        self.layout.setSpacing(10)
        self.layout.addWidget(self.drawing_folder)
        self.layout.addWidget(self.output_folder)
        self.layout.addWidget(self.page_setup)
        self.layout.addWidget(self.template_dwg)

    def browse_drawing_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Drawing Folder")
        if folder:
            self.drawing_folder.set_text(folder)

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder.set_text(folder)

    def browse_template_dwg(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template DWG",
            "",
            "AutoCAD Drawing (*.dwg);;All Files (*.*)"
        )
        if file_path:
            self.template_dwg.set_text(file_path)

    def values(self):
        return {
            "drawing_folder": self.drawing_folder.text().strip(),
            "output_folder": self.output_folder.text().strip(),
            "page_setup": self.page_setup.text().strip(),
            "template_dwg": self.template_dwg.text().strip(),
        }

    def set_values(self, values: dict):
        self.drawing_folder.set_text(values.get("drawing_folder", ""))
        self.output_folder.set_text(values.get("output_folder", ""))
        self.page_setup.set_text(values.get("page_setup", "Deliverable Publisher"))
        self.template_dwg.set_text(values.get("template_dwg", ""))