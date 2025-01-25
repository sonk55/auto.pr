from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, 
                           QLabel, QFrame, QHBoxLayout, QGroupBox,
                           QPushButton, QLineEdit, QToolButton)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon
from widgets.recipe_version_input import RecipeVersionInput
from utils.logger import setup_logger
from typing import List, Dict
from workspace.manager import WorkspaceManager
from dialogs.pr_dialog import PRDialog

logger = setup_logger(__name__)

class CollapsibleBox(QWidget):
    """접을 수 있는 브랜치 그룹 위젯"""
    def __init__(self, title: str, version_page=None, parent=None):
        super().__init__(parent)
        logger.debug(f"Creating CollapsibleBox with title: {title}")
        self.title_text = title
        self.version_page = version_page  # VersionInputPage 참조 저장
        self.is_collapsed = True
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 헤더
        self.header = QFrame()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # 토글 버튼
        self.toggle_button = QToolButton()
        self.toggle_button.setStyleSheet("""
            QToolButton { border: none; }
            QToolButton:hover { background-color: rgba(255, 255, 255, 0.1); }
        """)
        self.toggle_button.setIconSize(QSize(16, 16))
        self.toggle_button.clicked.connect(self.toggle_content)
        header_layout.addWidget(self.toggle_button)
        
        # 타이틀
        self.title_label = QLabel(self.title_text)
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        
        # 상태 표시 (예: 변경된 레시피 수)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.status_label)
        
        # PR 생성 버튼 추가
        self.create_pr_btn = QPushButton("Create PR")
        self.create_pr_btn.setEnabled(False)  # 기본적으로 비활성화
        self.create_pr_btn.clicked.connect(self.show_pr_dialog)
        header_layout.addWidget(self.create_pr_btn)
        
        header_layout.addStretch()
        
        layout.addWidget(self.header)
        
        # 컨텐츠
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 0, 0, 0)
        layout.addWidget(self.content)
        
        # 초기 상태 설정
        self.toggle_content()
        
    def toggle_content(self):
        self.is_collapsed = not self.is_collapsed
        visible = not self.is_collapsed
        logger.debug(f"Toggling {self.title_text}: {'expanded' if visible else 'collapsed'}")
        self.content.setVisible(visible)
        self.toggle_button.setText("▼" if visible else "▶")
        
    def add_widget(self, widget):
        self.content_layout.addWidget(widget)
        
    def update_status(self, text: str):
        self.status_label.setText(text)
        
    def enable_pr_button(self, enable: bool):
        """PR 버튼 활성화/비활성화"""
        logger.debug(f"Setting PR button enabled={enable} for {self.title_text}")
        self.create_pr_btn.setEnabled(enable)
        
    def show_pr_dialog(self):
        branch = self.title_text.split(": ")[1]
        logger.debug(f"Opening PR dialog for branch: {branch}")
        
        # 현재 브랜치의 버전 정보 수집
        version_info = {}
        if self.version_page:  # version_page가 있는 경우에만
            for (b, meta_name, recipe_name), input_widget in self.version_page.recipe_inputs.items():
                if b == branch:
                    version_info[(meta_name, recipe_name)] = input_widget.get_values()
            logger.debug(f"Collected version info for {branch}: {version_info}")
        else:
            logger.error("version_page is not set")
            
        dialog = PRDialog(branch, version_info, self)
        dialog.exec()

class VersionInputPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recipe_inputs = {}
        self.branch_boxes = {}  # 브랜치별 CollapsibleBox
        self.workspace = WorkspaceManager.get_instance()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 타이틀과 필터
        header_layout = QHBoxLayout()
        
        title = QLabel("Step 2: Enter Version Information")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        # 브랜치 필터
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter branches...")
        self.filter_input.textChanged.connect(self.filter_branches)
        self.filter_input.setMaximumWidth(200)
        header_layout.addWidget(self.filter_input)
        
        # 모두 펼치기/접기 버튼
        self.expand_all_btn = QPushButton("Expand All")
        self.expand_all_btn.clicked.connect(lambda: self.toggle_all_branches(False))
        self.expand_all_btn.setMaximumWidth(100)
        header_layout.addWidget(self.expand_all_btn)
        
        self.collapse_all_btn = QPushButton("Collapse All")
        self.collapse_all_btn.clicked.connect(lambda: self.toggle_all_branches(True))
        self.collapse_all_btn.setMaximumWidth(100)
        header_layout.addWidget(self.collapse_all_btn)
        
        layout.addLayout(header_layout)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 버전 입력 컨테이너
        self.version_container = QWidget()
        self.version_layout = QVBoxLayout(self.version_container)
        scroll.setWidget(self.version_container)
        
        layout.addWidget(scroll)
        
    def update_recipes(self, recipes: List[tuple], branches: List[str]):
        """레시피와 브랜치 정보 업데이트"""
        try:
            logger.debug(f"Updating recipes: {recipes} for branches: {branches}")
            
            # 기존 입력 위젯 제거
            while self.version_layout.count():
                item = self.version_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
            # 브랜치별 그룹 생성
            self.recipe_inputs = {}
            self.branch_boxes = {}
            
            for branch in branches:
                logger.debug(f"Processing branch: {branch}")
                # 메타 저장소 체크아웃
                for meta_name, _ in recipes:
                    try:
                        logger.debug(f"Checking out {meta_name} to {branch}")
                        self.workspace.checkout_branch(meta_name, branch)
                    except Exception as e:
                        logger.warning(f"Failed to checkout {meta_name} to {branch}: {e}")
                
                # 접을 수 있는 브랜치 그룹 생성 - self 전달
                box = CollapsibleBox(f"Branch: {branch}", version_page=self)
                self.branch_boxes[branch] = box
                
                # 각 레시피에 대한 입력 위젯 생성
                changed_recipes = 0
                for meta_name, recipe_name in recipes:
                    logger.debug(f"Creating input widget for {meta_name}/{recipe_name}")
                    input_widget = RecipeVersionInput(meta_name, recipe_name)
                    input_widget.update_info(branch)
                    
                    # 변경사항이 있는 경우 카운트
                    if input_widget.has_changes():
                        logger.debug(f"Changes detected in {recipe_name}")
                        changed_recipes += 1
                        box.is_collapsed = False  # 변경사항이 있는 브랜치는 자동으로 펼침
                    
                    self.recipe_inputs[(branch, meta_name, recipe_name)] = input_widget
                    box.add_widget(input_widget)
                
                # 상태 업데이트
                status_text = f"({changed_recipes} changes)" if changed_recipes > 0 else "(no changes)"
                logger.debug(f"Branch {branch} status: {status_text}")
                box.update_status(status_text)
                box.toggle_content()  # 초기 상태 적용
                
                # 변경사항이 있는 경우 PR 버튼 활성화
                if changed_recipes > 0:
                    logger.debug(f"Enabling PR button for {branch}")
                    box.enable_pr_button(True)
                    box.is_collapsed = False
                
                self.version_layout.addWidget(box)
            
            self.version_layout.addStretch()
            
        except Exception as e:
            logger.error(f"Failed to update recipes: {e}")
            
    def filter_branches(self, text: str):
        """브랜치 필터링"""
        text = text.lower()
        logger.debug(f"Filtering branches with text: {text}")
        for branch, box in self.branch_boxes.items():
            visible = text in branch.lower()
            logger.debug(f"Branch {branch} visibility: {visible}")
            box.setVisible(visible)
            
    def toggle_all_branches(self, collapse: bool):
        """모든 브랜치 그룹 펼치기/접기"""
        logger.debug(f"Toggling all branches: {'collapse' if collapse else 'expand'}")
        for box in self.branch_boxes.values():
            box.is_collapsed = collapse
            box.toggle_content()
        
    def validate(self) -> bool:
        """모든 필수 입력이 완료되었는지 확인"""
        valid = True
        for (branch, meta_name, recipe_name), input_widget in self.recipe_inputs.items():
            version, _ = input_widget.get_values()
            if not version:
                logger.warning(f"Missing version for {meta_name}/{recipe_name} in {branch}")
                valid = False
        logger.debug(f"Version input validation result: {valid}")
        return valid
        
    def get_version_info(self) -> Dict[str, Dict[tuple, tuple]]:
        """입력된 버전 정보를 반환"""
        info = {}
        for (branch, meta_name, recipe_name), input_widget in self.recipe_inputs.items():
            if branch not in info:
                info[branch] = {}
            values = input_widget.get_values()
            info[branch][(meta_name, recipe_name)] = values
            logger.debug(f"Version info for {meta_name}/{recipe_name} in {branch}: {values}")
        return info 