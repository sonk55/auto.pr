import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from atlassian import Bitbucket
from atlassian.bitbucket import Cloud 

class BitbucketAPI:
    _instance = None
    
    @classmethod
    def initialize(cls, cloud: Cloud):
        if cls._instance is None:
            cls._instance = cls(cloud)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise RuntimeError("BitbucketAPI not initialized. Call initialize() first.")
        return cls._instance
    
    def __init__(self, cloud: Cloud):
        if BitbucketAPI._instance is not None:
            raise RuntimeError("BitbucketAPI is a singleton. Use get_instance() instead.")
        self.bitbucket = cloud

    def get_pull_requests(self):
        try:
            pull_requests = self.bitbucket.get(f'pullrequests/{self.bitbucket.username}')
            return pull_requests['values']
        except Exception as e:
            print(f"Error getting pull requests: {e}")
            return []
        
    def get_pull_requests_meta(self):
        try:
            pull_requests = self.get_pull_requests()

            # pr['source']['repository']['name']가 meta-* 인 것만 추출
            pull_requests = [pr for pr in pull_requests if pr['source']['repository']['name'].startswith('meta-')]
            
            return pull_requests
        except Exception as e:
            print(f"Error getting pull requests: {e}")
            return []
        
    def get_current_user(self):
        try:
            user = self.get('user')
            return user
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None
        
    # curl --request GET \
    #   --url 'https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/src/{commit}/{path}' \
    #   --header 'Authorization: Bearer <access_token>' \
    #   --header 'Accept: application/json'
    def get_file_content(self, workspace, repo_slug, commit, path):
        url = f'https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/src/{commit}/{path}'
        response = self.bitbucket.get(url)
        return response
        
    def get(self, url):
        url = url.replace('https://api.bitbucket.org/2.0/', '')
        response = self.bitbucket.get(url)
        return response

    def create_pull_request(self, pr_data: dict):
        """Pull Request를 생성합니다."""
        try:
            workspace = self.bitbucket.username
            repo_slug = pr_data['source']['repository']
            
            # PR 생성 API 호출
            response = self.bitbucket.post(
                f'repositories/{workspace}/{repo_slug}/pullrequests',
                data={
                    'title': pr_data['title'],
                    'description': pr_data['description'],
                    'source': {
                        'branch': {
                            'name': pr_data['source']['branch']
                        }
                    },
                    'destination': {
                        'branch': {
                            'name': pr_data['destination']['branch']
                        }
                    }
                }
            )
            
            return response
            
        except Exception as e:
            print(f"Error creating pull request: {e}")
            raise

