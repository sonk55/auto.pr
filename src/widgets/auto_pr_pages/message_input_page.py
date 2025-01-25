from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QGroupBox, QLineEdit
from PyQt6.QtGui import QFont
from utils.logger import setup_logger  # 절대 경로 사용
import re
from workspace.manager import WorkspaceManager

logger = setup_logger(__name__)

class MessageInputPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("Initializing MessageInputPage")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 타이틀
        title = QLabel("Step 4: Enter PR Message")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # PR 제목
        title_group = QGroupBox("Title")
        title_layout = QVBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter PR title")
        title_layout.addWidget(self.title_edit)
        title_group.setLayout(title_layout)
        layout.addWidget(title_group)
        
        # PR 설명
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Enter PR description")
        desc_layout.addWidget(self.desc_edit)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)
        
        # 원인
        cause_group = QGroupBox("Cause")
        cause_layout = QVBoxLayout()
        self.cause_edit = QTextEdit()
        self.cause_edit.setPlaceholderText("Enter cause of changes")
        cause_layout.addWidget(self.cause_edit)
        cause_group.setLayout(cause_layout)
        layout.addWidget(cause_group)
        
        # 대책
        counter_group = QGroupBox("Countermeasure")
        counter_layout = QVBoxLayout()
        self.counter_edit = QTextEdit()
        self.counter_edit.setPlaceholderText("Enter countermeasure")
        counter_layout.addWidget(self.counter_edit)
        counter_group.setLayout(counter_layout)
        layout.addWidget(counter_group)
        
        # Jira
        jira_group = QGroupBox("Jira")
        jira_layout = QVBoxLayout()
        self.jira_edit = QTextEdit()
        self.jira_edit.setPlaceholderText("Enter Jira ticket numbers (one per line)")
        jira_layout.addWidget(self.jira_edit)
        jira_group.setLayout(jira_layout)
        layout.addWidget(jira_group)
        
    def validate(self) -> bool:
        """메시지가 입력되었는지 확인"""
        title = self.title_edit.text().strip()
        desc = self.desc_edit.toPlainText().strip()
        
        valid = bool(title and desc)
        logger.info(f"Message validation - Title: {len(title)}, Description: {len(desc)}, Valid: {valid}")
        return valid
        
    def get_message(self) -> dict:
        """입력된 PR 메시지 반환"""
        message = {
            'title': self.title_edit.text().strip(),
            'description': self.desc_edit.toPlainText().strip(),
            'cause': self.cause_edit.toPlainText().strip(),
            'countermeasure': self.counter_edit.toPlainText().strip(),
            'jiras': self.jira_edit.toPlainText().strip()
        }
        logger.debug(f"PR message: {message}")
        return message

    def set_auto_generated_message(self, updated_recipes: list, workspace: WorkspaceManager):
        """자동 생성된 메시지를 설정합니다."""
        # 제목 자동 생성
        title = ""
        for recipe in updated_recipes:
            if recipe['old_version'] != recipe['new_version']:
                title += f"{recipe['name']}={recipe['new_version'].replace('version/', '')} "
        self.title_edit.setText(title.strip())
        
        # 설명 자동 생성
        all_commit_messages = []
        description = []
        for recipe in updated_recipes:
            try:
                commits = workspace.get_commit_messages_between_tags(
                    recipe['name'],
                    recipe['old_version'],
                    recipe['new_version']
                )
                description.extend(commits)
                all_commit_messages.extend(commits)
            except Exception as e:
                logger.error(f"Failed to get commit messages for {recipe['name']}: {e}")
                
        self.desc_edit.setText("\n".join(description))
        
        # 원인과 대책
        causes = []
        countermeasures = []
        for commit in all_commit_messages:
            parsed = workspace.parse_commit_message(commit)
            if parsed.get('cause'):
                causes.append(parsed['cause'])
            if parsed.get('countermeasure'):
                countermeasures.append(parsed['countermeasure'])
                
        self.cause_edit.setText("\n".join(causes))
        self.counter_edit.setText("\n".join(countermeasures))
        
        # Jira 티켓
        jiras = set()
        for commit in all_commit_messages:
            jira_numbers = re.findall(r'(?:[A-Z][A-Z0-9]*-\d+)', commit)
            jiras.update(jira_numbers)
        self.jira_edit.setText("\n".join(sorted(jiras))) 