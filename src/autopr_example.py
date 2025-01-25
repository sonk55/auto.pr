#!/usr/bin/env python

import argparse
import datetime
import tempfile
import shutil
import os
import subprocess
import re
import json
import core.bitbucket as bitbucket

from config import ConfigManager
from core.confluence import confluence 
from collections import defaultdict
from util import tagUtils
from util.printUtils import *
import time

def get_user_input(prompt, default_value='', split=True):
    while True:
        try:
            input_str = input(Colors.YELLOW + prompt + Colors.RESET + f'\n(default={default_value}): ')

            if input_str == '':
                input_str = default_value

            print()

            if split:
                values = [value.strip() for value in input_str.replace(',', ' ').split()]
                print("Entered values:")
                for value in values:
                    print(Colors.YELLOW + ' - ' + value + Colors.RESET)
            else:
                values = input_str
                print("Entered values: " + Colors.YELLOW + f"{values}" + Colors.RESET)

            # Remove leading/trailing whitespace from each value
            #values = [value.strip() for value in values]

            # Confirmation
            confirmation = input("Is the input correct? (y/n): ")
            if confirmation.upper() == "Y":
                return values

            print("Please enter again.\n")
        except Exception as e:
            print("An error occurred:", str(e))
            print("Please enter again.\n")

def git_clone(url, branch_name):
    """
    Function that performs Git clone of a repository for a specific branch.

    Parameters:
        - url (str): Git repository URL.
        - branch_name (str): Name of the branch to clone.

    Returns:
        - str: Cloned directory path. Returns None if the clone operation fails.
    """
    try:
        # Execute Git clone command for the specified branch
        subprocess.run(['git', 'clone', '-b', branch_name, '--single-branch', url], check=True, stdout=subprocess.PIPE)
        print("Git clone completed successfully.")

        def remove_last_git(s):
            if s.endswith('.git'):
                return s[:-4]
            return s

        # Cloned directory path
        cloned_dir = os.path.join(os.getcwd(), remove_last_git(os.path.basename(url)))

        return cloned_dir
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during Git clone: {e}")
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

    return None

def find_recipe_file_path(meta_git_path, recipe_name):
    recipe_name = recipe_name + '.bb'
    for root, dirs, files in os.walk(meta_git_path):
        if recipe_name in files:
            return os.path.join(root, recipe_name)

    return None

def get_ccos_git_branch_name(recipe_file_path):
    """
    Function that retrieves the value of the 'CCOS_GIT_BRANCH_NAME' variable from a Yocto recipe file.

    Parameters:
        - recipe_file_path (str): Path to the Yocto recipe file.

    Returns:
        - str: Value of the 'CCOS_GIT_BRANCH_NAME' variable. Returns None if the file doesn't exist or the variable is not found.
    """
    try:
        with open(recipe_file_path, 'r') as file:
            for line in file:
                if line.startswith('CCOS_GIT_BRANCH_NAME'):
                    return line.split('=')[1].strip().replace('"', '').replace("'", '')
    except FileNotFoundError:
        print("File not found:", recipe_file_path)
    except Exception as e:
        print("An error occurred:", str(e))

    return '@s6mobis'

def update_ccos_git_branch(recipe_file_path, new_branch_name):
    try:
        with open(recipe_file_path, 'r') as file:
            lines = file.readlines()

        updated_lines = []
        found_variable = False

        for line in lines:
            if line.startswith('CCOS_GIT_BRANCH_NAME=') or line.startswith('CCOS_GIT_BRANCH_NAME ='):
                line = f'CCOS_GIT_BRANCH_NAME = "{new_branch_name}"\n'
                found_variable = True
            updated_lines.append(line)

        if not found_variable:
            updated_lines.append(f'CCOS_GIT_BRANCH_NAME = "{new_branch_name}"\n')

        with open(recipe_file_path, 'w') as file:
            file.writelines(updated_lines)

        print("CCOS_GIT_BRANCH_NAME variable updated successfully.")
    except Exception as e:
        print(f"Error occurred: {e}")

