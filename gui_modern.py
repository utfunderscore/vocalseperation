# coding: utf-8
__author__ = "Modern UI for MVSEP music separation model"

if __name__ == "__main__":
    import os

    gpu_use = "0"
    print("GPU use: {}".format(gpu_use))
    os.environ["CUDA_VISIBLE_DEVICES"] = "{}".format(gpu_use)

import sys
import os
import json
import platform
import subprocess

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import torch
from inference import predict_with_model, __VERSION__


class ThemeManager:
    """Manages theme detection and switching."""

    @staticmethod
    def detect_system_theme():
        """Detect if system is using dark or light mode."""
        system = platform.system()

        if system == "Darwin":
            try:
                cmd = "defaults read -g AppleInterfaceStyle"
                result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
                if result.stdout.strip() == "Dark":
                    return "dark"
            except:
                pass
        elif system == "Windows":
            try:
                import winreg

                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                reg_keypath = (
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                key = winreg.OpenKey(registry, reg_keypath)
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "dark" if value == 0 else "light"
            except:
                pass

        return "light"

    @staticmethod
    def load_stylesheet(theme):
        """Load stylesheet file for given theme."""
        theme_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "themes", f"{theme}.qss"
        )
        if os.path.exists(theme_file):
            with open(theme_file, "r") as f:
                return f.read()
        return ""


class IconManager:
    """Manages SVG icon loading and caching."""

    _cache = {}

    @classmethod
    def get_icon(cls, name, size=24):
        """Get cached icon by name."""
        if name not in cls._cache:
            icon_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "icons", f"{name}.svg"
            )
            if os.path.exists(icon_path):
                cls._cache[name] = QIcon(icon_path)
            else:
                cls._cache[name] = QIcon()
        return cls._cache[name]


class ConfigManager:
    """Manages application configuration persistence."""

    CONFIG_FILE = "gui_config.json"
    DEFAULT_CONFIG = {
        "theme": "auto",
        "output_folder": "",
        "cpu": False,
        "single_onnx": False,
        "large_gpu": False,
        "use_kim_model_1": False,
        "only_vocals": False,
        "chunk_size": 1000000,
        "overlap_large": 0.6,
        "overlap_small": 0.5,
        "log_console_visible": False,
        "recent_folders": [],
    }

    @classmethod
    def load(cls):
        """Load configuration from file."""
        config_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), cls.CONFIG_FILE
        )
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    merged = cls.DEFAULT_CONFIG.copy()
                    merged.update(config)
                    return merged
            except:
                pass
        return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save(cls, config):
        """Save configuration to file."""
        config_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), cls.CONFIG_FILE
        )
        try:
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")


class Worker(QObject):
    """Worker for background audio processing."""

    finished = pyqtSignal()
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    file_done = pyqtSignal(str)

    def __init__(self, options):
        super().__init__()
        self.options = options

    def run(self):
        # provide callbacks for progress and file completion
        self.options["update_percent_func"] = self.update_progress
        # expose a callable that predict_with_model can call when each file is done
        self.options["file_done_callback"] = self.notify_file_done
        predict_with_model(self.options)
        self.finished.emit()

    def update_progress(self, percent):
        self.progress.emit(percent)

    def notify_file_done(self, filepath):
        # emit signal to main thread about completed file
        self.file_done.emit(filepath)


