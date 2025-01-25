from atlassian import Bitbucket
from atlassian.bitbucket import Cloud
import json
bitbucket = Cloud(
    url="https://api.bitbucket.org",
    username="sonk551",
    password="",
)

def print_json(json_data):
    print(json.dumps(json_data, indent=4))

def get_my_pull_request(bitbucket) :
    try:
        # 현재 사용자의 PR 목록 가져오기
        pull_requests = bitbucket.get(f'pullrequests/{bitbucket.username}')
        
        print_json(pull_requests)
        
        for pr in pull_requests["values"]:
            
            print(f"PR Title: {pr['title']}\n"
                  f"PR ID: {pr['id']}\n"
                  f"PR Repository: {pr['source']['repository']['name']}\n"
                  f"PR State: {pr['state']}\n"
                  f"PR Created On: {pr['created_on']}\n"
                  f"PR Updated On: {pr['updated_on']}\n"
                  f"PR Author: {pr['author']['display_name']}\n"
                  f"PR Source Branch: {pr['source']['branch']['name']}\n"
                  f"PR Destination Branch: {pr['destination']['branch']['name']}\n"
                  f"PR Description: {pr['description']}\n"
                  )

        # PR 목록 반환
        return pull_requests["values"] if "values" in pull_requests else []
        
    except Exception as e:
        print(f"PR 목록을 가져오는 중 오류 발생: {e}")
        return []
    
pull_requests = get_my_pull_request(bitbucket)