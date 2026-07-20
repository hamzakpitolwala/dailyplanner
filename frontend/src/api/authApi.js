import { apiRequest } from './client';
import { AUTH_BASE } from '../utils/constants';

export const login = async (email, password) => {
  const response = await fetch(`${AUTH_BASE}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username: email, password }).toString(),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Login failed');
  return data;
};

export const register = async (email, username, password) => {
  const response = await fetch(`${AUTH_BASE}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Registration failed');
  return data;
};

export const fetchMe = async () => {
  return await apiRequest(`${AUTH_BASE}/me`);
};

export const getOAuthUrl = (provider) => {
  return `${AUTH_BASE}/${provider}/authorize`;
};
