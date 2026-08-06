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
    bronze_dir: str

    def __init__(self):
        object.__setattr__(self, "postgres_host", self._get_env("POSTGRES_HOST", "localhost"))
        object.__setattr__(self, "postgres_port", int(self._get_env("POSTGRES_PORT", 5432)))
        object.__setattr__(self, "postgres_db", self._get_env("POSTGRES_DB", "shopstream"))
        object.__setattr__(self, "postgres_user", self._get_env("POSTGRES_USER", "shopstream"))
        object.__setattr__(self, "postgres_password", self._get_env("POSTGRES_PASSWORD", "shopstream123"))
        
        # MinIO (S3-compatible) configs
        object.__setattr__(self, "minio_endpoint", self._get_env("MINIO_ENDPOINT", "localhost:9000"))
        object.__setattr__(self, "minio_access_key", self._get_env("MINIO_ACCESS_KEY", "admin"))
        object.__setattr__(self, "minio_secret_key", self._get_env("MINIO_SECRET_KEY", "admin12345"))
        object.__setattr__(self, "minio_bucket", self._get_env("MINIO_BUCKET", "shopstream-lake"))
        
        # Local dir for data lake bronze layer (legacy/fallback)
        bronze = Path(__file__).resolve().parents[1] / "data" / "bronze"
        bronze.mkdir(parents=True, exist_ok=True)
        object.__setattr__(self, "bronze_dir", str(bronze))

    @staticmethod
    def _get_env(key: str, default: str) -> str:
        from os import getenv
        value = getenv(key)
        if value is None:
            return default
        return value

settings = Settings()
