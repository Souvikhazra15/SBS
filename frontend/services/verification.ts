/**
 * Verification Service - AI-powered identity verification APIs
 * Handles document verification, face matching, deepfake detection, and risk scoring
 */

import { apiService } from './api'

export interface VerificationSession {
  id: string
  userId: string
  documentPath?: string
  selfiePath?: string
  forgeryScore?: number
  faceMatchScore?: number
  deepfakeScore?: number
  riskScore?: number
  decision: 'PENDING' | 'APPROVED' | 'REJECTED' | 'REVIEW_REQUIRED'
  createdAt: string
  updatedAt: string
}

export interface FakeDocumentResult {
  success: boolean
  sessionId: string
  forgeryScore: number
  confidence: number
  documentType: string
  isAuthentic: boolean
  issues: string[]
  metadata: {
    tamperingDetected: boolean
    ocrExtracted: Record<string, any>
    securityFeatures: Record<string, boolean>
  }
  error?: string
}

export interface FaceMatchingResult {
  sessionId: string
  matchScore: number
  confidence: number
  isMatch: boolean
  livenessScore: number
  livenessCheck: boolean
  metadata: {
    faceDetected: boolean
    qualityScore: number
    landmarks: any[]
  }
}

export interface DeepfakeResult {
  sessionId: string
  deepfakeScore: number
  confidence: number
  isDeepfake: boolean
  manipulationType: string
  metadata: {
    frameAnalysis: any[]
    audioAnalysis: any
    inconsistencies: string[]
  }
}

export interface RiskScoringResult {
  sessionId: string
  riskScore: number
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  decision: 'APPROVED' | 'REJECTED' | 'REVIEW_REQUIRED'
  factors: {
    name: string
    weight: number
    score: number
    description: string
  }[]
  recommendation: string
}

class VerificationService {
  /**
   * Upload a file for verification
   */
  async uploadFile(file: File, fileType: 'document' | 'selfie' | 'video', onProgress?: (progress: number) => void) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_type', fileType)

    return apiService.uploadFile('/api/v1/upload', file, onProgress)
  }

  /**
   * Create a new verification session
   */
  async createSession(): Promise<VerificationSession> {
    return apiService.post<VerificationSession>('/api/v1/verification/session')
  }

  /**
   * Get verification session by ID
   */
  async getSession(sessionId: string): Promise<VerificationSession> {
    return apiService.get<VerificationSession>(`/api/v1/verification/session/${sessionId}`)
  }

  /**
   * Run fake document detection with retry logic and timeout
   */
  async detectFakeDocument(
    file: File,
    sessionId?: string,
    onProgress?: (progress: number) => void
  ): Promise<FakeDocumentResult> {
    console.log('[VERIFICATION] Starting fake document detection...', { fileName: file.name, fileSize: file.size })
    
    const formData = new FormData()
    formData.append('file', file)
    if (sessionId) {
      formData.append('session_id', sessionId)
    }

    const maxRetries = 1
    let lastError: any = null

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (attempt > 0) {
          console.log(`[VERIFICATION] Retry attempt ${attempt}/${maxRetries}`)
        }

        console.log('[VERIFICATION] Sending request to backend...')
        const response = await apiService.post<FakeDocumentResult>(
          '/api/v1/fake-document/upload',
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
            timeout: 60000, // 60 second timeout
            onUploadProgress: (progressEvent: any) => {
              if (onProgress && progressEvent.total) {
                const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                console.log(`[VERIFICATION] Upload progress: ${progress}%`)
                onProgress(progress)
              }
            },
          }
        )

        console.log('[VERIFICATION] Response received:', response)
        
        // Check if response indicates success
        if (response.success === false) {
          throw new Error(response.error || 'Analysis failed')
        }

        console.log('[VERIFICATION] Analysis completed successfully')
        return response

      } catch (error: any) {
        lastError = error
        console.error(`[VERIFICATION] Attempt ${attempt + 1} failed:`, error)
        
        // Don't retry on certain errors
        if (error.response?.status === 401 || error.response?.status === 400) {
          break
        }
        
        // Wait before retrying
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
      }
    }

    // All attempts failed
    console.error('[VERIFICATION] All attempts failed:', lastError)
    throw new Error(
      lastError?.response?.data?.error || 
      lastError?.message || 
      'No response from server. Please check your connection and try again.'
    )
  }

  /**
   * Run face matching verification
   */
  async matchFace(
    documentFile: File,
    selfieFile: File,
    sessionId?: string,
    onProgress?: (progress: number) => void
  ): Promise<FaceMatchingResult> {
    const formData = new FormData()
    formData.append('document', documentFile)
    formData.append('selfie', selfieFile)
    if (sessionId) {
      formData.append('session_id', sessionId)
    }

    const response = await apiService.post<FaceMatchingResult>('/api/v1/face-matching/run', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: any) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })

    return response
  }

  /**
   * Run deepfake detection
   */
  async detectDeepfake(
    file: File,
    sessionId?: string,
    onProgress?: (progress: number) => void
  ): Promise<DeepfakeResult> {
    const formData = new FormData()
    formData.append('file', file)
    if (sessionId) {
      formData.append('session_id', sessionId)
    }

    const response = await apiService.post<DeepfakeResult>('/api/v1/deepfake/run', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: any) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })

    return response
  }

  /**
   * Run risk scoring analysis
   */
  async calculateRiskScore(sessionId: string): Promise<RiskScoringResult> {
    return apiService.post<RiskScoringResult>('/api/v1/risk-scoring/run', { session_id: sessionId })
  }

  /**
   * Get user's verification history
   */
  async getVerificationHistory(limit: number = 10): Promise<VerificationSession[]> {
    return apiService.get<VerificationSession[]>(`/api/v1/verification/history?limit=${limit}`)
  }
}

export const verificationService = new VerificationService()
