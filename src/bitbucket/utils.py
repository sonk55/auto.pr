def parse_info_from_diff(diff: str):
    # {
    #     "file": "meta-ccos-avn/audiostreamingmanager/audiostreamingmanager.bb", 
    #     "version": "version/0.0.1",
    #     "commit": "7683c0f6dd80cb9df933764771654020712a5369"
    # }
    
    print(diff)
    
    info = []
    
    # diff 문자열을 줄 단위로 분리
    lines = diff.split('\n')
    
    for line in lines:
        if line.startswith('+CCOS_VERSION'):
            # CCOS_VERSION = "0.0.1_7683c0f6dd80cb9df933764771654020712a5369" 형식에서 정보 추출
            version_str = line.split('"')[1]
            version, commit = version_str.split('_')
            
            # 이전 줄에서 파일 경로 찾기
            file_path = None
            for prev_line in reversed(lines[:lines.index(line)]):
                if prev_line.startswith('+++ b/'):
                    file_path = prev_line[6:]
                    break
                    
            if file_path:
                info.append({
                    "file": file_path,
                    "version": f"version/{version}",
                    "commit": commit
                })
        
    return info
