from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                           QLineEdit, QPushButton, QLabel,
                           QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt
import requests

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bitbucket Login")
        self.access_token = None
        self.setup_ui()
        
        # Set window modality
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Prevent closing with X button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Add logo or welcome text
        welcome_label = QLabel("Welcome to Bitbucket Monitor")
        welcome_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Login form
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        form_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox()
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.try_login)
        button_box.addButton(self.login_button, QDialogButtonBox.ButtonRole.AcceptRole)
        
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.reject)
        button_box.addButton(quit_button, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(button_box)

    def try_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password")
            return
        
        try:
            # Try to get access token using basic auth
            response = requests.post(
                "https://bitbucket.org/site/oauth2/access_token",
                auth=(username, password),
                data={"grant_type": "client_credentials"}
            )
            
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
                self.accept()
            else:
                QMessageBox.warning(self, "Login Error", "Invalid credentials")
                
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error", 
                               f"Failed to connect to Bitbucket: {str(e)}")

    def get_access_token(self):
        return self.access_token 