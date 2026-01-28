'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { Card } from '@/components/Card'
import { ArrowLeftIcon } from '@/components/icons/Icons'
import { LoadingSpinner } from '@/components/upload/LoadingSpinner'
import { useToast } from '@/components/Toast'
import { VideoKYCWebcam } from '@/components/videokyc/VideoKYCWebcam'
import { CaptureIdPhoto } from '@/components/videokyc/CaptureIdPhoto'
import { ChatInterface } from '@/components/videokyc/ChatInterface'
import { VoiceInput } from '@/components/videokyc/VoiceInput'
import { useVideoKYCStore } from '@/lib/stores/videoKycStore'
import { kycQuestions } from '@/lib/videoKycQuestions'
import { VerificationService } from '@/services/verification'

type SessionStatus = 'idle' | 'connecting' | 'verification-flow' | 'id-capture' | 'document-verification' | 'ai-analysis' | 'agent-review' | 'completed' | 'rejected'


export default function VideoKYCPage() {
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>('idle')
  const [textInput, setTextInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [extractedIdNumber, setExtractedIdNumber] = useState<string | null>(null)
  const [idConfidence, setIdConfidence] = useState<number | null>(null)
  const { showToast } = useToast()
  
  const {
    sessionId,
    setSessionId,
    currentStep,
    setCurrentStep,
    currentQuestion,
    setCurrentQuestion,
    kycData,
    updateKYCData,
    addMessage,
    messages,
    documentVerified,
    setDocumentVerified,
    faceMatched,
    setFaceMatched,
    livenessChecked,
    setLivenessChecked,
    riskScore,
    setRiskScore,
    agentName,
    setAgentName,
    reset
  } = useVideoKYCStore()

  // Text-to-Speech function
  const speak = useCallback((text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'en-US'
      utterance.rate = 0.9
      window.speechSynthesis.speak(utterance)
    }
  }, [])

  // Start session
  const startSession = async () => {
    setSessionStatus('connecting')
    const newSessionId = `VKC-${Date.now()}`
    setSessionId(newSessionId)
    
    setTimeout(() => {
      setSessionStatus('verification-flow')
      setCurrentStep(0)
      loadQuestion(0)
    }, 2000)
  }

  // Load question
  const loadQuestion = (step: number) => {
    if (step < kycQuestions.length) {
      const question = kycQuestions[step]
      setCurrentQuestion(question.question)
      addMessage({ text: question.question, type: 'agent' })
      speak(question.question)
    }
  }

  // Handle text submission
  const handleTextSubmit = async () => {
    if (!textInput.trim() || isProcessing) return

    setIsProcessing(true)
    const currentQuestionData = kycQuestions[currentStep]
    
    // Add user message
    addMessage({ text: textInput, type: 'user' })

    // Validate and save
    if (currentQuestionData.validation && !currentQuestionData.validation(textInput)) {
      showToast({
        type: 'error',
        title: 'Invalid Input',
        message: 'Please provide a valid response'
      })
      setIsProcessing(false)
      return
    }

    // Save to store
    updateKYCData(currentQuestionData.type as any, textInput)
    
    showToast({
      type: 'success',
      title: 'Response Recorded',
      message: 'Moving to next question...'
    })

    setTextInput('')
    
    // Move to next question
    setTimeout(() => {
      if (currentStep < kycQuestions.length - 1) {
        setCurrentStep(currentStep + 1)
        loadQuestion(currentStep + 1)
      } else {
        processVerification()
      }
      setIsProcessing(false)
    }, 1500)
  }

  // Handle image capture
  const handleImageCapture = async (imageSrc: string) => {
    setIsProcessing(true)
    const currentQuestionData = kycQuestions[currentStep]

    try {
      // Convert base64 to blob
      const response = await fetch(imageSrc)
      const blob = await response.blob()
      
      // Create form data
      const formData = new FormData()
      formData.append('image', blob, 'capture.png')
      formData.append('name', kycData.name || 'user')
      formData.append('dob', kycData.dob || 'unknown')
      formData.append('type', currentQuestionData.type)

      // Upload image
      const uploadResponse = await fetch('/api/video-kyc/upload', {
        method: 'POST',
        body: formData
      })

      if (!uploadResponse.ok) {
        throw new Error('Upload failed')
      }

      const { url, imageData } = await uploadResponse.json()

      // Save URL to store
      updateKYCData(currentQuestionData.type as any, url)

      addMessage({ text: 'Image captured and uploaded successfully', type: 'user' })
      
      showToast({
        type: 'success',
        title: 'Image Uploaded',
        message: 'Processing...'
      })

      // Move to next question
      setTimeout(() => {
        if (currentStep < kycQuestions.length - 1) {
          setCurrentStep(currentStep + 1)
          loadQuestion(currentStep + 1)
        } else {
          // Move to ID capture step after all questions
          setSessionStatus('id-capture')
          addMessage({ text: 'Great! Now please capture your ID document for verification.', type: 'agent' })
          speak('Please hold your ID document in front of the camera and capture it')
        }
        setIsProcessing(false)
      }, 1500)
    } catch (error) {
      console.error('Image upload error:', error)
      showToast({
        type: 'error',
        title: 'Upload Failed',
        message: 'Please try capturing again'
      })
      setIsProcessing(false)
    }
  }

  // Handle ID document capture
  const handleIdCapture = async (imageBlob: Blob, previewUrl: string) => {
    if (!sessionId) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'No active session found'
      })
      return
    }

    setIsProcessing(true)

    try {
      console.log('[VIDEO-KYC] Uploading ID document for OCR processing...')
      
      const result = await VerificationService.captureIdDocument(sessionId, imageBlob)

      if (result.success && result.idNumber) {
        setExtractedIdNumber(result.idNumber)
        setIdConfidence(result.confidence || 0)
        
        addMessage({ 
          text: `ID Number extracted: ${result.idNumber} (${result.idType}, Confidence: ${(result.confidence! * 100).toFixed(1)}%)`, 
          type: 'agent' 
        })
        
        showToast({
          type: 'success',
          title: 'ID Extracted Successfully',
          message: `ID Number: ${result.idNumber}`
        })

        speak(`ID number ${result.idNumber} extracted successfully. Proceeding to verification.`)
        
        // Move to document verification
        setTimeout(() => {
          processVerification()
        }, 2000)
      } else {
        addMessage({ 
          text: `OCR failed: ${result.error || 'Could not extract ID number'}. Please retake the photo.`, 
          type: 'agent' 
        })
        
        showToast({
          type: 'error',
          title: 'OCR Failed',
          message: result.message || result.error || 'Please ensure ID is clear and well-lit'
        })
        
        speak('ID extraction failed. Please try again with better lighting.')
      }
      
      setIsProcessing(false)
    } catch (error) {
      console.error('[VIDEO-KYC] ID capture error:', error)
      addMessage({ 
        text: 'Failed to process ID document. Please try again.', 
        type: 'agent' 
      })
      
      showToast({
        type: 'error',
        title: 'Processing Failed',
        message: 'Please try capturing again'
      })
      
      setIsProcessing(false)
    }
  }

  // Process verification
  const processVerification = async () => {
    setSessionStatus('document-verification')
    
    // Simulate document verification
    await new Promise(resolve => setTimeout(resolve, 2000))
    setDocumentVerified(true)
    
    setSessionStatus('ai-analysis')
    addMessage({ text: 'All information collected. Running AI verification...', type: 'agent' })
    speak('Running AI verification...')

    // Simulate AI analysis
    await new Promise(resolve => setTimeout(resolve, 3000))

    // Verify face matching
    if (kycData.profile && kycData.aadhar) {
      try {
        const verifyResponse = await fetch('/api/video-kyc/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            profile: kycData.profile,
            aadhar: kycData.aadhar,
            name: kycData.name,
            dob: kycData.dob
          })
        })

        const verifyResult = await verifyResponse.json()
        setFaceMatched(verifyResult.faceMatched)
        setLivenessChecked(verifyResult.livenessDetected)
      } catch (error) {
        console.error('Verification error:', error)
      }
    }

    // Save KYC data
    try {
      const saveResponse = await fetch('/api/video-kyc/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          ...kycData
        })
      })

      const saveResult = await saveResponse.json()
      if (saveResult.success) {
        setRiskScore(saveResult.riskScore)
      }
    } catch (error) {
      console.error('Save error:', error)
    }

    // Assign agent
    setSessionStatus('agent-review')
    const agents = ['Sarah Johnson', 'Michael Chen', 'Priya Sharma', 'David Williams']
    setAgentName(agents[Math.floor(Math.random() * agents.length)])
    
    addMessage({ text: 'An agent has been assigned to review your verification...', type: 'agent' })
    speak('An agent is now reviewing your verification')

    // Simulate agent review
    await new Promise(resolve => setTimeout(resolve, 5000))

    // Complete
    setSessionStatus('completed')
    addMessage({ text: 'KYC Verification completed successfully! You are now verified.', type: 'agent' })
    speak('KYC Verification completed successfully!')
    
    showToast({
      type: 'success',
      title: 'Verification Complete',
      message: 'Your identity has been verified!'
    })
  }

  // Handle voice input
  const handleVoiceTranscript = (transcript: string) => {
    setTextInput(transcript)
  }

  const currentQuestionData = kycQuestions[currentStep]

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
              <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-dark-900 dark:text-white mb-4">
                Video-KYC Verification
              </h1>
              <p className="text-lg text-dark-600 dark:text-dark-400 max-w-3xl">
                Real-time video verification with AI-powered identity authentication and live agent support for comprehensive KYC compliance.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container-wide py-16">
        {/* Process Flow */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-8 text-center">Verification Process</h2>
          <div className="grid md:grid-cols-5 gap-4">
            {[
              { step: '1', title: 'Start Session', description: 'Initialize verification', active: sessionStatus === 'connecting' || sessionStatus === 'idle' },
              { step: '2', title: 'Information', description: 'Answer questions', active: sessionStatus === 'verification-flow' },
              { step: '3', title: 'ID Capture', description: 'Scan ID document', active: sessionStatus === 'id-capture' },
              { step: '4', title: 'AI Analysis', description: 'Automated checks', active: sessionStatus === 'document-verification' || sessionStatus === 'ai-analysis' },
              { step: '5', title: 'Agent Review', description: 'Final approval', active: sessionStatus === 'agent-review' || sessionStatus === 'completed' }
            ].map((item, index) => (
              <Card key={index} className={`text-center p-4 transition-all duration-300 ${
                item.active ? 'ring-2 ring-primary-500 dark:ring-primary-400' : ''
              }`}>
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full font-bold text-lg mb-3 mx-auto transition-colors duration-300 ${
                  item.active 
                    ? 'bg-primary-600 dark:bg-primary-500 text-white animate-pulse' 
                    : 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                }`}>
                  {item.step}
                </div>
                <h3 className="font-semibold text-dark-900 dark:text-white mb-2">{item.title}</h3>
                <p className="text-sm text-dark-600 dark:text-dark-400">{item.description}</p>
              </Card>
            ))}
          </div>
        </div>

        {/* Session Info */}
        {sessionId && (
          <Card className="p-6 mb-8 bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-700">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <p className="text-sm text-dark-600 dark:text-dark-400 mb-1">Session ID</p>
                <p className="font-mono font-semibold text-dark-900 dark:text-white">{sessionId}</p>
              </div>
              {agentName && (
                <div>
                  <p className="text-sm text-dark-600 dark:text-dark-400 mb-1">Assigned Agent</p>
                  <p className="font-semibold text-dark-900 dark:text-white">{agentName}</p>
                </div>
              )}
              {sessionStatus === 'verification-flow' && (
                <div>
                  <p className="text-sm text-dark-600 dark:text-dark-400 mb-1">Progress</p>
                  <p className="font-semibold text-dark-900 dark:text-white">
                    Question {currentStep + 1} of {kycQuestions.length}
                  </p>
                </div>
              )}
              <div className="flex gap-4">
                <div className="text-center">
                  <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${documentVerified ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`} />
                  <p className="text-xs text-dark-600 dark:text-dark-400">Document</p>
                </div>
                <div className="text-center">
                  <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${faceMatched ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`} />
                  <p className="text-xs text-dark-600 dark:text-dark-400">Face Match</p>
                </div>
                <div className="text-center">
                  <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${livenessChecked ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`} />
                  <p className="text-xs text-dark-600 dark:text-dark-400">Liveness</p>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Main Content */}
        <div className="grid lg:grid-cols-2 gap-8 mb-16">
          {/* Left Side - Video/Camera */}
          <div>
            {sessionStatus === 'idle' && (
              <Card className="p-8 text-center h-full flex flex-col items-center justify-center">
                <div className="inline-flex p-6 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 mb-6">
                  <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-dark-900 dark:text-white mb-4">
                  Start Video-KYC Verification
                </h3>
                <p className="text-dark-600 dark:text-dark-400 mb-8 max-w-md">
                  Complete your identity verification in minutes with our AI-powered conversational video KYC system with voice and text input support.
                </p>
                <button
                  onClick={startSession}
                  className="px-8 py-4 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white font-semibold rounded-lg transition-all duration-300 transform hover:scale-105"
                >
                  Start Verification
                </button>
              </Card>
            )}

            {sessionStatus === 'connecting' && (
              <Card className="p-8 text-center h-full flex flex-col items-center justify-center">
                <LoadingSpinner size="lg" />
                <p className="text-lg text-dark-600 dark:text-dark-400 mt-6">
                  Initializing verification session...
                </p>
              </Card>
            )}

            {sessionStatus === 'verification-flow' && (
              <div>
                <VideoKYCWebcam
                  onCapture={handleImageCapture}
                  showCaptureButton={currentQuestionData?.requiresImage}
                />
                
                {currentQuestionData && !currentQuestionData.requiresImage && (
                  <Card className="p-6 mt-4">
                    <h3 className="text-lg font-semibold text-dark-900 dark:text-white mb-4">
                      Your Response
                    </h3>
                    <div className="flex gap-2 mb-4">
                      <input
                        type="text"
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleTextSubmit()}
                        placeholder="Type your answer or use voice input..."
                        className="flex-1 px-4 py-3 bg-white dark:bg-dark-800 border border-dark-300 dark:border-dark-700 rounded-lg text-dark-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                        disabled={isProcessing}
                      />
                      <VoiceInput onTranscript={handleVoiceTranscript} />
                    </div>
                    <button
                      onClick={handleTextSubmit}
                      disabled={!textInput.trim() || isProcessing}
                      className="w-full px-6 py-3 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white font-semibold rounded-lg transition-colors duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isProcessing ? (
                        <span className="flex items-center justify-center gap-2">
                          <LoadingSpinner size="sm" />
                          Processing...
                        </span>
                      ) : (
                        'Submit Answer'
                      )}
                    </button>
                  </Card>
                )}

                {currentQuestionData?.requiresImage && (
                  <Card className="p-6 mt-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700">
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      📷 Click the capture button on the camera to take a photo when ready
                    </p>
                  </Card>
                )}
              </div>
            )}

            {sessionStatus === 'id-capture' && (
              <div>
                <Card className="p-6 mb-4">
                  <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-2">
                    📄 Capture Your ID Document
                  </h3>
                  <p className="text-dark-600 dark:text-dark-400 text-sm mb-4">
                    We'll use OCR to extract your ID number automatically. Please ensure the document is clearly visible.
                  </p>
                </Card>

                <CaptureIdPhoto 
                  onCapture={handleIdCapture}
                  isProcessing={isProcessing}
                />

                {extractedIdNumber && (
                  <Card className="p-6 mt-4 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700">
                    <div className="flex items-start gap-3">
                      <div className="text-3xl">✅</div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-green-800 dark:text-green-300 mb-1">
                          ID Number Extracted
                        </h4>
                        <p className="text-green-700 dark:text-green-400 text-lg font-mono mb-2">
                          {extractedIdNumber}
                        </p>
                        <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-500">
                          <span>Confidence:</span>
                          <div className="flex-1 bg-green-200 dark:bg-green-800 rounded-full h-2">
                            <div 
                              className="bg-green-600 dark:bg-green-400 h-2 rounded-full"
                              style={{ width: `${(idConfidence || 0) * 100}%` }}
                            />
                          </div>
                          <span>{((idConfidence || 0) * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>
                  </Card>
                )}
              </div>
            )}

            {(sessionStatus === 'document-verification' || sessionStatus === 'ai-analysis') && (
              <Card className="p-8 text-center h-full flex flex-col items-center justify-center">
                <LoadingSpinner size="lg" />
                <p className="text-lg text-dark-600 dark:text-dark-400 mt-6 mb-2">
                  {sessionStatus === 'document-verification' ? 'Verifying Documents...' : 'AI Analysis in Progress...'}
                </p>
                <div className="space-y-2 text-sm text-dark-500 dark:text-dark-500">
                  <p>✓ Analyzing provided information</p>
                  <p>✓ Checking document authenticity</p>
                  <p>✓ Matching facial features</p>
                  <p>✓ Performing liveness detection</p>
                  <p>✓ Calculating risk score</p>
                </div>
              </Card>
            )}

            {sessionStatus === 'agent-review' && (
              <Card className="p-8">
                <div className="text-center mb-6">
                  <div className="inline-flex p-4 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 mb-4">
                    <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-2">
                    Agent Reviewing Your Verification
                  </h3>
                  <p className="text-dark-600 dark:text-dark-400">
                    {agentName} is reviewing your submission
                  </p>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <span className="text-dark-700 dark:text-dark-300">Document Verified</span>
                    <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <span className="text-dark-700 dark:text-dark-300">Face Match Passed</span>
                    <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <span className="text-dark-700 dark:text-dark-300">Liveness Confirmed</span>
                    <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  {riskScore && (
                    <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <span className="text-dark-700 dark:text-dark-300">Risk Score</span>
                      <span className="font-semibold text-blue-600 dark:text-blue-400">
                        {riskScore}/10
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="mt-6 flex items-center justify-center gap-2 text-blue-600 dark:text-blue-400">
                  <LoadingSpinner size="sm" />
                  <span className="text-sm">Awaiting final approval...</span>
                </div>
              </Card>
            )}

            {sessionStatus === 'completed' && (
              <Card className="p-8 text-center h-full flex flex-col items-center justify-center bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200 dark:border-green-700">
                <div className="inline-flex p-6 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 mb-6">
                  <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-green-700 dark:text-green-400 mb-4">
                  Verification Successful!
                </h3>
                <p className="text-dark-600 dark:text-dark-400 mb-6 max-w-md">
                  Your identity has been successfully verified. You can now access all features of the platform.
                </p>
                {sessionId && (
                  <div className="bg-white dark:bg-dark-800 rounded-lg p-4 mb-6 w-full max-w-md">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-dark-500 dark:text-dark-500 mb-1">Session ID</p>
                        <p className="font-mono text-dark-900 dark:text-white text-xs">{sessionId}</p>
                      </div>
                      <div>
                        <p className="text-dark-500 dark:text-dark-500 mb-1">Risk Score</p>
                        <p className="font-semibold text-green-600 dark:text-green-400">{riskScore}/10</p>
                      </div>
                    </div>
                  </div>
                )}
                <button
                  onClick={() => {
                    reset()
                    setSessionStatus('idle')
                  }}
                  className="px-8 py-3 border-2 border-green-600 dark:border-green-500 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 font-semibold rounded-lg transition-colors duration-300"
                >
                  Start New Verification
                </button>
              </Card>
            )}
          </div>

          {/* Right Side - Chat Interface */}
          <div>
            <Card className="p-6 h-[600px] flex flex-col">
              <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4 flex items-center gap-2">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Conversation
              </h3>
              <div className="flex-1 overflow-hidden">
                <ChatInterface />
              </div>
            </Card>
          </div>
        </div>

        {/* Features & Benefits Section */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          <Card className="p-6">
            <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4">Key Features</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <div>
                  <p className="font-medium text-dark-900 dark:text-white">Conversational Interface</p>
                  <p className="text-sm text-dark-600 dark:text-dark-400">Natural language questions with voice & text input</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <div>
                  <p className="font-medium text-dark-900 dark:text-white">Live Video Verification</p>
                  <p className="text-sm text-dark-600 dark:text-dark-400">Real-time camera capture with live instructions</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <div>
                  <p className="font-medium text-dark-900 dark:text-white">AI-Powered Analysis</p>
                  <p className="text-sm text-dark-600 dark:text-dark-400">Automated face matching, liveness & document verification</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <div>
                  <p className="font-medium text-dark-900 dark:text-white">Agent-Assisted Review</p>
                  <p className="text-sm text-dark-600 dark:text-dark-400">Human oversight for edge cases & final approval</p>
                </div>
              </li>
            </ul>
          </Card>

          <Card className="p-6">
            <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4">Verification Checks</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="font-medium text-dark-900 dark:text-white">Document Authentication</p>
                  <p className="text-sm text-dark-600 dark:text-dark-400">Verify Aadhar, PAN, and other ID documents</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="font-medium text-dark-900 dark:text-white">Face Matching</p>
                  <p className="text-sm text-dark-600 dark:text-dark-400">Match live face with document photo</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="font-medium text-dark-900 dark:text-white">Liveness Detection</p>
                  <p className="text-sm text-dark-600 dark:text-dark-400">Ensure physical presence & prevent spoofing</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="font-medium text-dark-900 dark:text-white">Risk Assessment</p>
                  <p className="text-sm text-dark-600 dark:text-dark-400">Calculate comprehensive risk score</p>
                </div>
              </li>
            </ul>
          </Card>
        </div>

        {/* Security & Compliance */}
        <Card className="p-8 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border-primary-200 dark:border-primary-700">
          <h3 className="text-2xl font-semibold text-dark-900 dark:text-white mb-6 text-center">
            Enterprise-Grade Security & Compliance
          </h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="inline-flex p-3 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 mb-3">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h4 className="font-semibold text-dark-900 dark:text-white mb-2">End-to-End Encryption</h4>
              <p className="text-sm text-dark-600 dark:text-dark-400">All data encrypted in transit and at rest</p>
            </div>
            <div className="text-center">
              <div className="inline-flex p-3 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 mb-3">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h4 className="font-semibold text-dark-900 dark:text-white mb-2">KYC/AML Compliant</h4>
              <p className="text-sm text-dark-600 dark:text-dark-400">Meets global regulatory requirements</p>
            </div>
            <div className="text-center">
              <div className="inline-flex p-3 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 mb-3">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h4 className="font-semibold text-dark-900 dark:text-white mb-2">Complete Audit Trail</h4>
              <p className="text-sm text-dark-600 dark:text-dark-400">Full verification history & logs</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