if __name__ == "__main__":
    import json
    from utils import parse_info_from_diff
    from abc import ABC, abstractmethod
    
    # API 테스트를 위한 추상 컴포넌트
    class APITest(ABC):
        @abstractmethod
        def execute(self):
            pass
            
    # PR 정보 출력을 위한 Leaf 컴포넌트
    class PRInfoTest(APITest):
        def __init__(self, pr):
            self.pr = pr
            
        def execute(self):
            print(f"PR Title: {self.pr['title']}\n"
                  f"PR ID: {self.pr['id']}\n"
                  f"PR Repository: {self.pr['source']['repository']['name']}\n"
                  f"PR State: {self.pr['state']}\n"
                  f"PR Created On: {self.pr['created_on']}\n"
                  f"PR Updated On: {self.pr['updated_on']}\n"
                  f"PR Author: {self.pr['author']['display_name']}\n"
                  f"PR Source Branch: {self.pr['source']['branch']['name']}\n"
                  f"PR Destination Branch: {self.pr['destination']['branch']['name']}\n"
                  f"PR Description: {self.pr['description']}\n"
                  )
            print("\n=== PR Links ===")
            print_links_menu(self.pr['links'])
            
    # Diff 정보 출력을 위한 Leaf 컴포넌트  
    class DiffInfoTest(APITest):
        def __init__(self, api, pr):
            self.api = api
            self.pr = pr
            
        def execute(self):
            diff = self.pr['links']['diff']['href']
            diff_info = self.api.get(diff)
            print(json.dumps(diff_info, indent=4))
            parsed_info = parse_info_from_diff(diff_info)
            print(parsed_info)
            
    # 여러 테스트를 조합하는 Composite 컴포넌트
    class TestSuite(APITest):
        def __init__(self):
            self.tests = []
            
        def add(self, test):
            self.tests.append(test)
            
        def execute(self):
            for test in self.tests:
                test.execute()

    def print_menu():
        print("\n=== Bitbucket API 테스트 메뉴 ===")
        print("1. PR 정보 보기")
        print("2. Diff 정보 보기") 
        print("3. 모든 테스트 실행")
        print("0. 종료")
        print("b. 이전 메뉴로")
        
    def print_pr_list(pull_requests):
        print("\n=== PR 목록 ===")
        for i, pr in enumerate(pull_requests, 1):
            print(f"{i}. {pr['title']} ({pr['source']['repository']['name']})")
        print("0. 이전 메뉴로")

    def print_links_menu(links):
        print(json.dumps(links, indent=4))
        print("\n=== 링크 메뉴 ===")
        menu_items = list(links.items())
        for i, (key, value) in enumerate(menu_items, 1):
            print(f"{i}. {key}")
        print("0. 이전 메뉴로")

        while True:
            choice = input("링크를 선택하세요: ")
            if choice == "0":
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(menu_items):
                    key, value = menu_items[idx]
                    print(f"\n=== {key} 링크 내용 ===")
                    print(json.dumps(value, indent=4))
                    if isinstance(value, dict) and value.get('href'):
                        sub_choice = input("\n1. href 링크 내용 보기\n0. 이전 메뉴로\n선택: ")
                        if sub_choice == "1":
                            print(f"\n=== {value['href']} 내용 ===")
                            try:
                                response = api.get(value['href'])
                                print(json.dumps(response, indent=4))
                            except Exception as e:
                                print(f"링크 내용을 가져오는 중 오류 발생: {e}")
                else:
                    print("잘못된 링크 번호입니다.")
            except ValueError:
                print("올바른 숫자를 입력하세요.")
                
    # API 테스트 실행
    bitbucket = Cloud(
        url="https://api.bitbucket.org",
        username="sonk551", 
        password="",
    )
    
    api = BitbucketAPI(bitbucket)
    
    # /repositories/{workspace}/{repo_slug}/src/{commit}/{path}
    
    pull_requests = api.get_pull_requests_meta()
    test_suite = TestSuite()
    
    while True:
        print_menu()
        choice = input("메뉴를 선택하세요: ")
        
        if choice == "0":
            break
        elif choice == "b":
            print("최상위 메뉴입니다.")
            continue
        elif choice == "1":
            while True:
                print_pr_list(pull_requests)
                pr_choice = input("PR을 선택하세요: ")
                
                if pr_choice == "0":
                    break
                    
                try:
                    pr_idx = int(pr_choice) - 1
                    if 0 <= pr_idx < len(pull_requests):
                        pr_test = PRInfoTest(pull_requests[pr_idx])
                        pr_test.execute()
                    else:
                        print("잘못된 PR 번호입니다.")
                except ValueError:
                    print("올바른 숫자를 입력하세요.")
                    
        elif choice == "2":
            while True:
                print_pr_list(pull_requests)
                pr_choice = input("Diff를 확인할 PR을 선택하세요: ")
                
                if pr_choice == "0":
                    break
                    
                try:
                    pr_idx = int(pr_choice) - 1
                    if 0 <= pr_idx < len(pull_requests):
                        diff_test = DiffInfoTest(api, pull_requests[pr_idx])
                        diff_test.execute()
                    else:
                        print("잘못된 PR 번호입니다.")
                except ValueError:
                    print("올바른 숫자를 입력하세요.")
                    
        elif choice == "3":
            for pr in pull_requests:
                test_suite.add(PRInfoTest(pr))
                test_suite.add(DiffInfoTest(api, pr))
            test_suite.execute()
            
        else:
            print("잘못된 메뉴 선택입니다.")
    
