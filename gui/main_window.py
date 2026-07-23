import os
import sys
import time
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QScrollArea, QLabel, 
                             QProgressBar, QMessageBox, QCheckBox, QSlider, QSpinBox, QFrame)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from core.scanner import ImageScanner, ScanCancelled
from core.utils import format_size, safe_delete
from gui.widgets import DuplicateGroupWidget

class ScanThread(QThread):
    discovery_update = pyqtSignal(int, str)
    progress_update = pyqtSignal(int, int, str)
    scan_complete = pyqtSignal(dict)
    scan_failed = pyqtSignal(str)
    scan_cancelled = pyqtSignal()
    skipped_files = pyqtSignal(list)

    def __init__(self, folder_path, threshold=0):
        super().__init__()
        self.folder_path = folder_path
        self.threshold = threshold
        self.scanner = ImageScanner()

    def run(self):
        def callback(current, total, current_file):
            self.progress_update.emit(current, total, current_file)
        
        try:
            duplicates = self.scanner.scan_directory(
                self.folder_path,
                callback,
                similarity=self.threshold,
                cancel_check=self.isInterruptionRequested,
                discovery_callback=lambda count, folder: self.discovery_update.emit(count, folder),
            )
            self.skipped_files.emit(self.scanner.skipped_files)
            self.scan_complete.emit(duplicates)
        except ScanCancelled:
            self.scan_cancelled.emit()
        except Exception as error:
            self.scan_failed.emit(str(error))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TwinHunter - Duplicate Image Detector")
        self.resize(1180, 820)
        self.setMinimumSize(900, 650)
        
        # Enable Drag & Drop
        self.setAcceptDrops(True)
        
        # Set Icon
        from PyQt5.QtGui import QIcon
        bundle_root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(bundle_root, "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.is_dark_mode = True
        self.duplicates = {}
        self.skipped_count = 0
        self.scan_started_at = None
        self.hashing_started_at = None
        self.init_ui()

    def get_dark_theme(self):
        return """
            QMainWindow, QWidget#appSurface { background-color: #0d1117; color: #f5f7fb; }
            QWidget { color: #f5f7fb; font-family: "Segoe UI Variable", "Segoe UI"; }
            QLabel { color: #f5f7fb; background: transparent; }
            QLabel#appTitle { color: #ffffff; font-size: 24px; font-weight: 700; }
            QLabel#appSubtitle { color: #929bad; font-size: 11px; }
            QLabel#sectionLabel { color: #aab3c2; font-size: 11px; font-weight: 600; }
            QLabel#pathPill { background-color: #171d27; border: 1px solid #2b3442;
                              border-radius: 11px; color: #dce3ee; padding: 9px 12px; }
            QLabel#groupHeader { color: #ffffff; font-size: 13px; font-weight: 650; }
            QLabel#infoLabel { color: #9da8b8; background: transparent; }
            QLabel#emptyHint { color: #737f91; font-size: 13px; }
            QFrame#toolbarCard, QFrame#settingsCard { background-color: #131923;
                border: 1px solid #26303e; border-radius: 16px; }
            QFrame#duplicateGroup { background-color: #131923; border: 1px solid #283341;
                border-radius: 18px; }
            QWidget#imageCard { background-color: #1a212d; border: 1px solid #2d3848;
                border-radius: 14px; }
            QWidget#imageCard:hover { background-color: #202a38; border: 1px solid #4e7cf5; }
            QLabel#imageLabel { background-color: #0b0f15; border: 1px solid #303b4b;
                border-radius: 10px; padding: 3px; }
            QPushButton { min-height: 32px; padding: 0 14px; border-radius: 9px;
                border: 1px solid #343f50; background-color: #202836; color: #eef2f8; font-weight: 600; }
            QPushButton:hover { background-color: #2a3546; border-color: #52627a; }
            QPushButton:pressed { background-color: #18202b; }
            QPushButton:disabled { color: #657084; background-color: #171d26; border-color: #242d39; }
            QPushButton#primaryButton { color: white; border: 1px solid #6691ff;
                background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #6b91ff, stop:1 #3d67df); }
            QPushButton#primaryButton:hover { background-color: #7297ff; }
            QPushButton#dangerButton { color: white; border: 1px solid #eb6675;
                background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #df596b, stop:1 #b9364b); }
            QPushButton#dangerButton:hover { background-color: #ea6476; }
            QSlider::groove:horizontal { height: 5px; background: #2b3544; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #628bff; border-radius: 2px; }
            QSlider::handle:horizontal { width: 17px; margin: -6px 0; border-radius: 8px;
                background: white; border: 2px solid #628bff; }
            QSpinBox { min-height: 30px; min-width: 64px; padding: 0 8px; border-radius: 8px;
                color: #f5f7fb; background: #1b2330; border: 1px solid #344154; }
            QCheckBox, QRadioButton { color: #d8deea; spacing: 7px; background: transparent; }
            QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; }
            QCheckBox::indicator:checked { background: #638bff; border: 1px solid #83a4ff; border-radius: 4px; }
            QCheckBox::indicator:unchecked { background: #111720; border: 1px solid #49566a; border-radius: 4px; }
            QRadioButton::indicator:checked { background: #638bff; border: 4px solid #dce6ff; border-radius: 8px; }
            QRadioButton::indicator:unchecked { background: #111720; border: 1px solid #566277; border-radius: 8px; }
            QProgressBar { min-height: 22px; border: 1px solid #303b4a; border-radius: 7px;
                background: #1a212c; color: #f5f7fb; text-align: center; font-size: 10px; font-weight: 600; }
            QProgressBar::chunk { border-radius: 6px; background: #426ee2; }
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 10px; background: transparent; margin: 2px; }
            QScrollBar::handle:vertical { min-height: 32px; background: #364154; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QToolTip { color: #f5f7fb; background-color: #202836; border: 1px solid #46546a; padding: 6px; }
            QFrame#hoverPreview { background-color: #111720; border: 1px solid #59677c; border-radius: 12px; }
            QMessageBox { background-color: #151b25; }
            QMessageBox QLabel { color: #f4f7fb; background: transparent; font-size: 11px;
                min-width: 280px; padding: 4px 2px; }
            QMessageBox QPushButton { min-width: 84px; color: #f4f7fb; background-color: #263143;
                border: 1px solid #46556d; }
            QMessageBox QPushButton:hover { background-color: #334158; border-color: #638bff; }
        """

    def get_light_theme(self):
        return """
            QMainWindow, QWidget#appSurface { background-color: #eef1f6; color: #172033; }
            QWidget { color: #172033; font-family: "Segoe UI Variable", "Segoe UI"; }
            QLabel { color: #172033; background: transparent; }
            QLabel#appTitle { color: #121a2a; font-size: 24px; font-weight: 700; }
            QLabel#appSubtitle { color: #6e7889; font-size: 11px; }
            QLabel#sectionLabel { color: #606b7d; font-size: 11px; font-weight: 600; }
            QLabel#pathPill { background-color: #f5f7fb; border: 1px solid #d6dce6;
                              border-radius: 11px; color: #344057; padding: 9px 12px; }
            QLabel#groupHeader { color: #172033; font-size: 13px; font-weight: 650; }
            QLabel#infoLabel { color: #657187; background: transparent; }
            QFrame#toolbarCard, QFrame#settingsCard { background-color: #ffffff;
                border: 1px solid #dce1e9; border-radius: 16px; }
            QFrame#duplicateGroup { background-color: #ffffff; border: 1px solid #dce2eb; border-radius: 18px; }
            QWidget#imageCard { background-color: #f7f9fc; border: 1px solid #dfe4ec; border-radius: 14px; }
            QWidget#imageCard:hover { background-color: #ffffff; border: 1px solid #7395ec; }
            QLabel#imageLabel { background-color: #e9edf3; border: 1px solid #d6dce6;
                border-radius: 10px; padding: 3px; }
            QPushButton { min-height: 32px; padding: 0 14px; border-radius: 9px;
                border: 1px solid #ccd3df; background-color: #f7f9fc; color: #263147; font-weight: 600; }
            QPushButton:hover { background-color: white; border-color: #9da9ba; }
            QPushButton:pressed { background-color: #e8ecf2; }
            QPushButton:disabled { color: #a2aaba; background-color: #edf0f4; border-color: #e1e5eb; }
            QPushButton#primaryButton { color: white; border: 1px solid #5079e8;
                background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #7198ff, stop:1 #4670e0); }
            QPushButton#dangerButton { color: white; border: 1px solid #cc4256;
                background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e86676, stop:1 #c74155); }
            QSlider::groove:horizontal { height: 5px; background: #d5dbe5; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #638bff; border-radius: 2px; }
            QSlider::handle:horizontal { width: 17px; margin: -6px 0; border-radius: 8px;
                background: white; border: 2px solid #638bff; }
            QSpinBox { min-height: 30px; min-width: 64px; padding: 0 8px; border-radius: 8px;
                color: #263147; background: white; border: 1px solid #ccd4e0; }
            QCheckBox, QRadioButton { color: #354157; spacing: 7px; background: transparent; }
            QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; }
            QCheckBox::indicator:checked { background: #638bff; border: 1px solid #527be8; border-radius: 4px; }
            QCheckBox::indicator:unchecked { background: white; border: 1px solid #aeb7c5; border-radius: 4px; }
            QRadioButton::indicator:checked { background: #638bff; border: 4px solid white; border-radius: 8px; }
            QRadioButton::indicator:unchecked { background: white; border: 1px solid #aeb7c5; border-radius: 8px; }
            QProgressBar { min-height: 22px; border: 1px solid #d1d8e3; border-radius: 7px;
                background: #e4e8ef; color: #263147; text-align: center; font-size: 10px; font-weight: 600; }
            QProgressBar::chunk { border-radius: 6px; background: #7798f1; }
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 10px; background: transparent; margin: 2px; }
            QScrollBar::handle:vertical { min-height: 32px; background: #bdc5d2; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QToolTip { color: #172033; background-color: white; border: 1px solid #cbd2de; padding: 6px; }
            QFrame#hoverPreview { background-color: white; border: 1px solid #cbd2de; border-radius: 12px; }
            QMessageBox { background-color: #f7f9fc; }
            QMessageBox QLabel { color: #172033; background: transparent; font-size: 11px;
                min-width: 280px; padding: 4px 2px; }
            QMessageBox QPushButton { min-width: 84px; color: #263147; background-color: #ffffff;
                border: 1px solid #b8c1cf; }
            QMessageBox QPushButton:hover { background-color: #edf2ff; border-color: #638bff; }
        """

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("appSurface")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(28, 22, 28, 22)
        main_layout.setSpacing(14)

        title_row = QHBoxLayout()
        title_stack = QVBoxLayout()
        title_stack.setSpacing(1)
        title = QLabel("TwinHunter")
        title.setObjectName("appTitle")
        subtitle = QLabel("A safer way to discover duplicate and visually similar photos")
        subtitle.setObjectName("appSubtitle")
        title_stack.addWidget(title)
        title_stack.addWidget(subtitle)
        title_row.addLayout(title_stack)
        title_row.addStretch()

        self.theme_btn = QPushButton("Light appearance")
        self.theme_btn.clicked.connect(self.toggle_theme)
        title_row.addWidget(self.theme_btn)
        main_layout.addLayout(title_row)

        # Top Bar
        toolbar_card = QFrame()
        toolbar_card.setObjectName("toolbarCard")
        top_bar = QHBoxLayout(toolbar_card)
        top_bar.setContentsMargins(14, 12, 14, 12)
        top_bar.setSpacing(10)
        self.path_label = QLabel("No folder selected (Drag folder here)")
        self.path_label.setObjectName("pathPill")
        self.path_label.setToolTip("Choose a folder or drag one anywhere onto this window")
        
        select_btn = QPushButton("Select Folder")
        select_btn.clicked.connect(self.select_folder)
        
        self.scan_btn = QPushButton("Scan Now")
        self.scan_btn.setObjectName("primaryButton")
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setEnabled(False)
        
        top_bar.addWidget(self.path_label, 1)
        top_bar.addWidget(select_btn)
        top_bar.addWidget(self.scan_btn)
        
        main_layout.addWidget(toolbar_card)
        
        # Settings Area (Threshold)
        settings_card = QFrame()
        settings_card.setObjectName("settingsCard")
        settings_layout = QHBoxLayout(settings_card)
        settings_layout.setContentsMargins(16, 11, 16, 11)
        settings_layout.setSpacing(12)
        settings_layout.setAlignment(Qt.AlignLeft)
        
        lbl = QLabel("Required similarity:")
        lbl.setObjectName("sectionLabel")
        lbl.setToolTip("100% = byte-identical files; lower values find visually similar scenes")
        settings_layout.addWidget(lbl)
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(70, 100)
        self.threshold_slider.setValue(85)
        self.threshold_slider.setFixedWidth(200)
        settings_layout.addWidget(self.threshold_slider)
        
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(70, 100)
        self.threshold_spin.setValue(85)
        self.threshold_spin.setSuffix("%")
        settings_layout.addWidget(self.threshold_spin)
        
        # Sync slider and spinbox
        self.threshold_slider.valueChanged.connect(self.threshold_spin.setValue)
        self.threshold_spin.valueChanged.connect(self.threshold_slider.setValue)
        
        settings_layout.addSpacing(8)
        mode_hint = QLabel("100% = identical files   •   85% = balanced visual matching   •   75% = broader scene matching")
        mode_hint.setObjectName("appSubtitle")
        settings_layout.addWidget(mode_hint)
        settings_layout.addStretch()
        main_layout.addWidget(settings_card)

        # Progress Area
        progress_layout = QVBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(100, 100)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setObjectName("imageLabel")
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

        self.cancel_btn = QPushButton("Cancel Scan")
        self.cancel_btn.clicked.connect(self.cancel_scan)
        self.cancel_btn.setVisible(False)
        progress_layout.addWidget(self.cancel_btn, 0, Qt.AlignCenter)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        self.preview_check = QCheckBox("Show Live Preview (May slow down scanning)")
        self.preview_check.setChecked(True)
        progress_layout.addWidget(self.preview_check, 0, Qt.AlignCenter)
        
        main_layout.addLayout(progress_layout)

        # Results Area
        scroll = QScrollArea()
        scroll.setObjectName("resultsScroll")
        scroll.setWidgetResizable(True)
        self.results_container = QWidget()
        self.results_container.setObjectName("appSurface")
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.results_container)
        main_layout.addWidget(scroll)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        self.stats_label = QLabel("Ready")
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self.delete_selected)
        
        select_all_btn = QPushButton("Select All (Keep Original)")
        select_all_btn.clicked.connect(self.select_all_duplicates)
        select_all_btn.setText("Select all except keepers")
        
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_duplicates)
        
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
            self.theme_btn.setText("Light appearance")
        else:
            self.setStyleSheet(self.get_light_theme())
            self.theme_btn.setText("Dark appearance")
            
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
        self.skipped_count = 0
        self.scan_started_at = time.monotonic()
        self.hashing_started_at = None
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Discovering images in subfolders…")
        if self.preview_check.isChecked():
            self.preview_label.setVisible(True)
        self.scan_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.stats_label.setText("Scanning...")
        
        threshold = self.threshold_slider.value()
        self.thread = ScanThread(self.folder_path, threshold)
        self.thread.progress_update.connect(self.update_progress)
        self.thread.discovery_update.connect(self.update_discovery)
        self.thread.scan_complete.connect(self.scan_finished)
        self.thread.scan_failed.connect(self.scan_failed)
        self.thread.scan_cancelled.connect(self.scan_cancelled)
        self.thread.skipped_files.connect(self.record_skipped_files)
        self.thread.start()

    @staticmethod
    def format_duration(seconds):
        seconds = max(0, int(round(seconds)))
        if seconds < 60:
            return f"{seconds}s"
        minutes, seconds = divmod(seconds, 60)
        if minutes < 60:
            return f"{minutes}m {seconds:02d}s"
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes:02d}m"

    def update_discovery(self, count, folder):
        self.status_label.setText(
            f"Discovering images… {count:,} found  ·  {os.path.basename(folder) or folder}"
        )

    def cancel_scan(self):
        if hasattr(self, "thread") and self.thread.isRunning():
            self.thread.requestInterruption()
            self.cancel_btn.setEnabled(False)
            self.status_label.setText("Cancelling…")

    def record_skipped_files(self, skipped_files):
        self.skipped_count = len(skipped_files)

    def reset_scan_controls(self):
        self.progress_bar.setVisible(False)
        self.preview_label.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("")
        self.scan_btn.setEnabled(True)

    def scan_failed(self, message):
        self.reset_scan_controls()
        self.stats_label.setText("Scan failed")
        QMessageBox.critical(self, "Scan Failed", message or "An unexpected scan error occurred.")

    def scan_cancelled(self):
        self.reset_scan_controls()
        self.stats_label.setText("Scan cancelled")

    def update_progress(self, current, total, current_file):
        if self.hashing_started_at is None:
            self.hashing_started_at = time.monotonic()
        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(current)
        elapsed = time.monotonic() - self.hashing_started_at
        if current >= 3 and elapsed > 0:
            remaining = (elapsed / current) * (total - current)
            eta = f"ETA {self.format_duration(remaining)}"
        else:
            eta = "Estimating time…"
        self.progress_bar.setFormat(f"{current:,} / {total:,}   •   {eta}")
        self.status_label.setText(f"Analyzing  ·  {os.path.basename(current_file)}")
        
        if self.preview_check.isChecked() and os.path.exists(current_file):
            pixmap = QPixmap(current_file)
            if not pixmap.isNull():
                self.preview_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

    def scan_finished(self, duplicates):
        self.duplicates = duplicates
        self.reset_scan_controls()
        
        total_dupes = 0
        total_size = 0
        
        if not duplicates:
            QMessageBox.information(self, "Scan Complete", "No duplicate images found.")
            skipped = f" ({self.skipped_count} unreadable files skipped)" if self.skipped_count else ""
            elapsed = time.monotonic() - self.scan_started_at if self.scan_started_at else 0
            self.stats_label.setText(f"No matches found{skipped} • {self.format_duration(elapsed)}")
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

        skipped = f" • {self.skipped_count} skipped" if self.skipped_count else ""
        elapsed = time.monotonic() - self.scan_started_at if self.scan_started_at else 0
        self.stats_label.setText(
            f"Found {len(duplicates)} groups ({total_dupes} files) • Reviewed size: "
            f"{format_size(total_size)} • {self.format_duration(elapsed)}{skipped}"
        )

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

        for i in range(self.results_layout.count()):
            widget = self.results_layout.itemAt(i).widget()
            if isinstance(widget, DuplicateGroupWidget):
                if widget.keeper_path() in widget.get_selected_files():
                    QMessageBox.critical(self, "Unsafe Selection", "Every group must retain its chosen keeper.")
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
            
            failed_count = len(files_to_delete) - deleted_count
            message = f"Moved {deleted_count} files to the Recycle Bin.\nSpace saved: {format_size(deleted_size)}"
            if failed_count:
                message += f"\n\n{failed_count} files could not be moved. They were left unchanged."
                QMessageBox.warning(self, "Deletion Partially Complete", message)
            else:
                QMessageBox.information(self, "Deletion Complete", message)
            
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
