from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
)

from ui.workflow_stepper import WorkflowStepper
from ui.progress_widget import TRIZProgressWidget


class ModuleWorkspace(QWidget):
    def __init__(
        self,
        title,
        subtitle="",
        steps=None,
        left_width=5,
        right_width=4,
        scroll=True,
    ):
        super().__init__()

        self.left_width = left_width
        self.right_width = right_width

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("Title")

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("Subtitle")

        root.addWidget(self.title_label)
        root.addWidget(self.subtitle_label)

        self.stepper = WorkflowStepper(steps=steps)
        self.progress_widget = TRIZProgressWidget()

        self.left_column = QVBoxLayout()
        self.left_column.setSpacing(14)

        self.right_column = QVBoxLayout()
        self.right_column.setSpacing(14)

        columns = QHBoxLayout()
        columns.setSpacing(14)
        columns.addLayout(self.left_column, stretch=left_width)
        columns.addLayout(self.right_column, stretch=right_width)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 4, 0)
        self.content_layout.setSpacing(12)

        self.content_layout.addWidget(self.stepper)
        self.content_layout.addLayout(columns)
        self.content_layout.addWidget(self.progress_widget)
        self.content_layout.addStretch()

        if scroll:
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setFrameShape(QScrollArea.NoFrame)
            self.scroll_area.setWidget(content)
            self.scroll_area.setStyleSheet(
                """
                QScrollArea {
                    background: transparent;
                    border: none;
                }

                QScrollArea > QWidget > QWidget {
                    background: transparent;
                }

                QScrollBar:vertical {
                    background: #0B1220;
                    width: 10px;
                    margin: 0px;
                    border-radius: 5px;
                }

                QScrollBar::handle:vertical {
                    background: #374151;
                    min-height: 30px;
                    border-radius: 5px;
                }

                QScrollBar::handle:vertical:hover {
                    background: #4B5563;
                }

                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                }

                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: transparent;
                }
                """
            )

            root.addWidget(self.scroll_area, stretch=1)
        else:
            root.addWidget(content, stretch=1)

    def add_left(self, widget, stretch=0):
        self.left_column.addWidget(widget, stretch=stretch)

    def add_right(self, widget, stretch=0):
        self.right_column.addWidget(widget, stretch=stretch)

    def add_left_stretch(self):
        self.left_column.addStretch()

    def add_right_stretch(self):
        self.right_column.addStretch()

    def add_between_columns_and_progress(self, widget):
        index = self.content_layout.indexOf(self.progress_widget)
        if index >= 0:
            self.content_layout.insertWidget(index, widget)
        else:
            self.content_layout.addWidget(widget)

    def set_active_step(self, step_number):
        self.stepper.set_active_step(step_number)

    def update_progress(self, current, total, status="Working", current_item=""):
        self.progress_widget.update_progress(current, total, status, current_item)

    def reset_progress(self):
        self.progress_widget.reset()
