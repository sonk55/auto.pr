from PyQt6.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.GlobalColor.transparent)
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        
        # Create widget to hold the layout
        self.widget = QWidget(self)
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title = QLabel("Bitbucket Monitor")
        title.setStyleSheet("""
            QLabel {
                color: #2684FF;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Add loading text
        self.message_label = QLabel("Initializing...")
        self.message_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
        """)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 5px;
                text-align: center;
                background-color: #2b2b2b;
            }
            QProgressBar::chunk {
                background-color: #2684FF;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # Set widget size and position
        self.widget.setFixedSize(400, 200)
        self.widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-radius: 10px;
                border: 1px solid #404040;
            }
        """)
        
        # Center the splash screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.widget.width()) // 2,
            (screen.height() - self.widget.height()) // 2
        )
        
    def set_progress(self, value: int, message: str = None):
        self.progress_bar.setValue(value)
        if message:
            self.message_label.setText(message)
        QApplication.processEvents() 