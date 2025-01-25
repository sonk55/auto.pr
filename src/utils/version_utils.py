from utils.logger import setup_logger

logger = setup_logger(__name__)

def generate_next_version(current_version: str) -> str:
    """현재 버전을 기반으로 다음 버전을 생성"""
    try:
        # version/ 접두사 제거
        version = current_version.replace('version/', '')
        
        # 접미사가 있는 경우 (예: 0.0.1-cinemoplayer)
        if '-' in version:
            version_num, suffix = version.split('-', 1)
            parts = version_num.split('.')
            
            # 마지막 숫자 증가
            if len(parts) > 0:
                parts[-1] = str(int(parts[-1]) + 1)
                
            return f"version/{'.' .join(parts)}-{suffix}"
            
        # 일반 버전 (예: 0.0.1)
        else:
            parts = version.split('.')
            
            # 마지막 숫자 증가
            if len(parts) > 0:
                parts[-1] = str(int(parts[-1]) + 1)
                
            return f"version/{'.' .join(parts)}"
            
    except Exception as e:
        logger.error(f"Failed to generate next version for {current_version}: {e}")
        return current_version 