from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

@dataclass(frozen=True)
class Settings:
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    def __init__(self):
        object.__setattr__(self, "postgres_host", self._get_env("POSTGRES_HOST", "localhost"))
        object.__setattr__(self, "postgres_port", int(self._get_env("POSTGRES_PORT", 5432)))
        object.__setattr__(self, "postgres_db", self._get_env("POSTGRES_DB", "shopstream"))
        object.__setattr__(self, "postgres_user", self._get_env("POSTGRES_USER", "shopstream"))
        object.__setattr__(self, "postgres_password", self._get_env("POSTGRES_PASSWORD", "shopstream123"))

    @staticmethod
    def _get_env(key: str, default: str) -> str:
        from os import getenv
        value = getenv(key)
        if value is None:
            return default
        return value

settings = Settings()
