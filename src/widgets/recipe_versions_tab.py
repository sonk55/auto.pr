from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, 
                           QTableWidgetItem, QHeaderView, QComboBox,
                           QHBoxLayout, QLabel, QPushButton, QProgressBar,
                           QFrame, QStyle)
from PyQt6.QtCore import Qt, pyqtSignal, QEventLoop
from PyQt6.QtGui import QColor, QFont, QIcon
from config.repo_config import RepoConfig
from config.branch_config import BranchManager
from workspace.manager import WorkspaceManager
import concurrent.futures
from utils.logger import setup_logger

logger = setup_logger(__name__)

class RecipeVersionsTab(QWidget):
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo_config = RepoConfig.get_instance()
        self.branch_manager = BranchManager.get_instance()
        self.workspace = WorkspaceManager.get_instance()
        logger.debug("Initializing RecipeVersionsTab")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 상단 컨트롤 패널
        control_panel = QFrame()
        control_panel.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        control_layout = QHBoxLayout(control_panel)
        
        # 브랜치 선택 영역
        branch_layout = QHBoxLayout()
        branch_label = QLabel("Branch:")
        branch_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        branch_layout.addWidget(branch_label)
        
        self.branch_combo = QComboBox()
        self.branch_combo.setMinimumWidth(200)
        self.branch_combo.currentTextChanged.connect(self.on_branch_changed)
        branch_layout.addWidget(self.branch_combo)
        
        control_layout.addLayout(branch_layout)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        refresh_btn.clicked.connect(self.refresh_versions)
        control_layout.addWidget(refresh_btn)
        
        # 진행 상태 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.hide()
        control_layout.addWidget(self.progress_bar)
        
        control_layout.addStretch()
        layout.addWidget(control_panel)
        
        # 버전 정보 테이블
        self.version_table = QTableWidget()
        self.version_table.setColumnCount(3)
        self.version_table.setHorizontalHeaderLabels([
            "Recipe", "Version", "Branch"
        ])
        self.version_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.version_table.setSortingEnabled(True)
        self.version_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 읽기 전용
        
        # 테이블 스타일 설정
        header = self.version_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)
        
        layout.addWidget(self.version_table)
        
        # 초기 데이터 로드
        self.load_branches()
        
    def load_branches(self):
        """브랜치 콤보박스 업데이트"""
        self.branch_combo.clear()
        for branch in self.branch_manager.branches:
            self.branch_combo.addItem(branch.name)
            
    def on_branch_changed(self, branch_name):
        """브랜치 선택 시 버전 정보 업데이트"""
        self.load_versions(branch_name)
        
    def wait_for_checkout(self, repo_name: str, branch_name: str) -> bool:
        """체크아웃이 완료될 때까지 대기"""
        loop = QEventLoop()
        success = True
        
        def on_finished(finished_repo, finished_branch):
            if finished_repo == repo_name and finished_branch == branch_name:
                loop.quit()
                
        def on_error(error_msg):
            nonlocal success
            success = False
            print(f"Checkout error: {error_msg}")
            loop.quit()
            
        # 시그널 연결
        self.workspace.checkout_finished.connect(on_finished)
        self.workspace.operation_error.connect(on_error)
        
        # 체크아웃 시작
        self.workspace.checkout_branch(repo_name, branch_name)
        
        # 완료될 때까지 대기
        loop.exec()
        
        # 시그널 연결 해제
        self.workspace.checkout_finished.disconnect(on_finished)
        self.workspace.operation_error.disconnect(on_error)
        
        return success
        
    def update_progress(self, value, max_value):
        """진행 상태 업데이트"""
        self.progress_bar.setMaximum(max_value)
        self.progress_bar.setValue(value)
        
    def load_versions(self, branch_name):
        """선택된 브랜치의 레시피 버전 정보 로드"""
        logger.info("Loading recipe versions")
        self.version_table.setRowCount(0)
        self.progress_bar.show()
        
        try:
            # 메타 저장소 체크아웃 (병렬 처리)
            total_repos = len(self.repo_config.meta_repos)
            self.update_progress(0, total_repos)
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for meta_repo in self.repo_config.meta_repos:
                    future = executor.submit(
                        self.wait_for_checkout,
                        meta_repo.name,
                        branch_name
                    )
                    futures.append((meta_repo, future))
                
                # 체크아웃 완료 대기 및 결과 처리
                for idx, (meta_repo, future) in enumerate(futures):
                    try:
                        if future.result():
                            self.load_meta_repo_recipes(meta_repo, branch_name)
                    except Exception as e:
                        print(f"Error processing {meta_repo.name}: {e}")
                    finally:
                        self.update_progress(idx + 1, total_repos)
                        
        finally:
            self.progress_bar.hide()
            self.version_table.sortItems(0)  # Recipe 이름으로 정렬
            
    def load_meta_repo_recipes(self, meta_repo, branch_name):
        """메타 저장소의 레시피 정보 로드"""
        for recipe in meta_repo.recipes:
            row = self.version_table.rowCount()
            self.version_table.insertRow(row)
            
            # 레시피 이름
            name_item = QTableWidgetItem(recipe.name)
            name_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.version_table.setItem(row, 0, name_item)
            
            try:
                # BB 파일에서 정보 읽기
                recipe_info = self.workspace.get_recipe_info(
                    meta_repo.name,
                    recipe.name,
                    branch_name
                )
                
                # 버전 정보
                version_item = QTableWidgetItem(recipe_info['CCOS_VERSION'])
                version_item.setForeground(QColor("#2ecc71"))
                self.version_table.setItem(row, 1, version_item)
                
                # 브랜치 정보
                branch_item = QTableWidgetItem(recipe_info['CCOS_GIT_BRANCH_NAME'])
                if recipe_info['CCOS_GIT_BRANCH_NAME'] != "@s6mobis":
                    branch_item.setForeground(QColor("#e74c3c"))
                self.version_table.setItem(row, 2, branch_item)
                
            except Exception as e:
                # 실패한 레시피도 표시하되 에러 표시
                self.version_table.insertRow(row)
                
                # 레시피 이름
                name_item = QTableWidgetItem(f"    ⚙️ {recipe.name}")
                self.version_table.setItem(row, 0, name_item)
                
                # 에러 메시지
                error_item = QTableWidgetItem("Failed to load")
                error_item.setToolTip(str(e))
                error_item.setForeground(QColor("#ff0000"))  # 빨간색으로 표시
                self.version_table.setItem(row, 1, error_item)
                
                # 빈 브랜치 칸
                self.version_table.setItem(row, 2, QTableWidgetItem(""))
                
                row += 1
                logger.error(f"Failed to load version info for {recipe.name}: {e}")
        
        logger.info("Finished loading recipe versions")
        
    def refresh_versions(self):
        """현재 선택된 브랜치의 버전 정보 새로고침"""
        current_branch = self.branch_combo.currentText()
        if current_branch:
            self.load_versions(current_branch)
            self.refresh_requested.emit() 