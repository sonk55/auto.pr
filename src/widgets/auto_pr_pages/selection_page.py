from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, 
                           QListWidgetItem, QLabel, QGroupBox,
                           QHBoxLayout, QLineEdit, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config.repo_config import RepoConfig
from config.branch_config import BranchManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

class BranchSearchBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("Initializing BranchSearchBar")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 검색 타입 선택
        self.search_type = QComboBox()
        self.search_type.addItems(["Name", "Tag"])
        layout.addWidget(self.search_type)
        
        # 검색창
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search branches...")
        layout.addWidget(self.search_input)

class SelectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo_config = RepoConfig.get_instance()
        self.branch_manager = BranchManager.get_instance()
        self.all_branches = []  # 전체 브랜치 목록 저장
        logger.debug("Initializing SelectionPage")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 타이틀
        title = QLabel("Step 1: Select Recipes and Branches")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 선택 영역 컨테이너
        selection_layout = QHBoxLayout()
        
        # 레시피 선택 그룹
        recipe_group = QGroupBox("Recipes")
        recipe_layout = QVBoxLayout(recipe_group)
        
        # 레시피 선택 도움말
        recipe_help = QLabel("Select recipes to update (Ctrl+Click for multiple selection)")
        recipe_help.setStyleSheet("font-style: italic;")
        recipe_layout.addWidget(recipe_help)
        
        # 레시피 리스트
        self.recipe_list = QListWidget()
        self.recipe_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # 메타 저장소별로 레시피 그룹화
        for meta_repo in self.repo_config.meta_repos:
            meta_item = QListWidgetItem(f"📁 {meta_repo.name}")
            meta_item.setFlags(Qt.ItemFlag.NoItemFlags)
            font = meta_item.font()
            font.setBold(True)
            meta_item.setFont(font)
            self.recipe_list.addItem(meta_item)
            
            for recipe in meta_repo.recipes:
                recipe_item = QListWidgetItem(f"    ⚙️ {recipe.name}")
                recipe_item.setData(Qt.ItemDataRole.UserRole, (meta_repo.name, recipe.name))
                self.recipe_list.addItem(recipe_item)
                
        recipe_layout.addWidget(self.recipe_list)
        selection_layout.addWidget(recipe_group)
        
        # 브랜치 선택 그룹
        branch_group = QGroupBox("Target Branches")
        branch_layout = QVBoxLayout(branch_group)
        
        # 브랜치 선택 도움말
        branch_help = QLabel("Select target branches for PR creation")
        branch_help.setStyleSheet("color: gray; font-style: italic;")
        branch_layout.addWidget(branch_help)
        
        # 브랜치 검색
        self.search_bar = BranchSearchBar()
        self.search_bar.search_input.textChanged.connect(self.filter_branches)
        self.search_bar.search_type.currentTextChanged.connect(self.filter_branches)
        branch_layout.addWidget(self.search_bar)
        
        # 브랜치 리스트
        self.branch_list = QListWidget()
        self.branch_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.branch_list.setStyleSheet(self.recipe_list.styleSheet())
        
        # 브랜치 목록 로드
        self.all_branches = [(branch.name, branch.tags) for branch in self.branch_manager.branches]
        self.update_branch_list(self.all_branches)
        
        branch_layout.addWidget(self.branch_list)
        selection_layout.addWidget(branch_group)
        
        layout.addLayout(selection_layout)
        
    def update_branch_list(self, branches):
        """브랜치 리스트 업데이트"""
        logger.debug(f"Updating branch list with {len(branches)} branches")
        self.branch_list.clear()
        for branch_name, tags in branches:
            item = QListWidgetItem(branch_name)
            if tags:
                item.setToolTip(f"Tags: {', '.join(tags)}")
            self.branch_list.addItem(item)
            
    def filter_branches(self):
        """검색 조건에 맞는 브랜치 필터링"""
        search_text = self.search_bar.search_input.text().lower()
        search_type = self.search_bar.search_type.currentText()
        logger.debug(f"Filtering branches - type: {search_type}, text: {search_text}")
        
        if not search_text:
            self.update_branch_list(self.all_branches)
            return
            
        filtered_branches = []
        for branch_name, tags in self.all_branches:
            if search_type == "Name":
                if search_text in branch_name.lower():
                    filtered_branches.append((branch_name, tags))
            else:  # Tag 검색
                if any(search_text in tag.lower() for tag in tags):
                    filtered_branches.append((branch_name, tags))
                    
        logger.debug(f"Found {len(filtered_branches)} matching branches")
        self.update_branch_list(filtered_branches)
        
    def validate(self) -> bool:
        """선택된 레시피와 브랜치가 있는지 확인"""
        recipes = self.get_selected_recipes()
        branches = self.get_selected_branches()
        valid = len(recipes) > 0 and len(branches) > 0
        logger.info(f"Selection validation - Recipes: {len(recipes)}, Branches: {len(branches)}, Valid: {valid}")
        return valid
        
    def get_selected_recipes(self) -> list:
        """선택된 레시피 목록 반환"""
        selected = []
        for item in self.recipe_list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                selected.append(data)
        logger.debug(f"Selected recipes: {selected}")
        return selected
        
    def get_selected_branches(self) -> list:
        """선택된 브랜치 목록 반환"""
        selected = [item.text() for item in self.branch_list.selectedItems()]
        logger.debug(f"Selected branches: {selected}")
        return selected 