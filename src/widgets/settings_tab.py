from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                           QComboBox, QLabel, QFormLayout)
from PyQt6.QtCore import pyqtSlot

class SettingsTab(QWidget):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Theme settings group
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.get_available_themes())
        self.theme_combo.setCurrentText(self.theme_manager.get_current_theme())
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)

        theme_layout.addRow("Theme:", self.theme_combo)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # Add stretch to prevent widgets from being stretched
        layout.addStretch()

    @pyqtSlot(str)
    def on_theme_changed(self, theme_name):
        self.theme_manager.apply_theme(theme_name) 