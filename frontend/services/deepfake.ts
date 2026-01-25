/**
 * Deepfake Detection Service
 * Handles video/image upload and analysis
 */

import { apiService } from './api'

export interface DeepfakeResult {
  success: boolean
  sessionId: string
  deepfakeScore: number
  decision: 'REAL' | 'FAKE' | 'UNKNOWN'
  isDeepfake: boolean
  confidence: number
  framesAnalyzed: number
  statistics?: {
    mean: number
    max: number
    min: number
    std: number
  }
  processingTimeMs: number
  modelVersion: string
  device: string
  timestamp: string
  error?: string
}

class DeepfakeService {
  /**
   * Upload and analyze video/image for deepfake detection
   */
  async analyzeMedia(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<DeepfakeResult> {
    console.log('[DEEPFAKE] Starting analysis...', { fileName: file.name, fileSize: file.size })
    
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await apiService.post<DeepfakeResult>(
        '/api/v1/deepfake/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minute timeout for large videos
          onUploadProgress: (progressEvent: any) => {
            if (onProgress && progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              console.log(`[DEEPFAKE] Upload progress: ${progress}%`)
              onProgress(progress)
            }
          },
        }
      )

      console.log('[DEEPFAKE] Analysis complete:', response)
      return response

    } catch (error: any) {
      console.error('[DEEPFAKE] Analysis failed:', error)
      throw new Error(
        error?.response?.data?.error || 
        error?.message || 
        'Deepfake analysis failed'
      )
    }
  }

  /**
   * Get model information
   */
  async getModelInfo() {
    return apiService.get('/api/v1/deepfake/info')
  }

  /**
   * Check service health
   */
  async checkHealth() {
    return apiService.get('/api/v1/deepfake/health')
  }
}

export const deepfakeService = new DeepfakeService()