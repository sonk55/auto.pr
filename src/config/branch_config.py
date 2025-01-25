import os
import json
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class BranchConfig:
    name: str
    tags: List[str] = None  # 브랜치의 태그 목록
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BranchConfig':
        return cls(
            name=data['name'],
            tags=data.get('tags', [])
        )

class BranchManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if BranchManager._instance is not None:
            raise RuntimeError("BranchManager is a singleton. Use get_instance() instead")
            
        self.config_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.config_dir, "branch.json")
        self.branches: List[BranchConfig] = []
        self.load_config()
        
    def load_config(self):
        """branch.json 파일에서 설정을 로드합니다."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.branches = [BranchConfig.from_dict(branch) for branch in data.get('branches', [])]
            else:
                # 기본 브랜치 설정
                self.branches = [BranchConfig("@s6mobis", ["release"])]
                self.save_config()
        except Exception as e:
            print(f"Error loading branch config: {e}")
            self.branches = [BranchConfig("@s6mobis", ["release"])]
    
    def save_config(self):
        """현재 설정을 branch.json 파일에 저장합니다."""
        try:
            data = {
                'branches': [
                    {
                        'name': branch.name,
                        'tags': branch.tags
                    }
                    for branch in self.branches
                ]
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving branch config: {e}")
            
    def get_tags_for_branch(self, branch_name: str) -> List[str]:
        """특정 브랜치의 태그 목록을 반환합니다."""
        for branch in self.branches:
            if branch.name == branch_name:
                return branch.tags
        return []

    def get_all_tags(self) -> List[str]:
        """모든 브랜치에서 사용 중인 태그 목록을 반환합니다."""
        tags = set()
        for branch in self.branches:
            tags.update(branch.tags)
        return sorted(list(tags)) 