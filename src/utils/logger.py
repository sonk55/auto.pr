import logging
import os
from datetime import datetime

def setup_logger(name: str) -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있다면 스킵
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 프로젝트 루트 디렉토리 찾기
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 로그 디렉토리 설정
    log_dir = os.path.join(project_root, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    today = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"{today}.log"),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 