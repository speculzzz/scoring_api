import pytest
from scoring import get_score, get_interests


########################
# get_score() tests

# Test successful data retrieval
def test_get_score_success(mock_server_store, mock_memcached, mock_uid_hash):
    # Simulate data from Memcached
    mock_memcached.get.return_value = b"3.14"
    # Simulate uid
    mock_uid_hash.hexdigest.return_value = "a1b2c3d4e5f6"

    result = get_score(mock_server_store)

    # Verify that store.get was called with the correct key
    mock_memcached.get.assert_called_once_with("uid:a1b2c3d4e5f6")
    # Verify that store.set was not called
    mock_memcached.set.assert_not_called()
    # Verify that the function returned the correct data
    assert result == 3.14

# Test successful for no data in Memcached
@pytest.mark.parametrize(
    "phone, email, birthday, gender, first_name, last_name, score",
    [
        (None, None, None, None, None, None, 0.0),
        ("79271234567", None, None, None, None, None, 1.5),
        ("79271234567", "my@email.ru", None, None, None, None, 3.0),
        ("79271234567", "my@email.ru", "10.10.2010", None, None, None, 3.0),
        ("79271234567", "my@email.ru", "10.10.2010", 1, None, None, 4.5),
        ("79271234567", "my@email.ru", "10.10.2010", 1, "James", None, 4.5),
        ("79271234567", "my@email.ru", "10.10.2010", 1, "James", "Bond", 5.0),
    ]
)
def test_get_score_no_data_success(mock_server_store, mock_memcached, mock_uid_hash,
                                   phone, email, birthday, gender, first_name, last_name, score):
    # Simulate data from Memcached
    mock_memcached.get.return_value = None
    # Simulate uid
    mock_uid_hash.hexdigest.return_value = "a1b2c3d4e5f6"

    result = get_score(mock_server_store, phone, email, birthday, gender, first_name, last_name)

    # Verify that store.set was called with the correct key
    mock_memcached.set.assert_called_once_with("uid:a1b2c3d4e5f6", str(score), expire=3600)
    # Verify that the function returned the correct data
    assert result == score

# Test successful when Memcached is not available
def test_get_score_memcached_error_success(mock_server_store, mock_memcached, mock_uid_hash):
    # Simulate an error when calling store.get/set
    mock_memcached.get.side_effect = Exception("MemcacheError")
    mock_memcached.set.side_effect = Exception("MemcacheError")
    # Simulate uid
    mock_uid_hash.hexdigest.return_value = "a1b2c3d4e5f6"

    result = get_score(mock_server_store)

    # Verify that store.get/set were called with the correct key
    mock_memcached.get.assert_called_once_with("uid:a1b2c3d4e5f6")
    mock_memcached.set.assert_called_once_with("uid:a1b2c3d4e5f6", "0.0", expire=3600)
    # Verify that the function returned the correct data
    assert result == 0.0


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
