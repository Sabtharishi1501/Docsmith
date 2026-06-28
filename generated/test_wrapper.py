import pytest
import requests
from unittest.mock import patch, MagicMock
from wrapper import StripeAPI

def test_stripe_api_init():
    api_key = "test_api_key"
    stripe_api = StripeAPI(api_key)
    assert stripe_api.base_url == "https://api.stripe.com/v1"
    assert stripe_api.api_key == api_key
    assert stripe_api.auth_header == f"Bearer {api_key}"

@patch('requests.get')
def test_retrieve_charge_success(mock_get):
    api_key = "test_api_key"
    charge_id = "test_charge_id"
    response_json = {"id": charge_id, "amount": 100}
    mock_response = MagicMock()
    mock_response.json.return_value = response_json
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    stripe_api = StripeAPI(api_key)
    charge = stripe_api.retrieve_charge(charge_id)
    assert charge == response_json
    mock_get.assert_called_once_with(f"{stripe_api.base_url}/charges/{charge_id}", headers={"Authorization": stripe_api.auth_header})

@patch('requests.get')
def test_retrieve_charge_401_unauthorized(mock_get):
    api_key = "test_api_key"
    charge_id = "test_charge_id"
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
    mock_get.return_value = mock_response
    stripe_api = StripeAPI(api_key)
    with pytest.raises(Exception) as e:
        stripe_api.retrieve_charge(charge_id)
    assert str(e.value) == "Failed to retrieve charge: 401 Unauthorized"
    mock_get.assert_called_once_with(f"{stripe_api.base_url}/charges/{charge_id}", headers={"Authorization": stripe_api.auth_header})

@patch('requests.get')
def test_retrieve_charge_404_not_found(mock_get):
    api_key = "test_api_key"
    charge_id = "test_charge_id"
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_get.return_value = mock_response
    stripe_api = StripeAPI(api_key)
    with pytest.raises(Exception) as e:
        stripe_api.retrieve_charge(charge_id)
    assert str(e.value) == "Failed to retrieve charge: 404 Not Found"
    mock_get.assert_called_once_with(f"{stripe_api.base_url}/charges/{charge_id}", headers={"Authorization": stripe_api.auth_header})

@patch('requests.get')
def test_retrieve_charge_500_server_error(mock_get):
    api_key = "test_api_key"
    charge_id = "test_charge_id"
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    mock_get.return_value = mock_response
    stripe_api = StripeAPI(api_key)
    with pytest.raises(Exception) as e:
        stripe_api.retrieve_charge(charge_id)
    assert str(e.value) == "Failed to retrieve charge: 500 Server Error"
    mock_get.assert_called_once_with(f"{stripe_api.base_url}/charges/{charge_id}", headers={"Authorization": stripe_api.auth_header})

@patch('requests.get')
def test_retrieve_charge_request_exception(mock_get):
    api_key = "test_api_key"
    charge_id = "test_charge_id"
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Test Request Exception")
    mock_get.return_value = mock_response
    stripe_api = StripeAPI(api_key)
    with pytest.raises(Exception) as e:
        stripe_api.retrieve_charge(charge_id)
    assert str(e.value) == "Failed to retrieve charge: Test Request Exception"
    mock_get.assert_called_once_with(f"{stripe_api.base_url}/charges/{charge_id}", headers={"Authorization": stripe_api.auth_header})

def test_retrieve_charge_invalid_input():
    api_key = "test_api_key"
    charge_id = None
    stripe_api = StripeAPI(api_key)
    with pytest.raises(TypeError):
        stripe_api.retrieve_charge(charge_id)

def test_retrieve_charge_empty_response():
    api_key = "test_api_key"
    charge_id = "test_charge_id"
    @patch('requests.get')
    def mock_retrieve_charge(mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        stripe_api = StripeAPI(api_key)
        charge = stripe_api.retrieve_charge(charge_id)
        assert charge == {}
    mock_retrieve_charge()