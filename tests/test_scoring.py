import pytest
from scoring import get_score, get_interests


########################
# get_score() tests

# Test successful data retrieval
def test_get_score_success(mock_server_store, mock_memcached):
    # Simulate data from Memcached
    mock_memcached.get.return_value = b"3.14"

    result = get_score(mock_server_store)

    # Verify that store.get was called with the correct key
    mock_memcached.get.assert_called_once_with("")
    # Verify that the function returned the correct data
    assert result == 3.14


########################
# get_interests() tests

# Test successful data retrieval
def test_get_interests_success(mock_server_store, mock_redis):
    # Simulate data from Redis
    mock_redis.get.return_value = b'["music", "books"]'

    result = get_interests(mock_server_store, cid=1)

    # Verify that store.get was called with the correct key
    mock_redis.get.assert_called_once_with("i:1")
    # Verify that the function returned the correct data
    assert result == ["music", "books"]

# Test for no data in Redis
def test_get_interests_no_data(mock_server_store, mock_redis):
    # Simulate no data in Redis
    mock_redis.get.return_value = None

    result = get_interests(mock_server_store, cid=1)

    # Verify that store.get was called with the correct key
    mock_redis.get.assert_called_once_with("i:1")
    # Verify that the function returned an empty list
    assert result == []

# Test for error handling
def test_get_interests_error(mock_server_store, mock_redis):
    # Simulate an error when calling store.get
    mock_redis.get.side_effect = Exception("Connection error")

    # Call the function and verify that the exception is raised
    with pytest.raises(Exception, match="Connection error"):
        get_interests(mock_server_store, cid=1)

    # Verify that store.get was called with the correct key
    mock_redis.get.assert_called_once_with("i:1")


if __name__ == "__main__":
    pytest.main()
