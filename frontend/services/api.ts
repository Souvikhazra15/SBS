/**
 * API Service - Core HTTP client configuration
 * Handles all API requests with authentication and error handling
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ApiError {
    message: string
    status: number
    details?: any
}

class ApiService {
    private client: AxiosInstance

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            timeout: 60000, // Increased to 60 seconds for file uploads
            headers: {
                'Content-Type': 'application/json',
            },
        })

        // Request interceptor - attach JWT token
        this.client.interceptors.request.use(
            (config: InternalAxiosRequestConfig) => {
                console.log('[API] Request:', config.method?.toUpperCase(), config.url)
                const token = this.getToken()
                if (token && config.headers) {
                    config.headers.Authorization = `Bearer ${token}`
                }
                return config
            },
            (error) => {
                console.error('[API] Request error:', error)
                return Promise.reject(error)
            }
        )

        // Response interceptor - handle errors globally
        this.client.interceptors.response.use(
            (response) => {
                console.log('[API] Response:', response.status, response.config.url)
                return response
            },
            async (error: AxiosError) => {
                console.error('[API] Response error:', error.response?.status, error.message)

                if (error.response?.status === 401) {
                    // Token expired - only redirect if not already on login/signup page
                    this.clearToken()
                    if (typeof window !== 'undefined' &&
                        !window.location.pathname.includes('/login') &&
                        !window.location.pathname.includes('/signup')) {
                        // Don't redirect during API calls, just clear token
                        console.warn('[API] Unauthorized - token cleared. User should log in.')
                    }
                }
                return Promise.reject(this.handleError(error))
            }
        )
    }

    private getToken(): string | null {
        if (typeof window === 'undefined') return null
        return localStorage.getItem('access_token')
    }

    private clearToken(): void {
        if (typeof window === 'undefined') return
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
    }

    private handleError(error: AxiosError): ApiError {
        if (error.response) {
            return {
                message: (error.response.data as any)?.detail || 'An error occurred',
                status: error.response.status,
                details: error.response.data,
            }
        } else if (error.request) {
            return {
                message: 'No response from server. Please check your connection.',
                status: 0,
            }
        } else {
            return {
                message: error.message || 'An unexpected error occurred',
                status: -1,
            }
        }
    }

    // Auth methods
    async login(email: string, password: string) {
        const response = await this.client.post('/api/v1/auth/login', { email, password })
        if (response.data.access_token) {
            localStorage.setItem('access_token', response.data.access_token)
            if (response.data.refresh_token) {
                localStorage.setItem('refresh_token', response.data.refresh_token)
            }
        }
        return response.data
    }

    async register(data: { email: string; password: string; firstName?: string; lastName?: string }) {
        const response = await this.client.post('/api/v1/auth/register', data)
        return response.data
    }

    async logout() {
        this.clearToken()
    }

    // Generic HTTP methods
    async get<T = any>(url: string, config?: any): Promise<T> {
        const response = await this.client.get(url, config)
        return response.data
    }

    async post<T = any>(url: string, data?: any, config?: any): Promise<T> {
        const response = await this.client.post(url, data, config)
        return response.data
    }

    async put<T = any>(url: string, data?: any, config?: any): Promise<T> {
        const response = await this.client.put(url, data, config)
        return response.data
    }

    async delete<T = any>(url: string, config?: any): Promise<T> {
        const response = await this.client.delete(url, config)
        return response.data
    }

    // File upload helper
    async uploadFile(url: string, file: File, onProgress?: (progress: number) => void) {
        const formData = new FormData()
        formData.append('file', file)

        return this.client.post(url, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                if (onProgress && progressEvent.total) {
                    const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                    onProgress(progress)
                }
            },
        })
    }
}

export const apiService = new ApiService()
export type { ApiError }
