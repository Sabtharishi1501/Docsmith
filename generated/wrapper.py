import requests


class StripeAPI:
    """
    A Python wrapper class for the Stripe API.
    """

    def __init__(self, api_key: str):
        """
        Initializes the StripeAPI class.

        Args:
            api_key (str): The Stripe API key.
        """
        self.base_url = "https://api.stripe.com/v1"
        self.api_key = api_key
        self.auth_header = f"Bearer {api_key}"

    def retrieve_charge(self, id: str) -> dict:
        """
        Retrieves a charge.

        Args:
            id (str): The ID of the charge.

        Returns:
            dict: The charge object.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        try:
            url = f"{self.base_url}/charges/{id}"
            headers = {"Authorization": self.auth_header}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to retrieve charge: {e}")


# Usage example:
# stripe_api = StripeAPI("your_stripe_api_key")
# charge = stripe_api.retrieve_charge("charge_id")
