import pytest
import requests
from unittest.mock import patch, MagicMock
from wrapper import StripeAPI

def test_init():
    api_key = "test_api_key"
    stripe_api = StripeAPI(api_key)
    assert stripe_api.base_url == "https://api.stripe.com"
    assert stripe_api.api_key == api_key
    assert stripe_api.headers["Authorization"] == f"Bearer {api_key}"
    assert stripe_api.headers["Content-Type"] == "application/x-www-form-urlencoded"

@patch("requests.post")
def test_create_charge_success(mock_post):
    api_key = "test_api_key"
    stripe_api = StripeAPI(api_key)
    amount = 1000
    currency = "usd"
    customer = "cus_123456789"
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "ch_123456789", "amount": amount, "currency": currency, "customer": customer}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    charge = stripe_api.create_charge(amount, currency, customer)
    assert charge["id"] == "ch_123456789"
    assert charge["amount"] == amount
    assert charge["currency"] == currency
    assert charge["customer"] == customer

@patch("requests.post")
def test_create_charge_401_unauthorized(mock_post):
    api_key = "test_api_key"
    stripe_api = StripeAPI(api_key)
    amount = 1000
    currency = "usd"
    customer = "cus_123456789"
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
    mock_post.return_value = mock_response
    charge = stripe_api.create_charge(amount, currency, customer)
    assert charge is None

@patch("requests.post")
def test_create_charge_404_not_found(mock_post):
    api_key = "test_api_key"
    stripe_api = StripeAPI(api_key)
    amount = 1000
    currency = "usd"
    customer = "cus_123456789"
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_post.return_value = mock_response
    charge = stripe_api.create_charge(amount, currency, customer)
    assert charge is None

@patch("requests.post")
def test_create_charge_500_server_error(mock_post):
    api_key = "test_api_key"
    stripe_api = StripeAPI(api_key)
    amount = 1000
    currency = "usd"
    customer = "cus_123456789"
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    mock_post.return_value = mock_response
    charge = stripe_api.create_charge(amount, currency, customer)
    assert charge is None

@patch("requests.post")
def test_create_charge_invalid_input(mock_post):
    api_key = "test_api_key"
    stripe_api = StripeAPI(api_key)
    amount = "invalid_amount"
    currency = "usd"
    customer = "cus_123456789"
    with pytest.raises(TypeError):
        stripe_api.create_charge(amount, currency, customer)

@patch("requests.post")
def test_create_charge_empty_response(mock_post):
    api_key = "test_api_key"
    stripe_api = StripeAPI(api_key)
    amount = 1000
    currency = "usd"
    customer = "cus_123456789"
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    charge = stripe_api.create_charge(amount, currency, customer)
    assert charge == {}

@patch("requests.post")
def test_create_charge_request_exception(mock_post):
    api_key = "test_api_key"
    stripe_api = StripeAPI(api_key)
    amount = 1000
    currency = "usd"
    customer = "cus_123456789"
    mock_post.side_effect = requests.exceptions.RequestException("Test request exception")
    charge = stripe_api.create_charge(amount, currency, customer)
    assert charge is None