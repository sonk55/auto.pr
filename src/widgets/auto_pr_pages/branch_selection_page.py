from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, 
                           QLabel, QListWidgetItem, QGroupBox, QHBoxLayout, QComboBox, QLineEdit)
from PyQt6.QtGui import QFont
from config.branch_config import BranchManager

class BranchSelectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.branch_manager = BranchManager.get_instance()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 타이틀
        title = QLabel("Step 3: Select Target Branches")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 브랜치 선택 모드
        mode_group = QGroupBox("Selection Mode")
        mode_layout = QHBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Manual", "All", "Filter"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(QLabel("Mode:"))
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # 필터 입력 (기본적으로 숨김)
        self.filter_group = QGroupBox("Filter")
        filter_layout = QVBoxLayout()
        
        # 사용 가능한 태그 표시
        tags_label = QLabel("Available tags:")
        tags_label.setStyleSheet("color: gray;")
        filter_layout.addWidget(tags_label)
        
        self.tags_list = QLabel()
        self.tags_list.setWordWrap(True)
        self.tags_list.setText(", ".join(self.branch_manager.get_all_tags()))
        filter_layout.addWidget(self.tags_list)
        
        # 필터 입력
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Enter filter (e.g. (KOR|GENIE)&STEP30)")
        self.filter_input.textChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_input)
        
        self.filter_group.setLayout(filter_layout)
        self.filter_group.hide()
        layout.addWidget(self.filter_group)
        
        # 브랜치 목록
        self.branch_list = QListWidget()
        self.branch_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.branch_list.setStyleSheet("""
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
        
        # 초기 브랜치 목록 로드
        self.load_branches()
        
    def on_mode_changed(self, mode):
        if mode == "Filter":
            self.filter_group.show()
        else:
            self.filter_group.hide()
            
        if mode == "All":
            # 모든 브랜치 선택
            for i in range(self.branch_list.count()):
                self.branch_list.item(i).setSelected(True)
        elif mode == "Manual":
            # 선택 해제
            self.branch_list.clearSelection()
            
    def on_filter_changed(self, filter_text):
        if not filter_text:
            return
            
        # 필터 조건에 맞는 브랜치 선택
        filtered_branches = self.branch_manager.get_branches_by_condition(filter_text)
        
        for i in range(self.branch_list.count()):
            item = self.branch_list.item(i)
            item.setSelected(item.text() in filtered_branches)
        
    def load_branches(self):
        # 브랜치 목록 로드
        for branch in self.branch_manager.branches:
            self.branch_list.addItem(branch.name)
        
    def validate(self) -> bool:
        """브랜치가 선택되었는지 확인"""
        return len(self.get_selected_branches()) > 0
        
    def get_selected_branches(self) -> list:
        """선택된 브랜치 목록 반환"""
        return [item.text() for item in self.branch_list.selectedItems()] 