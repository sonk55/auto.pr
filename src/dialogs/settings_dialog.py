from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, 
                           QComboBox, QLabel, QFormLayout,
                           QDialogButtonBox, QLineEdit, QTableWidget,
                           QTableWidgetItem, QHeaderView, QPushButton,
                           QHBoxLayout, QMessageBox, QInputDialog,
                           QTabWidget, QWidget, QTreeWidget,
                           QTreeWidgetItem, QSplitter, QStackedWidget,
                           QToolBar, QStyle, QMenu)
from PyQt6.QtCore import Qt
from config.server_config import ServerConfig
from config.repo_config import RepoConfig, Recipe, MetaRepo
from workspace.manager import WorkspaceManager
from config.branch_config import BranchManager, BranchConfig

class AddRecipeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Recipe")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.id_input = QLineEdit()
        form.addRow("Recipe ID:", self.id_input)
        
        self.name_input = QLineEdit()
        form.addRow("Recipe Name:", self.name_input)
        
        self.url_input = QLineEdit()
        form.addRow("Repository URL:", self.url_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_recipe(self):
        return Recipe(
            id=self.id_input.text(),
            name=self.name_input.text(),
            url=self.url_input.text()
        )

class AddMetaRepoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Meta Repository")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        form.addRow("Repository Name:", self.name_input)
        
        self.url_input = QLineEdit()
        form.addRow("Repository URL:", self.url_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_meta_repo(self):
        return MetaRepo(
            name=self.name_input.text(),
            url=self.url_input.text(),
            recipes=[]
        )

class ServerSettingsTab(QWidget):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.server_name = QLineEdit(self.config_manager.current_server.name)
        form_layout.addRow("Server Name:", self.server_name)
        
        self.server_url = QLineEdit(self.config_manager.current_server.url)
        form_layout.addRow("Server URL:", self.server_url)
        
        self.api_url = QLineEdit(self.config_manager.current_server.api_url)
        form_layout.addRow("API URL:", self.api_url)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
    def save_settings(self):
        self.config_manager.current_server = ServerConfig(
            name=self.server_name.text(),
            url=self.server_url.text(),
            api_url=self.api_url.text()
        )
        self.config_manager.save_server_config()

class RepositorySettingsTab(QWidget):
    def __init__(self, repo_config, parent=None):
        super().__init__(parent)
        self.repo_config = repo_config
        self.workspace = WorkspaceManager.get_instance()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QToolBar()
        
        # Add actions
        add_meta_action = toolbar.addAction("Add Meta Repo")
        add_meta_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        add_meta_action.triggered.connect(self.add_meta_repo)
        
        remove_action = toolbar.addAction("Remove")
        remove_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        remove_action.triggered.connect(self.remove_selected)
        
        toolbar.addSeparator()
        
        add_recipe_action = toolbar.addAction("Add Recipe")
        add_recipe_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        add_recipe_action.triggered.connect(self.add_recipe)
        
        layout.addWidget(toolbar)
        
        # Splitter for tree and details
        splitter = QSplitter()
        
        # Repository tree
        self.repo_tree = QTreeWidget()
        self.repo_tree.setHeaderLabels(["Name"])
        self.repo_tree.setColumnCount(1)
        self.repo_tree.itemSelectionChanged.connect(self.on_selection_changed)
        splitter.addWidget(self.repo_tree)
        
        # Details panel
        self.details_stack = QStackedWidget()
        
        # Meta repo details widget
        self.meta_details = QWidget()
        meta_layout = QFormLayout(self.meta_details)
        self.meta_name = QLineEdit()
        self.meta_url = QLineEdit()
        meta_layout.addRow("Name:", self.meta_name)
        meta_layout.addRow("URL:", self.meta_url)
        
        # Recipe details widget
        self.recipe_details = QWidget()
        recipe_layout = QFormLayout(self.recipe_details)
        self.recipe_id = QLineEdit()
        self.recipe_name = QLineEdit()
        self.recipe_url = QLineEdit()
        recipe_layout.addRow("ID:", self.recipe_id)
        recipe_layout.addRow("Name:", self.recipe_name)
        recipe_layout.addRow("URL:", self.recipe_url)
        
        # Add widgets to stack
        self.details_stack.addWidget(self.meta_details)
        self.details_stack.addWidget(self.recipe_details)
        self.details_stack.addWidget(QWidget())  # Empty widget for no selection
        
        splitter.addWidget(self.details_stack)
        
        layout.addWidget(splitter)
        
        # Apply button for details
        apply_btn = QPushButton("Apply Changes")
        apply_btn.clicked.connect(self.apply_changes)
        layout.addWidget(apply_btn)
        
        # Load initial data
        self.load_repos()
        
    def load_repos(self):
        self.repo_tree.clear()
        
        for meta_repo in self.repo_config.meta_repos:
            meta_item = QTreeWidgetItem([meta_repo.name])
            meta_item.setData(0, Qt.ItemDataRole.UserRole, ("meta", meta_repo))
            
            for recipe in meta_repo.recipes:
                recipe_item = QTreeWidgetItem([recipe.name])
                recipe_item.setData(0, Qt.ItemDataRole.UserRole, ("recipe", recipe))
                meta_item.addChild(recipe_item)
            
            self.repo_tree.addTopLevelItem(meta_item)
            
        self.repo_tree.expandAll()
    
    def on_selection_changed(self):
        items = self.repo_tree.selectedItems()
        if not items:
            self.details_stack.setCurrentIndex(2)  # Show empty widget
            return
            
        item = items[0]
        item_type, data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_type == "meta":
            self.meta_name.setText(data.name)
            self.meta_url.setText(data.url)
            self.details_stack.setCurrentIndex(0)
        elif item_type == "recipe":
            self.recipe_id.setText(data.id)
            self.recipe_name.setText(data.name)
            self.recipe_url.setText(data.url)
            self.details_stack.setCurrentIndex(1)
    
    def apply_changes(self):
        items = self.repo_tree.selectedItems()
        if not items:
            return
            
        item = items[0]
        item_type, data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_type == "meta":
            data.name = self.meta_name.text()
            data.url = self.meta_url.text()
            item.setText(0, data.name)
        elif item_type == "recipe":
            data.id = self.recipe_id.text()
            data.name = self.recipe_name.text()
            data.url = self.recipe_url.text()
            item.setText(0, data.name)
            
        self.repo_config.save_config()
    
    def add_meta_repo(self):
        dialog = AddMetaRepoDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            meta_repo = dialog.get_meta_repo()
            self.repo_config.add_meta_repo(meta_repo.name, meta_repo.url)
            
            # 메타 저장소 클론
            self.workspace.clone_repository(meta_repo.url, "@s6mobis", callback=self.on_clone_complete)
    
    def add_recipe(self):
        items = self.repo_tree.selectedItems()
        if not items:
            QMessageBox.warning(self, "Warning", "Please select a meta repository first")
            return
            
        item = items[0]
        item_type, data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_type != "meta":
            QMessageBox.warning(self, "Warning", "Please select a meta repository")
            return
            
        dialog = AddRecipeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            recipe = dialog.get_recipe()
            data.recipes.append(recipe)
            self.repo_config.save_config()
            
            # 레시피 저장소 클론
            self.workspace.clone_repository(
                recipe.url, 
                "@s6mobis", 
                folder_name=recipe.name,
                callback=self.on_clone_complete
            )
    
    def remove_selected(self):
        items = self.repo_tree.selectedItems()
        if not items:
            return
            
        item = items[0]
        item_type, data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_type == "meta":
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to remove {data.name} and all its recipes?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # 메타 저장소와 관련 레시피들의 워크스페이스 정리
                self.workspace.cleanup_repository(data.name)
                for recipe in data.recipes:
                    self.workspace.cleanup_repository(recipe.name)
                    
                self.repo_config.remove_meta_repo(data.name)
                self.load_repos()
                
        elif item_type == "recipe":
            parent_item = item.parent()
            meta_repo = parent_item.data(0, Qt.ItemDataRole.UserRole)[1]
            
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to remove recipe {data.name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # 레시피 워크스페이스 정리
                self.workspace.cleanup_repository(data.name)
                
                meta_repo.recipes = [r for r in meta_repo.recipes if r.id != data.id]
                self.repo_config.save_config()
                self.load_repos()
                
    def on_clone_complete(self, repo_path):
        """저장소 클론 완료 시 호출되는 콜백"""
        QMessageBox.information(
            self,
            "Success",
            f"Repository cloned successfully to:\n{repo_path}"
        )
        self.load_repos()

class ThemeSettingsTab(QWidget):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.get_available_themes())
        self.theme_combo.setCurrentText(self.theme_manager.get_current_theme())
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        
        form_layout.addRow("Theme:", self.theme_combo)
        layout.addLayout(form_layout)
        layout.addStretch()
        
    def on_theme_changed(self, theme_name):
        self.theme_manager.apply_theme(theme_name)

class AddBranchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Branch")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        form.addRow("Branch Name:", self.name_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_branch(self):
        return BranchConfig(
            name=self.name_input.text()
        )

class BranchSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.branch_manager = BranchManager.get_instance()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QToolBar()
        
        add_action = toolbar.addAction("Add Branch")
        add_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        add_action.triggered.connect(self.add_branch)
        
        remove_action = toolbar.addAction("Remove Branch")
        remove_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        remove_action.triggered.connect(self.remove_branch)
        
        layout.addWidget(toolbar)
        
        # Branch table
        self.branch_table = QTableWidget()
        self.branch_table.setColumnCount(2)
        self.branch_table.setHorizontalHeaderLabels(["Branch Name", "Tags"])
        self.branch_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.branch_table.customContextMenuRequested.connect(self.show_context_menu)
        self.branch_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        header = self.branch_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.branch_table)
        
        # Load initial data
        self.load_branches()
        
    def show_context_menu(self, pos):
        item = self.branch_table.itemAt(pos)
        if not item:
            return
            
        row = self.branch_table.row(item)
        branch = self.branch_manager.branches[row]
        
        menu = QMenu(self)
        
        # 태그 관련 메뉴
        if item.column() == 1:  # Tags column
            add_tag = menu.addAction("Add Tag")
            add_tag.triggered.connect(lambda: self.add_tag(row))
            
            if branch.tags:
                remove_tag = menu.addMenu("Remove Tag")
                for tag in branch.tags:
                    action = remove_tag.addAction(tag)
                    action.triggered.connect(lambda checked, t=tag: self.remove_tag(row, t))
                
                edit_tags = menu.addAction("Edit All Tags")
                edit_tags.triggered.connect(lambda: self.edit_tags(row))
        
        menu.exec(self.branch_table.viewport().mapToGlobal(pos))
    
    def on_item_double_clicked(self, item):
        if item.column() == 1:  # Tags column
            row = self.branch_table.row(item)
            self.edit_tags(row)
    
    def edit_tags(self, row):
        branch = self.branch_manager.branches[row]
        current_tags = ", ".join(branch.tags)
        
        text, ok = QInputDialog.getText(
            self,
            "Edit Tags",
            f"Edit tags for branch {branch.name} (comma separated):",
            text=current_tags
        )
        
        if ok:
            # 콤마로 구분된 태그를 리스트로 변환하고 공백 제거
            new_tags = [tag.strip() for tag in text.split(",") if tag.strip()]
            branch.tags = new_tags
            self.branch_manager.save_config()
            self.load_branches()
    
    def add_tag(self, row):
        branch = self.branch_manager.branches[row]
        
        # 현재 사용 중인 모든 태그 목록 가져오기
        existing_tags = self.branch_manager.get_all_tags()
        
        # 이미 추가된 태그는 제외
        available_tags = [tag for tag in existing_tags if tag not in branch.tags]
        
        if available_tags:
            tag, ok = QInputDialog.getItem(
                self,
                "Add Tag",
                f"Select or enter new tag for branch {branch.name}:",
                available_tags + ["<New Tag>"],
                0,
                True
            )
        else:
            tag, ok = QInputDialog.getText(
                self,
                "Add Tag",
                f"Enter new tag for branch {branch.name}:"
            )
        
        if ok and tag:
            if tag == "<New Tag>":
                new_tag, ok = QInputDialog.getText(
                    self,
                    "New Tag",
                    "Enter new tag name:"
                )
                if ok and new_tag:
                    tag = new_tag
            
            if tag and tag != "<New Tag>" and tag not in branch.tags:
                branch.tags.append(tag)
                self.branch_manager.save_config()
                self.load_branches()
    
    def remove_tag(self, row, tag):
        branch = self.branch_manager.branches[row]
        branch.tags.remove(tag)
        self.branch_manager.save_config()
        self.load_branches()

    def load_branches(self):
        self.branch_table.setRowCount(len(self.branch_manager.branches))
        
        for row, branch in enumerate(self.branch_manager.branches):
            name_item = QTableWidgetItem(branch.name)
            tags_item = QTableWidgetItem(", ".join(branch.tags))
            
            self.branch_table.setItem(row, 0, name_item)
            self.branch_table.setItem(row, 1, tags_item)
            
    def add_branch(self):
        dialog = AddBranchDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            branch = dialog.get_branch()
            self.branch_manager.branches.append(branch)
            self.branch_manager.save_config()
            self.load_branches()
            
    def remove_branch(self):
        current_row = self.branch_table.currentRow()
        if current_row >= 0:
            branch = self.branch_manager.branches[current_row]
            
            if branch.name == "@s6mobis":
                QMessageBox.warning(self, "Warning", "Cannot remove default branch @s6mobis")
                return
                
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to remove branch {branch.name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                del self.branch_manager.branches[current_row]
                self.branch_manager.save_config()
                self.load_branches()

class SettingsDialog(QDialog):
    def __init__(self, theme_manager, config_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.config_manager = config_manager
        self.repo_config = RepoConfig.get_instance()
        self.setWindowTitle("Settings")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Server settings tab
        self.server_tab = ServerSettingsTab(self.config_manager)
        tab_widget.addTab(self.server_tab, "Server")
        
        # Repository settings tab
        self.repo_tab = RepositorySettingsTab(self.repo_config)
        tab_widget.addTab(self.repo_tab, "Repositories")
        
        # Theme settings tab
        self.theme_tab = ThemeSettingsTab(self.theme_manager)
        tab_widget.addTab(self.theme_tab, "Theme")
        
        # Branch settings tab
        self.branch_tab = BranchSettingsTab()
        tab_widget.addTab(self.branch_tab, "Branches")
        
        layout.addWidget(tab_widget)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set dialog size
        self.resize(800, 600)

    def save_settings(self):
        # Save all settings from each tab
        self.server_tab.save_settings()
        self.repo_config.save_config()
        self.accept() 