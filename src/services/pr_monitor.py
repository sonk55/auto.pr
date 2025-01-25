from typing import List, Callable
import time
import threading
from bitbucket.api import BitbucketAPI
from models.pull_request import PullRequest

class PRMonitor:
    def __init__(self, bitbucket_api: BitbucketAPI):
        self.api = bitbucket_api
        self.callbacks: List[Callable[[List[PullRequest]], None]] = []
        self.is_monitoring = False
        self.monitor_thread = None

    def start_monitoring(self, interval_seconds: int = 60):
        """PR 모니터링을 시작합니다."""
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval_seconds,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """PR 모니터링을 중지합니다."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_loop(self, interval_seconds: int):
        while self.is_monitoring:
            try:
                prs = self.api.get_pull_requests()
                for callback in self.callbacks:
                    callback(prs)
            except Exception as e:
                print(f"모니터링 중 오류 발생: {e}")
            time.sleep(interval_seconds) 