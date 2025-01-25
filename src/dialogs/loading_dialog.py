from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QScreen, QPalette, QColor

class LoadingDialog(QDialog):
    def __init__(self, message: str = "Loading...", parent=None):
        super().__init__(parent)
        self.setup_ui(message)
        
    def setup_ui(self, message: str):
        # 배경 투명하게 설정
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 메인 프레임
        frame = QFrame(self)
        frame.setObjectName("loadingFrame")
        frame.setStyleSheet("""
            QFrame#loadingFrame {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QProgressBar {
                border: 2px solid white;
                border-radius: 5px;
                text-align: center;
                background-color: transparent;
            }
            QProgressBar::chunk {
                background-color: white;
            }
        """)
        
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        
        # 메시지 레이블
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(label)
        
        # 진행바
        progress = QProgressBar()
        progress.setRange(0, 0)  # 무한 진행바
        progress.setFixedHeight(10)
        frame_layout.addWidget(progress)
        
        layout.addWidget(frame)
        
        # 화면 중앙에 위치
        self.center_on_screen()
        
    def center_on_screen(self):
        """화면 중앙에 위치시킴"""
        frame = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft()) 