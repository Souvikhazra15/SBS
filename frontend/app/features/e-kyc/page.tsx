'use client'

import React, { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Card } from '@/components/Card'
import { CheckCircleIcon, ArrowLeftIcon } from '@/components/icons/Icons'
import {
  startEkycSession,
  uploadDocument,
  uploadSelfie,
  matchFaces,
  runEkycVerification,
  type EkycSession,
} from '@/services/ekyc'

// Upload icon component
const UploadIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
)

// Camera icon component
const CameraIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
)

type Step = 'document' | 'selfie' | 'processing' | 'result'

export default function EkycPage() {
  const router = useRouter()
  
  // Flow state - NO AUTH REQUIRED
  const [currentStep, setCurrentStep] = useState<Step>('document')
  const [session, setSession] = useState<EkycSession | null>(null)
  const [documentType, setDocumentType] = useState('AADHAAR')
  const [documentImage, setDocumentImage] = useState<File | null>(null)
  const [selfieImage, setSelfieImage] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [extractedData, setExtractedData] = useState<any>(null)
  const [showWebcam, setShowWebcam] = useState(false)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [faceMatchStatus, setFaceMatchStatus] = useState<string>('')
  
  const documentInputRef = useRef<HTMLInputElement>(null)
  const selfieInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Auto-start session on mount - NO AUTH CHECK
  useEffect(() => {
    if (!session && currentStep === 'document' && !isLoading) {
      const initSession = async () => {
        try {
          console.log('[EKYC] Auto-creating session (no auth required)...')
          const newSession = await startEkycSession()
          console.log('[EKYC] Full session object:', newSession)
          console.log('[EKYC] Session ID field:', newSession.session_id, '|', newSession.sessionId)
          setSession(newSession)
        } catch (err: any) {
          console.error('[EKYC] Failed to create session:', err)
          setError('Failed to initialize verification session. Please refresh the page.')
        }
      }
      
      initSession()
    }
  }, [session, currentStep, isLoading])

  // Handle document upload
  const handleDocumentUpload = async () => {
    if (!documentImage) {
      setError('Please upload your document')
      return
    }

    if (!session) {
      setError('Session not initialized. Please refresh the page.')
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      console.log('[EKYC] Full session object before upload:', session)
      console.log('[EKYC] Uploading document with session_id:', session.session_id, 'or sessionId:', session?.sessionId)
      console.log('[EKYC] Document type:', documentType)
      const result = await uploadDocument(session.session_id || session.sessionId, documentType, documentImage)
      setExtractedData(result)
      console.log('[EKYC] Document uploaded successfully')
      
      // Auto-advance to selfie
      setTimeout(() => {
        setCurrentStep('selfie')
      }, 1500)
    } catch (err: any) {
      console.error('[EKYC] Document upload error:', err)
      setError(err.message || 'Failed to upload document. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle selfie upload with face matching
  const handleSelfieUpload = async () => {
    if (!selfieImage) {
      setError('Please capture a selfie')
      return
    }

    if (!documentImage) {
      setError('Document image not found. Please restart the process.')
      return
    }

    if (!session) {
      setError('Session not found. Please restart the process.')
      return
    }

    try {
      setIsLoading(true)
      setError(null)
      setCurrentStep('processing')
      setFaceMatchStatus('Uploading images...')

      console.log('[FACE-MATCH] Starting face matching...')
      
      // Perform face matching
      const faceMatchResult = await matchFaces(
        session.session_id,
        documentImage,
        selfieImage,
        (status) => {
          setFaceMatchStatus(status)
        }
      )
      
      console.log('[FACE-MATCH] Result:', faceMatchResult)
      
      if (!faceMatchResult.success) {
        throw new Error(faceMatchResult.error || 'Face matching failed')
      }
      
      setFaceMatchStatus('Face matched successfully!')
      
      // Upload selfie after successful face match
      console.log('[EKYC] Uploading selfie...')
      await uploadSelfie(session.session_id, selfieImage)
      console.log('[EKYC] Selfie uploaded, running verification...')
      
      // Run verification
      const result = await runEkycVerification(session.session_id)
      setSession(result)
      console.log('[EKYC] Verification complete:', result.decision)
      
      setCurrentStep('result')
    } catch (err: any) {
      console.error('[EKYC] Verification error:', err)
      setCurrentStep('selfie') // Go back to selfie
      
      // Handle specific face matching errors
      if (err.code === 'FACE_NOT_DETECTED') {
        setError('No face detected in one or both images. Please ensure your face is clearly visible and try again.')
      } else if (err.code === 'MULTIPLE_FACES') {
        setError('Multiple faces detected. Please ensure only your face is visible in the photo.')
      } else if (err.code === 'NO_MATCH') {
        setError('Face does not match the ID photo. Please ensure good lighting and face the camera directly, then try again.')
      } else {
        setError(err.message || 'Failed to process verification. Please try again.')
      }
    } finally {
      setIsLoading(false)
      setFaceMatchStatus('')
    }
  }

  // Restart process
  const handleRestart = async () => {
    stopWebcam()
    setCurrentStep('document')
    setDocumentImage(null)
    setSelfieImage(null)
    setError(null)
    setExtractedData(null)
    setShowWebcam(false)
    
    // Create new session
    try {
      const newSession = await startEkycSession()
      setSession(newSession)
      console.log('[EKYC] New session created:', newSession.session_id)
    } catch (err) {
      console.error('[EKYC] Failed to create new session:', err)
    }
  }

  // Webcam functions
  const startWebcam = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false 
      })
      setStream(mediaStream)
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
        // Ensure video plays
        videoRef.current.play().catch(err => {
          console.error('Error playing video:', err)
        })
      }
      setShowWebcam(true)
      setError(null)
    } catch (err) {
      console.error('Error accessing webcam:', err)
      setError('Failed to access webcam. Please check your camera permissions.')
    }
  }

  const stopWebcam = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
    setShowWebcam(false)
  }

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current
      const canvas = canvasRef.current
      
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      
      const ctx = canvas.getContext('2d')
      if (ctx) {
        ctx.drawImage(video, 0, 0)
        
        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], 'selfie.jpg', { type: 'image/jpeg' })
            setSelfieImage(file)
            stopWebcam()
          }
        }, 'image/jpeg', 0.95)
      }
    }
  }

  // Connect stream to video element when it changes
  useEffect(() => {
    if (stream && videoRef.current) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  // Cleanup webcam on unmount
  useEffect(() => {
    return () => {
      stopWebcam()
    }
  }, [])

  const getStepStatus = (step: Step) => {
    const steps: Step[] = ['document', 'selfie', 'processing', 'result']
    const currentIndex = steps.indexOf(currentStep)
    const stepIndex = steps.indexOf(step)
    
    if (stepIndex < currentIndex) return 'completed'
    if (stepIndex === currentIndex) return 'active'
    return 'pending'
  }

  // No authentication barriers - show interface directly

  return (
    <div className="min-h-screen bg-white dark:bg-dark-900 transition-colors">
      {/* Header */}
      <div className="bg-primary-50 dark:bg-primary-900/20 border-b border-primary-200 dark:border-primary-800/30">
        <div className="container-wide py-8">
          <Link 
            href="/" 
            className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 mb-6 transition-colors"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            Back to Home
          </Link>
          
          <div className="flex items-start gap-6">
            <div className="inline-flex p-4 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400">
              <CheckCircleIcon className="w-12 h-12" />
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-dark-900 dark:text-white mb-4">
                e-KYC Verification
              </h1>
              <p className="text-lg text-dark-600 dark:text-dark-400 max-w-3xl">
                Complete electronic Know Your Customer verification with document authentication, face matching, and liveness detection.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container-wide py-16">
        {/* Status Tracker */}
        <div className="mb-12">
          <div className="flex items-center justify-between max-w-4xl mx-auto">
            {[
              { id: 'document', label: 'Document', icon: '📄' },
              { id: 'selfie', label: 'Selfie', icon: '🤳' },
              { id: 'processing', label: 'Processing', icon: '⚙️' },
              { id: 'result', label: 'Result', icon: '✓' },
            ].map((step, index, array) => {
              const status = getStepStatus(step.id as Step)
              return (
                <React.Fragment key={step.id}>
                  <div className="flex flex-col items-center">
                    <div className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl transition-all ${
                      status === 'completed' ? 'bg-green-500 text-white' :
                      status === 'active' ? 'bg-primary-600 text-white animate-pulse' :
                      'bg-gray-300 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                    }`}>
                      {status === 'completed' ? '✓' : step.icon}
                    </div>
                    <span className={`mt-2 text-sm font-medium ${
                      status === 'active' ? 'text-primary-600 dark:text-primary-400' : 'text-dark-600 dark:text-dark-400'
                    }`}>
                      {step.label}
                    </span>
                  </div>
                  {index < array.length - 1 && (
                    <div className={`flex-1 h-1 mx-4 transition-all ${
                      getStepStatus(array[index + 1].id as Step) === 'completed' || getStepStatus(array[index + 1].id as Step) === 'active'
                        ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-700'
                    }`} />
                  )}
                </React.Fragment>
              )
            })}
          </div>
        </div>

        {/* Inline Error Display */}
        {error && (
          <div className="mb-8 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg max-w-4xl mx-auto flex items-start gap-3">
            <span className="text-red-600 dark:text-red-400 text-xl">⚠️</span>
            <div className="flex-1">
              <p className="text-red-600 dark:text-red-400 font-medium">{error}</p>
              <button
                onClick={() => setError(null)}
                className="text-sm text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 mt-2"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Step 1: Document Upload */}
        {currentStep === 'document' && (
          <Card className="max-w-4xl mx-auto p-8">
            <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-6">Upload Identity Document</h2>
            
            <div className="space-y-6">
              {/* Session Info */}
              {session && session.session_id && (
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm">
                  <p className="text-blue-700 dark:text-blue-300">
                    ✓ Session active: <span className="font-mono">{session.session_id.slice(0, 8)}...</span>
                  </p>
                </div>
              )}

              {/* Document Type Selection */}
              <div>
                <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-2">
                  Document Type
                </label>
                <select
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg border border-dark-300 dark:border-dark-600 bg-white dark:bg-dark-800 text-dark-900 dark:text-white focus:ring-2 focus:ring-primary-500 outline-none"
                  disabled={isLoading}
                >
                  <option value="AADHAAR">Aadhaar Card</option>
                  <option value="PAN_CARD">PAN Card</option>
                  <option value="DRIVERS_LICENSE">Driving License</option>
                </select>
              </div>

              {/* Document Image Upload */}
              <div>
                <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-2">
                  Document Image *
                </label>
                <div 
                  onClick={() => documentInputRef.current?.click()}
                  className="border-2 border-dashed border-dark-300 dark:border-dark-600 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500 transition-colors"
                >
                  {documentImage ? (
                    <div>
                      <p className="text-green-600 dark:text-green-400 font-medium">✓ {documentImage.name}</p>
                      <p className="text-sm text-dark-600 dark:text-dark-400 mt-1">Click to change</p>
                    </div>
                  ) : (
                    <div>
                      <UploadIcon className="w-12 h-12 mx-auto mb-4 text-dark-400" />
                      <p className="text-dark-600 dark:text-dark-400">Click to upload your document</p>
                      <p className="text-sm text-dark-500 dark:text-dark-500 mt-2">Supported: JPG, PNG (max 10MB)</p>
                    </div>
                  )}
                </div>
                <input
                  ref={documentInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (file) {
                      if (file.size > 10 * 1024 * 1024) {
                        setError('File too large. Maximum size is 10MB.')
                        return
                      }
                      setDocumentImage(file)
                      setError(null)
                    }
                  }}
                  className="hidden"
                />
              </div>

              {/* Show extracted data if available */}
              {extractedData && (
                <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg animate-fade-in">
                  <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">✓ Document Processed Successfully</h3>
                  <div className="text-sm text-green-800 dark:text-green-200 space-y-1">
                    {extractedData.name && <p><strong>Name:</strong> {extractedData.name}</p>}
                    {extractedData.fatherName && <p><strong>Father's Name:</strong> {extractedData.fatherName}</p>}
                    {extractedData.dateOfBirth && <p><strong>Date of Birth:</strong> {extractedData.dateOfBirth}</p>}
                    {extractedData.documentNumber && <p><strong>Document Number:</strong> {extractedData.documentNumber}</p>}
                    {extractedData.confidence && (
                      <p><strong>Confidence:</strong> {(extractedData.confidence * 100).toFixed(1)}%</p>
                    )}
                  </div>
                </div>
              )}

              <button
                onClick={handleDocumentUpload}
                disabled={isLoading || !documentImage || !session}
                className="w-full px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    Processing Document...
                  </>
                ) : (
                  'Continue to Selfie →'
                )}
              </button>
            </div>
          </Card>
        )}

        {/* Step 2: Selfie Capture */}
        {currentStep === 'selfie' && (
          <Card className="max-w-4xl mx-auto p-8">
            <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-6">Capture Selfie</h2>
            
            <div className="space-y-6">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  📸 Please take a clear selfie to match with your document photo. Ensure good lighting and face the camera directly.
                </p>
              </div>

              {/* Webcam View */}
              {showWebcam ? (
                <div className="space-y-4">
                  <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '4/3' }}>
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex gap-4">
                    <button
                      onClick={capturePhoto}
                      className="flex-1 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      <CameraIcon className="w-5 h-5" />
                      Capture Photo
                    </button>
                    <button
                      onClick={stopWebcam}
                      className="px-6 py-3 border border-dark-300 dark:border-dark-600 text-dark-700 dark:text-dark-300 font-semibold rounded-lg hover:bg-dark-50 dark:hover:bg-dark-800 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : selfieImage ? (
                <div>
                  <div className="border-2 border-green-500 rounded-lg p-8 text-center bg-green-50 dark:bg-green-900/20">
                    <div className="text-green-600 dark:text-green-400 mb-4">
                      <CheckCircleIcon className="w-16 h-16 mx-auto" />
                    </div>
                    <p className="text-green-600 dark:text-green-400 font-medium text-lg">Selfie Captured Successfully!</p>
                    <p className="text-sm text-dark-600 dark:text-dark-400 mt-2">{selfieImage.name}</p>
                  </div>
                  <button
                    onClick={() => {
                      setSelfieImage(null)
                      startWebcam()
                    }}
                    className="mt-4 w-full px-6 py-3 border border-dark-300 dark:border-dark-600 text-dark-700 dark:text-dark-300 font-semibold rounded-lg hover:bg-dark-50 dark:hover:bg-dark-800 transition-colors"
                  >
                    Retake Photo
                  </button>
                </div>
              ) : (
                <div 
                  onClick={startWebcam}
                  className="border-2 border-dashed border-dark-300 dark:border-dark-600 rounded-lg p-12 text-center cursor-pointer hover:border-primary-500 transition-colors"
                >
                  <CameraIcon className="w-16 h-16 mx-auto mb-4 text-dark-400" />
                  <p className="text-dark-600 dark:text-dark-400 font-medium">Click to capture selfie</p>
                  <p className="text-sm text-dark-500 dark:text-dark-500 mt-2">Use your device camera</p>
                </div>
              )}

              {/* Hidden canvas for photo capture */}
              <canvas ref={canvasRef} className="hidden" />

              <div className="flex gap-4">
                <button
                  onClick={() => {
                    stopWebcam()
                    setCurrentStep('document')
                  }}
                  disabled={isLoading}
                  className="flex-1 px-6 py-3 border border-dark-300 dark:border-dark-600 text-dark-700 dark:text-dark-300 font-semibold rounded-lg hover:bg-dark-50 dark:hover:bg-dark-800 transition-colors disabled:opacity-50"
                >
                  ← Back
                </button>
                <button
                  onClick={handleSelfieUpload}
                  disabled={isLoading || !selfieImage}
                  className="flex-1 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                      Processing...
                    </>
                  ) : (
                    'Verify Identity →'
                  )}
                </button>
              </div>
            </div>
          </Card>
        )}

        {/* Step 3: Processing */}
        {currentStep === 'processing' && (
          <Card className="max-w-4xl mx-auto p-12 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary-600 border-t-transparent mx-auto mb-6"></div>
            <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-4">Processing Verification</h2>
            
            {/* Show face matching status */}
            {faceMatchStatus && (
              <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-blue-700 dark:text-blue-300 font-medium">
                  {faceMatchStatus}
                </p>
              </div>
            )}
            
            <p className="text-dark-600 dark:text-dark-400 mb-2">
              Please wait while we verify your documents and identity...
            </p>
            <div className="text-sm text-dark-500 dark:text-dark-500 space-y-1 mt-4">
              <p className="flex items-center justify-center gap-2">
                {faceMatchStatus.includes('Uploading') ? '⏳' : faceMatchStatus.includes('Detecting') ? '🔍' : faceMatchStatus.includes('Matching') ? '🎯' : '✓'} 
                Face Detection & Matching
              </p>
              <p>🔒 Liveness Detection</p>
              <p>📊 Risk Assessment</p>
            </div>
            <p className="text-xs text-dark-500 dark:text-dark-500 mt-4">
              This may take 10-30 seconds
            </p>
          </Card>
        )}

        {/* Step 4: Results */}
        {currentStep === 'result' && session && (
          <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
            {/* Decision Card */}
            <Card className={`p-8 text-center border-2 ${
              session.decision === 'APPROVED' ? 'bg-green-50 dark:bg-green-900/20 border-green-500' :
              session.decision === 'REJECTED' ? 'bg-red-50 dark:bg-red-900/20 border-red-500' :
              'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500'
            }`}>
              <div className="text-6xl mb-4 animate-bounce-in">
                {session.decision === 'APPROVED' ? '✅' :
                 session.decision === 'REJECTED' ? '❌' : '⚠️'}
              </div>
              <h2 className="text-3xl font-bold mb-4 text-dark-900 dark:text-white">
                {session.decision === 'APPROVED' ? 'Verification Approved!' :
                 session.decision === 'REJECTED' ? 'Verification Rejected' :
                 'Manual Review Required'}
              </h2>
              <p className="text-lg text-dark-600 dark:text-dark-400 max-w-2xl mx-auto">
                {session.decision === 'APPROVED' ? 'Your identity has been successfully verified. You can now access all services.' :
                 session.decision === 'REJECTED' ? (session.rejection_reason || 'We were unable to verify your identity. Please try again with clearer images.') :
                 'Your verification requires manual review by our team. We\'ll notify you once the review is complete.'}
              </p>
            </Card>

            {/* Scores */}
            <Card className="p-8">
              <h3 className="text-xl font-bold text-dark-900 dark:text-white mb-6">Verification Scores</h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-dark-700 dark:text-dark-300">Document Score</span>
                    <span className="font-bold text-dark-900 dark:text-white">
                      {(session.document_score || session.documentScore) ? `${(session.document_score || session.documentScore)?.toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all duration-1000"
                      style={{ width: `${session.document_score || session.documentScore || 0}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-dark-700 dark:text-dark-300">Face Match Score</span>
                    <span className="font-bold text-dark-900 dark:text-white">
                      {(session.face_match_score || session.faceMatchScore) ? `${(session.face_match_score || session.faceMatchScore)?.toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all duration-1000"
                      style={{ width: `${session.face_match_score || session.faceMatchScore || 0}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-dark-700 dark:text-dark-300">Liveness Score</span>
                    <span className="font-bold text-dark-900 dark:text-white">
                      {(session.liveness_score || session.livenessScore) ? `${(session.liveness_score || session.livenessScore)?.toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all duration-1000"
                      style={{ width: `${session.liveness_score || session.livenessScore || 0}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-dark-700 dark:text-dark-300 font-semibold">Overall Score</span>
                    <span className="font-bold text-dark-900 dark:text-white">
                      {(session.overall_score || session.overallScore) ? `${(session.overall_score || session.overallScore)?.toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-1000 ${
                        (session.overall_score || session.overallScore || 0) >= 70 ? 'bg-green-600' : 'bg-yellow-600'
                      }`}
                      style={{ width: `${session.overall_score || session.overallScore || 0}%` }}
                    />
                  </div>
                </div>
              </div>
            </Card>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={handleRestart}
                className="flex-1 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors"
              >
                Start New Verification
              </button>
              <Link
                href="/"
                className="flex-1 px-6 py-3 text-center border border-dark-300 dark:border-dark-600 text-dark-700 dark:text-dark-300 font-semibold rounded-lg hover:bg-dark-50 dark:hover:bg-dark-800 transition-colors"
              >
                Back to Home
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
