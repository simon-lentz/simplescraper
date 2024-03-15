import pytest
from unittest.mock import patch
from docker.errors import APIError


# Test functions
def test_create_container_success(mock_docker_manager, mock_container, mock_connection_data):  # noqa:E501
    docker_manager = mock_docker_manager
    with patch('docker.models.containers.ContainerCollection.run') as mock_run:
        mock_run.return_value = mock_container
        container = docker_manager.create_container(mock_connection_data)
        assert container is not None
        mock_run.assert_called_once()


def test_create_container_api_error(mock_docker_manager, mock_connection_data):  # noqa:E501
    docker_manager = mock_docker_manager
    with patch('docker.models.containers.ContainerCollection.run', side_effect=APIError("Docker API error")):  # noqa:E501
        with pytest.raises(APIError):
            docker_manager.create_container(mock_connection_data)


def test_cleanup_removes_container(mock_docker_manager, mock_container):  # noqa:E501
    docker_manager = mock_docker_manager
    docker_manager.cleanup(mock_container)
    mock_container.stop.assert_called_once()
    mock_container.remove.assert_called_once()


def test_cleanup_does_not_remove_container_when_flag_is_false(mock_docker_manager, mock_container):  # noqa:E501
    docker_manager = mock_docker_manager
    docker_manager.remove_on_cleanup = False
    docker_manager.cleanup(mock_container)
    mock_container.stop.assert_called_once()
    mock_container.remove.assert_not_called()


def test_cleanup_handles_api_error_on_stop(mock_docker_manager, mock_container):  # noqa:E501
    docker_manager = mock_docker_manager
    mock_container.stop.side_effect = APIError("Docker API error on stop")
    with pytest.raises(APIError):
        docker_manager.cleanup(mock_container)
    mock_container.stop.assert_called_once()
    mock_container.remove.assert_not_called()


def test_cleanup_handles_api_error_on_remove(mock_docker_manager, mock_container):  # noqa:E501
    docker_manager = mock_docker_manager
    mock_container.remove.side_effect = APIError("Docker API error on remove")
    with pytest.raises(APIError):
        docker_manager.cleanup(mock_container)
    mock_container.stop.assert_called_once()
    mock_container.remove.assert_called_once()
