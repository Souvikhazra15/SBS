'use client'

import React, { useState, useRef } from 'react'
import Link from 'next/link'
import { Card } from '@/components/Card'
import { CheckCircleIcon, ArrowLeftIcon } from '@/components/icons/Icons'

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
import {
  startEkycSession,
  uploadDocument,
  uploadSelfie,
  runEkycVerification,
  getEkycSession,
  type EkycSession,
} from '@/services/ekyc'

type Step = 'document' | 'selfie' | 'processing' | 'result'

export default function EkycPage() {
  const [currentStep, setCurrentStep] = useState<Step>('document')
  const [session, setSession] = useState<EkycSession | null>(null)
  const [documentType, setDocumentType] = useState('PASSPORT')
  const [frontImage, setFrontImage] = useState<File | null>(null)
  const [backImage, setBackImage] = useState<File | null>(null)
  const [selfieImage, setSelfieImage] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const frontInputRef = useRef<HTMLInputElement>(null)
  const backInputRef = useRef<HTMLInputElement>(null)
  const selfieInputRef = useRef<HTMLInputElement>(null)

  // Initialize session
  const initializeSession = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const newSession = await startEkycSession()
      setSession(newSession)
    } catch (err: any) {
      setError(err.message || 'Failed to start e-KYC session')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle document upload
  const handleDocumentUpload = async () => {
    if (!frontImage) {
      setError('Please upload at least the front of your document')
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      // Initialize session if not exists
      if (!session) {
        await initializeSession()
      }

      if (session) {
        await uploadDocument(session.session_id, documentType, frontImage, backImage || undefined)
        setCurrentStep('selfie')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to upload document')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle selfie upload
  const handleSelfieUpload = async () => {
    if (!selfieImage) {
      setError('Please capture a selfie')
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      if (session) {
        await uploadSelfie(session.session_id, selfieImage)
        setCurrentStep('processing')
        
        // Run verification
        const result = await runEkycVerification(session.session_id)
        setSession(result)
        setCurrentStep('result')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to process verification')
    } finally {
      setIsLoading(false)
    }
  }

  // Restart process
  const handleRestart = () => {
    setCurrentStep('document')
    setSession(null)
    setFrontImage(null)
    setBackImage(null)
    setSelfieImage(null)
    setError(null)
  }

  const getStepStatus = (step: Step) => {
    const steps: Step[] = ['document', 'selfie', 'processing', 'result']
    const currentIndex = steps.indexOf(currentStep)
    const stepIndex = steps.indexOf(step)
    
    if (stepIndex < currentIndex) return 'completed'
    if (stepIndex === currentIndex) return 'active'
    return 'pending'
  }

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

        {/* Error Display */}
        {error && (
          <div className="mb-8 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 max-w-4xl mx-auto">
            {error}
          </div>
        )}

        {/* Step 1: Document Upload */}
        {currentStep === 'document' && (
          <Card className="max-w-4xl mx-auto p-8">
            <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-6">Upload Identity Document</h2>
            
            <div className="space-y-6">
              {/* Document Type Selection */}
              <div>
                <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-2">
                  Document Type
                </label>
                <select
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg border border-dark-300 dark:border-dark-600 bg-white dark:bg-dark-800 text-dark-900 dark:text-white"
                >
                  <option value="PASSPORT">Passport</option>
                  <option value="DRIVERS_LICENSE">Driver's License</option>
                  <option value="NATIONAL_ID">National ID</option>
                  <option value="RESIDENCE_PERMIT">Residence Permit</option>
                  <option value="VOTER_ID">Voter ID</option>
                </select>
              </div>

              {/* Front Image Upload */}
              <div>
                <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-2">
                  Front of Document *
                </label>
                <div 
                  onClick={() => frontInputRef.current?.click()}
                  className="border-2 border-dashed border-dark-300 dark:border-dark-600 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500 transition-colors"
                >
                  {frontImage ? (
                    <div>
                      <p className="text-green-600 dark:text-green-400 font-medium">{frontImage.name}</p>
                      <p className="text-sm text-dark-600 dark:text-dark-400 mt-1">Click to change</p>
                    </div>
                  ) : (
                    <div>
                      <UploadIcon className="w-12 h-12 mx-auto mb-4 text-dark-400" />
                      <p className="text-dark-600 dark:text-dark-400">Click to upload front of document</p>
                    </div>
                  )}
                </div>
                <input
                  ref={frontInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => setFrontImage(e.target.files?.[0] || null)}
                  className="hidden"
                />
              </div>

              {/* Back Image Upload (Optional) */}
              <div>
                <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-2">
                  Back of Document (Optional)
                </label>
                <div 
                  onClick={() => backInputRef.current?.click()}
                  className="border-2 border-dashed border-dark-300 dark:border-dark-600 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500 transition-colors"
                >
                  {backImage ? (
                    <div>
                      <p className="text-green-600 dark:text-green-400 font-medium">{backImage.name}</p>
                      <p className="text-sm text-dark-600 dark:text-dark-400 mt-1">Click to change</p>
                    </div>
                  ) : (
                    <div>
                      <UploadIcon className="w-12 h-12 mx-auto mb-4 text-dark-400" />
                      <p className="text-dark-600 dark:text-dark-400">Click to upload back of document</p>
                    </div>
                  )}
                </div>
                <input
                  ref={backInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => setBackImage(e.target.files?.[0] || null)}
                  className="hidden"
                />
              </div>

              <button
                onClick={handleDocumentUpload}
                disabled={isLoading || !frontImage}
                className="w-full px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Uploading...' : 'Continue to Selfie'}
              </button>
            </div>
          </Card>
        )}

        {/* Step 2: Selfie Capture */}
        {currentStep === 'selfie' && (
          <Card className="max-w-4xl mx-auto p-8">
            <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-6">Capture Selfie</h2>
            
            <div className="space-y-6">
              <p className="text-dark-600 dark:text-dark-400">
                Please take a clear selfie to match with your document photo.
              </p>

              <div 
                onClick={() => selfieInputRef.current?.click()}
                className="border-2 border-dashed border-dark-300 dark:border-dark-600 rounded-lg p-12 text-center cursor-pointer hover:border-primary-500 transition-colors"
              >
                {selfieImage ? (
                  <div>
                    <p className="text-green-600 dark:text-green-400 font-medium">{selfieImage.name}</p>
                    <p className="text-sm text-dark-600 dark:text-dark-400 mt-1">Click to retake</p>
                  </div>
                ) : (
                  <div>
                    <CameraIcon className="w-16 h-16 mx-auto mb-4 text-dark-400" />
                    <p className="text-dark-600 dark:text-dark-400">Click to capture selfie</p>
                  </div>
                )}
              </div>
              <input
                ref={selfieInputRef}
                type="file"
                accept="image/*"
                capture="user"
                onChange={(e) => setSelfieImage(e.target.files?.[0] || null)}
                className="hidden"
              />

              <div className="flex gap-4">
                <button
                  onClick={() => setCurrentStep('document')}
                  className="flex-1 px-6 py-3 border border-dark-300 dark:border-dark-600 text-dark-700 dark:text-dark-300 font-semibold rounded-lg hover:bg-dark-50 dark:hover:bg-dark-800 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleSelfieUpload}
                  disabled={isLoading || !selfieImage}
                  className="flex-1 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Processing...' : 'Verify Identity'}
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
            <p className="text-dark-600 dark:text-dark-400">
              Please wait while we verify your documents and identity...
            </p>
          </Card>
        )}

        {/* Step 4: Results */}
        {currentStep === 'result' && session && (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Decision Card */}
            <Card className={`p-8 text-center ${
              session.decision === 'APPROVED' ? 'bg-green-50 dark:bg-green-900/20 border-green-500' :
              session.decision === 'REJECTED' ? 'bg-red-50 dark:bg-red-900/20 border-red-500' :
              'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500'
            }`}>
              <div className="text-6xl mb-4">
                {session.decision === 'APPROVED' ? '✅' :
                 session.decision === 'REJECTED' ? '❌' : '⚠️'}
              </div>
              <h2 className="text-3xl font-bold mb-4">
                {session.decision === 'APPROVED' ? 'Verification Approved' :
                 session.decision === 'REJECTED' ? 'Verification Rejected' :
                 'Manual Review Required'}
              </h2>
              <p className="text-lg text-dark-600 dark:text-dark-400">
                {session.decision === 'APPROVED' ? 'Your identity has been successfully verified!' :
                 session.decision === 'REJECTED' ? 'We were unable to verify your identity. Please try again.' :
                 'Your verification requires manual review. We\'ll notify you once complete.'}
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
                      {session.document_score?.toFixed(1) || 'N/A'}%
                    </span>
                  </div>
                  <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all"
                      style={{ width: `${session.document_score || 0}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-dark-700 dark:text-dark-300">Face Match Score</span>
                    <span className="font-bold text-dark-900 dark:text-white">
                      {session.face_match_score?.toFixed(1) || 'N/A'}%
                    </span>
                  </div>
                  <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all"
                      style={{ width: `${session.face_match_score || 0}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-dark-700 dark:text-dark-300">Liveness Score</span>
                    <span className="font-bold text-dark-900 dark:text-white">
                      {session.liveness_score?.toFixed(1) || 'N/A'}%
                    </span>
                  </div>
                  <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all"
                      style={{ width: `${session.liveness_score || 0}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-dark-700 dark:text-dark-300">Overall Score</span>
                    <span className="font-bold text-dark-900 dark:text-white">
                      {session.overall_score?.toFixed(1) || 'N/A'}%
                    </span>
                  </div>
                  <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full transition-all"
                      style={{ width: `${session.overall_score || 0}%` }}
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
