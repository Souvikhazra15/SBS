'use client'

import React, { useState, useRef } from 'react'
import Link from 'next/link'
import { Card } from '@/components/Card'
import { ShieldVerifyIcon, ArrowLeftIcon } from '@/components/icons/Icons'

export default function DeepfakePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [videoPreview, setVideoPreview] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (file: File) => {
    if (file.type.startsWith('video/')) {
      setSelectedFile(file)
      const url = URL.createObjectURL(file)
      setVideoPreview(url)
      setAnalysisResult(null)
    } else {
      alert('Please upload a video file')
    }
  }

  const handleAnalyze = async () => {
    if (!selectedFile) return

    setIsAnalyzing(true)
    
    // Simulate API call
    setTimeout(() => {
      // Mock result
      const mockResult = {
        isDeepfake: Math.random() > 0.5,
        confidence: (Math.random() * 40 + 60).toFixed(2),
        frameAnalysis: Math.floor(Math.random() * 50) + 20,
        artifacts: ['Facial inconsistency', 'Lighting mismatch', 'Temporal artifacts'].slice(0, Math.floor(Math.random() * 3) + 1)
      }
      setAnalysisResult(mockResult)
      setIsAnalyzing(false)
    }, 3000)
  }

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  const resetUpload = () => {
    setSelectedFile(null)
    setVideoPreview(null)
    setAnalysisResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
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
        {/* Upload Section */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-8 text-center">
            Analyze Video for Deepfakes
          </h2>
          
          <Card className="p-8 max-w-4xl mx-auto">
            {!selectedFile ? (
              <div
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
                  dragActive 
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' 
                    : 'border-dark-300 dark:border-dark-600 hover:border-primary-400 dark:hover:border-primary-500'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <div className="flex flex-col items-center gap-4">
                  <div className="w-20 h-20 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                    <svg className="w-10 h-10 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-dark-900 dark:text-white mb-2">
                      Drop your video here or click to browse
                    </p>
                    <p className="text-sm text-dark-600 dark:text-dark-400">
                      Supports MP4, AVI, MOV, WebM formats
                    </p>
                  </div>
                  <button
                    onClick={handleButtonClick}
                    className="px-6 py-3 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white font-semibold rounded-lg transition-colors"
                  >
                    Select Video File
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="video/*"
                    onChange={handleChange}
                    className="hidden"
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Video Preview */}
                <div className="relative">
                  {videoPreview && (
                    <video
                      src={videoPreview}
                      controls
                      className="w-full max-h-96 rounded-lg bg-black"
                    />
                  )}
                  <button
                    onClick={resetUpload}
                    className="absolute top-4 right-4 p-2 bg-red-500 hover:bg-red-600 text-white rounded-full transition-colors"
                    title="Remove video"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* File Info */}
                <div className="flex items-center justify-between p-4 bg-dark-50 dark:bg-dark-800/50 rounded-lg">
                  <div>
                    <p className="font-semibold text-dark-900 dark:text-white">{selectedFile.name}</p>
                    <p className="text-sm text-dark-600 dark:text-dark-400">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    onClick={handleAnalyze}
                    disabled={isAnalyzing}
                    className="px-6 py-3 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isAnalyzing ? (
                      <span className="flex items-center gap-2">
                        <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing...
                      </span>
                    ) : 'Analyze Video'}
                  </button>
                </div>

                {/* Analysis Results */}
                {analysisResult && (
                  <div className="p-6 bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 rounded-lg border border-primary-200 dark:border-primary-700">
                    <h3 className="text-xl font-bold text-dark-900 dark:text-white mb-4">Analysis Results</h3>
                    
                    <div className="grid md:grid-cols-2 gap-6 mb-6">
                      <div className="p-4 bg-white dark:bg-dark-800 rounded-lg">
                        <p className="text-sm text-dark-600 dark:text-dark-400 mb-2">Detection Status</p>
                        <p className={`text-2xl font-bold ${analysisResult.isDeepfake ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                          {analysisResult.isDeepfake ? 'Deepfake Detected' : 'Authentic'}
                        </p>
                      </div>
                      <div className="p-4 bg-white dark:bg-dark-800 rounded-lg">
                        <p className="text-sm text-dark-600 dark:text-dark-400 mb-2">Confidence Score</p>
                        <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                          {analysisResult.confidence}%
                        </p>
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-sm font-semibold text-dark-700 dark:text-dark-300 mb-2">
                        Frames Analyzed: {analysisResult.frameAnalysis}
                      </p>
                    </div>

                    {analysisResult.artifacts.length > 0 && (
                      <div>
                        <p className="text-sm font-semibold text-dark-700 dark:text-dark-300 mb-3">
                          Detected Artifacts:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {analysisResult.artifacts.map((artifact: string, index: number) => (
                            <span
                              key={index}
                              className="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm rounded-full"
                            >
                              {artifact}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>

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
              <Card key={index} className="text-center p-6 hover:shadow-lg transition-shadow">
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
          <Card className="p-8 bg-dark-50 dark:bg-dark-800/50 border-dark-200 dark:border-dark-700">
            <h3 className="text-2xl font-bold text-dark-900 dark:text-white mb-6">Inputs</h3>
            <ul className="space-y-4">
              <li className="flex items-start gap-3 text-dark-700 dark:text-dark-300">
                <span className="text-primary-500 dark:text-primary-400 mt-1">•</span>
                <span>Images and video files</span>
              </li>
              <li className="flex items-start gap-3 text-dark-700 dark:text-dark-300">
                <span className="text-primary-500 dark:text-primary-400 mt-1">•</span>
                <span>Live video streams</span>
              </li>
              <li className="flex items-start gap-3 text-dark-700 dark:text-dark-300">
                <span className="text-primary-500 dark:text-primary-400 mt-1">•</span>
                <span>Multiple file formats support</span>
              </li>
              <li className="flex items-start gap-3 text-dark-700 dark:text-dark-300">
                <span className="text-primary-500 dark:text-primary-400 mt-1">•</span>
                <span>Real-time camera feed</span>
              </li>
            </ul>
          </Card>

          <Card className="p-8 bg-dark-50 dark:bg-dark-800/50 border-dark-200 dark:border-dark-700">
            <h3 className="text-2xl font-bold text-dark-900 dark:text-white mb-6">Outputs</h3>
            <ul className="space-y-4">
              <li className="flex items-start gap-3 text-dark-700 dark:text-dark-300">
                <span className="text-green-500 dark:text-green-400 mt-1">✓</span>
                <span>Deepfake probability score</span>
              </li>
              <li className="flex items-start gap-3 text-dark-700 dark:text-dark-300">
                <span className="text-green-500 dark:text-green-400 mt-1">✓</span>
                <span>Manipulation detection report</span>
              </li>
              <li className="flex items-start gap-3 text-dark-700 dark:text-dark-300">
                <span className="text-green-500 dark:text-green-400 mt-1">✓</span>
                <span>Artifact analysis breakdown</span>
              </li>
              <li className="flex items-start gap-3 text-dark-700 dark:text-dark-300">
                <span className="text-green-500 dark:text-green-400 mt-1">✓</span>
                <span>Real-time alert system</span>
              </li>
            </ul>
          </Card>
        </div>

        {/* AI Technology */}
        <Card className="p-10 mb-16 bg-gradient-to-br from-primary-900/10 via-primary-800/5 to-transparent dark:from-primary-900/30 dark:via-primary-800/20 dark:to-transparent border-primary-200/50 dark:border-primary-700/50">
          <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-8 text-center">AI Technology</h2>
          <div className="grid md:grid-cols-2 gap-10">
            <div>
              <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-3">Neural Networks</h3>
              <p className="text-dark-600 dark:text-dark-400 mb-6 leading-relaxed">
                Advanced deep learning models trained on millions of synthetic and real media samples.
              </p>
              <ul className="space-y-3 text-dark-700 dark:text-dark-300">
                <li className="flex items-start gap-3">
                  <span className="text-primary-500 dark:text-primary-400 mt-1">•</span>
                  <span>Transformer-based architectures</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary-500 dark:text-primary-400 mt-1">•</span>
                  <span>Convolutional neural networks</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary-500 dark:text-primary-400 mt-1">•</span>
                  <span>Temporal consistency analysis</span>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-3">Detection Methods</h3>
              <p className="text-dark-600 dark:text-dark-400 mb-6 leading-relaxed">
                Multi-layered approach combining various detection techniques for maximum accuracy.
              </p>
              <ul className="space-y-3 text-dark-700 dark:text-dark-300">
                <li className="flex items-start gap-3">
                  <span className="text-primary-500 dark:text-primary-400 mt-1">•</span>
                  <span>Facial landmark consistency</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary-500 dark:text-primary-400 mt-1">•</span>
                  <span>Pixel-level artifact detection</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary-500 dark:text-primary-400 mt-1">•</span>
                  <span>Behavioral pattern analysis</span>
                </li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}