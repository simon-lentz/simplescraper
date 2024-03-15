import pytest


def test_connection_data_initialization(mock_connection_data):
    connection = mock_connection_data
    assert connection.name == mock_connection_data.name
    assert connection.port == mock_connection_data.port
    assert connection.proxy == mock_connection_data.proxy
    assert connection.container == mock_connection_data.container
    assert connection.driver == mock_connection_data.driver


def test_set_container(mock_connection_data, mock_container):
    connection = mock_connection_data
    connection.set_container(mock_container)
    assert connection.container == mock_container


def test_get_unset_container(mock_init_connection_data):
    connection = mock_init_connection_data
    with pytest.raises(ValueError):
        connection.get_container()


def test_set_driver(mock_connection_data, mock_driver):
    connection = mock_connection_data
    connection.set_driver(mock_driver)
    assert connection.driver == mock_driver


def test_get_unset_driver(mock_init_connection_data):
    connection = mock_init_connection_data
    with pytest.raises(ValueError):
        connection.get_driver()


def test_set_proxy(mock_connection_data):
    connection = mock_connection_data
    new_proxy = "127.0.0.1:8080"
    connection.set_proxy(new_proxy)
    assert connection.proxy == new_proxy


def test_get_unset_proxy(mock_init_connection_data):
    connection = mock_init_connection_data
    with pytest.raises(ValueError):
        connection.get_proxy()


def test_set_invalid_container_type(mock_connection_data):
    connection = mock_connection_data
    with pytest.raises(TypeError):
        connection.set_container("not_a_container")  # type: ignore


def test_set_invalid_driver_type(mock_connection_data):
    connection = mock_connection_data
    with pytest.raises(TypeError):
        connection.set_driver("not_a_driver")  # type:  ignore


@pytest.mark.parametrize(
    "invalid_proxy",
    ["", "256.256.256.256:8080", "123.456.78.90:8080", "1.2.3.4:abcd"]
)
def test_set_invalid_proxy_format(mock_connection_data, invalid_proxy):
    connection = mock_connection_data
    with pytest.raises(ValueError):
        connection.set_proxy(invalid_proxy)


def test_reset_proxy_to_invalid(mock_connection_data):
    connection = mock_connection_data
    valid_proxy = "127.0.0.1:8080"
    invalid_proxy = "invalid_proxy"
    # Set to valid proxy and check
    connection.set_proxy(valid_proxy)
    assert connection.get_proxy() == valid_proxy
    # Reset to invalid proxy and check
    with pytest.raises(ValueError):
        connection.set_proxy(invalid_proxy)
