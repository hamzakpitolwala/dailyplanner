const API_URL = '/fixed-blocks';

/**
 * Get Headers.
 */
const getHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
};

/**
 * Fetch Fixed Blocks.
 */
export const fetchFixedBlocks = async () => {
  const res = await fetch(API_URL, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch fixed blocks');
  return res.json();
};

/**
 * Create Fixed Block.
 */
export const createFixedBlock = async (data) => {
  const res = await fetch(API_URL, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to create fixed block');
  return res.json();
};

/**
 * Update Fixed Block.
 */
export const updateFixedBlock = async (id, data) => {
  const res = await fetch(`${API_URL}/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to update fixed block');
  return res.json();
};

/**
 * Delete Fixed Block.
 */
export const deleteFixedBlock = async (id) => {
  const res = await fetch(`${API_URL}/${id}`, {
    method: 'DELETE',
    headers: getHeaders()
  });
  if (!res.ok) throw new Error('Failed to delete fixed block');
  return true;
};
