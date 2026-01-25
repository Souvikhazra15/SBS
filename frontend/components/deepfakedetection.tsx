

import React, { useState } from 'react'
import Link from 'next/link'
import { Card } from '@/components/Card'
import { ShieldVerifyIcon, ArrowLeftIcon } from '@/components/icons/Icons'
import { FileUpload, UploadedFile } from '@/components/upload/FileUpload'
import { LoadingSpinner } from '@/components/upload/LoadingSpinner'
import { deepfakeService, DeepfakeResult } from '@/services/deepfake'
import { useToast } from '@/components/Toast'

type AnalysisStatus = 'idle' | 'uploading' | 'extracting' | 'analyzing' | 'saving' | 'success' | 'error'

export default function DeepfakePage() {
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null)
  const [status, setStatus] = useState<AnalysisStatus>('idle')
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<DeepfakeResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { showToast } = useToast()

  const getStatusText = () => {
    switch (status) {
      case 'uploading': return 'Uploading video...'
      case 'extracting': return 'Extracting frames...'
      case 'analyzing': return 'Running deepfake detection...'
      case 'saving': return 'Saving results...'
      default: return ''
    }
  }

  const handleAnalyze = async () => {
    if (!uploadedFile) return

    setStatus('uploading')
    setProgress(0)
    setResult(null)
    setError(null)

    try {
      // Upload phase
      setProgress(10)
      
      // Call API
      const apiResult = await deepfakeService.analyzeMedia(
        uploadedFile.file,
        (p: number) => {
          setProgress(10 + (p * 0.3)) // 10-40%
        }
      )

      // Simulate progress for UI feedback
      setStatus('extracting')
      setProgress(50)
      await new Promise(resolve => setTimeout(resolve, 800))

      setStatus('analyzing')
      setProgress(70)
      await new Promise(resolve => setTimeout(resolve, 1000))

      setStatus('saving')
      setProgress(90)
      await new Promise(resolve => setTimeout(resolve, 500))

      setProgress(100)
      setResult(apiResult)
      setStatus('success')

      showToast({
        type: apiResult.isDeepfake ? 'error' : 'success',
        title: 'Analysis Complete',
        message: `Decision: ${apiResult.decision} (Score: ${apiResult.deepfakeScore.toFixed(1)}%)`,
      })
    } catch (error: any) {
      console.error('Analysis error:', error)
      setError(error.message || 'Analysis failed')
      setStatus('error')
      showToast({
        type: 'error',
        title: 'Analysis Failed',
        message: error.message || 'An error occurred during analysis',
      })
    }
  }

  const handleReset = () => {
    setUploadedFile(null)
    setResult(null)
    setError(null)
    setStatus('idle')
    setProgress(0)
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
              <ShieldVerifyIcon className="w-12 h-12" />
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-dark-900 dark:text-white mb-4">
                Deepfake Detection
              </h1>
              <p className="text-lg text-dark-600 dark:text-dark-400 max-w-3xl">
                Sophisticated AI detects synthetic faces and video manipulations with high precision using advanced neural networks and behavioral analysis.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container-wide py-16">
        {/* Process Flow */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-8 text-center">Process Flow</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: '1', title: 'Media Upload', description: 'User uploads image or video for analysis' },
              { step: '2', title: 'Frame Analysis', description: 'AI analyzes each frame for manipulation signs' },
              { step: '3', title: 'Pattern Detection', description: 'Identify deepfake artifacts and inconsistencies' },
              { step: '4', title: 'Authenticity Score', description: 'Generate confidence score for media authenticity' }
            ].map((item, index) => (
              <Card key={index} className="text-center p-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-600 dark:bg-primary-500 text-white font-bold text-xl mb-4 mx-auto">
                  {item.step}
                </div>
                <h3 className="font-semibold text-dark-900 dark:text-white mb-2">{item.title}</h3>
                <p className="text-sm text-dark-600 dark:text-dark-400">{item.description}</p>
              </Card>
            ))}
          </div>
        </div>

        {/* Upload & Analysis Section */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-8 text-center">Upload & Analyze</h2>
          
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left Side - Upload */}
            <div>
              <FileUpload
                onFileSelect={setUploadedFile}
                acceptedTypes={['video/mp4', 'video/quicktime', 'video/x-msvideo', 'image/jpeg', 'image/png']}
                maxSize={100}
                label="Upload Video or Image"
                description="Upload a video (mp4, mov, avi) or image (jpg, png) for deepfake detection"
                icon={<ShieldVerifyIcon className="w-5 h-5" />}
                currentFile={uploadedFile}
              />
              
              {uploadedFile && status === 'idle' && (
                <button
                  onClick={handleAnalyze}
                  className="w-full mt-4 px-6 py-3 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white font-semibold rounded-lg transition-colors duration-300"
                >
                  Analyze for Deepfakes
                </button>
              )}
              
              {result && (
                <button
                  onClick={handleReset}
                  className="w-full mt-4 px-6 py-3 border border-primary-600 dark:border-primary-500 text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 font-semibold rounded-lg transition-colors duration-300"
                >
                  Analyze Another File
                </button>
              )}
            </div>

            {/* Right Side - Analysis Results */}
            <div>
              {status === 'idle' && !result && (
                <div className="h-full flex items-center justify-center bg-dark-50 dark:bg-dark-800 rounded-lg border-2 border-dashed border-dark-300 dark:border-dark-700 p-8">
                  <div className="text-center">
                    <ShieldVerifyIcon className="w-16 h-16 mx-auto text-dark-400 dark:text-dark-600 mb-4" />
                    <p className="text-dark-600 dark:text-dark-400">
                      Upload a video or image to start analysis
                    </p>
                  </div>
                </div>
              )}

              {['uploading', 'extracting', 'analyzing', 'saving'].includes(status) && (
                <div className="bg-white dark:bg-dark-800 rounded-lg border border-dark-200 dark:border-dark-700 p-6">
                  <h3 className="text-lg font-semibold text-dark-900 dark:text-white mb-6">
                    {getStatusText()}
                  </h3>
                  <LoadingSpinner size="lg" progress={progress} />
                  <div className="mt-6 space-y-3">
                    {['uploading', 'extracting', 'analyzing', 'saving'].map((step, idx) => (
                      <div key={step} className="flex items-center gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                          status === step ? 'bg-primary-600 text-white animate-pulse' :
                          ['uploading', 'extracting', 'analyzing', 'saving'].indexOf(status) > idx ? 'bg-green-500 text-white' :
                          'bg-dark-200 dark:bg-dark-700'
                        }`}>
                          {['uploading', 'extracting', 'analyzing', 'saving'].indexOf(status) > idx ? '✓' : idx + 1}
                        </div>
                        <span className={`text-sm ${
                          status === step ? 'text-primary-600 dark:text-primary-400 font-semibold' :
                          ['uploading', 'extracting', 'analyzing', 'saving'].indexOf(status) > idx ? 'text-green-600 dark:text-green-400' :
                          'text-dark-500 dark:text-dark-500'
                        }`}>
                          {step.charAt(0).toUpperCase() + step.slice(1)}...
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {status === 'success' && result && (
                <div className="bg-white dark:bg-dark-800 rounded-lg border border-dark-200 dark:border-dark-700 p-6">
                  <h3 className="text-lg font-semibold text-dark-900 dark:text-white mb-6">
                    Analysis Results
                  </h3>
                  
                  {/* Decision Badge */}
                  <div className={`inline-flex px-6 py-3 rounded-lg font-bold text-lg mb-6 ${
                    result.decision === 'FAKE' 
                      ? 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400'
                      : 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                  }`}>
                    {result.decision === 'FAKE' ? '⚠️ DEEPFAKE DETECTED' : '✓ AUTHENTIC MEDIA'}
                  </div>

                  {/* Score Display */}
                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-dark-600 dark:text-dark-400 font-medium">Deepfake Probability</span>
                      <span className="text-2xl font-bold text-dark-900 dark:text-white">
                        {result.deepfakeScore.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-4">
                      <div 
                        className={`h-4 rounded-full transition-all ${
                          result.deepfakeScore >= 50 ? 'bg-red-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${result.deepfakeScore}%` }}
                      />
                    </div>
                  </div>

                  {/* Details */}
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-dark-600 dark:text-dark-400">Confidence</span>
                      <span className="font-semibold text-dark-900 dark:text-white">
                        {(result.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-600 dark:text-dark-400">Frames Analyzed</span>
                      <span className="font-semibold text-dark-900 dark:text-white">
                        {result.framesAnalyzed}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-600 dark:text-dark-400">Processing Time</span>
                      <span className="font-semibold text-dark-900 dark:text-white">
                        {(result.processingTimeMs / 1000).toFixed(2)}s
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-600 dark:text-dark-400">Model Version</span>
                      <span className="font-semibold text-dark-900 dark:text-white">
                        {result.modelVersion}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-600 dark:text-dark-400">Device</span>
                      <span className="font-semibold text-dark-900 dark:text-white">
                        {result.device}
                      </span>
                    </div>
                  </div>

                  {/* Statistics */}
                  {result.statistics && (
                    <div className="mt-6 pt-6 border-t border-dark-200 dark:border-dark-700">
                      <h4 className="text-sm font-semibold text-dark-900 dark:text-white mb-3">
                        Frame Statistics
                      </h4>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-dark-600 dark:text-dark-400">Mean</span>
                          <div className="font-semibold text-dark-900 dark:text-white">
                            {result.statistics.mean.toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <span className="text-dark-600 dark:text-dark-400">Max</span>
                          <div className="font-semibold text-dark-900 dark:text-white">
                            {result.statistics.max.toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <span className="text-dark-600 dark:text-dark-400">Min</span>
                          <div className="font-semibold text-dark-900 dark:text-white">
                            {result.statistics.min.toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <span className="text-dark-600 dark:text-dark-400">Std Dev</span>
                          <div className="font-semibold text-dark-900 dark:text-white">
                            {result.statistics.std.toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {status === 'error' && (
                <div className="bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 p-6">
                  <h3 className="text-lg font-semibold text-red-900 dark:text-red-400 mb-4">
                    Analysis Failed
                  </h3>
                  <p className="text-red-700 dark:text-red-300">
                    {error || 'An error occurred during analysis'}
                  </p>
                  <button
                    onClick={handleReset}
                    className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                  >
                    Try Again
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Info sections... (keep existing) */}
      </div>
    </div>
    )
}
