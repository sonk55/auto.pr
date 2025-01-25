from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
import json
import os

class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)

    THEMES = {
        "Dark": {
            "name": "dark",
            "stylesheet": """
                QMainWindow, QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QLabel {
                    background: none;
                    border: none;
                    padding: 2px;
                }
                QGroupBox {
                    border: 1px solid #404040;
                    margin-top: 6px;
                    padding-top: 6px;
                }
                QGroupBox::title {
                    color: #ffffff;
                    padding: 0 3px;
                }
                QLineEdit {
                    background-color: #363636;
                    border: 1px solid #404040;
                    border-radius: 3px;
                    padding: 5px;
                    color: #ffffff;
                }
                QLineEdit:disabled {
                    background-color: #2b2b2b;
                    color: #808080;
                }
                QTableWidget {
                    background-color: #2b2b2b;
                    border: 1px solid #404040;
                    gridline-color: #404040;
                }
                QHeaderView::section {
                    background-color: #363636;
                    padding: 5px;
                    border: none;
                    border-right: 1px solid #404040;
                    border-bottom: 1px solid #404040;
                }
                QTableWidget::item {
                    padding: 5px;
                }
                QPushButton {
                    background-color: #0052CC;
                    color: #ffffff;
                    border: none;
                    border-radius: 3px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #0747A6;
                }
                QPushButton:disabled {
                    background-color: #505F79;
                }
                QMenuBar {
                    background-color: #363636;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #4a4a4a;
                }
                QMenu {
                    background-color: #363636;
                    color: #ffffff;
                }
                QMenu::item:selected {
                    background-color: #4a4a4a;
                }
                QTabWidget::pane {
                    border: 1px solid #404040;
                }
                QTabBar::tab {
                    background-color: #363636;
                    color: #ffffff;
                    padding: 8px 20px;
                    border: 1px solid #404040;
                }
                QTabBar::tab:selected {
                    background-color: #4a4a4a;
                }
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QListWidget {
                    border: 1px solid #404040;
                    border-radius: 4px;
                }
                QListWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #404040;
                }
                QListWidget::item:selected {
                    background-color: #0052CC;
                    color: #ffffff;
                }
                QListWidget::item:hover:!selected {
                    background-color: #363636;
                }
                QComboBox {
                    background-color: #363636;
                    border: 1px solid #404040;
                    border-radius: 3px;
                    padding: 5px;
                    color: #ffffff;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: url(resources/down_arrow_white.png);
                }
                QScrollArea {
                    border: 1px solid #404040;
                    border-radius: 4px;
                }
                QProgressBar {
                    border: 1px solid #404040;
                    border-radius: 3px;
                    background-color: #2b2b2b;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0052CC;
                }
                QTextEdit {
                    background-color: #363636;
                    border: 1px solid #404040;
                    border-radius: 3px;
                    padding: 5px;
                    color: #ffffff;
                }
                QFrame#PRItem {
                    background-color: #363636;
                    margin: 2px;
                    border: 1px solid #404040;
                    border-radius: 6px;
                }
                QLabel.title {
                    font-size: 13px;
                    font-weight: bold;
                }
                QLabel.branch {
                    color: #8F9BA8;
                    font-size: 11px;
                }
                QLabel.repo {
                    color: #85B8FF;
                    font-size: 11px;
                }
                QLabel.status-merged {
                    color: #57D9A3;
                }
                QLabel.status-declined {
                    color: #FF9C8F;
                }
                QLabel.status-open {
                    color: #85B8FF;
                }
                QWidget#ProgressOverlay {
                    background-color: rgba(0, 0, 0, 0.7);
                    border-radius: 10px;
                }
                QWidget#ProgressOverlay QLabel {
                    color: white;
                    font-size: 14px;
                }
            """
        },
        "Light": {
            "name": "light",
            "stylesheet": """
                QMainWindow, QWidget {
                    background-color: #ffffff;
                    color: #000000;
                }
                QLabel {
                    background: none;
                    border: none;
                    padding: 2px;
                }
                QGroupBox {
                    border: 1px solid #d0d0d0;
                    margin-top: 6px;
                    padding-top: 6px;
                }
                QGroupBox::title {
                    color: #000000;
                    padding: 0 3px;
                }
                QLineEdit {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                    border-radius: 3px;
                    padding: 5px;
                }
                QLineEdit:disabled {
                    background-color: #ffffff;
                    color: #808080;
                }
                QTableWidget {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                    gridline-color: #d0d0d0;
                }
                QHeaderView::section {
                    background-color: #f0f0f0;
                    padding: 5px;
                    border: none;
                    border-right: 1px solid #d0d0d0;
                    border-bottom: 1px solid #d0d0d0;
                }
                QTableWidget::item {
                    padding: 5px;
                }
                QPushButton {
                    background-color: #0052CC;
                    color: #ffffff;
                    border: none;
                    border-radius: 3px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #0747A6;
                }
                QPushButton:disabled {
                    background-color: #505F79;
                }
                QMenuBar {
                    background-color: #f0f0f0;
                }
                QMenuBar::item:selected {
                    background-color: #e0e0e0;
                }
                QMenu {
                    background-color: #ffffff;
                }
                QMenu::item:selected {
                    background-color: #e0e0e0;
                }
                QTabWidget::pane {
                    border: 1px solid #d0d0d0;
                }
                QTabBar::tab {
                    background-color: #f0f0f0;
                    padding: 8px 20px;
                    border: 1px solid #d0d0d0;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                }
                QDialog {
                    background-color: #ffffff;
                    color: #000000;
                }
                QListWidget {
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                }
                QListWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #d0d0d0;
                }
                QListWidget::item:selected {
                    background-color: #0052CC;
                    color: #ffffff;
                }
                QListWidget::item:hover:!selected {
                    background-color: #f0f0f0;
                }
                QComboBox {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                    border-radius: 3px;
                    padding: 5px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: url(resources/down_arrow_black.png);
                }
                QScrollArea {
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                }
                QProgressBar {
                    border: 1px solid #d0d0d0;
                    border-radius: 3px;
                    background-color: #ffffff;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0052CC;
                }
                QTextEdit {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                    border-radius: 3px;
                    padding: 5px;
                }
                QFrame#PRItem {
                    background-color: #f8f9fa;
                    margin: 2px;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                }
                QLabel.title {
                    font-size: 13px;
                    font-weight: bold;
                }
                QLabel.branch {
                    color: #6c757d;
                    font-size: 11px;
                }
                QLabel.repo {
                    color: #0052CC;
                    font-size: 11px;
                }
                QLabel.status-merged {
                    color: #2da44e;
                }
                QLabel.status-declined {
                    color: #cf222e;
                }
                QLabel.status-open {
                    color: #0052CC;
                }
                QWidget#ProgressOverlay {
                    background-color: rgba(0, 0, 0, 0.5);
                    border-radius: 10px;
                }
                QWidget#ProgressOverlay QLabel {
                    color: white;
                    font-size: 14px;
                }
            """
        },
        "Nord": {
            "name": "nord",
            "stylesheet": """
                QMainWindow, QWidget {
                    background-color: #2E3440;
                    color: #ECEFF4;
                }
                QLabel {
                    background: none;
                    border: none;
                    padding: 2px;
                }
                QGroupBox {
                    border: 1px solid #4C566A;
                    margin-top: 6px;
                    padding-top: 6px;
                }
                QGroupBox::title {
                    color: #ECEFF4;
                    padding: 0 3px;
                }
                QLineEdit {
                    background-color: #3B4252;
                    border: 1px solid #4C566A;
                    border-radius: 3px;
                    padding: 5px;
                    color: #ECEFF4;
                }
                QLineEdit:disabled {
                    background-color: #2E3440;
                    color: #808080;
                }
                QTableWidget {
                    background-color: #2E3440;
                    border: 1px solid #4C566A;
                    gridline-color: #4C566A;
                }
                QHeaderView::section {
                    background-color: #3B4252;
                    padding: 5px;
                    border: none;
                    border-right: 1px solid #4C566A;
                    border-bottom: 1px solid #4C566A;
                }
                QTableWidget::item {
                    padding: 5px;
                }
                QPushButton {
                    background-color: #5E81AC;
                    color: #ECEFF4;
                    border: none;
                    border-radius: 3px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #81A1C1;
                }
                QPushButton:disabled {
                    background-color: #4C566A;
                }
                QMenuBar {
                    background-color: #3B4252;
                }
                QMenuBar::item:selected {
                    background-color: #434C5E;
                }
                QMenu {
                    background-color: #3B4252;
                }
                QMenu::item:selected {
                    background-color: #434C5E;
                }
                QTabWidget::pane {
                    border: 1px solid #4C566A;
                }
                QTabBar::tab {
                    background-color: #3B4252;
                    color: #ECEFF4;
                    padding: 8px 20px;
                    border: 1px solid #4C566A;
                }
                QTabBar::tab:selected {
                    background-color: #434C5E;
                }
                QDialog {
                    background-color: #2E3440;
                    color: #ECEFF4;
                }
                QListWidget {
                    border: 1px solid #4C566A;
                    border-radius: 4px;
                }
                QListWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #4C566A;
                }
                QListWidget::item:selected {
                    background-color: #5E81AC;
                    color: #ECEFF4;
                }
                QListWidget::item:hover:!selected {
                    background-color: #3B4252;
                }
                QComboBox {
                    background-color: #3B4252;
                    border: 1px solid #4C566A;
                    border-radius: 3px;
                    padding: 5px;
                    color: #ECEFF4;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: url(resources/down_arrow_white.png);
                }
                QScrollArea {
                    border: 1px solid #4C566A;
                    border-radius: 4px;
                }
                QProgressBar {
                    border: 1px solid #4C566A;
                    border-radius: 3px;
                    background-color: #2E3440;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #5E81AC;
                }
                QTextEdit {
                    background-color: #3B4252;
                    border: 1px solid #4C566A;
                    border-radius: 3px;
                    padding: 5px;
                    color: #ECEFF4;
                }
            """
        }
    }

    def __init__(self):
        super().__init__()
        self.current_theme = "Dark"
        self.load_theme_preference()

    def apply_theme(self, theme_name: str):
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            QApplication.instance().setStyleSheet(self.THEMES[theme_name]["stylesheet"])
            self.theme_changed.emit(theme_name)
            self.save_theme_preference()

    def get_available_themes(self):
        return list(self.THEMES.keys())

    def get_current_theme(self):
        return self.current_theme

    def save_theme_preference(self):
        config_dir = os.path.expanduser("~/.config/bitbucket-monitor")
        os.makedirs(config_dir, exist_ok=True)
        
        with open(os.path.join(config_dir, "theme.json"), "w") as f:
            json.dump({"theme": self.current_theme}, f)

    def load_theme_preference(self):
        try:
            config_file = os.path.expanduser("~/.config/bitbucket-monitor/theme.json")
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    data = json.load(f)
                    self.apply_theme(data.get("theme", "Dark"))
        except Exception:
            self.apply_theme("Dark") 