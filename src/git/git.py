import os
import subprocess
from typing import List
import re
from utils.logger import setup_logger  # 절대 경로 사용


logger = setup_logger(__name__)

def run_git_command(command: list, cwd: str = None) -> str:
    """Git 명령어를 실행하고 결과를 반환합니다."""
    logger.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e.stderr}")
        raise

def git_clone(repo_url: str, branch: str, path: str, folder_name: str = None):
    """저장소를 클론합니다."""
    if folder_name:
        # 지정된 폴더 이름으로 클론
        command = ["git", "clone", "-b", branch, repo_url, folder_name]
        return run_git_command(command, cwd=path)
    else:
        # 기본 동작 (repo 이름으로 클론)
        command = ["git", "clone", "-b", branch, repo_url]
        return run_git_command(command, cwd=path)
    
def git_pull(path: str):
    """현재 브랜치에서 pull을 수행합니다."""
    command = ["git", "pull"]
    return run_git_command(command, cwd=path)
    
def git_checkout(path: str, branch: str):
    """지정된 브랜치로 체크아웃합니다."""
    command = ["git", "checkout", branch]
    return run_git_command(command, cwd=path)
    
def git_branch(path: str):
    """브랜치 목록을 반환합니다."""
    command = ["git", "branch"]
    return run_git_command(command, cwd=path)
    
def git_status(path: str):
    """저장소 상태를 반환합니다."""
    command = ["git", "status"]
    return run_git_command(command, cwd=path)

def get_remote_tag_hash(repo_url: str, tag: str):
    """원격 저장소의 태그 해시를 반환합니다."""
    command = ["git", "ls-remote", "--tags", repo_url, tag]
    return run_git_command(command)

def get_tag_hash_by_branch(path: str, branch: str):
    """ 브랜치 해시를 반환합니다."""
    # 브랜치에 병합된 태그 목록 가져오기
    command = ["git", "tag", "--merged", branch]
    tags = run_git_command(command, cwd=path).splitlines()
    
    # 각 태그의 해시값 가져오기
    result = {}
    for tag in tags:
        hash_command = ["git", "rev-parse", tag]
        hash_value = run_git_command(hash_command, cwd=path)
        result[tag] = hash_value
        
    return result
    
def git_current_branch(path: str) -> str:
    """현재 브랜치 이름을 반환합니다."""
    command = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    return run_git_command(command, cwd=path)

def git_add_all(path: str):
    """모든 변경사항을 스테이징합니다."""
    command = ["git", "add", "."]
    return run_git_command(command, cwd=path)

def git_commit(path: str, message: str):
    """변경사항을 커밋합니다."""
    command = ["git", "commit", "-m", message]
    return run_git_command(command, cwd=path)

def git_push(path: str, branch: str):
    """변경사항을 원격 저장소로 push합니다."""
    command = ["git", "push", "origin", branch]
    return run_git_command(command, cwd=path)

def get_commit_messages_between_tags(path: str, tag1: str, tag2: str) -> List[str]:
    """두 태그 사이의 커밋 메시지를 가져옵니다."""
    try:
        # 먼저 fetch 수행
        fetch_command = ["git", "fetch", "--all", "--tags"]
        run_git_command(fetch_command, cwd=path)
        
        # 전체 커밋 메시지를 가져옴
        command = ["git", "log", "--pretty=format:%s", f"{tag1}..{tag2}"]
        output = run_git_command(command, cwd=path)
        
        logger.info(f"Commit messages between {tag1} and {tag2}: {output}")
        
        # 각 커밋 메시지를 분리
        return output.split("\n")
        
    except Exception as e:
        logger.error(f"Error getting commit messages: {e}")
        return []
    
def get_jira_numbers_between_tags(path: str, tag1: str, tag2: str) -> List[str]:
    """두 태그 사이의 JIRA 번호를 가져옵니다."""
    command = ["git", "log", "--pretty=format:%B", f"{tag1}..{tag2}"]
    output = run_git_command(command, cwd=path)
    return re.findall(r'(?:[A-Z][A-Z0-9]*-\d+)', output)

def get_latest_tag(path: str) -> str:
    """저장소의 최신 태그를 반환합니다."""
    try:
        command = ["git", "tag", "--sort=-version:refname", "--list", "version/*"]
        output = run_git_command(command, cwd=path)
        tags = output.split('\n')
        return tags[0] if tags else ""
    except Exception as e:
        logger.error(f"Error getting latest tag: {e}")
        return ""

def get_head_tags(path: str) -> List[str]:
    """HEAD에 있는 태그들을 반환합니다."""
    try:
        command = ["git", "tag", "--points-at", "HEAD"]
        output = run_git_command(command, cwd=path)
        return [tag for tag in output.split('\n') if tag.startswith('version/')]
    except Exception as e:
        logger.error(f"Error getting HEAD tags: {e}")
        return []

def get_all_version_tags(path: str) -> List[str]:
    """저장소의 모든 버전 태그를 반환합니다."""
    try:
        command = ["git", "tag", "--list", "version/*"]
        output = run_git_command(command, cwd=path)
        return output.split('\n')
    except Exception as e:
        logger.error(f"Error getting version tags: {e}")
        return []

def get_commit_count_between_tags(path: str, tag1: str, tag2: str) -> int:
    """두 태그 사이의 커밋 수를 반환합니다."""
    try:
        command = ["git", "rev-list", "--count", f"{tag1}..{tag2}"]
        output = run_git_command(command, cwd=path)
        return int(output)
    except Exception as e:
        logger.error(f"Error getting commit count: {e}")
        return 0

def git_diff(path: str) -> str:
    """변경사항을 반환합니다."""
    try:
        # 스테이징되지 않은 변경사항
        command = ["git", "diff"]
        unstaged = run_git_command(command, cwd=path)
        
        # 스테이징된 변경사항
        command = ["git", "diff", "--cached"]
        staged = run_git_command(command, cwd=path)
        
        # 둘 다 있으면 합치기
        if unstaged and staged:
            return "=== Staged Changes ===\n" + staged + "\n=== Unstaged Changes ===\n" + unstaged
        elif staged:
            return staged
        else:
            return unstaged
            
    except Exception as e:
        logger.error(f"Error getting diff: {e}")
        return ""

def create_tag(path: str, tag: str, message: str) -> None:
    """태그를 생성합니다."""
    command = ["git", "tag", "-a", tag, "-m", message]
    run_git_command(command, cwd=path)
    
def push_tag(path: str, tag: str) -> None:
    """태그를 원격 저장소에 푸시합니다."""
    command = ["git", "push", "origin", tag]
    run_git_command(command, cwd=path)

if __name__ == "__main__":
    import os
    
    # 테스트를 위한 경로와 브랜치
    workspace_path = os.path.expanduser("~/.auto-pr/workspace")
    repo_path = os.path.join(workspace_path, "audiostreamingmanager")
    
    if os.path.exists(repo_path):
        print(get_tag_hash_by_branch(repo_path, "@s6mobis"))
    else:
        print(f"저장소가 존재하지 않습니다: {repo_path}")