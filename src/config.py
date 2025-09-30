import os
from typing import List

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения"""

    # API Keys
    alpha_vantage_api_key: str = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
    exchangerate_api_key: str = os.getenv("EXCHANGERATE_API_KEY", "")
    currency_api_key: str = os.getenv("CURRENCY_API_KEY", "")

    # Paths
    data_file_path: str = "data/operations.xlsx"
    user_settings_path: str = "user_settings.json"

    # API endpoints
    alpha_vantage_url: str = "https://www.alphavantage.co/query"
    exchangerate_url: str = "https://api.exchangerate.host/latest"
    currency_api_url: str = "https://api.currencyapi.com/v3/latest"

    # Cache settings
    cache_ttl: int = 3600  # 1 hour

    # Date formats to try
    date_formats: List[str] = [
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y.%m.%d"
    ]

    class Config:
        env_file = ".env"


settings = Settings()
