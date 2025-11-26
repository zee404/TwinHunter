from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QCheckBox, QFrame, QSizePolicy, QPushButton)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

class ImageItemWidget(QWidget):
    def __init__(self, file_path, size_str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.size_str = size_str
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Thumbnail
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setAlignment(Qt.AlignCenter)
        # self.image_label.setStyleSheet("background-color: #333; border: 1px solid #555;")
        self.image_label.setObjectName("imageLabel") # Use ID for styling
        
        # Load thumbnail
        pixmap = QPixmap(self.file_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
        else:
            self.image_label.setText("No Image")
            
        layout.addWidget(self.image_label)
        
        # Info
        self.path_label = QLabel(self.file_path)
        self.path_label.setWordWrap(True)
        self.path_label.setObjectName("infoLabel")
        self.path_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.path_label)
        
        self.size_label = QLabel(self.size_str)
        self.size_label.setObjectName("infoLabel")
        self.size_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.size_label)
        
        # Checkbox
        self.checkbox = QCheckBox("Delete")
        layout.addWidget(self.checkbox)
        
    def is_checked(self):
        return self.checkbox.isChecked()

class DuplicateGroupWidget(QFrame):
    def __init__(self, hash_val, files, parent=None):
        super().__init__(parent)
        self.hash_val = hash_val
        self.files = files
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShape(QFrame.StyledPanel)
        # self.setStyleSheet("DuplicateGroupWidget { border: 1px solid #444; margin: 5px; border-radius: 5px; background-color: #2b2b2b; }")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header Layout
        header_layout = QHBoxLayout()
        
        header = QLabel(f"Duplicate Group (Hash: {self.hash_val[:8]}...)")
        header.setObjectName("groupHeader")
        header.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        if len(self.files) > 1:
            select_copies_btn = QPushButton("Select Copies")
            select_copies_btn.setFixedWidth(90)
            select_copies_btn.clicked.connect(self.select_all_except_first)
            header_layout.addWidget(select_copies_btn)
            
            deselect_btn = QPushButton("Deselect All")
            deselect_btn.setFixedWidth(80)
            deselect_btn.clicked.connect(self.deselect_all)
            header_layout.addWidget(deselect_btn)
            
        layout.addLayout(header_layout)
        
        images_layout = QHBoxLayout()
        images_layout.setAlignment(Qt.AlignLeft)
        
        from core.utils import get_file_size, format_size
        
        self.image_widgets = []
        for file_path in self.files:
            size = get_file_size(file_path)
            size_str = format_size(size)
            widget = ImageItemWidget(file_path, size_str)
            images_layout.addWidget(widget)
            self.image_widgets.append(widget)
            
        layout.addLayout(images_layout)
        
    def get_selected_files(self):
        selected = []
        for widget in self.image_widgets:
            if widget.is_checked():
                selected.append(widget.file_path)
        return selected

    def select_all_except_first(self):
        # Sort by file path length or creation time? 
        # For now, we assume the first one in the list is the "original" or "keeper".
        # The list order depends on os.walk which is usually arbitrary but stable.
        # Let's just keep the first one.
        if not self.image_widgets:
            return
            
        # Uncheck the first one
        self.image_widgets[0].checkbox.setChecked(False)
        
        # Check the rest
        for widget in self.image_widgets[1:]:
            widget.checkbox.setChecked(True)

    def select_all(self):
        for widget in self.image_widgets:
            widget.checkbox.setChecked(True)

    def deselect_all(self):
        for widget in self.image_widgets:
            widget.checkbox.setChecked(False)
