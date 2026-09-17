import axios from 'axios';
import { router } from 'expo-router';

import { clearSession, getSessionToken } from '../auth/session';
import { API_URL } from '../config';

export const apiClient = axios.create({ baseURL: API_URL });

apiClient.interceptors.request.use((config) => {
  const token = getSessionToken();
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`);
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await clearSession();
      router.replace('/login');
    }
    return Promise.reject(error);
  },
);
