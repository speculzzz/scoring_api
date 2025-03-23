import pytest
from pymemcache.exceptions import MemcacheError
from tenacity import RetryError
from store import MAX_RETRIES, MemcachedWrapper


# Test successful set operation
def test_set_success(mock_memcached):
    wrapper = MemcachedWrapper()
    wrapper.set("key1", 3.14)

    # Verify that set was called with the correct arguments
    mock_memcached.set.assert_called_once_with("key1", "3.14", expire=0)

# Test successful get operation
def test_get_success(mock_memcached):
    wrapper = MemcachedWrapper()
    mock_memcached.get.return_value = b"3.14"  # Memcached returns bytes

    result = wrapper.get("key1")

    # Verify that get was called and returned the correct value
    mock_memcached.get.assert_called_once_with("key1")
    assert result == 3.14

# Test retry on connection error (get)
def test_get_retry_on_connection_error(mock_memcached):
    wrapper = MemcachedWrapper()

    # Simulate connection errors twice, then success
    mock_memcached.get.side_effect = [MemcacheError, MemcacheError, b"3.14"]

    result = wrapper.get("key1")

    # Verify that get was called 3 times and returned the correct value
    assert mock_memcached.get.call_count == 3
    assert result == 3.14

# Test retry exhaustion (set)
def test_set_retry_exhausted(mock_memcached):
    wrapper = MemcachedWrapper()

    # Simulate continuous connection errors
    mock_memcached.set.side_effect = MemcacheError

    # Expect RetryError to be raised
    with pytest.raises(RetryError):
        wrapper.set("key1", 3.14)

    # Verify that set was called MAX_RETRIES times
    assert mock_memcached.set.call_count == MAX_RETRIES

# Test retry exhaustion (get)
def test_get_retry_exhausted(mock_memcached):
    wrapper = MemcachedWrapper()

    # Simulate continuous connection errors
    mock_memcached.get.side_effect = MemcacheError

    # Expect RetryError to be raised
    with pytest.raises(RetryError):
        wrapper.get("key1")

    # Verify that get was called MAX_RETRIES times
    assert mock_memcached.get.call_count == MAX_RETRIES
