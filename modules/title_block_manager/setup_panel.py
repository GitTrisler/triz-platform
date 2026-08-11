from PySide6.QtWidgets import QFileDialog

from ui.triz_widgets import TRIZCard, FormField


class SetupPanel(TRIZCard):
    def __init__(self):
        super().__init__("Set Up", step=1, color="#A78BFA")

        self.drawing_folder = FormField(
            label="Drawing Folder",
            placeholder="Select ISO or drawing folder...",
            browse_text="Browse",
            browse_callback=self.browse_drawing_folder,
        )

        self.output_folder = FormField(
            label="Excel Output Folder",
            placeholder="Where generated template should be saved...",
            browse_text="Browse",
            browse_callback=self.browse_output_folder,
        )

        self.excel_file = FormField(
            label="Completed Excel File",
            placeholder="Optional until update time...",
            browse_text="Browse",
            browse_callback=self.browse_excel_file,
        )

        self.block_name = FormField(
            label="Block Name",
            placeholder="TITLEBLOCK",
        )

        self.key_column = FormField(
            label="Key Column",
            placeholder="CADFILE",
        )

        self.layout.setSpacing(10)
        self.layout.addWidget(self.drawing_folder)
        self.layout.addWidget(self.output_folder)
        self.layout.addWidget(self.excel_file)
        self.layout.addWidget(self.block_name)
        self.layout.addWidget(self.key_column)

    def browse_drawing_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Drawing Folder")
        if folder:
            self.drawing_folder.set_text(folder)

            # Default output folder to the selected drawing folder if empty.
            if not self.output_folder.text().strip():
                self.output_folder.set_text(folder)

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Excel Output Folder")
        if folder:
            self.output_folder.set_text(folder)

    def browse_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Completed Excel Workbook",
            "",
            "Excel Files (*.xlsx *.xlsm *.xls);;All Files (*.*)"
        )
        if file_path:
            self.excel_file.set_text(file_path)

    def values(self):
        return {
            "drawing_folder": self.drawing_folder.text().strip(),
            "output_folder": self.output_folder.text().strip(),
            "excel_file": self.excel_file.text().strip(),
            "block_name": self.block_name.text().strip(),
            "key_column": self.key_column.text().strip(),
        }

    def set_values(self, values: dict):
        self.drawing_folder.set_text(values.get("drawing_folder", ""))
        self.output_folder.set_text(values.get("output_folder", ""))
        self.excel_file.set_text(values.get("excel_file", ""))
        self.block_name.set_text(values.get("block_name", "TITLEBLOCK"))
        self.key_column.set_text(values.get("key_column", "CADFILE"))