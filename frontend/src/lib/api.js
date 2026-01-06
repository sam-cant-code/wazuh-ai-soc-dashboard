import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1', // Matches your backend config
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for consistent error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error.response?.data?.detail || error.message);
    return Promise.reject(error);
  }
);