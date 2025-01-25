import os
import json
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Recipe:
    id: str
    name: str
    url: str

@dataclass
class MetaRepo:
    name: str
    url: str
    recipes: List[Recipe]

    @classmethod
    def from_dict(cls, data: dict) -> 'MetaRepo':
        recipes = [Recipe(**recipe) for recipe in data.get('recipes', [])]
        return cls(
            name=data['name'],
            url=data['url'],
            recipes=recipes
        )

class RepoConfig:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if RepoConfig._instance is not None:
            raise RuntimeError("RepoConfig is a singleton. Use get_instance() instead")
            
        self.config_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.config_dir, "repo.json")
        self.meta_repos: List[MetaRepo] = []
        self.load_config()
        
    def load_config(self):
        """repo.json 파일에서 설정을 로드합니다."""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.meta_repos = [MetaRepo.from_dict(repo) for repo in data.get('meta', [])]
        except Exception as e:
            print(f"Error loading repo config: {e}")
            self.meta_repos = []
    
    def save_config(self):
        """현재 설정을 repo.json 파일에 저장합니다."""
        try:
            data = {
                'meta': [
                    {
                        'name': repo.name,
                        'url': repo.url,
                        'recipes': [
                            {
                                'id': recipe.id,
                                'name': recipe.name,
                                'url': recipe.url
                            }
                            for recipe in repo.recipes
                        ]
                    }
                    for repo in self.meta_repos
                ]
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving repo config: {e}")
    
    def get_meta_repo(self, name: str) -> Optional[MetaRepo]:
        """메타 저장소를 이름으로 찾습니다."""
        for repo in self.meta_repos:
            if repo.name == name:
                return repo
        return None
    
    def get_recipe(self, meta_name: str, recipe_id: str) -> Optional[Recipe]:
        """특정 메타 저장소의 레시피를 ID로 찾습니다."""
        meta_repo = self.get_meta_repo(meta_name)
        if meta_repo:
            for recipe in meta_repo.recipes:                                                  
                if recipe.id == recipe_id:
                    return recipe
        return None
    
    def add_meta_repo(self, name: str, url: str, recipes: List[Recipe] = None):
        """새로운 메타 저장소를 추가합니다."""
        if recipes is None:
            recipes = []
        self.meta_repos.append(MetaRepo(name=name, url=url, recipes=recipes))
        self.save_config()
    
    def update_meta_repo(self, name: str, url: str = None, recipes: List[Recipe] = None):
        """기존 메타 저장소를 업데이트합니다."""
        meta_repo = self.get_meta_repo(name)
        if meta_repo:
            if url:
                meta_repo.url = url
            if recipes is not None:
                meta_repo.recipes = recipes
            self.save_config()
    
    def remove_meta_repo(self, name: str):
        """메타 저장소를 제거합니다."""
        self.meta_repos = [repo for repo in self.meta_repos if repo.name != name]
        self.save_config() 
        
if __name__ == "__main__":
    repo_config = RepoConfig.get_instance()
    print(repo_config.meta_repos)
    
    # 메타 저장소 추가
    repo_config.add_meta_repo("TestRepo", "https://github.com/example/test-repo.git")
    print(repo_config.meta_repos)
    
    # # 메타 저장소 업데이트
    # repo_config.update_meta_repo("TestRepo", url="https://github.com/example/test-repo-updated.git")
    # print(repo_config.meta_repos)
    
    # # 메타 저장소 제거
    # repo_config.remove_meta_repo("TestRepo")
    # print(repo_config.meta_repos)
