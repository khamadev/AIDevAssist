import redis

from app.core.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def blacklist_token(jti: str, expires_in_seconds: int) -> None:
    redis_client.setex(f"blacklist:{jti}", expires_in_seconds, "1")


def is_token_blacklisted(jti: str) -> bool:
    return redis_client.exists(f"blacklist:{jti}") == 1
