from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PullRequest:
    id: int
    title: str
    description: str
    source_branch: str
    target_branch: str
    author: str
    created_on: datetime
    updated_on: datetime
    state: str
    is_merged: bool 