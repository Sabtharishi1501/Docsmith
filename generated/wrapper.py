import requests


class StripeAPI:
    def __init__(self, api_key: str):
        """
        Initialize the Stripe API wrapper.

        Args:
        api_key (str): The Stripe API key.
        """
        self.base_url = "https://api.stripe.com"
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def create_charge(self, amount: int, currency: str, customer: str) -> dict:
        """
        Create a new charge.

        Args:
        amount (int): The amount to charge.
        currency (str): The currency of the charge.
        customer (str): The ID of the customer to charge.

        Returns:
        dict: The charge object.

        Raises:
        requests.exceptions.RequestException: If the request fails.
        """
        try:
            params = {"amount": amount, "currency": currency, "customer": customer}
            response = requests.post(
                f"{self.base_url}/v1/charges", headers=self.headers, data=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None


# Usage example:
# stripe_api = StripeAPI("your_stripe_api_key")
# charge = stripe_api.create_charge(1000, "usd", "cus_123456789")
# print(charge)
