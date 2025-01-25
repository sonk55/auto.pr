from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, 
                           QLineEdit, QPushButton, QLabel,
                           QCheckBox, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt6.QtGui import QPixmap, QResizeEvent
from atlassian import Bitbucket
from atlassian.bitbucket import Cloud
import requests
import json
import os
from config.server_config import ConfigManager
from bitbucket.api import BitbucketAPI
class LoginWorker(QThread):
    finished = pyqtSignal(object)  # 성공 시 bitbucket 객체 전달
    error = pyqtSignal(str)  # 에러 메시지 전달
    
    def __init__(self, server_config, username, password):
        super().__init__()
        self.server_config = server_config
        self.username = username
        self.password = password
        
    def run(self):
        try:
            bitbucket = Cloud(
                url=self.server_config.api_url,
                username=self.username,
                password=self.password,
            )
            
            # Test connection
            response = bitbucket.get('user')
            print(f"Login successful: {response['username']}")
            
            self.finished.emit(bitbucket)
            
        except Exception as e:
            self.error.emit(str(e))

class LoginPage(QWidget):
    login_successful = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.setup_ui()
        self.load_credentials()

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create a frame for the content with some styling
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
        """)
        
        # Content layout with stretches for vertical and horizontal centering
        main_layout = QVBoxLayout(self.content_frame)
        main_layout.setSpacing(20)
        
        # Center container
        center_container = QWidget()
        content_layout = QVBoxLayout(center_container)
        content_layout.setSpacing(20)
        
        # Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.logo_label)
        
        # Welcome text
        self.welcome_label = QLabel("Welcome to Bitbucket Monitor")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.welcome_label)
        
        # Login form
        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)
        self.form_layout.setContentsMargins(0, 20, 0, 20)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        self.form_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self.username_input.styleSheet())
        self.form_layout.addRow("Password:", self.password_input)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        self.form_layout.addRow("", self.remember_checkbox)
        
        content_layout.addWidget(form_widget)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #2684FF;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052CC;
            }
        """)
        self.login_button.clicked.connect(self.try_login)
        content_layout.addWidget(self.login_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add center container to main layout with stretches
        main_layout.addStretch(1)
        main_layout.addWidget(center_container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch(1)
        
        # Add the content frame to the main layout
        layout.addWidget(self.content_frame)
        
        # Progress overlay
        self.progress_overlay = QWidget(self)
        self.progress_overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 10px;
            }
            QLabel {
                color: white;
                font-size: 14px;
                background: transparent;
            }
        """)
        overlay_layout = QVBoxLayout(self.progress_overlay)
        self.progress_label = QLabel("Logging in...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(self.progress_label)
        self.progress_overlay.hide()
        
        # Initial update of sizes
        self.update_sizes()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.update_sizes()
        # Overlay를 페이지 크기에 맞춤
        self.progress_overlay.resize(self.size())

    def update_sizes(self):
        # Get the window size
        width = self.width()
        height = self.height()
        
        # Calculate responsive sizes
        content_width = int(min(max(width * 0.8, 300), 500))
        logo_size = int(min(max(height * 0.15, 60), 120))
        font_size = int(min(max(height * 0.03, 14), 24))
        input_width = int(min(content_width * 0.7, 300))
        button_width = int(min(content_width * 0.5, 200))
        
        # Update center container width
        self.content_frame.setMinimumWidth(content_width)
        
        # Update logo size
        try:
            self.logo_label.setPixmap(QPixmap("resources/logo.png").scaled(
                logo_size, logo_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        except FileNotFoundError:
            self.logo_label.setText("LOGO")
            self.logo_label.setStyleSheet(f"""
                font-size: {int(logo_size/2)}px;
                color: #2684FF;
                font-weight: bold;
            """)
        
        # Update welcome text size
        self.welcome_label.setStyleSheet(f"""
            font-size: {font_size}px;
            font-weight: bold;
            margin: {int(font_size/2)}px;
            color: #2684FF;
        """)
        
        # Update input fields width
        self.username_input.setFixedWidth(input_width)
        self.password_input.setFixedWidth(input_width)
        
        # Update button width
        self.login_button.setFixedWidth(button_width)
        
        # Update form layout spacing
        form_spacing = int(height * 0.02)
        self.form_layout.setSpacing(form_spacing)

    def show_progress(self, message="Logging in..."):
        self.progress_label.setText(message)
        self.progress_overlay.show()
        
    def hide_progress(self):
        self.progress_overlay.hide()

    def try_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(
                self, 
                "Login Error", 
                "Please enter both username and App Password.\n\n"
                "Note: You need to use an App Password, not your account password.\n"
                "1. Go to Bitbucket Settings -> App passwords\n"
                "2. Create a new App password\n"
                "3. Grant the following permissions:\n"
                "   - Account: Read\n"
                "   - Workspace membership: Read\n"
                "   - Repositories: Read\n"
                "   - Pull requests: Read\n"
                "4. Copy and use the generated App password here"
            )
            return
        
        self.show_progress()
        
        # 로그인 워커 생성 및 시작
        self.login_worker = LoginWorker(
            self.config_manager.current_server,
            username,
            password
        )
        
        def on_login_success(bitbucket):
            # Save credentials if remember me is checked
            if self.remember_checkbox.isChecked():
                self.config_manager.save_credentials(username, password)
            
            self.hide_progress()
            self.login_successful.emit(bitbucket)
        
        def on_login_error(error_msg):
            self.hide_progress()
            QMessageBox.critical(self, "Login Error", f"Failed to login: {error_msg}")
        
        self.login_worker.finished.connect(on_login_success)
        self.login_worker.error.connect(on_login_error)
        self.login_worker.start()

    def load_credentials(self):
        username, password = self.config_manager.load_credentials()
        if username and password:
            self.username_input.setText(username)
            self.password_input.setText(password)
            self.remember_checkbox.setChecked(True) 