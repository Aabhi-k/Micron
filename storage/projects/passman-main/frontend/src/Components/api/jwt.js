import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

// Use the environment variable to match your api.js setup
const API_URL = import.meta.env.VITE_API_URL;

// Constants
const TOKEN_KEY = 'auth_token';

/**
 * Set Authorization header for axios requests
 */
const setAuthHeader = (token) => {
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common['Authorization'];
  }
};

/**
 * Store authentication token in localStorage and set auth header
 */
const storeToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
  setAuthHeader(token);
};

/**
 * Remove authentication token and clear auth header
 */
const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem('userId'); 
  setAuthHeader(null);
};

/**
 * Get token expiration time in seconds
 */
const getTokenExpiryTime = (token) => {
  try {
    const decoded = jwtDecode(token);
    return decoded.exp;
  } catch (error) {
    console.error('Error decoding token:', error);
    return null;
  }
};

/**
 * Check if token is expired
 */
const isTokenExpired = (token) => {
  try {
    if (!token) return true;
    
    const expiryTime = getTokenExpiryTime(token);
    if (!expiryTime) return true;
    
    // Check if token has expired
    return expiryTime < (Date.now() / 1000);
  } catch (error) {
    console.error('Error checking token expiry:', error);
    return true;
  }
};

/**
 * Get current auth token
 */
const getToken = () => localStorage.getItem(TOKEN_KEY);

/**
 * Check if user is authenticated with a valid non-expired token
 */
const isAuthenticated = () => {
  const token = getToken();
  if (!token) return false;
  
  // If token is expired, clear it and return false
  if (isTokenExpired(token)) {
    removeToken();
    return false;
  }
  
  return true;
};

/**
 * Set up axios interceptors for handling unauthorized responses
 */
const setupInterceptors = () => {
  // Remove any existing interceptors to prevent duplicates
  axios.interceptors.request.eject(axios.interceptors.request.handlers?.[0]);
  axios.interceptors.response.eject(axios.interceptors.response.handlers?.[0]);
  
  // Request interceptor - add current token to every request
  axios.interceptors.request.use(
    (config) => {
      const token = getToken();
      
      // Check if token is expired
      if (token && isTokenExpired(token)) {
        removeToken();
        // Don't add expired token to request
      } else if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      return config;
    },
    (error) => Promise.reject(error)
  );
  
  // Response interceptor - handle 401 errors
  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      // Don't redirect for login/register endpoints when they return 401
      const isAuthEndpoint = error.config.url.includes('/api/auth/login') || 
                            error.config.url.includes('/api/auth/register');
      
      if (error.response?.status === 401 && !isAuthEndpoint) {
        console.log('Session expired. Please log in again.');
        removeToken();
        window.location.href = '/login';
      }
      
      return Promise.reject(error);
    }
  );
};

/**
 * Initialize authentication when app loads
 */
const initAuth = () => {
  const token = getToken();
  
  if (token) {
    try {
      // Check if token is valid and not expired
      if (!isTokenExpired(token)) {
        setAuthHeader(token);
      } else {
        // If token is expired, remove it
        console.log('Session expired during initialization. Please log in again.');
        removeToken();
      }
    } catch (error) {
      // Handle corrupted tokens
      console.error('Invalid token found, removing it:', error);
      removeToken();
    }
  }
  
  setupInterceptors();
};

/**
 * Login user and store token
 */
const login = async (email, password) => {
  try {
    const response = await axios.post(`${API_URL}/auth/login`, { email, password });
    const { token } = response.data;
    
    if (!token) {
      throw new Error('No token received from server');
    }
    
    storeToken(token);
    return response.data;
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
};

/**
 * Log out user and remove token
 */
const logout = () => {
  // Optionally notify server about logout
  const token = getToken();
  if (token) {
    axios.post(`${API_URL}/auth/logout`, {})
      .catch(error => console.warn('Logout notification failed:', error));
  }
  
  removeToken();
  window.location.href = '/login';
};

/**
 * Get user info from token
 */
const getUserInfo = () => {
  try {
    const token = getToken();
    if (!token) return null;
    
    const decoded = jwtDecode(token);
    return {
      userId: decoded.sub || decoded.userId,
      email: decoded.email,
      username: decoded.username
    };
  } catch (error) {
    console.error('Error decoding user info from token:', error);
    return null;
  }
};

export const authService = {
  login,
  logout,
  isAuthenticated,
  initAuth,
  getToken,
  setAuthHeader,
  getUserInfo
};

export default authService;