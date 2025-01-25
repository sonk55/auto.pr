import os
import sys

# src 디렉토리를 PYTHONPATH에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_window import MainWindow
from widgets.splash_screen import SplashScreen
from themes.theme_manager import ThemeManager

def main():
    app = QApplication(sys.argv)
    
    # Apply initial dark theme
    theme_manager = ThemeManager()
    theme_manager.apply_theme("Dark")
    
    # Show splash screen first
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    window = None  # MainWindow 인스턴스를 나중에 생성
    
    def create_main_window():
        nonlocal window
        # Update progress
        splash.set_progress(30, "Loading configurations...")
        app.processEvents()
        
        # Create main window
        window = MainWindow()
        
        # Continue with progress
        splash.set_progress(60, "Cloning repositories...")
        app.processEvents()
        
        QTimer.singleShot(500, lambda: splash.set_progress(90, "Preparing interface..."))
        QTimer.singleShot(1000, finish_splash)
    
    def finish_splash():
        splash.set_progress(100, "Ready!")
        window.show()
        splash.finish(window)
    
    # Start window creation after showing splash screen
    QTimer.singleShot(100, create_main_window)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 