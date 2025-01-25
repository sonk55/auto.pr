from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QScrollArea,
                           QFrame, QListWidget, QListWidgetItem, QDialog)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QColor, QFont, QIcon
from datetime import datetime
from bitbucket.api import BitbucketAPI
from bitbucket.utils import parse_info_from_diff
from dialogs.edit_version_dialog import EditVersionDialog
from workspace.manager import WorkspaceManager
from git import git
class PRItemWidget(QFrame):
    def __init__(self, pr_data, parent=None):
        super().__init__(parent)
        self.pr_data = pr_data
        self.setObjectName("PRItem")  # 테마 스타일 적용을 위한 객체 이름
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Title
        title = QLabel(f"Title: {self.pr_data['title']}")
        title.setProperty("class", "title")  # 테마 스타일 적용
        title.setWordWrap(False)
        title.setMaximumWidth(600)
        
        # Branch info
        branch_label = QLabel(f"→ {self.pr_data['destination']['branch']['name']}")
        branch_label.setProperty("class", "branch")  # 테마 스타일 적용
        
        # Repository badge
        repo_name = self.pr_data['source']['repository']['name']
        repo_label = QLabel(repo_name)
        repo_label.setProperty("class", "repo")  # 테마 스타일 적용
        
        # Status badge
        status = self.pr_data['state']
        status_label = QLabel(status)
        status_label.setProperty("class", f"status-{status.lower()}")  # 테마 스타일 적용
        
        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(self.on_edit_clicked)
        
        layout.addWidget(title)
        layout.addWidget(branch_label)
        layout.addWidget(repo_label)
        layout.addWidget(status_label)
        layout.addWidget(edit_btn)

    def on_edit_clicked(self):
        diff_url = self.pr_data.get('links', {}).get('diff', {}).get('href')
        source_branch = self.pr_data['source']['branch']['name']
        repo_name = self.pr_data['source']['repository']['name']
        
        bitbucket = BitbucketAPI.get_instance()
        diff_info = parse_info_from_diff(bitbucket.get(diff_url))
        
        dialog = EditVersionDialog(diff_info, self.pr_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_versions = dialog.get_updated_versions()
            updated_branch = dialog.get_updated_branch()
            
            # 브랜치 변경이 있는 경우
            if updated_branch != source_branch:
                WorkspaceManager.get_instance().checkout_branch(repo_name, updated_branch)
            
            # 버전 업데이트
            tag_hash = git.get_remote_tag_hash(repo_name, updated_versions)
            WorkspaceManager.get_instance().update_bb_file(repo_name, "audiostreamingmanager.bb", updated_versions)



class HomeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_prs()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_prs)
        self.timer.start(5 * 60 * 1000)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(QIcon("resources/pr_icon.png").pixmap(24, 24))
        title_layout.addWidget(title_icon)
        
        title = QLabel("Pull Requests")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()
        header_layout.addLayout(title_layout)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background-color: #0052CC;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0747A6;
            }
        """)
        refresh_btn.clicked.connect(self.load_prs)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # PR List
        self.pr_list = QListWidget()
        self.pr_list.setSpacing(4)
        self.pr_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 0px;
                background-color: transparent;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
        """)
        
        layout.addWidget(self.pr_list)

    def load_prs(self):
        try:
            self.pr_list.clear()
            bitbucket = BitbucketAPI.get_instance()
            prs = bitbucket.get_pull_requests_meta()
            
            for pr in prs:
                item = QListWidgetItem(self.pr_list)
                widget = PRItemWidget(pr)
                item.setSizeHint(widget.sizeHint())
                self.pr_list.addItem(item)
                self.pr_list.setItemWidget(item, widget)
                
        except Exception as e:
            print(f"Error loading PRs: {e}") 