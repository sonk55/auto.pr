from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QTextEdit,
                           QFrame, QTableWidget, QTableWidgetItem,
                           QHeaderView, QStyle, QProgressBar, QCheckBox,
                           QGroupBox, QScrollArea, QListWidget, QListWidgetItem,
                           QLineEdit, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config.branch_config import BranchManager
from config.repo_config import RepoConfig
from workspace.manager import WorkspaceManager
from typing import Dict, List
from widgets.recipe_version_input import RecipeVersionInput
from widgets.auto_pr_pages.recipe_selection_page import RecipeSelectionPage
from widgets.auto_pr_pages.version_input_page import VersionInputPage
from widgets.auto_pr_pages.branch_selection_page import BranchSelectionPage
from widgets.auto_pr_pages.message_input_page import MessageInputPage
from widgets.auto_pr_pages.selection_page import SelectionPage
from utils.logger import setup_logger
from bitbucket.api import BitbucketAPI
import re
from git import git

logger = setup_logger(__name__)

class AutoPRTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo_config = RepoConfig.get_instance()
        self.branch_manager = BranchManager.get_instance()
        self.workspace = WorkspaceManager.get_instance()
        logger.debug("Initializing AutoPRTab")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 스택 위젯 설정
        self.stack = QStackedWidget()
        
        # 각 페이지 추가
        self.selection_page = SelectionPage()
        self.version_page = VersionInputPage()
        self.message_page = MessageInputPage()
        
        self.stack.addWidget(self.selection_page)
        self.stack.addWidget(self.version_page)
        self.stack.addWidget(self.message_page)
        
        # 네비게이션 버튼
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        
        layout.addWidget(self.stack)
        layout.addLayout(nav_layout)
        
    def next_page(self):
        current = self.stack.currentIndex()
        logger.debug(f"Moving to next page from index {current}")
        
        if current < self.stack.count() - 1:
            if self.validate_current_page():
                if current == 0:  # SelectionPage -> VersionInputPage
                    selected_recipes = self.selection_page.get_selected_recipes()
                    selected_branches = self.selection_page.get_selected_branches()
                    logger.info(f"Moving to version input with {len(selected_recipes)} recipes and {len(selected_branches)} branches")
                    self.version_page.update_recipes(selected_recipes, selected_branches)
                elif current == 1:  # VersionInputPage -> MessageInputPage
                    # 버전 정보 가져오기
                    version_info = self.version_page.get_version_info()
                    
                    # 각 브랜치별로 자동 메시지 생성
                    for target_branch, recipes in version_info.items():
                        updated_recipes = []
                        
                        # 먼저 모든 레시피 저장소를 최신으로 업데이트
                        workspace = WorkspaceManager.get_instance()
                        for (meta_name, recipe_name), (new_version, new_branch) in recipes.items():
                            try:
                                # 레시피 저장소 업데이트
                                workspace.checkout_branch(recipe_name, new_branch)
                                git.git_pull(workspace.active_repositories[recipe_name])
                                
                                # 메타 저장소 업데이트
                                workspace.checkout_branch(meta_name, target_branch)
                                git.git_pull(workspace.active_repositories[meta_name])
                                
                                # 현재 버전 정보 가져오기
                                current_info = workspace.get_recipe_info(meta_name, recipe_name, target_branch)
                                
                                updated_recipes.append({
                                    'name': recipe_name,
                                    'old_version': current_info['CCOS_VERSION'],
                                    'new_version': new_version,
                                    'old_branch': current_info['CCOS_GIT_BRANCH_NAME'],
                                    'new_branch': new_branch
                                })
                            except Exception as e:
                                logger.error(f"Failed to update repository {recipe_name}: {e}")
                                QMessageBox.critical(self, "Error", 
                                    f"Failed to update repository {recipe_name}: {str(e)}")
                                return
                            
                        # 자동 메시지 생성
                        self.message_page.set_auto_generated_message(
                            updated_recipes,
                            workspace
                        )
                
                self.stack.setCurrentIndex(current + 1)
                self.prev_btn.setEnabled(True)
                if current + 1 == self.stack.count() - 1:
                    self.next_btn.setText("Create PRs")
                
    def prev_page(self):
        current = self.stack.currentIndex()
        logger.debug(f"Moving to previous page from index {current}")
        
        if current > 0:
            self.stack.setCurrentIndex(current - 1)
            self.next_btn.setText("Next")
            if current - 1 == 0:
                self.prev_btn.setEnabled(False)
                
    def validate_current_page(self) -> bool:
        """현재 페이지의 입력 데이터 검증"""
        current_widget = self.stack.currentWidget()
        valid = current_widget.validate()
        logger.info(f"Current page ({current_widget.__class__.__name__}) validation: {valid}")
        return valid
        
    def load_branches(self):
        """브랜치 목록 업데이트"""
        self.branch_list.clear()
        for branch in self.branch_manager.branches:
            self.branch_list.addItem(branch.name)
            
    def get_selected_recipes(self) -> List[tuple]:
        """선택된 레시피 목록 반환 [(meta_name, recipe_name), ...]"""
        selected = []
        for item in self.recipe_list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:  # 메타 레포 헤더가 아닌 경우만
                selected.append(data)
        return selected
        
    def get_selected_branches(self) -> List[str]:
        """선택된 브랜치 목록 반환"""
        return [item.text() for item in self.branch_list.selectedItems()]
        
    def update_version_inputs(self):
        """선택된 레시피에 따라 버전 입력 UI 업데이트"""
        # 기존 입력 위젯 제거
        while self.version_inputs_layout.count():
            item = self.version_inputs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 선택된 레시피에 대한 입력 위젯 추가
        self.recipe_inputs = {}  # 입력 위젯 저장
        for meta_name, recipe_name in self.get_selected_recipes():
            input_widget = RecipeVersionInput(meta_name, recipe_name)
            self.recipe_inputs[(meta_name, recipe_name)] = input_widget
            self.version_inputs_layout.addWidget(input_widget)
        
        self.version_inputs_layout.addStretch()
        
    def create_pull_requests(self):
        """PR 생성 처리"""
        version_info = self.version_page.get_version_info()
        user_message = self.message_page.get_message()
        
        if not version_info:
            logger.warning("No version information provided")
            return
            
        if not user_message:
            logger.warning("No PR message provided")
            return
            
        logger.info(f"Creating PRs with message: {user_message}")
        logger.debug(f"Version info: {version_info}")
        
        # 진행 상태 표시
        self.progress_bar.show()
        self.progress_bar.setMaximum(len(version_info))  # 브랜치 수만큼 설정
        self.progress_bar.setValue(0)
        
        try:
            workspace = WorkspaceManager.get_instance()
            bitbucket = BitbucketAPI.get_instance()
            
            for target_branch, recipes in version_info.items():
                logger.info(f"Processing target branch: {target_branch}")
                
                # 메타 저장소별로 그룹화
                meta_groups = {}
                for (meta_name, recipe_name), (version, branch) in recipes.items():
                    if meta_name not in meta_groups:
                        meta_groups[meta_name] = []
                    meta_groups[meta_name].append({
                        'recipe_name': recipe_name,
                        'version': version,
                        'branch': branch
                    })
                
                # 각 메타 저장소에 대해 PR 생성
                for meta_name, recipe_updates in meta_groups.items():
                    logger.info(f"Creating PR for meta repo: {meta_name}")
                    
                    # 메타 저장소 체크아웃
                    workspace.checkout_branch(meta_name, target_branch)
                    
                    # BB 파일 업데이트
                    updated_recipes = []
                    for update in recipe_updates:
                        recipe_name = update['recipe_name']
                        version = update['version']
                        branch = update['branch']
                        
                        # 레시피 저장소의 태그 해시 가져오기
                        tags = workspace.get_tag_hash_by_branch(recipe_name, branch)
                        if version not in tags:
                            raise Exception(f"Version {version} not found in {recipe_name} tags")
                        
                        # BB 파일 업데이트
                        workspace.update_bb_file(meta_name, f"{recipe_name}.bb", {
                            'version': version,
                            'branch': branch,
                            'tag': tags[version]
                        })
                        
                        # 업데이트된 레시피 정보 저장
                        updated_recipes.append({
                            'name': recipe_name,
                            'old_version': workspace.get_recipe_info(meta_name, recipe_name, target_branch)['CCOS_VERSION'],
                            'new_version': version,
                            'old_branch': workspace.get_recipe_info(meta_name, recipe_name, target_branch)['CCOS_GIT_BRANCH_NAME'],
                            'new_branch': branch
                        })
                    
                    # 자동 커밋 메시지 생성
                    commit_message = self.generate_commit_message(
                        meta_name, 
                        target_branch, 
                        updated_recipes,
                        user_message
                    )
                    
                    workspace.update_changes(meta_name, commit_message)
                    
                    # PR 생성
                    pr_data = {
                        'title': f"Update CCOS versions for {target_branch}",
                        'description': commit_message,
                        'source': {
                            'branch': target_branch,
                            'repository': meta_name
                        },
                        'destination': {
                            'branch': target_branch
                        }
                    }
                    
                    bitbucket.create_pull_request(pr_data)
                
                self.progress_bar.setValue(self.progress_bar.value() + 1)
                
            QMessageBox.information(self, "Success", "Pull requests created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating PRs: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create pull requests: {str(e)}")
            
        finally:
            self.progress_bar.hide()
            
    def generate_commit_message(self, meta_name: str, target_branch: str, 
                              updated_recipes: list, user_message: dict) -> str:
        """커밋 메시지를 자동으로 생성합니다."""
        workspace = WorkspaceManager.get_instance()
        
        # 각 레시피의 커밋 메시지 수집
        all_commit_messages = []
        for recipe in updated_recipes:
            try:
                # 이전 버전과 새 버전 사이의 커밋 메시지 가져오기
                commits = workspace.get_commit_messages_between_tags(
                    recipe['name'],
                    recipe['old_version'],
                    recipe['new_version']
                )
                all_commit_messages.extend(commits)
            except Exception as e:
                logger.warning(f"Failed to get commit messages for {recipe['name']}: {e}")
        
        # 커밋 메시지 분석
        description = []
        causes = []
        countermeasures = []
        jiras = set()
        
        for commit in all_commit_messages:
            # 커밋 메시지 파싱
            parsed = workspace.parse_commit_message(commit)
            
            if parsed.get('description'):
                description.append(parsed['description'])
            if parsed.get('cause'):
                causes.append(parsed['cause'])
            if parsed.get('countermeasure'):
                countermeasures.append(parsed['countermeasure'])
                
            # Jira 번호 추출
            if parsed.get('jira'):
                jiras.update(re.findall(r'(?:[A-Z][A-Z0-9]*-\d+)', parsed['jira']))
        
        # 메시지 생성
        message = f"Update CCOS versions for {target_branch}\n\n"
        
        # 설명
        if description:
            message += "Description:\n"
            message += "\n".join(description) + "\n\n"
            
        # 원인
        if causes:
            message += "Cause:\n"
            message += "\n".join(causes) + "\n\n"
            
        # 대책
        if countermeasures:
            message += "Countermeasure:\n"
            message += "\n".join(countermeasures) + "\n\n"
            
        # 변경사항 요약
        message += "Changes:\n"
        message += f"- Repository: {meta_name}\n"
        message += f"- Target Branch: {target_branch}\n\n"
        
        # 레시피별 상세 변경사항
        message += "Updated Recipes:\n"
        for recipe in updated_recipes:
            message += f"- {recipe['name']}:\n"
            if recipe['old_version'] != recipe['new_version']:
                message += f"  - Version: {recipe['old_version']} -> {recipe['new_version']}\n"
            if recipe['old_branch'] != recipe['new_branch']:
                message += f"  - Branch: {recipe['old_branch']} -> {recipe['new_branch']}\n"
                
        # Jira 티켓
        if jiras:
            message += "\nJiras:\n"
            message += "\n".join(sorted(jiras)) + "\n"
                
        return message 