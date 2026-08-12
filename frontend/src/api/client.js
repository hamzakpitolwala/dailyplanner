export const apiRequest = async (path, options = {}) => {
  const token = localStorage.getItem('token');
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const response = await fetch(path, {
    ...options,
    headers: {
      ...authHeaders,
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  });

  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (err) {
    if (!response.ok) {
      throw new Error(text || 'Request failed');
    }
    data = null;
  }

  if (!response.ok) {
    let errorMsg = 'Request failed';
    if (data?.error?.message) {
      errorMsg = data.error.message;
    } else if (data?.detail) {
      errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    }
    throw new Error(errorMsg);
  }
  return data;
};
