from PyQt6.QtCore import QObject, pyqtSignal, QThread
import os
import shutil
from git import git
import re
from typing import List
from utils.logger import setup_logger  # 절대 경로 사용

logger = setup_logger(__name__)

class GitWorker(QThread):
    finished = pyqtSignal(object)  # 결과를 전달
    error = pyqtSignal(Exception)  # 에러를 전달
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)

class WorkspaceManager(QObject):
    clone_finished = pyqtSignal(str)  # repo_path
    checkout_finished = pyqtSignal(str, str)  # repo_name, branch_name
    operation_error = pyqtSignal(str)  # error message
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if WorkspaceManager._instance is not None:
            raise RuntimeError("WorkspaceManager is a singleton. Use get_instance() instead")
        super().__init__()    
        self.workspace_dir = os.path.expanduser("~/.auto-pr/workspace")
        os.makedirs(self.workspace_dir, exist_ok=True)
        WorkspaceManager._instance = self
        self.active_repositories = {}
        self.workers = []  # Keep track of workers to prevent garbage collection
    
    def _clone_repository_sync(self, repo_url, branch_name, folder_name=None):
        """동기 방식의 저장소 클론 (내부 사용)"""
        if folder_name:
            repo_name = folder_name
        else:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            
        repo_path = os.path.join(self.workspace_dir, repo_name)
        
        try:
            if repo_name in self.active_repositories:
                repo_path = self.active_repositories[repo_name]
                if os.path.exists(repo_path):
                    git.git_checkout(repo_path, branch_name)
                    git.git_pull(repo_path)
                    return repo_path
            
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
            
            # 상위 디렉토리에 클론
            git.git_clone(repo_url, branch_name, self.workspace_dir, folder_name)
            self.active_repositories[repo_name] = repo_path
            return repo_path
            
        except Exception as e:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
            if repo_name in self.active_repositories:
                del self.active_repositories[repo_name]
            raise
    
    def clone_repository(self, repo_url, branch_name, folder_name=None, callback=None):
        """비동기 방식의 저장소 클론"""
        worker = GitWorker(self._clone_repository_sync, repo_url, branch_name, folder_name)
        
        def on_finished(repo_path):
            self.clone_finished.emit(repo_path)
            if callback:
                callback(repo_path)
            self.workers.remove(worker)
            
        def on_error(e):
            self.operation_error.emit(str(e))
            self.workers.remove(worker)
        
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        self.workers.append(worker)
        worker.start()
    
    def _checkout_branch_sync(self, repo_name, branch_name):
        """동기 방식의 브랜치 체크아웃 (내부 사용)"""
        repo_path = self.active_repositories[repo_name]
        current_branch = git.git_current_branch(repo_path)
        
        if current_branch != branch_name:
            git.git_checkout(repo_path, branch_name)
        git.git_pull(repo_path)
        return repo_path
    
    def checkout_branch(self, repo_name, branch_name, callback=None):
        """비동기 방식의 브랜치 체크아웃"""
        print(repo_name, branch_name)
        worker = GitWorker(self._checkout_branch_sync, repo_name, branch_name)
        
        def on_finished(repo_path):
            self.checkout_finished.emit(repo_name, branch_name)
            if callback:
                callback(repo_path)
            self.workers.remove(worker)
            
        def on_error(e):
            self.operation_error.emit(str(e))
            self.workers.remove(worker)
        
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        self.workers.append(worker)
        worker.start()
    
    def find_bb_file(self, meta_name: str, recipe_name: str) -> str:
        """BB 파일 경로를 찾습니다."""
        # 폴더가 있다면 더 타고 들어가서 찾기
        meta_path = os.path.join(self.workspace_dir, meta_name)
        if os.path.exists(meta_path):
            for root, dirs, files in os.walk(meta_path):
                if f'{recipe_name}.bb' in files:
                    return os.path.join(root, f"{recipe_name}.bb")
    
    def get_recipe_info(self, meta_name: str, recipe_name: str, branch_name: str) -> dict:
        """레시피의 BB 파일에서 버전 정보를 읽어옵니다."""
        try:
            # BB 파일 경로 구성
            bb_path = self.find_bb_file(meta_name, recipe_name)
            
            if not os.path.exists(bb_path):
                raise FileNotFoundError(f"BB file not found: {bb_path}")
            elif bb_path == None:
                raise FileNotFoundError(f"BB file not found: {bb_path}")
            
            # BB 파일 읽기
            version = None
            git_branch = "@s6mobis"  # 기본값 설정
            
            with open(bb_path, 'r') as f:
                for line in f:
                    print(line)
                    line = line.strip()
                    if line.startswith('CCOS_VERSION'):
                        # "0.0.1_abcd1234" -> "version/0.0.1" 형식으로 변환
                        value = line.split('=')[1].strip().strip('"')
                        version = f"version/{value.split('_')[0]}"
                    elif line.startswith('CCOS_GIT_BRANCH_NAME'):
                        git_branch = line.split('=')[1].strip().strip('"')
                    
                    if version:  # version만 찾으면 break (git_branch는 기본값 있음)
                        break
            
            if not version:
                raise ValueError(f"CCOS_VERSION not found in BB file: {bb_path}")
            
            return {
                'CCOS_VERSION': version,
                'CCOS_GIT_BRANCH_NAME': git_branch
            }
            
        except Exception as e:
            print(f"Error reading BB file for {bb_path}: {e}")
            return {
                'CCOS_VERSION': 'N/A',
                'CCOS_GIT_BRANCH_NAME': '@s6mobis'  # 에러 시에도 기본값 반환
            }
        
    def update_bb_file(self, repo_name, file_name, version_info):
        """BB 파일을 업데이트합니다."""
        repo_path = self.active_repositories[repo_name]
        
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository not found: {repo_path}")
            
        # 파일 찾기
        file_path = None
        for root, dirs, files in os.walk(repo_path):
            if file_name in files:
                file_path = os.path.join(root, file_name)
                break
                
        if not file_path:
            raise FileNotFoundError(f"File not found: {file_name}")
        
        # BB 파일 업데이트
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        found_version = False
        found_branch = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            # CCOS_VERSION 또는 CCOS_VERSION = 형태 모두 처리
            if line.replace(" ", "").startswith('CCOS_VERSION='):
                # = 위치 찾기
                eq_pos = line.find('=')
                prefix = line[:eq_pos+1]  # 기존의 CCOS_VERSION= 형식 유지
                version = f'{version_info["version"].replace("version/", "")}_{version_info["tag"]}'
                lines[i] = f'{prefix}"{version}"\n'
                found_version = True
            # CCOS_GIT_BRANCH_NAME 또는 CCOS_GIT_BRANCH_NAME = 형태 모두 처리
            elif line.replace(" ", "").startswith('CCOS_GIT_BRANCH_NAME='):
                eq_pos = line.find('=')
                prefix = line[:eq_pos+1]  # 기존의 CCOS_GIT_BRANCH_NAME= 형식 유지
                lines[i] = f'{prefix}"{version_info["branch"]}"\n'
                found_branch = True
                
        # branch가 @s6mobis가 아니고 CCOS_GIT_BRANCH_NAME이 없으면 추가
        if version_info["branch"] != "@s6mobis" and not found_branch:
            lines.append(f'CCOS_GIT_BRANCH_NAME="{version_info["branch"]}"\n')
        
        with open(file_path, 'w') as f:
            f.writelines(lines)
            
    def cleanup_repository(self, repo_name):
        """특정 저장소 정리"""
        if repo_name in self.active_repositories:
            repo_path = self.active_repositories[repo_name]
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
            del self.active_repositories[repo_name]
    
    def cleanup_all(self):
        """모든 저장소 정리"""
        for repo_path in self.active_repositories.values():
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
        self.active_repositories.clear()

    def update_changes(self, repo_name, commit_message):
        """변경사항을 커밋하고 push합니다."""
        repo_path = self.active_repositories[repo_name]
        
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository not found: {repo_path}")
            
        try:
            # 현재 브랜치 확인
            current_branch = git.git_current_branch(repo_path)
            
            # 변경된 파일들을 스테이징
            git.git_add_all(repo_path)
            
            # 커밋 수행
            git.git_commit(repo_path, commit_message)
            
            # push 수행
            git.git_push(repo_path, current_branch)
            
        except Exception as e:
            raise Exception(f"Failed to commit and push changes: {str(e)}")
        
    def get_tag_hash_by_branch(self, repo_name, branch_name):
        """브랜치 해시를 반환합니다."""
        repo_path = self.active_repositories[repo_name]
        return git.get_tag_hash_by_branch(repo_path, branch_name)

    def get_commit_messages_between_tags(self, repo_name: str, tag1: str, tag2: str) -> List[str]:
        """두 태그 사이의 커밋 메시지를 가져옵니다."""
        repo_path = self.active_repositories.get(repo_name)
        if not repo_path:
            raise Exception(f"Repository {repo_name} not found")
            
        return git.get_commit_messages_between_tags(repo_path, tag1, tag2)
    
    def get_jira_numbers_between_tags(self, repo_name: str, tag1: str, tag2: str) -> List[str]:
        """두 태그 사이의 JIRA 번호를 가져옵니다."""
        repo_path = self.active_repositories.get(repo_name)
        if not repo_path:
            raise Exception(f"Repository {repo_name} not found")
            
        return git.get_jira_numbers_between_tags(repo_path, tag1, tag2)
        
    def parse_commit_message(self, commit_message: str) -> dict:
        """커밋 메시지를 파싱합니다."""
        try:
            result = {}
            
            # 첫 줄을 title로 사용
            lines = commit_message.strip().split('\n')
            if lines:
                result['title'] = lines[0].strip()
            
            # JIRA 티켓 추출
            jira_matches = re.findall(r'(?:[A-Z][A-Z0-9]*-\d+)', commit_message)
            if jira_matches:
                result['jira'] = ' '.join(jira_matches)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse commit message: {e}")
            return {}

    def get_latest_tag(self, repo_name: str) -> str:
        """저장소의 최신 태그를 반환합니다."""
        repo_path = self.active_repositories.get(repo_name)
        if not repo_path:
            raise Exception(f"Repository {repo_name} not found")
            
        return git.get_latest_tag(repo_path)
        
    def get_head_tags(self, repo_name: str) -> List[str]:
        """HEAD에 있는 태그들을 반환합니다."""
        repo_path = self.active_repositories.get(repo_name)
        if not repo_path:
            raise Exception(f"Repository {repo_name} not found")
            
        return git.get_head_tags(repo_path)
        
    def get_all_version_tags(self, repo_name: str) -> List[str]:
        """저장소의 모든 버전 태그를 반환합니다."""
        repo_path = self.active_repositories.get(repo_name)
        if not repo_path:
            raise Exception(f"Repository {repo_name} not found")
            
        return git.get_all_version_tags(repo_path)
        
    def get_commit_count_between_tags(self, repo_name: str, tag1: str, tag2: str) -> int:
        """두 태그 사이의 커밋 수를 반환합니다."""
        repo_path = self.active_repositories.get(repo_name)
        if not repo_path:
            raise Exception(f"Repository {repo_name} not found")
            
        return git.get_commit_count_between_tags(repo_path, tag1, tag2)

    def get_modified_repositories(self) -> List[str]:
        """변경사항이 있는 저장소 목록을 반환합니다."""
        modified_repos = []
        for repo_name, repo_path in self.active_repositories.items():
            try:
                # git status 실행
                status = git.git_status(repo_path)
                # 변경사항이 있으면 목록에 추가
                if "nothing to commit" not in status:
                    modified_repos.append(repo_name)
            except Exception as e:
                logger.error(f"Failed to get status for {repo_name}: {e}")
        return modified_repos

    def get_diff(self, repo_name: str) -> str:
        """저장소의 변경사항을 반환합니다."""
        repo_path = self.active_repositories.get(repo_name)
        if not repo_path:
            raise Exception(f"Repository {repo_name} not found")
        
        return git.git_diff(repo_path)

    def create_version_tag(self, repo_name: str, tag: str, message: str = None) -> bool:
        """새로운 버전 태그를 생성합니다."""
        try:
            repo_path = self.active_repositories.get(repo_name)
            if not repo_path:
                raise Exception(f"Repository {repo_name} not found")
            
            # 태그 생성
            if not message:
                message = f"Create tag {tag}"
            
            git.create_tag(repo_path, tag, message)
            
            # 원격 저장소에 태그 푸시
            git.push_tag(repo_path, tag)
            
            logger.info(f"Successfully created and pushed tag {tag} for {repo_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create tag {tag} for {repo_name}: {e}")
            return False

if __name__ == "__main__":
    manager = WorkspaceManager.get_instance()
    
    print(manager.find_bb_file("meta-ccos-avn", "audiostreamingmanager"))
