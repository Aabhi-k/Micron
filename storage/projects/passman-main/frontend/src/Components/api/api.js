import axios from 'axios';
import { authService } from './jwt';

const apiURL = import.meta.env.VITE_API_URL;

// Create api instance
const api = axios.create({
  baseURL: apiURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Apply auth token interceptor to our api instance
api.interceptors.request.use(
  (config) => {
    const token = authService.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 errors
// api.interceptors.response.use(
//   (response) => response,
//   (error) => {
//     if (error.response?.status === 401) {
//       console.log('Session expired. Please log in again.');
//       authService.logout(); // This will remove token and redirect to login
//     }
//     return Promise.reject(error);
//   }
// );

/**
 * Register a new user
 */
export const registerUser = async (userData) => {
  try {
    // Clear any existing auth tokens before registration
    localStorage.removeItem('token');
    
    const response = await api.post('/auth/register', userData);
    return response;
  } catch (error) {
    console.error('Error registering user:', error);
    throw error;
  }
};

/**
 * Login user with credentials
 */
export const loginUser = async (credentials) => {
  try {
    const response = await authService.login(credentials.email, credentials.password);
    return { status: 200, data: response };
  } catch (error) {
    console.error('Error logging in user:', error);
    throw error;
  }
};

/**
 * Get current user details
 */
export const getUserDetails = async () => {
  try {
    const response = await api.get('/user/details');
    return response;
  } catch (error) {
    console.error('Error fetching user details:', error);
    throw error;
  }
};

/**
 * Update user profile details
 */
export const updateUserDetails = async (userData) => {
  try {
    const response = await api.put('/user/update', userData);
    return response;
  } catch (error) {
    console.error('Error updating user details:', error);
    throw error;
  }
};

/**
 * Change user password
 */
export const changeUserPassword = async (passwordData) => {
  try {
    const response = await api.post('/user/change-password', passwordData);
    return response;
  } catch (error) {
    console.error('Error changing password:', error);
    throw error;
  }
};

/**
 * Save a new password entry
 */
export const savePassword = async (passwordData) => {
  try {
    const response = await api.post('/passwords/insert', passwordData);
    return response;
  } catch (error) {
    console.error('Error inserting password:', error);
    throw error;
  }
};

/**
 * Get all passwords for a user
 */
export const getAllPasswords = async (userId) => {
  try {
    const response = await api.get(`/passwords/getall/${userId}`);
    return response;
  } catch (error) {
    console.error('Error fetching passwords:', error);
    throw error;
  }
};

/**
 * Get details for a specific password
 */
export const getPasswordDetails = async (passwordId, userId) => {
  try {
    const response = await api.get(`/passwords/${userId}/${passwordId}`);
    return response;
  } catch (error) {
    console.error('Error fetching password details:', error);
    throw error;
  }
};

/**
 * Update an existing password
 */
export const updatePassword = async (passwordData) => {
  try {
    const response = await api.put(`/passwords/update/${passwordData.id}`, passwordData);
    return response;
  } catch (error) {
    console.error('Error updating password:', error);
    throw error;
  }
};

/**
 * Delete a password entry
 */
export const deletePassword = async (passwordId) => {
  try {
    const response = await api.delete(`/passwords/delete/${passwordId}`);
    return response;
  } catch (error) {
    console.error('Error deleting password:', error);
    throw error;
  }
};

// Initialize auth on import
authService.initAuth();

export default api;