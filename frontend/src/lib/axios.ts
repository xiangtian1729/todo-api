import axios, { AxiosError } from 'axios';
import { getToken, setToken } from './token-store';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      setToken(null);
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

/** Type-safe helper to extract API error messages */
export function getApiErrorMessage(error: unknown, fallback = 'An error occurred'): string {
  if (error instanceof AxiosError) {
    return error.response?.data?.detail || fallback;
  }
  return fallback;
}

export default api;
