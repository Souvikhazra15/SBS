/**
 * Auth Service
 * 
 * Handles user authentication, token management, and session validation
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  role: string;
  status: string;
  createdAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

/**
 * Validate current user session
 * Calls /auth/me to verify JWT token validity
 */
export async function validateSession(): Promise<User | null> {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      console.log('[AUTH] No token found');
      return null;
    }

    console.log('[AUTH] Validating session with /auth/me');
    const response = await axios.get(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log('[AUTH] Session valid:', response.data.email);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 401) {
      console.error('[AUTH] Session invalid - token expired or invalid');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    } else {
      console.error('[AUTH] Session validation error:', error.message);
    }
    return null;
  }
}

/**
 * Login user with email and password
 */
export async function login(credentials: LoginCredentials): Promise<AuthTokens> {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, credentials);
    const tokens = response.data;

    // Store token
    localStorage.setItem('token', tokens.access_token);
    if (tokens.refresh_token) {
      localStorage.setItem('refresh_token', tokens.refresh_token);
    }

    // Fetch and store user data
    const user = await validateSession();
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    }

    console.log('[AUTH] Login successful');
    return tokens;
  } catch (error: any) {
    console.error('[AUTH] Login failed:', error.response?.data || error.message);
    throw new Error(error.response?.data?.detail || 'Login failed');
  }
}

/**
 * Register new user
 */
export async function register(data: RegisterData): Promise<AuthTokens> {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/v1/auth/register`, data);
    const tokens = response.data;

    // Store token
    localStorage.setItem('token', tokens.access_token);
    if (tokens.refresh_token) {
      localStorage.setItem('refresh_token', tokens.refresh_token);
    }

    // Fetch and store user data
    const user = await validateSession();
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    }

    console.log('[AUTH] Registration successful');
    return tokens;
  } catch (error: any) {
    console.error('[AUTH] Registration failed:', error.response?.data || error.message);
    throw new Error(error.response?.data?.detail || 'Registration failed');
  }
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  try {
    const token = localStorage.getItem('token');
    if (token) {
      await axios.post(`${API_BASE_URL}/api/v1/auth/logout`, {}, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    }
  } catch (error) {
    console.error('[AUTH] Logout request failed:', error);
  } finally {
    // Clear local storage regardless
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    console.log('[AUTH] Logged out');
  }
}

/**
 * Refresh access token
 */
export async function refreshAccessToken(): Promise<string | null> {
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return null;
    }

    const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
      refresh_token: refreshToken,
    });

    const tokens = response.data;
    localStorage.setItem('token', tokens.access_token);
    if (tokens.refresh_token) {
      localStorage.setItem('refresh_token', tokens.refresh_token);
    }

    console.log('[AUTH] Token refreshed');
    return tokens.access_token;
  } catch (error) {
    console.error('[AUTH] Token refresh failed:', error);
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    return null;
  }
}

/**
 * Get stored user data
 */
export function getStoredUser(): User | null {
  try {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch {
    return null;
  }
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!localStorage.getItem('token');
}
