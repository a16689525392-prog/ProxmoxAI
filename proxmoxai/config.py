from functools import lru_cache
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_api_key: str
    mock_mode: bool = True
    allowed_vmids: str = "101,102,103"
    pve_api_url: str = ""
    pve_token_id: str = ""
    pve_token_secret: str = ""
    pve_verify_ssl: bool = True
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"

    @field_validator("app_api_key")
    @classmethod
    def check_key(cls, value):
        if len(value) < 12 or value.isspace():
            raise ValueError("APP_API_KEY must be at least 12 characters")
        return value

    @property
    def vmids(self):
        return {int(s.strip()) for s in self.allowed_vmids.split(",") if s.strip()}

    @model_validator(mode="after")
    def validate_runtime(self):
        if not self.vmids or any(v < 100 or v > 999999999 for v in self.vmids):
            raise ValueError("ALLOWED_VMIDS invalid")
        if not self.mock_mode:
            u = urlparse(self.pve_api_url)
            if u.scheme != "https" or not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in ("", "/"):
                raise ValueError("PVE_API_URL must be an HTTPS origin")
            if not self.pve_token_id or not self.pve_token_secret:
                raise ValueError("Real PVE token required")
        if self.openai_api_key and urlparse(self.openai_base_url).scheme != "https":
            raise ValueError("LLM API must use HTTPS")
        return self

@lru_cache
def get_settings():
    return Settings()
