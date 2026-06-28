class StripeAPI {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'https://api.stripe.com/v1';
    this.headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/x-www-form-urlencoded'
    };
  }

  async createInvoicePreview(invoiceData) {
    try {
      const response = await fetch(`${this.baseUrl}/invoices`, {
        method: 'POST',
        headers: this.headers,
        body: new URLSearchParams(invoiceData).toString()
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      throw new Error(`Error creating invoice preview: ${error.message}`);
    }
  }

  async createCustomer(customerData) {
    try {
      const response = await fetch(`${this.baseUrl}/customers`, {
        method: 'POST',
        headers: this.headers,
        body: new URLSearchParams(customerData).toString()
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      throw new Error(`Error creating customer: ${error.message}`);
    }
  }
}

const stripeApi = new StripeAPI('YOUR_API_KEY');
stripeApi.createInvoicePreview({}).then((invoicePreview) => console.log(invoicePreview)).catch((error) => console.error(error));
stripeApi.createCustomer({ name: 'John Doe', email: 'john@example.com' }).then((customer) => console.log(customer)).catch((error) => console.error(error));