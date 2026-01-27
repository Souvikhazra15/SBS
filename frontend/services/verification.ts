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

// ============================================
// VIDEO KYC INTERFACES
// ============================================

export interface VideoKYCSession {
  id: string
  userId: string
  sessionStatus: 'IDLE' | 'IN_PROGRESS' | 'DOCUMENT_VERIFICATION' | 'AI_ANALYSIS' | 'AGENT_REVIEW' | 'COMPLETED' | 'REJECTED' | 'EXPIRED'
  currentStep: number
  totalSteps: number
  name?: string
  dateOfBirth?: string
  address?: string
  income?: string
  employment?: string
  aadhar?: string
  pan?: string
  profileImagePath?: string
  signatureImagePath?: string
  documentImagePath?: string
  documentVerified: boolean
  faceMatched: boolean
  livenessChecked: boolean
  riskScore?: number
  forgeryScore?: number
  faceMatchScore?: number
  deepfakeScore?: number
  finalDecision: 'PENDING' | 'APPROVED' | 'REJECTED' | 'MANUAL_REVIEW'
  sessionStartedAt: string
  sessionCompletedAt?: string
}

export interface VideoKYCSessionData {
  name?: string
  dateOfBirth?: string
  address?: string
  income?: string
  employment?: string
  aadhar?: string
  pan?: string
  currentStep?: number
}

export interface VideoKYCFileUploadResponse {
  success: boolean
  sessionId: string
  filePath: string
  fileType: string
  message: string
}

export interface VideoKYCAnswerResponse {
  id: string
  sessionId: string
  questionId: string
  answerText?: string
  answerType: string
  imageUrl?: string
  audioUrl?: string
  isValid: boolean
  validationErrors?: Record<string, any>
  answeredAt: string
  responseTime?: number
}

export interface VideoKYCChatMessageResponse {
  id: string
  sessionId: string
  messageText: string
  messageType: string
  timestamp: string
}

export interface VideoKYCAIAnalysisResponse {
  success: boolean
  sessionId: string
  documentVerified: boolean
  faceMatched: boolean
  livenessChecked: boolean
  forgeryScore?: number
  faceMatchScore?: number
  deepfakeScore?: number
  riskScore?: number
  recommendation: string
  details: Record<string, any>
}

export interface VideoKYCSessionCompleteResponse {
  success: boolean
  sessionId: string
  finalDecision: 'APPROVED' | 'REJECTED' | 'MANUAL_REVIEW'
  message: string
  session: VideoKYCSession
}

export interface VideoKYCSessionHistoryResponse {
  sessions: VideoKYCSession[]
  total: number
  page: number
  pageSize: number
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

  // ============================================
  // VIDEO KYC METHODS
  // ============================================

  /**
   * Create a new Video KYC session
   */
  async createVideoKYCSession(): Promise<VideoKYCSession> {
    return apiService.post<VideoKYCSession>('/api/v1/video-kyc/session/create')
  }

  /**
   * Get Video KYC session by ID
   */
  async getVideoKYCSession(sessionId: string): Promise<VideoKYCSession> {
    return apiService.get<VideoKYCSession>(`/api/v1/video-kyc/session/${sessionId}`)
  }

  /**
   * Update Video KYC session data
   */
  async updateVideoKYCSession(sessionId: string, data: Partial<VideoKYCSessionData>): Promise<VideoKYCSession> {
    return apiService.put<VideoKYCSession>(`/api/v1/video-kyc/session/${sessionId}/update`, data)
  }

  /**
   * Upload image for Video KYC (profile, signature, document)
   */
  async uploadVideoKYCImage(
    sessionId: string,
    file: File,
    fileType: 'profile' | 'signature' | 'document',
    name: string,
    dob?: string,
    onProgress?: (progress: number) => void
  ): Promise<VideoKYCFileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)
    formData.append('file_type', fileType)
    formData.append('name', name)
    if (dob) {
      formData.append('dob', dob)
    }

    return apiService.post<VideoKYCFileUploadResponse>('/api/v1/video-kyc/upload', formData, {
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
  }

  /**
   * Submit an answer to a Video KYC question
   */
  async submitVideoKYCAnswer(
    sessionId: string,
    questionId: string,
    answerText: string,
    answerType: string = 'text',
    responseTime?: number
  ): Promise<VideoKYCAnswerResponse> {
    return apiService.post<VideoKYCAnswerResponse>('/api/v1/video-kyc/answer/submit', {
      sessionId,
      questionId,
      answerText,
      answerType,
      responseTime,
    })
  }

  /**
   * Add a chat message to Video KYC session
   */
  async addVideoKYCChatMessage(
    sessionId: string,
    messageText: string,
    messageType: 'agent' | 'user' | 'system'
  ): Promise<VideoKYCChatMessageResponse> {
    return apiService.post<VideoKYCChatMessageResponse>('/api/v1/video-kyc/chat/message', {
      sessionId,
      messageText,
      messageType,
    })
  }

  /**
   * Run AI analysis on Video KYC session
   */
  async runVideoKYCAIAnalysis(sessionId: string): Promise<VideoKYCAIAnalysisResponse> {
    return apiService.post<VideoKYCAIAnalysisResponse>('/api/v1/video-kyc/analysis/run', {
      sessionId,
    })
  }

  /**
   * Complete Video KYC session with final decision
   */
  async completeVideoKYCSession(
    sessionId: string,
    finalDecision: 'APPROVED' | 'REJECTED' | 'MANUAL_REVIEW',
    agentName?: string,
    agentReviewNotes?: string,
    rejectionReason?: string
  ): Promise<VideoKYCSessionCompleteResponse> {
    return apiService.post<VideoKYCSessionCompleteResponse>('/api/v1/video-kyc/session/complete', {
      sessionId,
      finalDecision,
      agentName,
      agentReviewNotes,
      rejectionReason,
    })
  }

  /**
   * Get Video KYC session history
   */
  async getVideoKYCHistory(limit: number = 10, page: number = 1): Promise<VideoKYCSessionHistoryResponse> {
    return apiService.get<VideoKYCSessionHistoryResponse>(
      `/api/v1/video-kyc/session/history?limit=${limit}&page=${page}`
    )
  }
}

export const verificationService = new VerificationService()
