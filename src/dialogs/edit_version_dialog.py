from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QTableWidget,
                           QTableWidgetItem, QHeaderView, QLineEdit,
                           QFormLayout, QGroupBox, QMessageBox, QWidget)
from PyQt6.QtCore import Qt, QTimer
from workspace.manager import WorkspaceManager

class EditVersionDialog(QDialog):
    def __init__(self, diff_info, pr_data, parent=None):
        super().__init__(parent)
        self.diff_info = diff_info
        self.pr_data = pr_data
        self.original_values = {}  # 원본 값 저장
        self.setWindowTitle("Edit PR Details")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Branch info group
        branch_group = QGroupBox("Branch Information")
        branch_layout = QFormLayout()
        
        # Source branch
        self.source_branch = QLineEdit(self.pr_data['source']['branch']['name'])
        branch_layout.addRow("Source Branch:", self.source_branch)
        
        # Target branch
        self.target_branch = QLineEdit(self.pr_data['destination']['branch']['name'])
        self.target_branch.setReadOnly(True)
        branch_layout.addRow("Target Branch:", self.target_branch)
        
        branch_group.setLayout(branch_layout)
        layout.addWidget(branch_group)
        
        # Version info group
        version_group = QGroupBox("Version Information")
        version_layout = QVBoxLayout()
        
        # Loading indicator
        self.loading_label = QLabel("Loading versions...")
        layout.addWidget(self.loading_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "File", "Version", "Branch Name"
        ])
        
        # Load versions asynchronously
        self.load_versions()
        
        # Set table properties
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        version_layout.addWidget(self.table)
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)
        
        # Progress overlay
        self.progress_overlay = QWidget(self)
        self.progress_overlay.setObjectName("ProgressOverlay")  # 테마 스타일 적용
        overlay_layout = QVBoxLayout(self.progress_overlay)
        self.progress_label = QLabel("Updating files...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(self.progress_label)
        self.progress_overlay.hide()
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.resize(600, 400)
    
    def showEvent(self, event):
        super().showEvent(event)
        # Overlay를 dialog 크기에 맞춤
        self.progress_overlay.resize(self.size())
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Overlay를 dialog 크기에 맞춤
        self.progress_overlay.resize(self.size())
    
    def show_progress(self, message):
        self.progress_label.setText(message)
        self.progress_overlay.show()
        
    def hide_progress(self):
        self.progress_overlay.hide()
    
    def show_result(self, success, message):
        self.hide_progress()
        if success:
            QMessageBox.information(self, "Success", message)
            super().accept()  # 다이얼로그를 닫습니다
        else:
            QMessageBox.critical(self, "Error", message)
    
    def has_changes(self):
        """변경사항이 있는지 확인합니다."""
        # 브랜치 변경 확인
        if self.source_branch.text() != self.pr_data['source']['branch']['name']:
            return True
            
        # 버전/브랜치 변경 확인
        for row in range(self.table.rowCount()):
            current_version = self.table.item(row, 1).text()
            current_branch = self.table.item(row, 2).text()
            original = self.original_values[row]
            
            if (current_version != original['version'] or 
                current_branch != original['branch']):
                return True
                
        return False

    def accept(self):
        if not self.has_changes():
            super().accept()  # 변경사항이 없으면 바로 닫기
            return
            
        # Confirmation message for changes
        msg = "The following items will be changed:\n\n"
        
        # 브랜치 변경 확인
        if self.source_branch.text() != self.pr_data['source']['branch']['name']:
            msg += f"Branch: {self.pr_data['source']['branch']['name']} → {self.source_branch.text()}\n\n"
        
        # 파일 변경 확인
        for row in range(self.table.rowCount()):
            current_version = self.table.item(row, 1).text()
            current_branch = self.table.item(row, 2).text()
            original = self.original_values[row]
            file_name = self.table.item(row, 0).text()
            
            if (current_version != original['version'] or 
                current_branch != original['branch']):
                msg += f"File: {file_name}\n"
                if current_version != original['version']:
                    msg += f"  Version: {original['version']} → {current_version}\n"
                if current_branch != original['branch']:
                    msg += f"  Branch: {original['branch']} → {current_branch}\n"
                msg += "\n"
        
        msg += "Are you sure you want to save these changes?"
        
        reply = QMessageBox.question(
            self,
            "Confirm Changes",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            workspace = WorkspaceManager.get_instance()
            repo_name = self.pr_data['source']['repository']['name']
            updated_versions = self.get_updated_versions()
            updated_branch = self.get_updated_branch()
            source_branch = self.pr_data['source']['branch']['name']
            
            self.show_progress("Updating files...")
            
            def on_checkout_complete(repo_path):
                try:
                    # BB 파일 업데이트 (변경된 항목만)
                    for version_info in updated_versions:
                        file_name = version_info['file'].split('/')[-1]
                        recipe_name = file_name.split('.')[0]
                        version = version_info['version']
                        
                        tags = workspace.get_tag_hash_by_branch(recipe_name, version_info['branch'])
                        
                        if version not in tags:
                            raise Exception(f"{version} not found in tags")
                        else:
                            version_info['tag'] = tags[version]
                            
                        workspace.update_bb_file(repo_name, file_name, version_info)
                    
                    if updated_versions:  # 변경된 파일이 있을 때만 커밋
                        # 변경사항 commit
                        commit_message = "Update CCOS version and branch\n\n"
                        for version_info in updated_versions:
                            file_name = version_info['file'].split('/')[-1]
                            commit_message += f"- {file_name}:\n"
                            commit_message += f"  - Version: {version_info['version']}\n"
                            commit_message += f"  - Branch: {version_info['branch']}\n"
                        
                        workspace.update_changes(repo_name, commit_message)
                    
                    self.show_result(True, "Files updated and committed successfully!")
                    
                except Exception as e:
                    self.show_result(False, f"Failed to update files: {str(e)}")
            
            def on_error(error_msg):
                self.show_result(False, f"Failed to checkout branch: {error_msg}")
            
            # 브랜치 변경이 있는 경우에만 비동기 처리
            if updated_branch != source_branch:
                workspace.operation_error.connect(on_error)
                workspace.checkout_branch(repo_name, updated_branch, callback=on_checkout_complete)
            else:
                on_checkout_complete(workspace.active_repositories[repo_name])
    
    def load_versions(self):
        workspace = WorkspaceManager.get_instance()
        
        def on_checkout_complete(repo_path):
            self.loading_label.hide()
            self.fill_table()
            
        def on_error(error_msg):
            self.loading_label.setText(f"Error: {error_msg}")
            
        workspace.operation_error.connect(on_error)
        workspace.checkout_branch(
            self.pr_data['source']['repository']['name'],
            self.source_branch.text(),
            callback=on_checkout_complete
        )
    
    def fill_table(self):
        # Fill table with version information
        self.table.setRowCount(len(self.diff_info))
        for row, info in enumerate(self.diff_info):
            file_path = info['file']
            # File name
            file_item = QTableWidgetItem(file_path.split('/')[-1])
            file_item.setFlags(file_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, file_item)
            
            workspace = WorkspaceManager.get_instance()
            recipe_info = workspace.get_recipe_info(
                self.pr_data['source']['repository']['name'], 
                file_path.split('/')[-1].split('.')[0],
                self.source_branch.text()
            )
            
            # Version (editable)
            version = QTableWidgetItem(recipe_info['CCOS_VERSION'])
            self.table.setItem(row, 1, version)
            
            # Branch name (editable)
            branch_name = recipe_info['CCOS_GIT_BRANCH_NAME'] or '@s6mobis'
            branch_item = QTableWidgetItem(branch_name)
            self.table.setItem(row, 2, branch_item)
            
            self.original_values[row] = {
                'file': file_path,
                'version': recipe_info['CCOS_VERSION'],
                'branch': recipe_info['CCOS_GIT_BRANCH_NAME'] or '@s6mobis'
            }
    
    def get_updated_versions(self):
        """변경된 항목만 반환"""
        updated_info = []
        for row in range(self.table.rowCount()):
            current_version = self.table.item(row, 1).text()
            current_branch = self.table.item(row, 2).text()
            original = self.original_values[row]
            
            # 버전이나 브랜치가 변경된 경우만 포함
            if (current_version != original['version'] or 
                current_branch != original['branch']):
                updated_info.append({
                    'file': self.diff_info[row]['file'],
                    'version': current_version,
                    'branch': current_branch,
                    'commit': self.diff_info[row]['commit'],
                })
        return updated_info
    
    def get_updated_branch(self):
        """Return the updated branch information"""
        return self.source_branch.text() 