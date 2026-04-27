import { getCookie } from '../utils/csrf';

// Helper to get CSRF token
const getCsrfToken = () => getCookie('csrftoken');

// Custom fetch wrapper to handle CSRF and JSON
const apiFetch = async (url, options = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...options.headers,
  };

  // Add CSRF token for non-GET requests
  if (options.method && options.method.toUpperCase() !== 'GET') {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || errorData.detail || 'API request failed');
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
};

export const authApi = {
  login: (credentials) => apiFetch('/api/auth/login/', {
    method: 'POST',
    body: JSON.stringify(credentials)
  }),
  
  signup: (userData) => apiFetch('/api/auth/signup/', {
    method: 'POST',
    body: JSON.stringify(userData)
  }),
  
  logout: () => apiFetch('/api/auth/logout/', {
    method: 'POST'
  }),
  
  getCurrentUser: () => apiFetch('/api/auth/user/', {
    method: 'GET'
  }),
};

export default apiFetch;
