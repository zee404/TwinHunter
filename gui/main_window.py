import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QScrollArea, QLabel, 
                             QProgressBar, QMessageBox, QCheckBox)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from core.scanner import ImageScanner
from core.utils import format_size, safe_delete
from gui.widgets import DuplicateGroupWidget

class ScanThread(QThread):
    progress_update = pyqtSignal(int, int, str)
    scan_complete = pyqtSignal(dict)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.scanner = ImageScanner()

    def run(self):
        def callback(current, total, current_file):
            self.progress_update.emit(current, total, current_file)
        
        duplicates = self.scanner.scan_directory(self.folder_path, callback)
        self.scan_complete.emit(duplicates)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TwinHunter - Duplicate Image Detector")
        self.resize(1000, 800)
        
        # Enable Drag & Drop
        self.setAcceptDrops(True)
        
        # Set Icon
        from PyQt5.QtGui import QIcon
        icon_path = os.path.join("assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.is_dark_mode = True
        self.duplicates = {}
        self.init_ui()

    def get_dark_theme(self):
        return """
            QMainWindow { background-color: #2b2b2b; color: #ddd; }
            QLabel { color: #ddd; }
            QScrollArea { border: none; background-color: #2b2b2b; }
            QWidget { background-color: #2b2b2b; }
            QPushButton { border-radius: 3px; border: 1px solid #555; background-color: #3c3c3c; color: #ddd; }
            QPushButton:hover { background-color: #4c4c4c; }
            QProgressBar { border: 1px solid #555; border-radius: 3px; text-align: center; }
            QProgressBar::chunk { background-color: #007acc; }
            DuplicateGroupWidget { border: 1px solid #444; margin: 5px; border-radius: 5px; background-color: #2b2b2b; }
            QLabel#imageLabel { background-color: #333; border: 1px solid #555; }
            QLabel#groupHeader { color: #ddd; }
            QLabel#infoLabel { color: #aaa; }
        """

    def get_light_theme(self):
        return """
            QMainWindow { background-color: #f0f0f0; color: #000000; }
            QLabel { color: #000000; }
            QScrollArea { border: none; background-color: #f0f0f0; }
            QWidget { background-color: #f0f0f0; color: #000000; }
            QPushButton { border-radius: 3px; border: 1px solid #ccc; background-color: #e0e0e0; color: #000000; }
            QPushButton:hover { background-color: #d0d0d0; }
            QProgressBar { border: 1px solid #ccc; border-radius: 3px; text-align: center; color: #000000; }
            QProgressBar::chunk { background-color: #007acc; }
            DuplicateGroupWidget { border: 1px solid #ccc; margin: 5px; border-radius: 5px; background-color: #ffffff; color: #000000; }
            QLabel#imageLabel { background-color: #e0e0e0; border: 1px solid #ccc; }
            QCheckBox { color: #000000; }
            QLabel#groupHeader { color: #000000; }
            QLabel#infoLabel { color: #555555; }
        """

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top Bar
        top_bar = QHBoxLayout()
        self.path_label = QLabel("No folder selected (Drag folder here)")
        self.path_label.setStyleSheet("border: 1px solid #555; padding: 5px; border-radius: 3px; color: #ddd;")
        
        select_btn = QPushButton("Select Folder")
        select_btn.clicked.connect(self.select_folder)
        select_btn.setStyleSheet("padding: 5px 10px;")
        
        self.scan_btn = QPushButton("Scan Now")
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setEnabled(False)
        self.scan_btn.setStyleSheet("padding: 5px 10px; background-color: #007acc; color: white; font-weight: bold;")
        
        top_bar.addWidget(self.path_label, 1)
        top_bar.addWidget(select_btn)
        top_bar.addWidget(self.scan_btn)
        
        self.theme_btn = QPushButton("Light Mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setStyleSheet("padding: 5px 10px;")
        top_bar.addWidget(self.theme_btn)
        
        main_layout.addLayout(top_bar)

        # Progress Area
        progress_layout = QVBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(100, 100)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #333; border: 1px solid #555;")
        self.preview_label.setVisible(False)
        
        # Center the preview
        preview_container = QHBoxLayout()
        preview_container.addStretch()
        preview_container.addWidget(self.preview_label)
        preview_container.addStretch()
        progress_layout.addLayout(preview_container)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        self.preview_check = QCheckBox("Show Live Preview (May slow down scanning)")
        self.preview_check.setChecked(True)
        self.preview_check.setStyleSheet("margin-top: 5px;")
        progress_layout.addWidget(self.preview_check, 0, Qt.AlignCenter)
        
        main_layout.addLayout(progress_layout)

        # Results Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.results_container)
        main_layout.addWidget(scroll)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        self.stats_label = QLabel("Ready")
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected)
        delete_btn.setStyleSheet("padding: 5px 10px; background-color: #d9534f; color: white; font-weight: bold;")
        
        select_all_btn = QPushButton("Select All (Keep Original)")
        select_all_btn.clicked.connect(self.select_all_duplicates)
        select_all_btn.setStyleSheet("padding: 5px 10px; background-color: #f0ad4e; color: white; font-weight: bold;")
        
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_duplicates)
        deselect_all_btn.setStyleSheet("padding: 5px 10px; background-color: #5bc0de; color: white; font-weight: bold;")
        
        bottom_bar.addWidget(self.stats_label, 1)
        bottom_bar.addWidget(select_all_btn)
        bottom_bar.addWidget(deselect_all_btn)
        bottom_bar.addWidget(delete_btn)
        main_layout.addLayout(bottom_bar)

        # Apply Dark Theme
        # Apply Initial Theme
        self.apply_theme()

    def apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet(self.get_dark_theme())
            self.theme_btn.setText("Light Mode")
        else:
            self.setStyleSheet(self.get_light_theme())
            self.theme_btn.setText("Dark Mode")
            
    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        
        # Re-apply styles to existing widgets if needed (sometimes required for dynamic updates)
        # For DuplicateGroupWidget, we might need to update them explicitly if they don't inherit well.
        # But setStyleSheet on MainWindow usually propagates.
        # However, our DuplicateGroupWidget has its own setStyleSheet in __init__.
        # We need to update them.
        for i in range(self.results_layout.count()):
            widget = self.results_layout.itemAt(i).widget()
            if isinstance(widget, DuplicateGroupWidget):
                # We need to update the style of the group widget itself
                # The colors are hardcoded in the stylesheet strings above.
                # But the widget's own style might override or be separate.
                # Let's just re-set the stylesheet on the main window, it should cascade 
                # IF the widgets don't have conflicting inline styles.
                # Wait, DuplicateGroupWidget DOES have inline style in __init__.
                # We should remove that and use the global stylesheet with class selector.
                pass

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path = folder
            self.path_label.setText(folder)
            self.scan_btn.setEnabled(True)
            self.clear_results()

    def start_scan(self):
        self.clear_results()
        self.progress_bar.setVisible(True)
        if self.preview_check.isChecked():
            self.preview_label.setVisible(True)
        self.scan_btn.setEnabled(False)
        self.stats_label.setText("Scanning...")
        
        self.thread = ScanThread(self.folder_path)
        self.thread.progress_update.connect(self.update_progress)
        self.thread.scan_complete.connect(self.scan_finished)
        self.thread.start()

    def update_progress(self, current, total, current_file):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Scanning: {os.path.basename(current_file)}")
        
        if self.preview_check.isChecked() and os.path.exists(current_file):
            pixmap = QPixmap(current_file)
            if not pixmap.isNull():
                self.preview_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

    def scan_finished(self, duplicates):
        self.duplicates = duplicates
        self.progress_bar.setVisible(False)
        self.preview_label.setVisible(False)
        self.status_label.setText("")
        self.scan_btn.setEnabled(True)
        
        total_dupes = 0
        total_size = 0
        
        if not duplicates:
            QMessageBox.information(self, "Scan Complete", "No duplicate images found.")
            self.stats_label.setText("No duplicates found.")
            return

        for hash_val, files in duplicates.items():
            group_widget = DuplicateGroupWidget(hash_val, files)
            self.results_layout.addWidget(group_widget)
            
            # Stats (count all but one as potential savings)
            # Actually, we don't know which one user will keep, but let's assume 1 kept.
            # For now just sum all duplicates size
            from core.utils import get_file_size
            group_size = sum(get_file_size(f) for f in files)
            # Assuming we keep 1, we save size of (n-1) files. 
            # But files might have different sizes (if different formats but same content? unlikely with hash)
            # Actually hash is content based.
            # Let's just say "Found X groups".
            total_dupes += len(files)
            # Estimate saved space: sum of all files - sum of 1 file per group (approx)
            # Let's just show total size of ALL duplicates for now.
            total_size += group_size

        self.stats_label.setText(f"Found {len(duplicates)} groups ({total_dupes} files). Total size: {format_size(total_size)}")

    def clear_results(self):
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.duplicates = {}

    def delete_selected(self):
        files_to_delete = []
        for i in range(self.results_layout.count()):
            widget = self.results_layout.itemAt(i).widget()
            if isinstance(widget, DuplicateGroupWidget):
                files_to_delete.extend(widget.get_selected_files())
        
        if not files_to_delete:
            QMessageBox.warning(self, "No Selection", "Please select images to delete.")
            return

        confirm = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete {len(files_to_delete)} files?\nThey will be moved to the Recycle Bin.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            deleted_count = 0
            deleted_size = 0
            from core.utils import get_file_size
            
            for file_path in files_to_delete:
                size = get_file_size(file_path)
                if safe_delete(file_path):
                    deleted_count += 1
                    deleted_size += size
            
            QMessageBox.information(self, "Deletion Complete", 
                                  f"Successfully deleted {deleted_count} files.\nSpace saved: {format_size(deleted_size)}")
            
            # Refresh results (simple way: remove deleted widgets or re-scan)
            # For now, let's just re-scan or remove the widgets manually.
            # Re-scanning is safer to ensure state is correct.
            self.start_scan()

    def select_all_duplicates(self):
        if not self.duplicates:
            return
            
        for i in range(self.results_layout.count()):
            widget = self.results_layout.itemAt(i).widget()
            if isinstance(widget, DuplicateGroupWidget):
                widget.select_all_except_first()

    def deselect_all_duplicates(self):
        if not self.duplicates:
            return
            
        for i in range(self.results_layout.count()):
            widget = self.results_layout.itemAt(i).widget()
            if isinstance(widget, DuplicateGroupWidget):
                widget.deselect_all()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Check if at least one URL is a directory
            for url in event.mimeData().urls():
                if url.isLocalFile() and os.path.isdir(url.toLocalFile()):
                    event.accept()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    self.folder_path = path
                    self.path_label.setText(path)
                    self.scan_btn.setEnabled(True)
                    self.clear_results()
                    # Optional: Auto-start scan? Let's wait for user to click scan.
                    break
