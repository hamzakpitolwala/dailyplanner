import { apiRequest } from './client';

export const userApi = {
  fetchUserProfile: async () => {
    return await apiRequest('/users/me/profile');
  },

  updateUserProfile: async (data) => {
    return await apiRequest('/users/me/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
};
