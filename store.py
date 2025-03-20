import json
import redis
from abc import ABC, abstractmethod
from pymemcache.client.base import Client
from pymemcache.exceptions import MemcacheError
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from typing import Optional

MAX_RETRIES = 4

DEFAULT_HOSTNAME = 'localhost'
DEFAULT_REDIS_PORT = 6379
DEFAULT_MEMCACHED_PORT = 11211
DEFAULT_TIMEOUT = 5


class RedisWrapper:
    redis_retryer = retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(redis.ConnectionError)
    )

    def __init__(self, host: str = DEFAULT_HOSTNAME, port: int = DEFAULT_REDIS_PORT,
                 db: int = 0, timeout: int = DEFAULT_TIMEOUT):
        self._client = redis.Redis(
            host=host, port=port, db=db,
            socket_timeout=timeout,
            socket_connect_timeout=timeout,
            retry_on_timeout=True,
            socket_keepalive=True
        )

    @redis_retryer
    def set(self, key: str, value: list[str]) -> None:
        json_value = json.dumps(value)
        self._client.set(key, json_value)

    @redis_retryer
    def get(self, key: str) -> Optional[list[str]]:
        result = self._client.get(key)
        return json.loads(result.decode('utf-8')) if result else None

    def close(self) -> None:
        self._client.close()


class MemcachedWrapper:
    memcached_retryer = retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(MemcacheError)
    )

    def __init__(self, host: str = DEFAULT_HOSTNAME, port: int = DEFAULT_MEMCACHED_PORT,
                 timeout: int = DEFAULT_TIMEOUT):
        self._client = Client(
            (host, port),
            connect_timeout=timeout,
            timeout=timeout,
            no_delay = True
        )

    @memcached_retryer
    def set(self, key: str, value: float, expire: int = 0) -> None:
        self._client.set(key, str(value), expire=expire)

    @memcached_retryer
    def get(self, key: str) -> Optional[float]:
        result = self._client.get(key)
        return float(result.decode('utf-8')) if result else None

    def close(self) -> None:
        self._client.close()


class Store(ABC):
    @abstractmethod
    def cache_set(self, key: str, value: float, expire: int = 0) -> None:
        pass

    @abstractmethod
    def cache_get(self, key: str) -> Optional[float]:
        pass

    @abstractmethod
    def set(self, key: str, value: list[str]) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[list[str]]:
        pass


class ServerStore(Store):
    def __init__(self, server: str = DEFAULT_HOSTNAME, memcache_port: int = DEFAULT_MEMCACHED_PORT,
                 redis_port: int = DEFAULT_REDIS_PORT, timeout: int = DEFAULT_TIMEOUT, logger=None):
        self.memcache_client = MemcachedWrapper(host=server, port=memcache_port, timeout=timeout)
        self.redis_client = RedisWrapper(host=server, port=redis_port,timeout=timeout)
        self.logger = logger

    def cache_set(self, key: str, value: float, expire: int = 0) -> None:
        if self.logger is not None:
            self.logger.info(f"Set to memcached: '{key}' -> {value}")
        self.memcache_client.set(key, value, expire=expire)

    def cache_get(self, key: str) -> Optional[float]:
        if self.logger is not None:
            self.logger.info(f"Get from memcached: '{key}'")
        return self.memcache_client.get(key)

    def set(self, key: str, value: list[str]) -> None:
        if self.logger is not None:
            self.logger.info(f"Set to redis: '{key}' -> {value}")
        self.redis_client.set(key, value)

    def get(self, key: str) -> Optional[list[str]]:
        if self.logger is not None:
            self.logger.info(f"Get from redis: '{key}'")
        return self.redis_client.get(key)

    def close(self) -> None:
        self.memcache_client.close()
        self.redis_client.close()


if __name__ == "__main__":
    from tests.conftest import PrintLogger

    redis_wrapper = RedisWrapper()
    memcached_wrapper = MemcachedWrapper()
    store = ServerStore(logger=PrintLogger())

    try:
        redis_wrapper.set('key1', ['str11', 'str12'])
        redis_wrapper.set('key2', ['str21', 'str22'])
        memcached_wrapper.set('key1', 3.14)
        memcached_wrapper.set('key2', 2.71)

        print(redis_wrapper.get('key1'))  # Output: ['str11', 'str12']
        print(redis_wrapper.get('key2'))  # Output: ['str21', 'str22']
        print(redis_wrapper.get('key3'))  # Output: None (key not found)
        print(memcached_wrapper.get('key1'))  # Output: 3.14
        print(memcached_wrapper.get('key2'))  # Output: 2.71
        print(memcached_wrapper.get('key3'))  # Output: None (key not found)

        store.set('key1', ['str11', 'str12'])
        store.cache_set('key1', 3.14)
        print(store.get('key1'))  # Output: ['str11', 'str12']
        print(store.cache_get('key1'))  # Output: 3.14

    finally:
        redis_wrapper.close()
        memcached_wrapper.close()

        store.close()
