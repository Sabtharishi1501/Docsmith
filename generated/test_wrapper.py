import axios from 'axios';
import StripeAPI from './StripeAPI';

jest.mock('axios');

describe('StripeAPI', () => {
  const apiKey = 'YOUR_API_KEY';
  const baseUrl = 'https://api.stripe.com/v1';
  const headers = {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/x-www-form-urlencoded'
  };

  let stripeApi;

  beforeEach(() => {
    stripeApi = new StripeAPI(apiKey);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('createInvoicePreview', () => {
    it('should create invoice preview successfully', async () => {
      const invoiceData = { amount: 100, currency: 'usd' };
      const response = { id: 'inv_123', amount: 100, currency: 'usd' };
      axios.post.mockResolvedValue({ status: 200, data: response });

      const result = await stripeApi.createInvoicePreview(invoiceData);
      expect(result).toEqual(response);
      expect(axios.post).toHaveBeenCalledTimes(1);
      expect(axios.post).toHaveBeenCalledWith(`${baseUrl}/invoices`, expect.any(String), { headers });
    });

    it('should throw error for invalid input', async () => {
      const invoiceData = null;
      await expect(stripeApi.createInvoicePreview(invoiceData)).rejects.toThrowError('Error creating invoice preview: Cannot read properties of null (reading \'toString\')');
    });

    it('should throw error for HTTP error', async () => {
      const invoiceData = { amount: 100, currency: 'usd' };
      axios.post.mockRejectedValue({ response: { status: 401, statusText: 'Unauthorized' } });

      await expect(stripeApi.createInvoicePreview(invoiceData)).rejects.toThrowError('Error creating invoice preview: HTTP error! status: 401');
    });

    it('should throw error for server error', async () => {
      const invoiceData = { amount: 100, currency: 'usd' };
      axios.post.mockRejectedValue(new Error('Server error'));

      await expect(stripeApi.createInvoicePreview(invoiceData)).rejects.toThrowError('Error creating invoice preview: Server error');
    });
  });

  describe('createCustomer', () => {
    it('should create customer successfully', async () => {
      const customerData = { name: 'John Doe', email: 'john@example.com' };
      const response = { id: 'cus_123', name: 'John Doe', email: 'john@example.com' };
      axios.post.mockResolvedValue({ status: 200, data: response });

      const result = await stripeApi.createCustomer(customerData);
      expect(result).toEqual(response);
      expect(axios.post).toHaveBeenCalledTimes(1);
      expect(axios.post).toHaveBeenCalledWith(`${baseUrl}/customers`, expect.any(String), { headers });
    });

    it('should throw error for invalid input', async () => {
      const customerData = null;
      await expect(stripeApi.createCustomer(customerData)).rejects.toThrowError('Error creating customer: Cannot read properties of null (reading \'toString\')');
    });

    it('should throw error for HTTP error', async () => {
      const customerData = { name: 'John Doe', email: 'john@example.com' };
      axios.post.mockRejectedValue({ response: { status: 404, statusText: 'Not Found' } });

      await expect(stripeApi.createCustomer(customerData)).rejects.toThrowError('Error creating customer: HTTP error! status: 404');
    });

    it('should throw error for server error', async () => {
      const customerData = { name: 'John Doe', email: 'john@example.com' };
      axios.post.mockRejectedValue(new Error('Server error'));

      await expect(stripeApi.createCustomer(customerData)).rejects.toThrowError('Error creating customer: Server error');
    });
  });
});