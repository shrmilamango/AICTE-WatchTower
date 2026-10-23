const BASE_URL = '/api/v1';

export class ApiError extends Error {
  constructor(status, code, message, details = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('watchtower_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  // Remove Content-Type for FormData uploads
  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 204) {
    return null;
  }

  // Handle blob responses (e.g. CSV exports, file downloads)
  const contentType = response.headers.get('content-type');
  if (contentType && (contentType.includes('text/csv') || contentType.includes('application/octet-stream') || contentType.includes('application/pdf'))) {
    if (!response.ok) {
      throw new ApiError(response.status, 'DOWNLOAD_FAILED', 'Failed to download file');
    }
    return response.blob();
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorInfo = data.error || {};
    throw new ApiError(
      response.status,
      errorInfo.code || 'UNKNOWN_ERROR',
      errorInfo.message || 'An unexpected error occurred',
      errorInfo.details || {}
    );
  }

  return data;
}

export const api = {
  get: (url) => request(url, { method: 'GET' }),
  post: (url, body) => request(url, { method: 'POST', body: JSON.stringify(body) }),
  put: (url, body) => request(url, { method: 'PUT', body: JSON.stringify(body) }),
  patch: (url, body) => request(url, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (url) => request(url, { method: 'DELETE' }),
  upload: (url, formData) => request(url, { method: 'POST', body: formData }),
};
