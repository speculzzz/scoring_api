import pytest
from redis.exceptions import ConnectionError
from tenacity import RetryError
from store import MAX_RETRIES, ServerStore
from tests.conftest import mock_server_store


##### Redis part #####
# Test successful set operation
def test_set_success(mock_server_store, mock_redis):
    mock_server_store.set("key1", ["str1", "str2"])

    # Verify that set was called with the correct arguments
    mock_redis.set.assert_called_once_with("key1", '["str1", "str2"]')

# Test successful get operation
def test_get_success(mock_server_store, mock_redis):
    mock_redis.get.return_value = b'["str1", "str2"]'

    result = mock_server_store.get("key1")

    # Verify that get was called and returned the correct value
    mock_redis.get.assert_called_once_with("key1")
    assert result == ["str1", "str2"]

# Test get when the key is not found
def test_get_key_not_found(mock_server_store, mock_redis):
    mock_redis.get.return_value = None  # Key does not exist

    result = mock_server_store.get("key1")

    # Verify that get was called and returned None
    mock_redis.get.assert_called_once_with("key1")
    assert result is None

# Test retry on connection error (set)
def test_set_retry_on_connection_error(mock_server_store, mock_redis):
    # Simulate connection errors twice, then success
    mock_redis.set.side_effect = [ConnectionError, ConnectionError, None]

    mock_server_store.set("key1", ["str1", "str2"])

    # Verify that set was called 3 times
    assert mock_redis.set.call_count == 3
    mock_redis.set.assert_called_with("key1", '["str1", "str2"]')

# Test retry on connection error (get)
def test_get_retry_on_connection_error(mock_server_store, mock_redis):
    # Simulate connection errors twice, then success
    mock_redis.get.side_effect = [ConnectionError, ConnectionError, b'["str1", "str2"]']

    result = mock_server_store.get("key1")

    # Verify that get was called 3 times and returned the correct value
    assert mock_redis.get.call_count == 3
    assert result == ["str1", "str2"]

# Test retry exhaustion (set)
def test_set_retry_exhausted(mock_server_store, mock_redis):
    # Simulate continuous connection errors
    mock_redis.set.side_effect = ConnectionError

    # Expect RetryError to be raised
    with pytest.raises(RetryError):
        mock_server_store.set("key1", ["str1", "str2"])

    # Verify that set was called MAX_RETRIES times
    assert mock_redis.set.call_count == MAX_RETRIES

# Test retry exhaustion (get)
def test_get_retry_exhausted(mock_server_store, mock_redis):
    # Simulate continuous connection errors
    mock_redis.get.side_effect = ConnectionError

    # Expect RetryError to be raised
    with pytest.raises(RetryError):
        mock_server_store.get("key1")

    # Verify that get was called MAX_RETRIES times
    assert mock_redis.get.call_count == MAX_RETRIES

##### Memcached part #####
# Test successful cache_set operation
def test_cache_set_success(mock_server_store, mock_memcached):
    mock_server_store.cache_set("key1", 3.14)

    # Verify that set was called with the correct arguments
    mock_memcached.set.assert_called_once_with("key1", "3.14", expire=0)

# Test successful cache_get operation
def test_cache_get_success(mock_server_store, mock_memcached):
    mock_memcached.get.return_value = b"3.14"  # Memcached returns bytes

    result = mock_server_store.cache_get("key1")

    # Verify that get was called and returned the correct value
    mock_memcached.get.assert_called_once_with("key1")
    assert result == 3.14
