/**
 * E-KYC Service
 * 
 * API service for e-KYC verification including document upload,
 * selfie capture, verification processing, and session management.
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
  frontImage: File,
  backImage?: File
): Promise<any> => {
  try {
    const token = localStorage.getItem('token');
    
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('document_type', documentType);
    formData.append('front_image', frontImage);
    
    if (backImage) {
      formData.append('back_image', backImage);
    }
    
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/e-kyc/upload-document`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    return response.data;
  } catch (error: any) {
    console.error('Failed to upload document:', error);
    throw new Error(error.response?.data?.detail || 'Failed to upload document');
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
    const token = localStorage.getItem('token');
    
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('selfie_image', selfieImage);
    
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/e-kyc/upload-selfie`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
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
 * Run e-KYC verification
 */
export const runEkycVerification = async (sessionId: string): Promise<EkycSession> => {
  try {
    const token = localStorage.getItem('token');
    
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/e-kyc/run`,
      { session_id: sessionId },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
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
    const token = localStorage.getItem('token');
    
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/e-kyc/${sessionId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
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
