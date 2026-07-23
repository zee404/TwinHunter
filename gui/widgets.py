import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QPixmap
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from core.utils import format_size, get_file_size, get_image_quality


class HoverImageLabel(QLabel):
    """Thumbnail that shows a larger, non-interactive preview on hover."""

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.popup = None

    def enterEvent(self, event):
        pixmap = QPixmap(self.file_path)
        if pixmap.isNull():
            return super().enterEvent(event)

        self.popup = QFrame(None, Qt.ToolTip | Qt.FramelessWindowHint)
        self.popup.setObjectName("hoverPreview")
        layout = QVBoxLayout(self.popup)
        image = QLabel()
        image.setPixmap(pixmap.scaled(700, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        image.setAlignment(Qt.AlignCenter)
        name = QLabel(os.path.basename(self.file_path))
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(image)
        layout.addWidget(name)
        self.popup.adjustSize()
        position = QCursor.pos()
        self.popup.move(position.x() + 18, position.y() + 18)
        self.popup.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.popup:
            self.popup.close()
            self.popup.deleteLater()
            self.popup = None
        super().leaveEvent(event)


class ImageItemWidget(QWidget):
    keeper_selected = pyqtSignal(object)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setObjectName("imageCard")
        self.setFixedWidth(202)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 13)
        layout.setSpacing(7)
        self.image_label = HoverImageLabel(self.file_path)
        self.image_label.setFixedSize(176, 156)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setObjectName("imageLabel")
        self.image_label.setToolTip("Hover to enlarge")

        pixmap = QPixmap(self.file_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(
                pixmap.scaled(168, 148, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.image_label.setText("No preview")
        layout.addWidget(self.image_label)

        name_label = QLabel(os.path.basename(self.file_path))
        name_label.setObjectName("groupHeader")
        name_label.setToolTip(self.file_path)
        name_label.setTextInteractionFlags(Qt.NoTextInteraction)
        layout.addWidget(name_label)

        folder_label = QLabel(os.path.dirname(self.file_path))
        folder_label.setObjectName("infoLabel")
        folder_label.setWordWrap(True)
        folder_label.setMaximumHeight(34)
        folder_label.setToolTip(self.file_path)
        folder_label.setTextInteractionFlags(Qt.NoTextInteraction)
        layout.addWidget(folder_label)

        try:
            from PIL import Image
            with Image.open(self.file_path) as image:
                dimensions = f"{image.width} × {image.height}"
        except (OSError, ValueError):
            dimensions = "Unknown dimensions"
        info = QLabel(f"{dimensions}  •  {format_size(get_file_size(self.file_path))}")
        info.setObjectName("infoLabel")
        info.setTextInteractionFlags(Qt.NoTextInteraction)
        layout.addWidget(info)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: rgba(128, 140, 160, 55);")
        layout.addWidget(separator)

        self.keep_radio = QRadioButton("Keep this image")
        self.keep_radio.toggled.connect(self._keeper_changed)
        layout.addWidget(self.keep_radio)
        self.checkbox = QCheckBox("Move to Recycle Bin")
        layout.addWidget(self.checkbox)

    def _keeper_changed(self, checked):
        if checked:
            self.checkbox.setChecked(False)
            self.checkbox.setEnabled(False)
            self.keeper_selected.emit(self)
        else:
            self.checkbox.setEnabled(True)

    def is_checked(self):
        return self.checkbox.isChecked()


class DuplicateGroupWidget(QFrame):
    def __init__(self, group_id, files, parent=None):
        super().__init__(parent)
        self.group_id = group_id
        self.files = sorted(files, key=str.casefold)
        self.setObjectName("duplicateGroup")
        self.setFrameShape(QFrame.StyledPanel)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        header = QLabel(f"Match group  ·  {len(self.files)} images")
        header.setObjectName("groupHeader")
        header.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        select_copies_btn = QPushButton("Select copies")
        select_copies_btn.clicked.connect(self.select_all_except_keeper)
        header_layout.addWidget(select_copies_btn)
        deselect_btn = QPushButton("Deselect All")
        deselect_btn.clicked.connect(self.deselect_all)
        header_layout.addWidget(deselect_btn)
        layout.addLayout(header_layout)

        # A group can be wider than the window. The outer results area supplies
        # horizontal scrolling while every item remains directly comparable.
        images_layout = QHBoxLayout()
        images_layout.setAlignment(Qt.AlignLeft)
        images_layout.setSpacing(12)
        self.keeper_group = QButtonGroup(self)
        self.keeper_group.setExclusive(True)
        self.image_widgets = []
        for file_path in self.files:
            widget = ImageItemWidget(file_path)
            widget.keeper_selected.connect(self._keeper_selected)
            self.keeper_group.addButton(widget.keep_radio)
            images_layout.addWidget(widget)
            self.image_widgets.append(widget)
        layout.addLayout(images_layout)

        # Default to the highest-resolution/largest image, never traversal order.
        keeper = max(self.image_widgets, key=lambda item: get_image_quality(item.file_path))
        keeper.keep_radio.setChecked(True)

    def _keeper_selected(self, keeper):
        for widget in self.image_widgets:
            if widget is not keeper:
                widget.checkbox.setEnabled(True)

    def get_selected_files(self):
        return [widget.file_path for widget in self.image_widgets if widget.is_checked()]

    def keeper_path(self):
        for widget in self.image_widgets:
            if widget.keep_radio.isChecked():
                return widget.file_path
        return None

    def select_all_except_keeper(self):
        for widget in self.image_widgets:
            widget.checkbox.setChecked(not widget.keep_radio.isChecked())

    # Compatibility with the main-window action name.
    select_all_except_first = select_all_except_keeper

    def deselect_all(self):
        for widget in self.image_widgets:
            widget.checkbox.setChecked(False)