def get_ccos_version(recipe_path):
    try:
        with open(recipe_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith("CCOS_VERSION"):
                    value = line.split("=")[1].strip().strip('" ')
                    return 'version/' + value.split('_')[0]

        # CCOS_VERSION variable not found
        print("CCOS_VERSION variable not found in the recipe file.")
        return None

    except FileNotFoundError:
        print(f"Recipe file '{recipe_path}' not found.")
        return None
    except Exception as e:
        print(f"Error occurred while reading the recipe file: {e}")
        return None

def get_commit_count_between_tags(git_path, tag_name):
    try:
        # Execute Git command to get the commit count between tags
        result = subprocess.run(['git', '-C', git_path, 'rev-list', f'{tag_name}..HEAD'], stdout=subprocess.PIPE)
        if result.returncode == 0:
            commit_count = len(result.stdout.decode().strip().split('\n'))
            return commit_count
        else:
            raise Exception(f"Error occurred during Git command execution:\n{result.stderr}")

    except subprocess.CalledProcessError as e:
        raise Exception(f"Error occurred during Git command execution: {e}")

    except Exception as e:
        raise Exception(f"Error occurred: {e}")

    return 0

def get_latest_tag(git_path):
    try:
        # subprocess.run(['git', '-C', git_path, 'fetch', '--tags'])

        # Get the list of tags
        process = subprocess.Popen(['git', '-C', git_path, 'tag', '--list', 'version/*'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()

        # Decode and split the tag names
        tags = stdout.decode().strip().splitlines()

        numeric_tags = sorted(filter(lambda tag: re.match(r'version/\d+', tag), tags), key=lambda tag: list(map(int, re.findall(r'\d+', tag))), reverse=True)


        latest_tag = numeric_tags[0]

        latest_version = list(map(int, re.findall(r'\d+', latest_tag)))

        return "version/" + ".".join(map(str, latest_version))

    except subprocess.CalledProcessError as e:
        print(f"Error occurred during Git operations: {e}")
    except Exception as e:
        print(f"Error occurred: {e}")

    return None

def auto_version_up(git_path):
    try:
        # subprocess.run(['git', '-C', git_path, 'fetch', '--tags'])

        # Get the list of tags
        process = subprocess.Popen(['git', '-C', git_path, 'tag', '--list', 'version/*'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()

        # Decode and split the tag names
        tags = stdout.decode().strip().splitlines()

        #numeric_tags = sorted(filter(lambda tag: re.match(r'version/\d+', tag), tags), reverse=True)
        numeric_tags = sorted(filter(lambda tag: re.match(r'version/\d+', tag), tags), key=lambda tag: list(map(int, re.findall(r'\d+', tag))), reverse=True)


        latest_tag = numeric_tags[0]

        latest_version = list(map(int, re.findall(r'\d+', latest_tag)))

        # Perform version up
        new_version = latest_version[-1] + 1
        latest_version[-1] = new_version

        # Generate the new tag name
        new_tag = "version/" + ".".join(map(str, latest_version))

        # Confirm with the user before creating the new tag and pushing
        print()
        print(Colors.RED + "** WARNING **" + Colors.RESET)
        confirmation = input(f"Create a new tag '{new_tag}' and push to remote? (y/n): ")

        if confirmation.lower() == 'y':
            # Create the new tag
            subprocess.run(['git', '-C', git_path, 'tag', '-a', '-m', new_tag, new_tag], check=True)

            input(f"PUSH NEW TAGS to REMOTE BRANCH... press enter.")
            # Push the new tag to remote
            subprocess.run(['git', '-C', git_path, 'push', 'origin', new_tag], check=True)

            return new_tag
        else:
            print("Tag creation and push cancelled by user.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during Git operations: {e}")
    except Exception as e:
        print(f"Error occurred: {e}")

    return None

def get_commit_messages_between_tags(git_path, tag1, tag2):
    try:
        # Git command to get the commit titles between two tags
        command = ['git', '-C', git_path, 'log', '--pretty=format:%s', f'{tag1}..{tag2}']

        # Execute the git command and capture the output
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()

        # Decode the output and split it into individual commit titles
        commit_titles = stdout.decode().strip().split('\n')

        return '\n'.join(commit_titles)
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def extract_jira_numbers_between_tags(git_path, tag1, tag2):
    # 커밋 메시지에서 Jira 번호를 추출할 패턴
    pattern = r'(?:[A-Z][A-Z0-9]*-\d+)'

    # 두 태그 사이의 커밋 목록을 가져오기
    cmd = ['git', '-C', git_path, 'log', '--pretty=format:%B', '{}..{}'.format(tag1, tag2)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    commit_messages = result.stdout.strip().split('\n\n')

    # 커밋 메시지에서 Jira 번호 추출
    jira_numbers = []
    for message in commit_messages:
        jira_numbers += re.findall(pattern, message)

    return '\n'.join(jira_numbers)

def extract_message_between_tags(git_path, tag1, tag2, key):
    """
        commit message :
        # [커밋 유형]: 제목 (50자 이내로 간결하게)
        # 예시: ENH: 새로운 기능 추가

        # Description:
        # 커밋에 대한 상세 설명 (필수)

        # Cause:
        # 이슈 발생 원인 (선택, 없으면 Description 내용 사용)

        # Countermeasure:
        # 문제 해결 방법 (선택, 없으면 Description 내용 사용)

        # Dependency:
        # 의존성 (선택)

        # Jira:
        # Jira 이슈 태그 (선택)
    """
    # 두 태그 사이의 커밋 목록을 가져오기
    cmd = ['git', '-C', git_path, 'log', '--pretty=format:%B', '{}..{}'.format(tag1, tag2)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    commit_messages = result.stdout.strip().split('\n\n')

    # 함수 실행 및 결과 출력
    parsed_data = parse_commit_message(result.stdout)
    # for key, value in parsed_data.items():
    #     print(f"{key.capitalize()}: {value}")

    return parsed_data[key]

def parse_commit_message(commit_message):
    # 각 태그를 식별하기 위한 정규 표현식 패턴 정의
    patterns = {
        "type": r'^\[(.*?)\]:\s*(.*)',  # [커밋 유형]: 제목
        "description": r'^Description:\n([\s\S]*?)(?=\n(?:Cause:|Countermeasure:|Dependency:|Jira:|$))',
        "cause": r'^Cause:\n([\s\S]*?)(?=\n(?:Countermeasure:|Dependency:|Jira:|$))',
        "countermeasure": r'^Countermeasure:\n([\s\S]*?)(?=\n(?:Dependency:|Jira:|$))',
        "dependency": r'^Dependency:\n([\s\S]*?)(?=\n(?:Jira:|$))',
        "jira": r'^Jira:\n([\s\S]*)'
    }

    # 태그별로 데이터를 추출
    result = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, commit_message, re.MULTILINE)
        result[key] = match.group(1).strip() if match else ""

    return result

def get_tag_hash(git_path, tag_name):
    # Git 명령어로 태그의 해시 값을 가져오기
    cmd = ['git', '-C', git_path, 'rev-parse', tag_name]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    if result.returncode == 0:
        tag_hash = result.stdout.strip()
        return tag_hash

    return None

def update_ccos_version(recipe_path, new_value):
    with open(recipe_path, 'r') as file:
        lines = file.readlines()

    updated_lines = []
    ccos_version_updated = False
    for line in lines:
        if line.startswith("CCOS_VERSION"):
            line = line.strip()  # 좌우 공백 제거
            if "=" in line:
                parts = line.split("=")
                if len(parts) == 2:
                    line = f"{parts[0]}= \"{new_value}\""  # 변경된 값으로 대체
            line += "\n"  # 줄바꿈 문자 추가
            ccos_version_updated = True
        updated_lines.append(line)

    if not ccos_version_updated:
        updated_lines.append(f"CCOS_VERSION = \"{new_value}\"\n")  # 변경된 결과 추가

    with open(recipe_path, 'w') as file:
        file.writelines(updated_lines)

def colorize_git_diff(diff_output):
    colored_diff = ''
    lines = diff_output.split('\n')
    for line in lines:
        if line.startswith('+'):
            colored_diff += '\033[32m' + line + '\033[0m\n'  # 녹색
        elif line.startswith('-'):
            colored_diff += '\033[31m' + line + '\033[0m\n'  # 빨간색
        else:
            colored_diff += line + '\n'
    return colored_diff

def git_diff(git_path):
    try:
        # 'git diff' 명령어 실행
        command = ['git', '-C', git_path, 'diff']
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 출력 결과 반환
        return colorize_git_diff(result.stdout.decode('utf-8').strip())
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return None

def git_checkout_branch(git_path, branch):
    try:
        # 'git diff' 명령어 실행
        command = ['git', '-C', git_path, 'checkout', branch]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        command = ['git', '-C', git_path, 'reset', '--hard', f'origin/{branch}']
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        return True

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

        return False

def head_version_tag(git_path):
    ret = []
    result = subprocess.run(['git', '-C', git_path, 'tag', '--points-at', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        output = result.stdout.decode().strip().split('\n')
        for tag in output:
            if tag.startswith('version/'):
                ret.append(tag)

    return ', '.join(ret)

def create_new_branch_and_commit_push(git_path, message, meta_branch_name, prefix=''):
    # 문자열의 첫 번째 줄을 가져옴
    first_line = message.strip().split('\n')[0]

    # 공백을 언더바로 변경
    modified_string = re.sub(r'\s+', '_', first_line)

    # 현재 시간 가져오기
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # prefix와 postfix를 추가한 최종 브랜치명 생성
    branch_name = f"{prefix}AUTOPR/{meta_branch_name}/{current_time}/{modified_string}"

    try:
        # 브랜치 분기
        subprocess.run(['git', '-C', git_path, 'checkout', '-b', branch_name], check=True)
        print(f"Branch '{branch_name}' created.")

        # 커밋 메시지로 사용할 전체 문자열
        commit_message = message.strip()

        # 변경된 파일들을 git에 추가
        subprocess.run(['git', '-C', git_path, 'add', '-A'], check=True)

        # 커밋
        subprocess.run(['git', '-C', git_path, 'commit', '-m', commit_message], check=True)
        print("Changes committed.")

        # 푸시
        subprocess.run(['git', '-C', git_path, 'push', '-u', 'origin', branch_name], check=True)
        print("Changes pushed to remote repository.")

        return branch_name

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return None

def change_working_directory(folder_name):
    current_directory = os.getcwd()
    target_folder_path = os.path.join(current_directory, folder_name)

    if not os.path.exists(target_folder_path):
        os.makedirs(target_folder_path)

    os.chdir(target_folder_path)

def is_same_git_url(url, git_folder):
    # 현재 Git 저장소의 URL 가져오기
    result = subprocess.run(['git', '-C', git_folder, 'config', '--get', 'remote.origin.url'], stdout=subprocess.PIPE, check=True)
    if result.returncode == 0:
        current_url = result.stdout.strip().decode()
        return current_url == url

    # Git 저장소의 URL을 가져올 수 없는 경우
    return False

def sync_git_repository(url, branch_name=''):
    working_directory = os.getcwd()

    try:
        folder_name = url.split('/')[-1].replace('.git', '')
        folder_path = os.path.join(working_directory, folder_name)

        if os.path.exists(folder_path):
            git_folder = os.path.join(folder_path, '.git')
            if os.path.isdir(folder_path) and is_same_git_url(url, git_folder):
                """
                print(f' * Found existing git - {folder_path}')
                confirmation = input("Use existing git?\n *All modifications will be removed.. (y/n): ")
                if confirmation.lower() == "y":
                    pass
                else:
                    raise Exception("Try again... terminate... ")
                """

                os.chdir(folder_path)
                subprocess.run(['git', 'reset', '--hard', 'HEAD'])
                subprocess.run(['git', 'fetch'])
                subprocess.run(['git', 'pull'])
                # subprocess.run(['git', 'checkout', branch_name])
                # subprocess.run(['git', 'reset', '--hard', f'origin/{branch_name}'])

            else:
                # Error
                print(f'ERROR - check the {folder_path}')
                return None

        else:
            # clone
            subprocess.run(['git', 'clone', url])
            os.chdir(folder_path)
            # subprocess.run(['git', 'checkout', branch_name])
            subprocess.run(['git', 'gc'])
            subprocess.run(['git', 'repack', '-d', '-l'])

        os.chdir(working_directory)  # 상위 폴더로 이동
    except Exception as e:
        print(f'Error occurred: {e}')
        os.chdir(working_directory)
        return None

    return folder_path

def main(args):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # if os.path.isabs(args.repo):  # 절대경로인 경우
    #     if os.path.isfile(args.repo):
    #         repo_file_path = os.path.abspath(args.repo)
    #     else:
    #         raise FileNotFoundError(f"File does not exist: {file_path}")

    # else:  # 상대경로인 경우
    #     abs_path = os.path.abspath(args.repo)
    #     if os.path.isfile(abs_path):
    #         repo_file_path = abs_path
    #     else:
    #         raise FileNotFoundError(f"File does not exist: {abs_path}")
        
    my_confluence = confluence()
    config = ConfigManager()
    author = config.get_id('confluence')
    access_token = config.get_token('bitbucket')
    repos = config.get_repos()
    possible_recipes = [recipe for meta in repos.keys() for recipe in repos[meta]['recipes'].keys()]

    branches = config.get_branches() if args.show else []
    recipes = possible_recipes if args.show else []
    reviewers = config.get_reviewers_id()
    print(reviewers)

    if not args.show:
        branch_name = get_user_input("Input branch name of meta", '@s6mobis', split=True)
        if 'all' in branch_name:
            branches = config.get_branches()
        elif 'filter' in branch_name:
            print(Colors.YELLOW)
            print(f'Available filters: {config.get_all_available_tags()}')
            print(Colors.RESET)

            filter = get_user_input("Enter the filter formula you want to use *ex) (KOR|GENIE)&STEP30", 'UNFIXED', split=False)
            branches = config.get_branches_by_condition(filter)
            
            print(Colors.YELLOW)
            print(f" Branch: {', '.join(branches)}")
            print(Colors.RESET)

        else:
            branches = branch_name if isinstance(branch_name, list) else [branch_name]

        print()

        recipes = get_user_input(f"Input recipes\n\tpossible recipes: {', '.join(['all'] + possible_recipes)}", 'all')
        if recipes == ['all']:
            recipes = possible_recipes

        print(Colors.GREEN)
        print(f" Branch: {', '.join(branches)}")
        print(f" Recipes: {', '.join(recipes)}")
        print(Colors.RESET)
        confirmation = input("Is this correct? (y/n): ")
        if confirmation.lower() == "y":
            pass
        else:
            print("Try again... terminate... ")
            return

    working_metas = defaultdict(list)
    for recipe in recipes:
        metas = repos.keys()
        found = False
        for meta in metas:
            if recipe in repos[meta]['recipes'].keys():
                working_metas[meta].append(recipe)
                found = True
                break

        if not found:
            print(f"Can't find \'{recipe}\', please check the \'repo.json\'")
            return

    change_working_directory('working_directory')

    print()
    print(Colors.YELLOW + f"Prepare meta repositories....\nIf this is your first attempt, it may take a lot of time." + Colors.RESET)
    for meta in working_metas.keys():
        print(f' - {meta}')
    print()

    meta_pathes = {}

    for meta in working_metas.keys():
        print()
        print(Colors.YELLOW + f"Prepare {meta} ....\nIf this is your first attempt, it may take a lot of time." + Colors.RESET)
        print()
        meta_path = sync_git_repository(repos[meta]['url'])
        if meta_path is None:
            print(f'Something wrong with {meta}')
            return

        meta_pathes[meta] = meta_path

    print(Colors.YELLOW)
    print(f'Working Directories:')
    for meta_name, meta_path in meta_pathes.items():
        print(f'{meta_name}: {meta_path}')
    print(Colors.RESET)

    for branch in branches:
        recipe_states = []
        for meta, recipes in working_metas.items():
            if not git_checkout_branch(meta_pathes[meta], branch):
                for recipe in working_metas[meta]:
                    recipe_name = repos[meta]['recipes'][recipe]['name']
                    recipe_states.append({
                        'recipe': f"{recipe_name}.bb",
                        'CCOS_GIT_BRANCH_NAME': "NONE",
                        'CCOS_VERSION': "NONE"
                    })
                continue

            for recipe in recipes:
                recipe_name = repos[meta]['recipes'][recipe]['name']
                recipe_path = find_recipe_file_path(meta_pathes[meta], recipe_name)
                recipe_state = {
                    'recipe': f"{recipe_name}.bb",
                    'CCOS_GIT_BRANCH_NAME': "NONE",
                    'CCOS_VERSION': "NONE"
                }

                if recipe_path:
                    recipe_state['CCOS_GIT_BRANCH_NAME'] = get_ccos_git_branch_name(recipe_path)
                    recipe_state['CCOS_VERSION'] = get_ccos_version(recipe_path)
                else:
                    print(Colors.RED + f"Can't find '{recipe_name}.bb' in {meta_pathes[meta]}" + Colors.RESET)

                recipe_states.append(recipe_state)

        print_recipe_state(branch, recipe_states)

    if args.show:
        return

    confirmation = input(Colors.RED + "Do you want to change the recipes? (y/n): " + Colors.RESET)
    if confirmation.lower() == "y":
        pass
    else:
        return
    try: 
        pr_state = []
        for branch in branches: 
            temp_dir = tempfile.mkdtemp()
            print()
            print(f"Change Working Directory: {temp_dir}")
            print()
            os.chdir(temp_dir)
            for meta in working_metas.keys():
                meta_git_path = meta_pathes[meta]
                git_checkout_branch(meta_git_path, branch)
                pr_message = defaultdict(str)

                for recipe in working_metas[meta]:
                    recipe_name = repos[meta]['recipes'][recipe]['name']
                    recipe_path = find_recipe_file_path(meta_git_path, recipe_name)
                    recipe_branch_name = get_ccos_git_branch_name(recipe_path)
                    recipe_CCOS_VERSION = repos[meta]['recipes'][recipe].get(branch, {}).get('CCOS_VERSION', '')
                    recipe_CCOS_GIT_BRANCH_NAME = repos[meta]['recipes'][recipe].get(branch, {}).get('CCOS_GIT_BRANCH_NAME', '')
                    original_recipe_branch_name = recipe_branch_name

                    print()
                    print("  Recipe: " + Colors.YELLOW + f"{recipe_name}.bb" + Colors.RESET)
                    print("  Target branch: " + Colors.YELLOW + f"{branch}" + Colors.RESET)
                    print()

                    if not recipe_path :
                        print(Colors.RED + f"Can't find '{recipe_name}.bb' in {meta_pathes[meta]}" + Colors.RESET)
                        input("Press any key for next step...")
                        continue

                    if recipe_CCOS_GIT_BRANCH_NAME == '' :
                        confirmation = input(Colors.RED + f"Do you want to change CCOS_GIT_BRANCH_NAME? (current:\'{recipe_branch_name}\') (y/n): " + Colors.RESET)
                        if confirmation.lower() == "y":
                            new_branch_name = get_user_input(f'Enter branch name:', f'{recipe_branch_name}', split=False)
                            if new_branch_name == recipe_branch_name:
                                print(Colors.YELLOW)
                                print(f'CCOS_GIT_BRANCH_NAME is already {new_branch_name}')
                                print(Colors.RESET)

                            else:
                                update_ccos_git_branch(recipe_path, new_branch_name)
                                recipe_branch_name = new_branch_name
                    else :
                        new_branch_name = recipe_CCOS_GIT_BRANCH_NAME

                        if new_branch_name == recipe_branch_name:
                            print(Colors.YELLOW)
                            print(f'CCOS_GIT_BRANCH_NAME is already {new_branch_name}')
                            print(Colors.RESET)
                        
                        else:
                            update_ccos_git_branch(recipe_path, new_branch_name)
                            recipe_branch_name = new_branch_name

                    print()
                    print("  Recipe: " + Colors.YELLOW + f"{recipe_name}.bb" + Colors.RESET)
                    print("  CCOS_GIT_BRANCH_NAME: " + Colors.GREEN + f"{recipe_branch_name}" + Colors.RESET)
                    print()

                    src_git_path = git_clone(repos[meta]['recipes'][recipe]['url'], recipe_branch_name)
                    ccos_version = get_ccos_version(recipe_path)

                    try:
                        num_new_commits = get_commit_count_between_tags(src_git_path, ccos_version)
                        if num_new_commits == 0:
                            print(f" ** There are no new commits - SKIP")
                            continue

                        print(f" ** There are new commits({num_new_commits}) between CCOS_VERSION and HEAD")
                    except Exception as e:
                        print(f'{e}')

                    head_tagging = head_version_tag(src_git_path)
                    print(Colors.YELLOW)
                    print(f" CCOS_VERSION = \"{ccos_version}\"")
                    print(f" Latest tag   = \"{get_latest_tag(src_git_path)}\"")
                    print(f" HEAD         = \"{head_tagging}\"")
                    print(Colors.RESET)

                    if recipe_CCOS_VERSION == '':
                        new_tag = get_user_input("Enter \'existing tag(with \"version/\")\' or \'HEAD\'(auto-tagging if no tag on HEAD)", 'HEAD', split=False)
                    else :
                        new_tag = recipe_CCOS_VERSION

                    if new_tag == 'HEAD':
                        if len(head_tagging) == 0:
                            new_tag = auto_version_up(src_git_path)
                            if new_tag is None:
                                print()
                                raise Exception("Try later...")
                        elif len(head_tagging.split(',')) == 1:
                            new_tag = head_tagging
                            print(f'Use \"{head_tagging}\" for CCOS_VERSION')
                        else:
                            print()
                            raise Exception(f'\'HEAD\' has serveral tags. You should use specific tag.')

                    if new_tag == ccos_version:
                        print()
                        print(f" ** \"{new_tag}\" is same with CCOS_VERSION - SKIP")
                        print()
                        input("Press any key for next step...")
                        continue

                    if get_tag_hash(src_git_path, new_tag) is None:
                        print()
                        raise Exception(f" ** \"{new_tag}\" is not valid")

                    new_ccos_version = f'{new_tag.replace("version/", "")}_{get_tag_hash(src_git_path, new_tag)}'

                    update_ccos_version(recipe_path, new_ccos_version)

                    pr_message['title'] += recipe_name + '=' + new_tag.replace("version/", "") + " "
                    pr_message['description'] += get_commit_messages_between_tags(src_git_path, ccos_version, new_tag) + '\n'
                    pr_message['jiras'] += extract_jira_numbers_between_tags(src_git_path, ccos_version, new_tag) + '\n'
                    pr_message['cause'] += extract_message_between_tags(src_git_path, ccos_version, new_tag, "cause") + '\n'
                    pr_message['countermeasure'] += extract_message_between_tags(src_git_path, ccos_version, new_tag, "countermeasure") + '\n'

                    print(Colors.YELLOW)
                    print(f'=========================================================')
                    print(f"Will be committed as...")
                    print(f" Recipe: {recipe_name}.bb")
                    if original_recipe_branch_name != recipe_branch_name:
                        print(f" CCOS_GIT_BRANCH_NAME: {original_recipe_branch_name}" + Colors.GREEN + f" -> {recipe_branch_name}" + Colors.YELLOW)
                    else:
                        print(f" CCOS_GIT_BRANCH_NAME: {recipe_branch_name}")
                    if ccos_version != new_tag:
                        print(f" CCOS_VERSION = {ccos_version}" + Colors.GREEN + f" -> {new_tag}" + Colors.YELLOW)
                    else:
                        print(f" CCOS_VERSION = {new_tag}")
                    print(f'=========================================================')
                    print(Colors.RESET)
                    input("Press any key for next step...")

                if not bool(pr_message):
                    print()
                    print(f' There are no changes in {meta} - SKIP')
                    print()
                    continue

                # remove duplicated jiras
                pr_message['jiras'] = "\n".join(set(pr_message['jiras'].split("\n")))

                print()
                print()
                print()
                print()
                print(f"==============================================================================================")
                print(Colors.GREEN + f"GIT DIFF - {meta}" + Colors.RESET)
                print(f"")
                print(git_diff(meta_git_path))
                print(f"==============================================================================================")

                pr_commit_message  = pr_message['title'] + '\n'
                pr_commit_message += '\n'
                pr_commit_message += pr_message['description'] + '\n'
                pr_commit_message += '\n'
                if config.is_feature_enabled("auto_hotfix"):
                    pr_commit_message += 'Cause:' + '\n'
                    pr_commit_message += pr_message['cause'] + '\n'
                    pr_commit_message += '\n'
                    pr_commit_message += 'Countermeasure:' + '\n'
                    pr_commit_message += pr_message['countermeasure'] + '\n'
                    pr_commit_message += '\n'
                pr_commit_message += 'Jiras:' + '\n'
                pr_commit_message += pr_message['jiras'] + '\n'

                print()
                print()
                print(f"==============================================================================================")
                print(Colors.GREEN + f"COMMIT MESSAGE - {meta}" + Colors.RESET)
                print(f"")
                print(Colors.YELLOW + pr_commit_message + Colors.RESET)
                print(f"==============================================================================================")

                confirmation = input(Colors.RED + "Would you like to create a commit and push it for the PR? (y/n): " + Colors.RESET)
                if confirmation.lower() == "y":
                    pr_branch_type = "hotfix/" if config.is_feature_enabled("auto_hotfix") else ""
                    pr_branch_name = create_new_branch_and_commit_push(meta_git_path, pr_commit_message, branch, prefix=pr_branch_type)

                else:
                    print()
                    raise Exception("Try later... please check the pushed tags...")

                print('The commit has been pushed to the ' +  Colors.RED + f'{pr_branch_name}' + Colors.RESET + ' branch.')

                pr_link = None
                hotfix_link = None
                if access_token:
                    confirmation = input(Colors.RED + "Would you like to create a Pull Request? (y/n): " + Colors.RESET)
                    if confirmation.lower() == "y":
                        # return {pr_link, pr_id}
                        pr_link, pr_id = bitbucket.create_pull_request(meta, pr_branch_name, branch, pr_message['title'], pr_commit_message, access_token, reviewers)
                
                
                # if (pr_link) :
                #     confirmation = input(Colors.RED + "Would you like to write a hotfix? (y/n): " + Colors.RESET)
                #     if confirmation.lower() == "y":
                #         hotfix_comment = {
                #             "issue" : pr_message['description'],
                #             "cause" : pr_message['cause'],
                #             "countermeasure" : pr_message['countermeasure'],
                #             "author" : author,
                #             "link" : pr_link
                #         }
                #         print(hotfix_comment)
                #         hotfix_link = my_confluence.add_comment_to_hotfix_page_by_branch_name(branch, hotfix_comment)

                pr_state.append({
                    'branch': branch,
                    'PR': True if pr_link else False,
                    'PR_URL': pr_link if pr_link else '',
                    'Hotfix': "Failed",
                    'Hotfix_URL': hotfix_link if hotfix_link else ''
                })
                    
                input("Pushing completed. press any key for next step...")
                
        if config.is_feature_enabled("auto_hotfix"):
            print(Colors.GREEN)
            print("\nCreating hotfix, please wait...", end='', flush=True)
            for _ in range(10):
                print('.', end='', flush=True)
                time.sleep(0.5)
            print()
            print(Colors.RESET)

            for pr in pr_state:
                try :
                    hotfix_page_url = my_confluence.get_hotfix_link_for_branch(pr['branch'])
                    auto_hotfix_page_url = my_confluence.get_auto_hotfix_link_for_branch(pr['branch'])
                    auto_hotfix_page_id = my_confluence.get_auto_hotfix_page_id_by_branch_name(pr['branch'])

                    pr["Hotfix_URL"] = hotfix_page_url if hotfix_page_url else "Can not hotfix page"

                    if pr['PR_URL'] != '' and auto_hotfix_page_url and config.is_feature_enabled("auto_hotfix"):
                        if my_confluence.check_pr_link_exists(auto_hotfix_page_id, pr['PR_URL']):
                            pr["Hotfix"] = "Success"
                            pr["Hotfix_URL"] = auto_hotfix_page_url if auto_hotfix_page_url else "Can not auto hotfix page"
                except Exception as e:
                    print(f"Error is occured: {str(e)}")

        print_pr_state(pr_state)

    except Exception as e:
        print(f"Error is occured: {str(e)}")

    finally:
        try:
            print()
            print()
            input("DONE - press any key for terminating...")
            print()
        except Exception as e:
            pass
        finally:
            if os.path.exists(temp_dir):
                print()
                print()
                print(f'* rmdir - {temp_dir}')
                print()
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    pass
            else:
                pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-r", "--repo", default="repo.json", help="File name for repository")
    parser.add_argument("-s", "--show", action='store_true', help="Display the latest versions of the recipes.")
    args = parser.parse_args()

    main(args)