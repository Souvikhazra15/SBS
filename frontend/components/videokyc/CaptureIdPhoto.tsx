'use client'

import React, { useRef, useState, useCallback, useEffect } from 'react'
import { useToast } from '@/components/Toast'

interface CaptureIdPhotoProps {
  onCapture: (imageBlob: Blob, previewUrl: string) => void
  isProcessing?: boolean
}

export function CaptureIdPhoto({ onCapture, isProcessing = false }: CaptureIdPhotoProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [isCapturing, setIsCapturing] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const { showToast } = useToast()

  useEffect(() => {
    startCamera()
    return () => {
      stopCamera()
    }
  }, [])

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { 
          width: 1920, 
          height: 1080, 
          facingMode: 'environment' // Use back camera for ID capture
        },
        audio: false
      })
      setStream(mediaStream)
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
      }
    } catch (error) {
      console.error('[VIDEO-KYC] Error accessing camera:', error)
      showToast({
        type: 'error',
        title: 'Camera Access Denied',
        message: 'Please allow camera access to capture your ID document'
      })
    }
  }

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
  }

  const captureImage = useCallback(async () => {
    if (!videoRef.current || isCapturing || isProcessing) return

    setIsCapturing(true)
    
    try {
      console.log('[VIDEO-KYC] ID frame captured')
      
      const video = videoRef.current
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
        
        // Convert to blob for upload
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob)
            setPreviewUrl(url)
            onCapture(blob, url)
          }
        }, 'image/jpeg', 0.95)
        
        showToast({
          type: 'success',
          title: 'ID Captured',
          message: 'Processing document...'
        })
      }
    } catch (error) {
      console.error('[VIDEO-KYC] Error capturing image:', error)
      showToast({
        type: 'error',
        title: 'Capture Failed',
        message: 'Failed to capture image. Please try again.'
      })
    } finally {
      setIsCapturing(false)
    }
  }, [isCapturing, isProcessing, onCapture, showToast])

  const retake = () => {
    setPreviewUrl(null)
    startCamera()
  }

  if (previewUrl) {
    return (
      <div className="space-y-4">
        <div className="relative bg-dark-900 rounded-lg overflow-hidden">
          <img 
            src={previewUrl} 
            alt="Captured ID" 
            className="w-full h-auto"
          />
          {isProcessing && (
            <div className="absolute inset-0 bg-dark-900/80 flex items-center justify-center">
              <div className="text-center space-y-3">
                <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-white font-medium">Running OCR...</p>
                <p className="text-dark-400 text-sm">Extracting ID number from document</p>
              </div>
            </div>
          )}
        </div>
        
        {!isProcessing && (
          <button
            onClick={retake}
            className="w-full px-6 py-3 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
          >
            Retake Photo
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Camera Preview */}
      <div className="relative bg-dark-900 rounded-lg overflow-hidden aspect-video">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-full h-full object-cover"
        />
        
        {/* ID Card Overlay Frame */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="relative w-4/5 aspect-[1.6/1]">
            {/* Corner markers */}
            <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-primary-500" />
            <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-primary-500" />
            <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-primary-500" />
            <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-primary-500" />
            
            {/* Semi-transparent overlay outside frame */}
            <div className="absolute -inset-[100%] border-[100vw] border-black/60" style={{ pointerEvents: 'none' }} />
          </div>
        </div>
        
        {/* Instructions Overlay */}
        <div className="absolute top-4 left-0 right-0 text-center pointer-events-none">
          <div className="inline-block bg-dark-900/90 backdrop-blur-sm px-6 py-3 rounded-full">
            <p className="text-white font-semibold text-sm md:text-base">
              📄 Hold your ID card inside the frame
            </p>
            <p className="text-dark-300 text-xs mt-1">
              Ensure text is clear and readable
            </p>
          </div>
        </div>
        
        {/* Quality Indicators */}
        <div className="absolute bottom-20 left-0 right-0 flex justify-center gap-4 pointer-events-none">
          <div className="bg-dark-900/90 backdrop-blur-sm px-4 py-2 rounded-full flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-white text-xs">Good Lighting</span>
          </div>
          <div className="bg-dark-900/90 backdrop-blur-sm px-4 py-2 rounded-full flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-white text-xs">Focus Ready</span>
          </div>
        </div>
      </div>

      {/* Capture Button */}
      <button
        onClick={captureImage}
        disabled={isCapturing || isProcessing || !stream}
        className="w-full px-8 py-4 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white rounded-lg font-semibold text-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-105"
      >
        {isCapturing ? (
          <span className="flex items-center justify-center gap-2">
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Capturing...
          </span>
        ) : (
          <>
            📸 Capture ID Document
          </>
        )}
      </button>

      {/* Helper Tips */}
      <div className="bg-dark-800 rounded-lg p-4 space-y-2">
        <p className="text-white font-semibold text-sm">📋 Tips for best results:</p>
        <ul className="text-dark-300 text-xs space-y-1 ml-4">
          <li>• Place ID flat on a contrasting surface</li>
          <li>• Ensure good lighting without glare</li>
          <li>• Keep camera steady when capturing</li>
          <li>• Make sure all text is visible and clear</li>
        </ul>
      </div>
    </div>
  )
}
