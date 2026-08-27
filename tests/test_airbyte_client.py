"""Unit and integration tests for Airbyte programmatic client and replication orchestrator."""

from unittest.mock import MagicMock, patch

import pytest

from src.load.airbyte_client import AirbyteClient


@pytest.fixture
def client():
    return AirbyteClient(host="localhost", port=8000, username="airbyte", password="password")


def test_airbyte_client_init(client):
    """Test client initialization and URL properties."""
    assert client.host == "localhost"
    assert client.port == 8000
    assert client.base_url == "http://localhost:8000/api/v1"
    assert client.public_url == "http://localhost:8000/api/public/v1"


@patch("requests.get")
def test_airbyte_health_check_success(mock_get, client):
    """Test health check when server responds OK."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"available": true}'
    mock_resp.json.return_value = {"available": True}
    mock_get.return_value = mock_resp

    health = client.check_health()
    assert health["available"] is True
    assert health["status_code"] == 200


@patch("requests.get", side_effect=Exception("Connection refused"))
def test_airbyte_health_check_failure(mock_get, client):
    """Test health check when server is down."""
    health = client.check_health()
    assert health["available"] is False
    assert health["status_code"] is None


@patch("requests.post")
def test_get_or_create_workspace(mock_post, client):
    """Test workspace discovery."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "workspaces": [{"workspaceId": "ws-12345", "name": "StreamPulse"}]
    }
    mock_post.return_value = mock_resp

    ws_id = client.get_or_create_workspace(workspace_name="StreamPulse")
    assert ws_id == "ws-12345"


@patch("requests.post")
def test_get_or_create_source(mock_post, client):
    """Test source creation/discovery."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "sources": [{"sourceId": "src-9999", "name": "StreamPulse_Daily_2026_Catalog"}]
    }
    mock_post.return_value = mock_resp

    src_id = client.get_or_create_source(
        workspace_id="ws-12345",
        source_name="StreamPulse_Daily_2026_Catalog",
    )
    assert src_id == "src-9999"


@patch("requests.post")
def test_get_or_create_destination(mock_post, client):
    """Test destination creation/discovery."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "destinations": [{"destinationId": "dst-8888", "name": "StreamPulse_PostgreSQL_Warehouse"}]
    }
    mock_post.return_value = mock_resp

    dst_id = client.get_or_create_destination(
        workspace_id="ws-12345",
        dest_name="StreamPulse_PostgreSQL_Warehouse",
    )
    assert dst_id == "dst-8888"


@patch("requests.post")
def test_get_or_create_connection(mock_post, client):
    """Test connection creation/discovery."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "connections": [{"connectionId": "conn-7777", "name": "Daily_2026_Catalog_to_Staging"}]
    }
    mock_post.return_value = mock_resp

    conn_id = client.get_or_create_connection(
        workspace_id="ws-12345",
        source_id="src-9999",
        destination_id="dst-8888",
        connection_name="Daily_2026_Catalog_to_Staging",
    )
    assert conn_id == "conn-7777"


@patch("requests.post")
def test_trigger_sync(mock_post, client):
    """Test triggering a sync job."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "job": {"id": 101, "status": "running"}
    }
    mock_post.return_value = mock_resp

    res = client.trigger_sync(connection_id="conn-7777")
    assert res["success"] is True
    assert res["job_id"] == 101


@patch("requests.post")
def test_get_job_status(mock_post, client):
    """Test querying job status."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "job": {
            "id": 101,
            "status": "succeeded",
            "recordsSynced": 50,
            "bytesSynced": 10240,
        }
    }
    mock_post.return_value = mock_resp

    status = client.get_job_status(job_id=101)
    assert status["status"] == "succeeded"
    assert status["records_synced"] == 50
