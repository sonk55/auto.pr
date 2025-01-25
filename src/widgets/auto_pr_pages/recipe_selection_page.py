from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, 
                           QListWidgetItem, QLabel, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config.repo_config import RepoConfig

class RecipeSelectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo_config = RepoConfig.get_instance()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 타이틀
        title = QLabel("Step 1: Select Recipes")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 도움말
        help_text = QLabel("Select recipes to update (Ctrl+Click for multiple selection)")
        help_text.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(help_text)
        
        # 레시피 리스트
        self.recipe_list = QListWidget()
        self.recipe_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.recipe_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: rgba(255, 255, 255, 30);
            }
        """)
        
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
                
        layout.addWidget(self.recipe_list)
        
    def validate(self) -> bool:
        """선택된 레시피가 있는지 확인"""
        return len(self.get_selected_recipes()) > 0
        
    def get_selected_recipes(self) -> list:
        """선택된 레시피 목록 반환 [(meta_name, recipe_name), ...]"""
        selected = []
        for item in self.recipe_list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:  # 메타 레포 헤더가 아닌 경우만
                selected.append(data)
        return selected 