class CollapsibleGroupBox(QWidget):
    """Collapsible group box with toggle button."""

    def __init__(self, title, expanded=True, parent=None):
        super().__init__(parent)

        self.is_expanded = expanded

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(30)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 0, 8, 0)
        header_layout.setSpacing(8)

        self.toggle_btn = QToolButton()
        self.toggle_btn.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.toggle_btn.setFixedSize(18, 18)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                color: #999;
            }
            QToolButton:hover {
                color: #fff;
            }
        """)
        self.toggle_btn.setAutoRaise(True)
        self.toggle_btn.clicked.connect(self.toggle)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #e0e0e0;")

        header_layout.addWidget(self.toggle_btn)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 5, 10, 10)
        self.content_layout.setAlignment(Qt.AlignTop)

        layout.addWidget(header)
        layout.addWidget(self.content_widget)

        self.update_visibility()

    def toggle(self):
        """Toggle collapse state."""
        self.is_expanded = not self.is_expanded
        self.toggle_btn.setArrowType(
            Qt.DownArrow if self.is_expanded else Qt.RightArrow
        )
        self.update_visibility()

    def update_visibility(self):
        """Update content visibility based on state."""
        self.content_widget.setVisible(self.is_expanded)

    def addWidget(self, widget):
        """Add widget to content layout."""
        self.content_layout.addWidget(widget)

    def addLayout(self, layout):
        """Add layout to content layout."""
        self.content_layout.addLayout(layout)

    def layout(self):
        """Get the content layout."""
        return self.content_layout


class LogConsole(QTextEdit):
    """Toggleable log console for processing messages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(150)
        self.setVisible(False)
        self.setStyleSheet(
            "font-family: 'Consolas', 'Monaco', monospace; font-size: 9pt;"
        )

    def add_message(self, message):
        """Add a message to log."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append(f"[{timestamp}] {message}")

        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class ModernMainWindow(QMainWindow):
    """Main application window with modern UI."""

    def __init__(self):
        super().__init__()
        self.config = ConfigManager.load()
        self.input_files = []
        self.is_processing = False
        self.thread = None
        self.worker = None

        self.init_gpu_detection()
        self.init_ui()
        self.apply_theme()
        self.load_settings()

    def init_gpu_detection(self):
        """Detect GPU and set default settings."""
        try:
            if torch.cuda.is_available():
                t = torch.cuda.get_device_properties(0).total_memory / (
                    1024 * 1024 * 1024
                )
                if t > 11.5:
                    print(f"GPU memory: {t:.2f} GB - Using conservative chunk size")
                    self.config["large_gpu"] = False
                    self.config["chunk_size"] = 200000
                elif t < 8:
                    self.config["large_gpu"] = False
                    self.config["single_onnx"] = True
                    self.config["chunk_size"] = 500000
            else:
                self.config["cpu"] = True
        except:
            self.config["cpu"] = True

    def init_ui(self):
        self.setWindowTitle("Stem Splitter")
        self.setMinimumSize(600, 900)
        self.resize(1100, 800)
        self.setAcceptDrops(True)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        self.create_header(main_layout)
        self.create_content(main_layout)
        self.create_progress_section(main_layout)
        self.create_action_buttons(main_layout)

        self.create_status_bar()
        self.update_table_columns()

    def create_header(self, layout):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        layout.addLayout(header_layout)

    def create_content(self, layout):
        self.content_splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setAlignment(Qt.AlignTop)

        self.input_group = QGroupBox("Input Files")
        input_group_layout = QVBoxLayout(self.input_group)

        input_btn_layout = QHBoxLayout()
        input_btn = QPushButton("Add Files")
        input_btn.setCursor(Qt.PointingHandCursor)
        input_btn.clicked.connect(self.select_input_files)
        input_btn_layout.addWidget(input_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_input_files)
        input_btn_layout.addWidget(clear_btn)

        input_btn_layout.addStretch()

        file_count_label = QLabel("0 files")
        file_count_label.setProperty("subheading", "true")
        self.file_count_label = file_count_label
        input_btn_layout.addWidget(file_count_label)

        input_group_layout.addLayout(input_btn_layout)

        self.file_table = QTableWidget()
        # Add an Enabled checkbox column, then File Name, Size, Format
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["", "File Name", "Size", "Format"])
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.horizontalHeader().setStretchLastSection(False)
        self.file_table.setMinimumHeight(200)
        self.file_table.setShowGrid(False)
        self.file_table.setAlternatingRowColors(True)

        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(3, 70)

        input_group_layout.addWidget(self.file_table)
        self.file_table.hide()

        drop_zone = QLabel("Drag & drop audio files here")
        drop_zone.setAlignment(Qt.AlignCenter)
        drop_zone.setMinimumHeight(200)
        drop_zone.setStyleSheet("""
            QLabel {
                border: 2px dashed #3d3d3d;
                border-radius: 8px;
                padding: 20px;
                color: #616161;
                background-color: transparent;
            }
        """)
        drop_zone.setProperty("class", "drop-zone")
        self.drop_zone = drop_zone
        input_group_layout.addWidget(drop_zone)

        left_layout.addWidget(self.input_group)

        right_widget = QWidget()
        right_widget.setMaximumWidth(500)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignTop)

        output_group = QGroupBox("Output Settings")
        output_group_layout = QVBoxLayout(output_group)

        folder_layout = QHBoxLayout()
        folder_label = QLabel("Output Folder:")
        folder_layout.addWidget(folder_label)

        self.output_folder_edit = QLineEdit()
        folder_layout.addWidget(self.output_folder_edit)

        browse_btn = QPushButton()
        browse_btn.setIcon(IconManager.get_icon("folder"))
        browse_btn.setIconSize(QSize(16, 16))
        browse_btn.setFixedWidth(40)
        browse_btn.setMinimumHeight(36)
        browse_btn.setToolTip("Browse folder")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self.select_output_folder)
        folder_layout.addWidget(browse_btn)

        output_group_layout.addLayout(folder_layout)

        preset_layout = QHBoxLayout()
        preset_label = QLabel("Quick Presets:")
        preset_label.setMinimumHeight(36)
        preset_label.setAlignment(Qt.AlignVCenter)
        preset_layout.addWidget(preset_label)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Default results folder")
        self.preset_combo.addItem("Same as input folder")
        self.preset_combo.addItem("Desktop")
        self.preset_combo.addItem("Documents")
        self.preset_combo.addItem("Downloads")
        self.preset_combo.currentIndexChanged.connect(self.apply_preset)
        preset_layout.addWidget(self.preset_combo)

        output_group_layout.addLayout(preset_layout)

        right_layout.addWidget(output_group)

        self.create_settings_panel(right_layout)

        self.content_splitter.addWidget(left_widget)
        self.content_splitter.addWidget(right_widget)
        self.content_splitter.setStretchFactor(0, 1)
        self.content_splitter.setStretchFactor(1, 1)
        self.content_splitter.splitterMoved.connect(self.on_splitter_moved)

        layout.addWidget(self.content_splitter)

    def create_settings_panel(self, layout):
        settings_group = QGroupBox("Settings")
        settings_group_layout = QVBoxLayout(settings_group)
        settings_group_layout.setAlignment(Qt.AlignTop)

        appearance_group = CollapsibleGroupBox("Appearance", expanded=False)
        self.checkbox_dark_mode = QCheckBox("Dark Mode")
        self.checkbox_dark_mode.setToolTip("Toggle between dark and light themes")
        self.checkbox_dark_mode.clicked.connect(self.toggle_theme)
        appearance_group.addWidget(self.checkbox_dark_mode)

        settings_group_layout.addWidget(appearance_group)

        performance_group = CollapsibleGroupBox("Performance", expanded=False)
        self.checkbox_cpu = QCheckBox("Use CPU instead of GPU")
        self.checkbox_cpu.setToolTip(
            "CPU mode is slower but may be necessary if GPU is unavailable"
        )
        performance_group.addWidget(self.checkbox_cpu)

        self.checkbox_large_gpu = QCheckBox("Use Large GPU Mode")
        self.checkbox_large_gpu.setToolTip(
            "Faster processing but requires 11+ GB GPU memory"
        )
        performance_group.addWidget(self.checkbox_large_gpu)

        self.checkbox_single_onnx = QCheckBox("Use Single ONNX")
        self.checkbox_single_onnx.setToolTip(
            "Reduces GPU memory usage but may affect quality"
        )
        performance_group.addWidget(self.checkbox_single_onnx)

        settings_group_layout.addWidget(performance_group)

        processing_group = CollapsibleGroupBox("Processing", expanded=True)
        self.checkbox_only_vocals = QCheckBox("Only generate vocals/instrumental")
        self.checkbox_only_vocals.setToolTip("Skip bass, drums, and other stems")
        processing_group.addWidget(self.checkbox_only_vocals)

        kim_layout = QHBoxLayout()
        kim_label = QLabel("Kim Model Version:")
        kim_label.setMinimumHeight(36)
        kim_label.setAlignment(Qt.AlignVCenter)
        kim_layout.addWidget(kim_label)

        self.kim_combo = QComboBox()
        self.kim_combo.addItem("Model 2 (Recommended)", False)
        self.kim_combo.addItem("Model 1 (Legacy)", True)
        kim_layout.addWidget(self.kim_combo)
        kim_layout.addStretch()

        processing_group.layout().addLayout(kim_layout)

        settings_group_layout.addWidget(processing_group)

        advanced_group = CollapsibleGroupBox("Advanced", expanded=False)
        advanced_grid = QGridLayout()
        advanced_grid.setAlignment(Qt.AlignTop)

        advanced_grid.addWidget(QLabel("Chunk Size:"), 0, 0)
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(100000, 10000000)
        self.chunk_size_spin.setSingleStep(100000)
        self.chunk_size_spin.setToolTip(
            "Size of chunks processed at once. Lower values use less memory."
        )
        advanced_grid.addWidget(self.chunk_size_spin, 0, 1)

        advanced_grid.addWidget(QLabel("Overlap Large:"), 1, 0)
        self.overlap_large_spin = QDoubleSpinBox()
        self.overlap_large_spin.setRange(0.001, 0.999)
        self.overlap_large_spin.setSingleStep(0.05)
        self.overlap_large_spin.setDecimals(3)
        self.overlap_large_spin.setToolTip(
            "Overlap for light models. Higher values = better quality, slower."
        )
        advanced_grid.addWidget(self.overlap_large_spin, 1, 1)

        advanced_grid.addWidget(QLabel("Overlap Small:"), 2, 0)
        self.overlap_small_spin = QDoubleSpinBox()
        self.overlap_small_spin.setRange(0.001, 0.999)
        self.overlap_small_spin.setSingleStep(0.05)
        self.overlap_small_spin.setDecimals(3)
        self.overlap_small_spin.setToolTip(
            "Overlap for heavy models. Higher values = better quality, slower."
        )
        advanced_grid.addWidget(self.overlap_small_spin, 2, 1)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_advanced_settings)
        advanced_grid.addWidget(reset_btn, 3, 0, 1, 2)

        advanced_group.layout().addLayout(advanced_grid)
        settings_group_layout.addWidget(advanced_group)

        self.log_console = LogConsole()
        self.log_console.hide()
        settings_group_layout.addWidget(self.log_console)

        layout.addWidget(settings_group)

    def create_progress_section(self, layout):
        progress_group = QGroupBox("Progress")
        progress_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress_bar.hide()
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.hide()
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(progress_group)

    def create_action_buttons(self, layout):
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_btn = QPushButton("Start Separation")
        self.start_btn.setProperty("primary", "true")
        self.start_btn.setMinimumHeight(36)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_separation)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setMinimumHeight(36)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.clicked.connect(self.stop_separation)
        button_layout.addWidget(self.stop_btn)

        layout.addLayout(button_layout)

    def create_status_bar(self):
        self.status_bar = QStatusBar()

        self.device_label = QLabel()
        self.device_label.setProperty("subheading", "true")
        self.status_bar.addWidget(self.device_label)

        self.setStatusBar(self.status_bar)
        self.update_device_info()

    def apply_theme(self):
        """Apply current theme to application."""
        theme_name = self.config["theme"]
        if theme_name == "auto":
            theme_name = ThemeManager.detect_system_theme()

        stylesheet = ThemeManager.load_stylesheet(theme_name)
        if stylesheet:
            self.setStyleSheet(stylesheet)

        self.current_theme = theme_name

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self.current_theme == "dark":
            self.config["theme"] = "light"
        else:
            self.config["theme"] = "dark"
        self.apply_theme()
        ConfigManager.save(self.config)

    def load_settings(self):
        """Load settings from config to UI."""
        self.checkbox_cpu.setChecked(self.config["cpu"])
        self.checkbox_single_onnx.setChecked(self.config["single_onnx"])
        self.checkbox_large_gpu.setChecked(self.config["large_gpu"])
        self.checkbox_only_vocals.setChecked(self.config["only_vocals"])

        theme_name = self.config["theme"]
        if theme_name == "auto":
            theme_name = ThemeManager.detect_system_theme()
        self.checkbox_dark_mode.setChecked(theme_name == "dark")

        self.kim_combo.setCurrentIndex(1 if self.config["use_kim_model_1"] else 0)

        self.chunk_size_spin.setValue(self.config["chunk_size"])
        self.overlap_large_spin.setValue(self.config["overlap_large"])
        self.overlap_small_spin.setValue(self.config["overlap_small"])

        output_folder = self.config.get("output_folder", "")
        if not output_folder:
            output_folder = (
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
                + "/"
            )
            self.config["output_folder"] = output_folder

        self.output_folder_edit.setText(output_folder)

        self.log_console.setVisible(False)

        self.update_device_info()

    def save_settings(self):
        """Save current UI settings to config."""
        self.config["cpu"] = self.checkbox_cpu.isChecked()
        self.config["single_onnx"] = self.checkbox_single_onnx.isChecked()
        self.config["large_gpu"] = self.checkbox_large_gpu.isChecked()
        self.config["only_vocals"] = self.checkbox_only_vocals.isChecked()
        self.config["use_kim_model_1"] = self.kim_combo.currentData()
        self.config["chunk_size"] = self.chunk_size_spin.value()
        self.config["overlap_large"] = self.overlap_large_spin.value()
        self.config["overlap_small"] = self.overlap_small_spin.value()
        self.config["output_folder"] = self.output_folder_edit.text()
        self.config["log_console_visible"] = self.log_console.isVisible()

        theme_name = "dark" if self.checkbox_dark_mode.isChecked() else "light"
        if self.config["theme"] == "auto":
            detected_theme = ThemeManager.detect_system_theme()
            if detected_theme != theme_name:
                self.config["theme"] = theme_name
        elif self.config["theme"] != theme_name:
            self.config["theme"] = theme_name

        ConfigManager.save(self.config)

    def update_device_info(self):
        """Update device info in status bar."""
        if self.checkbox_cpu.isChecked():
            device = "CPU"
        elif torch.cuda.is_available():
            device = "GPU (CUDA available)"
        else:
            device = "CPU (CUDA not available)"
        self.device_label.setText(f"Device: {device}")

    def select_input_files(self):
        """Open file dialog to select input audio files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Audio Files",
            "",
            "Audio Files (*.wav *.mp3 *.flac *.ogg *.m4a);;All Files (*)",
        )

        for file in files:
            self.add_file_to_list(file)

    def add_file_to_list(self, filepath):
        """Add a file to input list with an enabled checkbox."""
        if filepath not in self.input_files:
            self.input_files.append(filepath)

            row = self.file_table.rowCount()
            self.file_table.insertRow(row)

            filename = os.path.basename(filepath)
            size = self.get_file_size(filepath)
            format = os.path.splitext(filepath)[1].upper().lstrip(".")

            # Enabled checkbox in column 0 (use a checkable table item)
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(
                checkbox_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
            )
            checkbox_item.setCheckState(Qt.Checked)
            self.file_table.setItem(row, 0, checkbox_item)

            # File name in column 1 (store full path in user data)
            filename_item = QTableWidgetItem(filename)
            filename_item.setData(Qt.UserRole, filepath)
            filename_item.setFlags(
                filename_item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable
            )
            self.file_table.setItem(row, 1, filename_item)

            self.file_table.setItem(row, 2, QTableWidgetItem(size))
            self.file_table.setItem(row, 3, QTableWidgetItem(format))

            self.file_count_label.setText(f"{len(self.input_files)} files")
            self.progress_bar.setValue(0)

            if len(self.input_files) > 0:
                self.drop_zone.hide()
                self.file_table.show()

    def get_file_size(self, filepath):
        """Get human-readable file size."""
        try:
            size = os.path.getsize(filepath)
            for unit in ["B", "KB", "MB", "GB"]:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "N/A"

    def remove_file_from_list(self, filepath):
        """Remove a file from the input list."""
        if filepath in self.input_files:
            self.input_files.remove(filepath)

            for row in range(self.file_table.rowCount()):
                filename_item = self.file_table.item(row, 1)
                if filename_item and os.path.basename(filepath) == filename_item.text():
                    self.file_table.removeRow(row)
                    break

            self.file_count_label.setText(f"{len(self.input_files)} files")

            if len(self.input_files) == 0:
                self.file_table.hide()
                self.drop_zone.show()

    def clear_input_files(self):
        """Clear all files from the input list."""
        self.input_files.clear()
        self.file_table.setRowCount(0)
        self.file_count_label.setText("0 files")
        self.progress_bar.setValue(0)

        self.file_table.hide()
        self.drop_zone.show()

    def select_output_folder(self):
        """Open folder dialog to select output directory."""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder_edit.setText(folder + "/")
            self.save_settings()

    def apply_preset(self, index):
        """Apply selected output folder preset."""
        home = os.path.expanduser("~")

        presets = {
            0: os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"),
            1: "same_as_input",
            2: os.path.join(home, "Desktop"),
            3: os.path.join(home, "Documents"),
            4: os.path.join(home, "Downloads"),
        }

        if index in presets and presets[index] != "same_as_input":
            self.output_folder_edit.setText(presets[index] + "/")
            self.save_settings()

    def reset_advanced_settings(self):
        """Reset advanced settings to defaults."""
        self.chunk_size_spin.setValue(1000000)
        self.overlap_large_spin.setValue(0.6)
        self.overlap_small_spin.setValue(0.5)
        """Reset advanced settings to defaults."""
        self.chunk_size_spin.setValue(1000000)
        self.overlap_large_spin.setValue(0.6)
        self.overlap_small_spin.setValue(0.5)

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.accept()
            if self.drop_zone.isVisible():
                self.drop_zone.setStyleSheet("""
                    QLabel {
                        border: 2px dashed #4d4d4d;
                        border-radius: 8px;
                        padding: 20px;
                        color: #b0b0b0;
                        background-color: #2d2d2d;
                    }
                """)
            else:
                self.input_group.setStyleSheet("""
                    QGroupBox {
                        border: 2px dashed #4d4d4d;
                        background-color: #2d2d2d;
                    }
                """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        if self.drop_zone.isVisible():
            self.drop_zone.setStyleSheet("""
                QLabel {
                    border: 2px dashed #3d3d3d;
                    border-radius: 8px;
                    padding: 20px;
                    color: #616161;
                    background-color: transparent;
                }
            """)
        else:
            self.input_group.setStyleSheet("")

    def dropEvent(self, event):
        """Handle drop event."""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file in files:
            self.add_file_to_list(file)

        if self.drop_zone.isVisible():
            self.drop_zone.setStyleSheet("""
                QLabel {
                    border: 2px dashed #3d3d3d;
                    border-radius: 8px;
                    padding: 20px;
                    color: #616161;
                    background-color: transparent;
                }
            """)
        else:
            self.input_group.setStyleSheet("")
        event.accept()

    def start_separation(self):
        """Start audio separation processing for enabled files."""
        # collect enabled files from table (checkable QTableWidgetItem in col 0)
        enabled_files = []
        for row in range(self.file_table.rowCount()):
            checkbox_item = self.file_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                name_item = self.file_table.item(row, 1)
                if name_item:
                    filepath = name_item.data(Qt.UserRole)
                    enabled_files.append(filepath)

        if not enabled_files:
            QMessageBox.warning(
                self,
                "No Files",
                "No enabled files to process. Toggle files on to convert.",
            )
            return

        self.save_settings()

        self.is_processing = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.progress_label.show()
        self.progress_label.setText("Starting processing...")

        options = {
            "input_audio": enabled_files,
            "output_folder": self.output_folder_edit.text(),
            "cpu": self.checkbox_cpu.isChecked(),
            "single_onnx": self.checkbox_single_onnx.isChecked(),
            "large_gpu": self.checkbox_large_gpu.isChecked(),
            "chunk_size": self.chunk_size_spin.value(),
            "overlap_large": self.overlap_large_spin.value(),
            "overlap_small": self.overlap_small_spin.value(),
            "use_kim_model_1": self.kim_combo.currentData(),
            "only_vocals": self.checkbox_only_vocals.isChecked(),
        }

        self.thread = QThread()
        self.worker = Worker(options)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.processing_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log_console.add_message)
        self.worker.file_done.connect(self.on_file_done)

        self.thread.start()

        self.log_console.add_message("Processing started...")
        self.log_console.add_message(f"Processing {len(enabled_files)} file(s)")
        self.log_console.add_message(f"Output folder: {options['output_folder']}")

    def stop_separation(self):
        """Stop ongoing processing."""
        if self.thread and self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
            self.processing_finished()
            self.log_console.add_message("Processing stopped by user")

    def update_progress(self, percent):
        """Update progress bar."""
        self.progress_bar.setValue(percent)
        if percent > 0 and percent < 100:
            self.progress_label.setText(f"Processing... {percent}%")
        elif percent == 100:
            self.progress_label.setText("Processing complete!")

    def processing_finished(self):
        """Handle processing completion."""
        self.is_processing = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_console.add_message("Processing finished")

        # After processing completes, any files that were processed should be toggled off
        # (predict_with_model will call file_done per file so most will already be toggled)
        self.update_device_info()

    def on_file_done(self, filepath):
        """Called when a file has finished processing; toggle it off in the table."""
        # find the row with the matching filepath and uncheck its checkbox item
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 1)
            if item and item.data(Qt.UserRole) == filepath:
                checkbox_item = self.file_table.item(row, 0)
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Unchecked)
                break

    def update_table_columns(self):
        """Update table column visibility based on window width."""
        width = self.width()

        # Hide Name/Size for small widths but keep checkbox visible
        if width < 600:
            self.file_table.setColumnHidden(1, True)
            self.file_table.setColumnHidden(2, True)
            self.file_table.setColumnHidden(3, True)
        elif width < 800:
            self.file_table.setColumnHidden(1, True)
            self.file_table.setColumnHidden(2, True)
            self.file_table.setColumnHidden(3, False)
        else:
            self.file_table.setColumnHidden(1, False)
            self.file_table.setColumnHidden(2, False)
            self.file_table.setColumnHidden(3, False)

    def resizeEvent(self, event):
        """Handle window resize to show/hide table columns based on width."""
        super().resizeEvent(event)
        self.update_table_columns()
        print(f"Window size: {self.width()} x {self.height()}")

    def on_splitter_moved(self, pos, index):
        """Handle splitter movement when user resizes columns."""
        print(f"Window size: {self.width()} x {self.height()}")

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Delete:
            current_row = self.file_table.currentRow()
            if current_row >= 0:
                filename_item = self.file_table.item(current_row, 1)
                if filename_item:
                    for filepath in self.input_files:
                        if os.path.basename(filepath) == filename_item.text():
                            self.remove_file_from_list(filepath)
                            break
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Handle window close event."""
        if self.is_processing:
            reply = QMessageBox.question(
                self,
                "Processing in Progress",
                "Processing is still running. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.stop_separation()
                self.save_settings()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_settings()
            event.accept()


def main():
    app = QApplication(sys.argv)

    window = ModernMainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    print("Version: {}".format(__VERSION__))
    main()
