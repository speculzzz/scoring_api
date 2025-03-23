import pytest
from redis import Redis
from pymemcache.client.base import Client
from store import ServerStore


# Fixture to mock Redis
@pytest.fixture
def mock_redis(mocker):
    mock_client = mocker.Mock(spec=Redis)
    mocker.patch("redis.Redis", return_value=mock_client)
    return mock_client

# Fixture to mock Memcached
@pytest.fixture
def mock_memcached(mocker):
    mock_client = mocker.Mock(spec=Client)
    mocker.patch("store.Client", return_value=mock_client)
    return mock_client


class PrintLogger:
    """Mock logger that uses print for logging."""
    def info(self, message, *args, **kwargs):
        print(f"[INFO] {self._format_message(message, *args, **kwargs)}")

    def error(self, message, *args, **kwargs):
        print(f"[ERROR] {self._format_message(message, *args, **kwargs)}")

    def exception(self, message, *args, **kwargs):
        print(f"[EXCEPTION] {self._format_message(message, *args, **kwargs)}")

    def _format_message(self, message, *args, **kwargs):
        """Formats the message with args and kwargs."""
        if args or kwargs:
            return message % args if args else message.format(**kwargs)
        return message

@pytest.fixture
def print_logger():
    return PrintLogger()


# Fixture to mock ServerStore
@pytest.fixture
def mock_server_store(mock_memcached, mock_redis, print_logger):
    return ServerStore(logger=print_logger)
