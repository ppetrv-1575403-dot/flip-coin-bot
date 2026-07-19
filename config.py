import os
from dataclasses import dataclass, field


class ConfigError(RuntimeError):
    """Отсутствует или некорректна обязательная переменная окружения."""


@dataclass(frozen=True)
class Settings:
    bot_token: str
    bot_username: str
    webhook_base_url: str
    webhook_path: str
    port: int
    redis_url: str
    coin_animation_id: str
    qrng_pool_size: int
    qrng_refill_threshold: int
    ad_links: list[str] = field(default_factory=list)

    @property
    def full_webhook_url(self) -> str:
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"


def _load_ad_links() -> list[str]:
    """Читает AD_LINK_1, AD_LINK_2, ... до первого отсутствующего номера."""
    links = []
    i = 1
    while True:
        link = os.environ.get(f"AD_LINK_{i}", "")
        if not link:
            break
        links.append(link)
        i += 1
    return links


def load_settings() -> Settings:
    """Единая точка чтения и валидации конфигурации. Вызывается один раз при старте."""
    token = os.environ.get("TG_BOT_TOKEN", "")
    if not token:
        raise ConfigError("TG_BOT_TOKEN не задан")

    webhook_base_url = os.environ.get("WEBHOOK_URL") or os.environ.get("RENDER_EXTERNAL_URL", "")
    if not webhook_base_url:
        raise ConfigError(
            "Не задан WEBHOOK_URL и не найдена RENDER_EXTERNAL_URL. "
            "Укажи URL вручную в переменных окружения."
        )

    return Settings(
        bot_token=token,
        bot_username=os.environ.get("BOT_USERNAME", ""),
        webhook_base_url=webhook_base_url,
        webhook_path="/webhook",
        port=int(os.environ.get("PORT", 8080)),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379"),
        coin_animation_id=os.environ.get("COIN_ANIMATION_ID", ""),
        qrng_pool_size=int(os.environ.get("QRNG_POOL_SIZE", 500)),
        qrng_refill_threshold=int(os.environ.get("QRNG_REFILL_THRESHOLD", 100)),
        ad_links=_load_ad_links(),
    )
