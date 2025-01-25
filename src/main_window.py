from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMenuBar, QMenu, QStackedWidget
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from themes.theme_manager import ThemeManager
from config.server_config import ConfigManager
from dialogs.settings_dialog import SettingsDialog
from widgets.login_page import LoginPage
from atlassian import Bitbucket
from bitbucket.api import BitbucketAPI
from widgets.home_tab import HomeTab
from config.repo_config import RepoConfig
from workspace.manager import WorkspaceManager
from widgets.recipe_versions_tab import RecipeVersionsTab
from widgets.auto_pr_tab import AutoPRTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.config_manager = ConfigManager()
        self.workspace = WorkspaceManager()
        
        # Bitbucket API 초기화
        self.bitbucket = None
        self.initialize_bitbucket()
        
        self.setWindowTitle("Bitbucket Monitoring Tool")
        self.setup_ui()
        self.create_menus()
        self.show_login_page()
        self.setup_workspace()

    def initialize_bitbucket(self):
        """Bitbucket API 초기화"""
        try:
            # 저장된 인증 정보 로드
            username, password = self.config_manager.load_credentials()
            if username and password:
                self.bitbucket = Bitbucket(
                    url='https://bitbucket.org',
                    username=username,
                    password=password
                )
                BitbucketAPI.initialize(self.bitbucket)
        except Exception as e:
            print(f"Failed to initialize Bitbucket API: {e}")

    def setup_workspace(self):
        self.repo_config = RepoConfig.get_instance()
        self.repo_config.load_config()
        
        for repo in self.repo_config.meta_repos:
            self.workspace.clone_repository(repo.url, "@s6mobis")
            for recipe in repo.recipes:
                self.workspace.clone_repository(recipe.url, "@s6mobis", recipe.name)

    def setup_ui(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create main content
        self.tab_widget = QTabWidget()
        
        # Create and add tabs
        self.home_tab = HomeTab(self)
        self.tab_widget.addTab(self.home_tab, "Home")
        
        # Add recipe versions tab
        self.versions_tab = RecipeVersionsTab()
        self.tab_widget.addTab(self.versions_tab, "Recipe Versions")
        
        # Add auto PR tab
        self.auto_pr_tab = AutoPRTab()
        self.tab_widget.addTab(self.auto_pr_tab, "Auto PR")
        
        # Add more tabs here as needed
        # self.tab_widget.addTab(self.repositories_tab, "Repositories")
        # self.tab_widget.addTab(self.settings_tab, "Settings")
        
        self.stacked_widget.addWidget(self.tab_widget)
        
        # Create login page
        self.login_page = LoginPage()
        self.login_page.login_successful.connect(self.on_login_successful)
        self.stacked_widget.addWidget(self.login_page)
        
        self.resize(1200, 800)

    def get_bitbucket(self):
        return self.bitbucket

    def show_login_page(self):
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.menuBar().setVisible(False)

    def on_login_successful(self, bitbucket: Bitbucket):
        """Handle successful login"""
        self.bitbucket = BitbucketAPI.initialize(bitbucket)
        self.stacked_widget.setCurrentWidget(self.tab_widget)
        self.menuBar().setVisible(True)
        
        try:
            user = self.bitbucket.get_current_user()
            self.setWindowTitle(f"Bitbucket Monitor - {user['username']}")
        except Exception as e:
            print(f"Error getting user info: {e}")

    def create_menus(self):
        menubar = self.menuBar()
        menubar.setVisible(False)  # Initially hidden until login
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # View menu
        view_menu = menubar.addMenu("View")

        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.setStatusTip("Open settings dialog")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

    def show_settings(self):
        dialog = SettingsDialog(self.theme_manager, self.config_manager, self)
        dialog.exec() 