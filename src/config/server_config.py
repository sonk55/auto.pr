import os
import json
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServerConfig:
    name: str
    url: str
    api_url: str

    @classmethod
    def get_default(cls) -> 'ServerConfig':
        return cls(
            name="Bitbucket Cloud",
            url="https://bitbucket.org",
            api_url="https://api.bitbucket.org"
        )

class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.expanduser("~/.config/bitbucket-monitor")
        self.server_config_file = os.path.join(self.config_dir, "server_config.json")
        self.credentials_file = os.path.join(self.config_dir, "credentials.json")
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.current_server: Optional[ServerConfig] = None
        self.load_server_config()

    def load_server_config(self) -> ServerConfig:
        try:
            if os.path.exists(self.server_config_file):
                with open(self.server_config_file, 'r') as f:
                    data = json.load(f)
                    self.current_server = ServerConfig(**data)
            else:
                self.current_server = ServerConfig.get_default()
                self.save_server_config()
        except Exception:
            self.current_server = ServerConfig.get_default()
        
        return self.current_server

    def save_server_config(self):
        with open(self.server_config_file, 'w') as f:
            json.dump({
                'name': self.current_server.name,
                'url': self.current_server.url,
                'api_url': self.current_server.api_url
            }, f, indent=4)

    def save_credentials(self, username: str, password: str):
        with open(self.credentials_file, 'w') as f:
            json.dump({
                'username': username,
                'password': password  # In a real app, this should be encrypted
            }, f)

    def load_credentials(self) -> tuple[str, str]:
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    data = json.load(f)
                    return data.get('username', ''), data.get('password', '')
        except Exception:
            pass
        return '', '' 