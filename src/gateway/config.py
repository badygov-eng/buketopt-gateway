"""Настройки приложения (pydantic-settings)."""

from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация шлюза. Секреты: `~/.secrets/buketopt-gateway/` или env."""

    model_config = SettingsConfigDict(
        env_prefix="GATEWAY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_keys: str = Field(
        default="",
        description="Список допустимых X-Api-Key через запятую",
    )
    bitrix_base_url: HttpUrl = Field(
        default=HttpUrl("https://ai-test.buketopt.ru"),
        description="Базовый URL сайта Битрикса (без завершающего /)",
    )
    bitrix_http_timeout_sec: float = Field(default=45.0, ge=1.0, le=120.0)
    bitrix_verify_tls: bool = Field(
        default=False,
        description="False для стенда с самоподписанным TLS",
    )
    default_payment_method_id: int = Field(
        default=15,
        description="ID ПС по умолчанию (стенд: Сбер=15)",
    )
    use_simple_order: bool = Field(
        default=False,
        description="Передавать simple_order=1 (ослабленная валидация Bitrix, high-risk)",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
