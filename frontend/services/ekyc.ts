/**
 * E-KYC Service
 * 
 * API service for e-KYC verification including document upload,
 * selfie capture, verification processing, and session management.
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Configure axios interceptor for JWT
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[AUTH] Token attached to request');
    } else {
      console.warn('[AUTH] No token found in localStorage');
    }
    return config;
  },
  (error) => {
    console.error('[AUTH] Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Configure axios response interceptor for 401 handling
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('[AUTH] 401 Unauthorized - clearing token and redirecting');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login?error=session_expired';
      }
    }
    console.error('[AUTH] Request failed:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ===== Types =====

export interface EkycSession {
  id: string;
  user_id: string;
  session_id: string;
  status: string;
  decision: string;
  document_score?: number;
  face_match_score?: number;
  liveness_score?: number;
  overall_score?: number;
  rejection_reason?: string;
  review_notes?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  documents: EkycDocument[];
  results: EkycResult[];
}

export interface EkycDocument {
  id: string;
  session_id: string;
  type: string;
  front_image_url: string;
  back_image_url?: string;
  document_number?: string;
  full_name?: string;
  date_of_birth?: string;
  expiry_date?: string;
  issuing_country?: string;
  is_authentic?: boolean;
  confidence_score?: number;
  tampering_detected: boolean;
  uploaded_at: string;
  processed_at?: string;
}

export interface EkycResult {
  id: string;
  session_id: string;
  verification_type: string;
  score: number;
  is_passed: boolean;
  confidence?: number;
  details?: any;
  model_version?: string;
  processed_at: string;
  processing_time?: number;
}

export interface EkycSessionHistory {
  sessions: EkycSession[];
  total: number;
  page: number;
  page_size: number;
}

// ===== API Methods =====

/**
 * Start a new e-KYC verification session
 */
export const startEkycSession = async (): Promise<EkycSession> => {
  try {
    const token = localStorage.getItem('token');
    
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/e-kyc/start`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    
    return response.data;
  } catch (error: any) {
    console.error('Failed to start e-KYC session:', error);
    throw new Error(error.response?.data?.detail || 'Failed to start e-KYC session');
  }
};

/**
 * Upload document to e-KYC session
 */
export const uploadDocument = async (
  sessionId: string,
  documentType: string,
  documentImage: File
): Promise<any> => {
  try {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('document_type', documentType);
    formData.append('document_image', documentImage);
    
    console.log('[EKYC] Uploading document:', { sessionId, documentType, fileName: documentImage.name });
    
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/e-kyc/upload-document`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    console.log('[EKYC] Document uploaded successfully:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('[EKYC] Failed to upload document:', error);
    console.error('[EKYC] Error details:', error.response?.data);
    
    if (error.response?.status === 401) {
      throw new Error('Authentication failed. Please log in again.');
    }
    
    throw new Error(
      error.response?.data?.detail ||
      error.response?.data?.message ||
      'Failed to upload document'
    );
  }
};

/**
 * Upload selfie to e-KYC session
 */
export const uploadSelfie = async (
  sessionId: string,
  selfieImage: File
): Promise<any> => {
  try {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('selfie_image', selfieImage);
    
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/e-kyc/upload-selfie`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    return response.data;
  } catch (error: any) {
    console.error('Failed to upload selfie:', error);
    throw new Error(error.response?.data?.detail || 'Failed to upload selfie');
  }
};

/**
 * Perform face matching between ID document and selfie
 */
export const matchFaces = async (
  sessionId: string,
  idImage: File,
  selfieImage: File,
  onProgress?: (status: string) => void
): Promise<any> => {
  try {
    onProgress?.('Uploading images...');
    
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('id_image', idImage);
    formData.append('selfie_image', selfieImage);
    
    console.log('[FACE-MATCH] Sending face match request:', { sessionId });
    
    onProgress?.('Detecting faces...');
    
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/e-kyc/face-match`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    console.log('[FACE-MATCH] Response:', response.data);
    
    onProgress?.('Matching...');
    
    // Check if face matching was successful
    if (!response.data.success) {
      const errorData = response.data;
      throw {
        message: errorData.error || 'Face matching failed',
        code: errorData.error_code || errorData.decision,
        details: errorData,
        isApiError: true
      };
    }
    
    onProgress?.('Completed');
    
    return response.data;
  } catch (error: any) {
    console.error('[FACE-MATCH] Failed:', error);
    
    // If already formatted error, re-throw
    if (error.isApiError) {
      throw error;
    }
    
    // Extract error details from axios error
    const errorMessage = 
      error.response?.data?.error ||
      error.response?.data?.detail ||
      error.message ||
      'Face matching failed';
    
    const errorCode = error.response?.data?.error_code || error.response?.data?.decision;
    
    throw {
      message: errorMessage,
      code: errorCode,
      details: error.response?.data
    };
  }
};

/**
 * Run e-KYC verification
 */
export const runEkycVerification = async (sessionId: string): Promise<EkycSession> => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/e-kyc/run`,
      { session_id: sessionId },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    return response.data;
  } catch (error: any) {
    console.error('Failed to run e-KYC verification:', error);
    throw new Error(error.response?.data?.detail || 'Failed to run e-KYC verification');
  }
};

/**
 * Get e-KYC session by ID
 */
export const getEkycSession = async (sessionId: string): Promise<EkycSession> => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/e-kyc/${sessionId}`
    );
    
    return response.data;
  } catch (error: any) {
    console.error('Failed to fetch e-KYC session:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch e-KYC session');
  }
};

/**
 * Get e-KYC session history for current user
 */
export const getEkycHistory = async (
  page: number = 1,
  pageSize: number = 20
): Promise<EkycSessionHistory> => {
  try {
    const token = localStorage.getItem('token');
    
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/e-kyc/history/my`,
      {
        params: { page, page_size: pageSize },
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );
    
    return response.data;
  } catch (error: any) {
    console.error('Failed to fetch e-KYC history:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch e-KYC history');
  }
};

/**
 * Convert file to base64
 */
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = (error) => reject(error);
  });
};
