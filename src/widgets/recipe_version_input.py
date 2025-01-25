from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, 
                           QGridLayout, QComboBox, QDialog, QMessageBox, QApplication)
from PyQt6.QtGui import QFont
from workspace.manager import WorkspaceManager
from utils.logger import setup_logger
from utils.version_utils import generate_next_version
from dialogs.loading_dialog import LoadingDialog
from dialogs.pr_dialog import PRDialog
from PyQt6.QtCore import Qt

logger = setup_logger(__name__)

class RecipeVersionInput(QFrame):
    def __init__(self, meta_name: str, recipe_name: str, parent=None):
        super().__init__(parent)
        self.meta_name = meta_name
        self.recipe_name = recipe_name
        self.workspace = WorkspaceManager.get_instance()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 레시피 정보 헤더
        header = QHBoxLayout()
        recipe_label = QLabel(f"{self.meta_name}/{self.recipe_name}")
        recipe_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        header.addWidget(recipe_label)
        
        # 커밋 수 표시
        self.commit_count_label = QLabel()
        self.commit_count_label.setStyleSheet("color: gray;")
        header.addWidget(self.commit_count_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # 버전 정보 그리드
        info_layout = QGridLayout()
        
        # 현재 버전
        info_layout.addWidget(QLabel("Current Version:"), 0, 0)
        self.current_version = QLabel()
        info_layout.addWidget(self.current_version, 0, 1)
        
        # 최신 태그
        info_layout.addWidget(QLabel("Latest Tag:"), 1, 0)
        self.latest_tag = QLabel()
        info_layout.addWidget(self.latest_tag, 1, 1)
        
        # HEAD 태그
        info_layout.addWidget(QLabel("HEAD Tags:"), 2, 0)
        self.head_tags = QLabel()
        info_layout.addWidget(self.head_tags, 2, 1)
        
        layout.addLayout(info_layout)
        
        # 버전 선택
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("New Version:"))
        self.version_input = QComboBox()
        self.version_input.setEditable(True)
        self.version_input.addItem("HEAD")  # 자동 태깅 옵션
        version_layout.addWidget(self.version_input)
        
        # 브랜치 선택
        branch_layout = QHBoxLayout()
        branch_layout.addWidget(QLabel("Branch:"))
        self.branch_input = QLineEdit()
        self.branch_input.setPlaceholderText("@s6mobis")
        branch_layout.addWidget(self.branch_input)
        
        layout.addLayout(version_layout)
        layout.addLayout(branch_layout)
        
    def update_info(self, branch: str):
        """버전 정보 업데이트"""
        try:
            # 현재 정보 가져오기
            current_info = self.workspace.get_recipe_info(self.meta_name, self.recipe_name, branch)
            current_version = current_info['CCOS_VERSION']
            self.current_version.setText(current_version)
            
            # 저장소 최신 정보
            latest = self.workspace.get_latest_tag(self.recipe_name)
            self.latest_tag.setText(latest)
            
            head_tags = self.workspace.get_head_tags(self.recipe_name)
            self.head_tags.setText(", ".join(head_tags) if head_tags else "None")
            
            # 커밋 수 표시
            commit_count = self.workspace.get_commit_count_between_tags(
                self.recipe_name,
                current_version,
                "HEAD"
            )
            if commit_count > 0:
                self.commit_count_label.setText(f"({commit_count} new commits)")
                self.commit_count_label.setStyleSheet("color: #cf222e;")  # 빨간색으로 표시
                
                # HEAD에 태그가 없으면 자동으로 다음 버전 생성
                if not head_tags:
                    next_version = generate_next_version(current_version)
                    logger.info(f"Generated next version for {self.recipe_name}: {next_version}")
                    
                    # 버전 선택 콤보박스 업데이트
                    self.version_input.clear()
                    self.version_input.addItem(next_version)  # 자동 생성된 버전을 첫 번째로
                    self.version_input.addItem("HEAD")
                    for tag in self.workspace.get_all_version_tags(self.recipe_name):
                        self.version_input.addItem(tag)
                    
                    # 자동 생성된 버전 선택
                    self.version_input.setCurrentText(next_version)
                else:
                    # 기존 동작 유지
                    self.version_input.clear()
                    self.version_input.addItem("HEAD")
                    for tag in self.workspace.get_all_version_tags(self.recipe_name):
                        self.version_input.addItem(tag)
            else:
                self.commit_count_label.setText("(up to date)")
                self.commit_count_label.setStyleSheet("color: #2da44e;")  # 초록색으로 표시
                
                # 변경사항이 없으면 기본 버전 목록만 표시
                self.version_input.clear()
                self.version_input.addItem("HEAD")
                for tag in self.workspace.get_all_version_tags(self.recipe_name):
                    self.version_input.addItem(tag)
                
        except Exception as e:
            logger.error(f"Failed to update version info: {e}")

    def get_values(self) -> tuple:
        """입력된 버전과 브랜치 정보 반환"""
        version = self.version_input.currentText()
        branch = self.branch_input.text() or "@s6mobis"
        return version, branch 

    def has_changes(self) -> bool:
        """변경사항이 있는지 확인"""
        try:
            commit_count = self.workspace.get_commit_count_between_tags(
                self.recipe_name,
                self.current_version.text(),
                "HEAD"
            )
            return commit_count > 0
        except Exception:
            return False 

    def create_pr(self):
        """PR 생성 버튼 클릭 핸들러"""
        try:
            # 로딩 대화상자 표시
            loading = LoadingDialog("Preparing PR dialog...", self)
            loading.show()
            QApplication.processEvents()  # 이벤트 처리하여 로딩 화면이 즉시 표시되도록 함
            
            # PR 대화상자 준비
            try:
                dialog = PRDialog(self.branch_input.text(), self.get_version_info())
                loading.close()
                
                # PR 대화상자 표시
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.update_version_info()
                    
            except Exception as e:
                loading.close()
                QMessageBox.critical(self, "Error", f"Failed to prepare PR dialog: {str(e)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create PR: {str(e)}") 