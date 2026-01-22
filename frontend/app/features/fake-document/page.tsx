'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { Card } from '@/components/Card'
import { ShieldVerifyIcon, ArrowLeftIcon } from '@/components/icons/Icons'
import { FileUpload, UploadedFile } from '@/components/upload/FileUpload'
import { AnalysisResultDisplay, AnalysisResult } from '@/components/upload/AnalysisResult'
import { LoadingSpinner, AnalysisProgress } from '@/components/upload/LoadingSpinner'
import { verificationService, FakeDocumentResult } from '@/services/verification'
import { useToast } from '@/components/Toast'

export default function FakeDocumentPage() {
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const { showToast } = useToast()

  const [analysisSteps, setAnalysisSteps] = useState([
    { label: 'Uploading document...', status: 'pending' as const },
    { label: 'Extracting text with OCR...', status: 'pending' as const },
    { label: 'Checking for forgery...', status: 'pending' as const },
    { label: 'Saving results...', status: 'pending' as const },
  ])

  const handleAnalyze = async () => {
    if (!uploadedFile) return

    setIsAnalyzing(true)
    setProgress(0)
    setResult(null)

    // Update steps
    const updateStep = (index: number, status: 'pending' | 'processing' | 'completed' | 'error') => {
      setAnalysisSteps(prev => prev.map((step, i) => i === index ? { ...step, status } : step))
    }

    try {
      // Step 1: Uploading
      updateStep(0, 'processing')
      setProgress(10)

      // Call the API
      console.log('Starting document analysis...')
      const apiResult = await verificationService.detectFakeDocument(
        uploadedFile.file,
        undefined,
        (p) => {
          console.log(`Upload progress: ${p}%`)
          setProgress(10 + (p * 0.3)) // 10-40%
        }
      )

      updateStep(0, 'completed')
      updateStep(1, 'processing')
      setProgress(50)

      // Step 2: OCR extraction
      await new Promise(resolve => setTimeout(resolve, 800))
      updateStep(1, 'completed')
      updateStep(2, 'processing')
      setProgress(70)
      
      // Step 3: Forgery analysis
      await new Promise(resolve => setTimeout(resolve, 800))
      updateStep(2, 'completed')
      updateStep(3, 'processing')
      setProgress(90)
      
      // Step 4: Saving
      await new Promise(resolve => setTimeout(resolve, 500))
      updateStep(3, 'completed')
      setProgress(100)

      console.log('Analysis result:', apiResult)

      // Check if the API call was successful
      if (apiResult.success === false) {
        throw new Error(apiResult.error || 'Analysis failed')
      }

      // Transform API result to AnalysisResult
      const analysisResult: AnalysisResult = {
        score: apiResult.forgeryScore,
        confidence: apiResult.confidence,
        status: apiResult.isAuthentic ? 'APPROVED' : 'REJECTED',
        details: [
          { label: 'Document Type', value: apiResult.documentType || 'Unknown', type: 'info' },
          { label: 'Authenticity', value: apiResult.isAuthentic ? 'Genuine' : 'Suspicious', type: apiResult.isAuthentic ? 'success' : 'error' },
          { label: 'Forgery Score', value: `${apiResult.forgeryScore.toFixed(1)}%`, type: apiResult.forgeryScore > 70 ? 'success' : 'error' },
          { label: 'Confidence', value: `${(apiResult.confidence * 100).toFixed(1)}%`, type: 'info' },
          { label: 'Tampering Detected', value: apiResult.metadata.tamperingDetected ? 'Yes' : 'No', type: apiResult.metadata.tamperingDetected ? 'error' : 'success' },
        ],
        issues: apiResult.issues.filter(Boolean),
        recommendation: apiResult.isAuthentic 
          ? 'Document appears authentic and passes security checks.'
          : 'Document shows signs of tampering or forgery. Manual review recommended.',
      }

      setResult(analysisResult)
      showToast({
        type: 'success',
        title: 'Analysis Complete',
        message: `Forgery score: ${apiResult.forgeryScore.toFixed(1)}%`,
      })
    } catch (error: any) {
      console.error('Analysis error:', error)
      const failedIndex = analysisSteps.findIndex(s => s.status === 'processing')
      if (failedIndex >= 0) {
        updateStep(failedIndex, 'error')
      }
      showToast({
        type: 'error',
        title: 'Analysis Failed',
        message: error.message || 'No response from server. Please check your connection.',
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleReset = () => {
    setUploadedFile(null)
    setResult(null)
    setProgress(0)
    setAnalysisSteps(prev => prev.map(s => ({ ...s, status: 'pending' as const })))
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
                Fake Document Detection
              </h1>
              <p className="text-lg text-dark-600 dark:text-dark-400 max-w-3xl">
                Advanced algorithms detect fraudulent, expired, or altered government-issued documents in real-time using computer vision and machine learning.
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
              { step: '1', title: 'Document Upload', description: 'User uploads government ID or passport' },
              { step: '2', title: 'Image Analysis', description: 'AI analyzes document structure and features' },
              { step: '3', title: 'Security Check', description: 'Validate holograms, watermarks, and security elements' },
              { step: '4', title: 'Result Report', description: 'Generate fraud score and detailed analysis report' }
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

        {/* Inputs & Outputs */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          <Card className="p-6">
            <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4">Inputs</h3>
            <ul className="space-y-2 text-dark-600 dark:text-dark-400">
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                Government-issued ID documents
              </li>
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                Passports and travel documents
              </li>
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                Driver's licenses
              </li>
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                High-resolution document images
              </li>
            </ul>
          </Card>

          <Card className="p-6">
            <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4">Outputs</h3>
            <ul className="space-y-2 text-dark-600 dark:text-dark-400">
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Fraud confidence score (0-100%)
              </li>
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Document authenticity verification
              </li>
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Security feature analysis
              </li>
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Detailed fraud report
              </li>
            </ul>
          </Card>
        </div>

        {/* AI Model */}
        <Card className="p-8 mb-16 bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 border-primary-200 dark:border-primary-700">
          <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4">AI Technology</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-dark-800 dark:text-dark-200 mb-2">Computer Vision Models</h4>
              <p className="text-dark-600 dark:text-dark-400 text-sm mb-4">
                Advanced CNN architectures trained on millions of document samples from 195+ countries.
              </p>
              <ul className="text-sm text-dark-600 dark:text-dark-400 space-y-1">
                <li>• ResNet-based feature extraction</li>
                <li>• OCR with Tesseract integration</li>
                <li>• Template matching algorithms</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-dark-800 dark:text-dark-200 mb-2">Security Analysis</h4>
              <p className="text-dark-600 dark:text-dark-400 text-sm mb-4">
                Multi-layer security validation using both traditional and AI-powered techniques.
              </p>
              <ul className="text-sm text-dark-600 dark:text-dark-400 space-y-1">
                <li>• Hologram detection algorithms</li>
                <li>• Watermark verification</li>
                <li>• Font and typography analysis</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* Upload & Analysis Section */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-8 text-center">Upload & Analysis</h2>
          
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left Side - Upload */}
            <div>
              <FileUpload
                onFileSelect={setUploadedFile}
                acceptedTypes={['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']}
                maxSize={10}
                label="Upload Document"
                description="Upload a government-issued ID, passport, or driver's license for verification"
                icon={<ShieldVerifyIcon className="w-5 h-5" />}
                currentFile={uploadedFile}
              />
              
              {uploadedFile && !isAnalyzing && !result && (
                <button
                  onClick={handleAnalyze}
                  className="w-full mt-4 px-6 py-3 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white font-semibold rounded-lg transition-colors duration-300"
                >
                  Analyze Document
                </button>
              )}
              
              {result && (
                <button
                  onClick={handleReset}
                  className="w-full mt-4 px-6 py-3 border border-primary-600 dark:border-primary-500 text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 font-semibold rounded-lg transition-colors duration-300"
                >
                  Analyze Another Document
                </button>
              )}
            </div>

            {/* Right Side - Analysis */}
            <div>
              {!uploadedFile && !result && (
                <div className="h-full flex items-center justify-center bg-dark-50 dark:bg-dark-800 rounded-lg border-2 border-dashed border-dark-300 dark:border-dark-700 p-8">
                  <div className="text-center">
                    <ShieldVerifyIcon className="w-16 h-16 mx-auto text-dark-400 dark:text-dark-600 mb-4" />
                    <p className="text-dark-600 dark:text-dark-400">
                      Upload a document to start analysis
                    </p>
                  </div>
                </div>
              )}

              {isAnalyzing && (
                <div className="bg-white dark:bg-dark-800 rounded-lg border border-dark-200 dark:border-dark-700 p-6">
                  <h3 className="text-lg font-semibold text-dark-900 dark:text-white mb-6">
                    Analyzing Document...
                  </h3>
                  <LoadingSpinner size="lg" progress={progress} />
                  <div className="mt-8">
                    <AnalysisProgress steps={analysisSteps} />
                  </div>
                </div>
              )}

              {result && (
                <AnalysisResultDisplay
                  result={result}
                  title="Document Verification Results"
                  scoreLabel="Authenticity Score"
                  maxScore={100}
                />
              )}
            </div>
          </div>
        </div>

        {/* CTA Section - Removed buttons */}
        <div className="text-center">
          <h3 className="text-2xl font-bold text-dark-900 dark:text-white mb-4">
            Ready to Test Document Verification?
          </h3>
          <p className="text-dark-600 dark:text-dark-400 mb-8 max-w-2xl mx-auto">
            Try our advanced fake document detection system with your own documents using the upload section above.
          </p>
        </div>
      </div>
    </div>
  )
}