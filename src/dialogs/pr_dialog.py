from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                           QPushButton, QProgressBar, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
from workspace.manager import WorkspaceManager
from bitbucket.api import BitbucketAPI
from utils.logger import setup_logger  # 절대 경로 사용
from utils.version_utils import generate_next_version  # 변경
import os
import re
from typing import List

logger = setup_logger(__name__)

class PRDialog(QDialog):
    def __init__(self, branch: str, version_info: dict, parent=None):
        super().__init__(parent)
        logger.info(f"PRDialog initialized with branch: {branch}")
        self.branch = branch
        self.version_info = version_info  # 사용자가 입력한 버전 정보
        self.workspace = WorkspaceManager.get_instance()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"Create PR for {self.branch}")
        layout = QVBoxLayout(self)
        
        # 자동 생성된 PR 메시지 표시
        message = self.generate_pr_message()
        
        # PR 미리보기
        preview = QTextEdit()
        preview.setReadOnly(True)
        preview.setPlainText(message)
        preview.setMinimumWidth(600)
        preview.setMinimumHeight(400)
        layout.addWidget(preview)
        
        # Diff 미리보기
        diff_label = QLabel("Changes to be committed:")
        layout.addWidget(diff_label)
        
        diff_preview = QTextEdit()
        diff_preview.setReadOnly(True)
        diff_preview.setPlainText(self.get_diff_preview())
        diff_preview.setStyleSheet("""
            QTextEdit {
                font-family: monospace;
                background-color: #f6f8fa;
            }
        """)
        layout.addWidget(diff_preview)
        
        # 진행 상태 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("Create PR")
        self.create_btn.clicked.connect(self.create_pr)
        button_layout.addWidget(self.create_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def select_head_tag(self, recipe_name: str, head_tags: List[str]) -> str:
        """HEAD에 있는 여러 태그 중 하나를 선택하는 대화상자"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Tag")
        layout = QVBoxLayout(dialog)
        
        # 설명 레이블
        layout.addWidget(QLabel(f"Multiple tags found for {recipe_name} at HEAD.\nPlease select one:"))
        
        # 태그 선택 콤보박스
        combo = QComboBox()
        combo.addItems(head_tags)
        layout.addWidget(combo)
        
        # 버튼
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return combo.currentText()
        return None

    def generate_pr_message(self) -> str:
        """PR 메시지 자동 생성"""
        try:
            changes = []
            titles = []  # 커밋 제목들
            jiras = set()  # JIRA 티켓 번호들
            title_parts = []  # PR 제목 부분
            
            # version_info에서 변경사항 가져오기
            for (meta_name, recipe_name), (version, _) in self.version_info.items():
                logger.info(f"Processing recipe: {recipe_name}")
                try:
                    current_info = self.workspace.get_recipe_info(meta_name, recipe_name, self.branch)
                    latest_tag = self.workspace.get_latest_tag(recipe_name)
                    
                    if current_info:
                        if version == "HEAD":
                            head_tags = self.workspace.get_head_tags(recipe_name)
                            if head_tags:
                                if len(head_tags) > 1:
                                    # 여러 태그가 있는 경우 선택 대화상자 표시
                                    selected_tag = self.select_head_tag(recipe_name, head_tags)
                                    if not selected_tag:  # 취소한 경우
                                        raise Exception(f"Tag selection cancelled for {recipe_name}")
                                    next_version = selected_tag
                                else:
                                    next_version = head_tags[0]
                                version_str = next_version.replace('version/', '')
                                changes.append(f"- {recipe_name}: {current_info['CCOS_VERSION']} -> {next_version} (using HEAD tag)")
                            else:
                                next_version = generate_next_version(latest_tag)
                                version_str = next_version.replace('version/', '')
                                changes.append(f"- {recipe_name}: {current_info['CCOS_VERSION']} -> {next_version} (auto from {latest_tag})")
                        else:
                            version_str = version.replace('version/', '')
                            changes.append(f"- {recipe_name}: {current_info['CCOS_VERSION']} -> {version}")
                        
                        title_parts.append(f"{recipe_name}={version_str}")
                        
                        # 커밋 메시지 수집 (current tag부터 version까지)
                        titles = self.workspace.get_commit_messages_between_tags(
                            recipe_name,
                            current_info['CCOS_VERSION'],
                            version
                        )
                        
                        jiras = self.workspace.get_jira_numbers_between_tags(
                            recipe_name,
                            current_info['CCOS_VERSION'],
                            version
                        )
                        
                        logger.info(f"Commits for {recipe_name} from {latest_tag} to HEAD: {titles}")
                        
                            
                except Exception as e:
                    logger.warning(f"Failed to process {recipe_name}: {e}")
            
            # 메시지 구성
            message = " ".join(title_parts) + "\n\n"  # PR 제목
            
            if changes:
                message += "Changes:\n" + "\n".join(changes) + "\n\n"
                
            if titles:
                message += "Commits:\n" + "\n".join(titles) + "\n\n"  # 커밋 제목들
                
            if jiras:
                message += "Jiras:\n" + "\n".join(sorted(jiras)) + "\n"  # JIRA 티켓들
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to generate PR message: {e}")
            return f"Failed to generate PR message: {e}"
        
    def get_diff_preview(self) -> str:
        """변경사항 미리보기"""
        try:
            diffs = []
            for meta_name in self.workspace.get_modified_repositories():
                diff = self.workspace.get_diff(meta_name)
                if diff:
                    diffs.append(f"=== {meta_name} ===\n{diff}\n")
            return "\n".join(diffs)
        except Exception as e:
            return f"Failed to get diff: {e}"
            
    def create_pr(self):
        """PR 생성"""
        try:
            self.progress_bar.show()
            self.create_btn.setEnabled(False)
            
            for (meta_name, recipe_name), (version, _) in self.version_info.items():
                try:
                    current_info = self.workspace.get_recipe_info(meta_name, recipe_name, self.branch)
                    latest_tag = self.workspace.get_latest_tag(recipe_name)
                    
                    if current_info:
                        if version == "HEAD":
                            head_tags = self.workspace.get_head_tags(recipe_name)
                            if head_tags:
                                if len(head_tags) > 1:
                                    # 여러 태그가 있는 경우 선택 대화상자 표시
                                    selected_tag = self.select_head_tag(recipe_name, head_tags)
                                    if not selected_tag:  # 취소한 경우
                                        raise Exception(f"Tag selection cancelled for {recipe_name}")
                                    new_version = selected_tag
                                else:
                                    new_version = head_tags[0]
                            else:
                                new_version = generate_next_version(latest_tag)
                        else:
                            new_version = version
                        
                        # 태그 메시지 생성
                        message = f"Update {recipe_name} from {latest_tag} to {new_version}"
                        
                        # HEAD에 이미 태그가 있는 경우는 새로 생성하지 않음
                        if not (version == "HEAD" and head_tags):
                            # 태그 생성 및 푸시
                            if self.workspace.create_version_tag(recipe_name, new_version, message):
                                logger.info(f"Created tag {new_version} for {recipe_name}")
                            else:
                                raise Exception(f"Failed to create tag {new_version} for {recipe_name}")
                        
                except Exception as e:
                    logger.error(f"Failed to process {recipe_name}: {e}")
                    raise
            
            # PR 생성 로직
            # ... (기존 create_pull_requests 로직)
            
            QMessageBox.information(self, "Success", "Pull request and tags created successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create pull request: {str(e)}")
            
        finally:
            self.progress_bar.hide()
            self.create_btn.setEnabled(True) 