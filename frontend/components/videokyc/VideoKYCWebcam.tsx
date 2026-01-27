'use client'

import React, { useRef, useState, useCallback, useEffect } from 'react'
import { useVideoKYCStore } from '@/lib/stores/videoKycStore'
import { useToast } from '@/components/Toast'

interface VideoKYCWebcamProps {
  onCapture?: (imageSrc: string) => void
  showCaptureButton?: boolean
}

export function VideoKYCWebcam({ onCapture, showCaptureButton = false }: VideoKYCWebcamProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [isCapturing, setIsCapturing] = useState(false)
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
        video: { width: 1280, height: 720, facingMode: 'user' },
        audio: false
      })
      setStream(mediaStream)
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
      }
    } catch (error) {
      console.error('Error accessing camera:', error)
      showToast({
        type: 'error',
        title: 'Camera Access Denied',
        message: 'Please allow camera access to continue with verification'
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
    if (!videoRef.current || isCapturing) return

    setIsCapturing(true)
    
    try {
      const video = videoRef.current
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
        const imageSrc = canvas.toDataURL('image/png')
        
        if (onCapture) {
          onCapture(imageSrc)
        }
        
        showToast({
          type: 'success',
          title: 'Image Captured',
          message: 'Processing your image...'
        })
      }
    } catch (error) {
      console.error('Error capturing image:', error)
      showToast({
        type: 'error',
        title: 'Capture Failed',
        message: 'Failed to capture image. Please try again.'
      })
    } finally {
      setIsCapturing(false)
    }
  }, [isCapturing, onCapture, showToast])

  return (
    <div className="relative w-full">
      <div className="relative bg-dark-900 rounded-lg overflow-hidden aspect-video">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-full h-full object-cover mirror-effect"
          style={{ transform: 'scaleX(-1)' }}
        />
        
        {/* Recording indicator */}
        <div className="absolute top-4 left-4 flex items-center gap-2 bg-red-600 text-white px-3 py-1.5 rounded-full">
          <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
          <span className="text-sm font-semibold">LIVE</span>
        </div>

        {/* Face detection overlay */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-80 border-2 border-primary-500 rounded-lg">
            <div className="absolute top-0 left-0 w-6 h-6 border-t-4 border-l-4 border-primary-500"></div>
            <div className="absolute top-0 right-0 w-6 h-6 border-t-4 border-r-4 border-primary-500"></div>
            <div className="absolute bottom-0 left-0 w-6 h-6 border-b-4 border-l-4 border-primary-500"></div>
            <div className="absolute bottom-0 right-0 w-6 h-6 border-b-4 border-r-4 border-primary-500"></div>
          </div>
        </div>

        {/* Capture button overlay */}
        {showCaptureButton && (
          <button
            onClick={captureImage}
            disabled={isCapturing}
            className="absolute bottom-4 left-1/2 -translate-x-1/2 w-16 h-16 rounded-full bg-white hover:bg-gray-100 disabled:bg-gray-300 shadow-lg flex items-center justify-center transition-all duration-200 hover:scale-110 disabled:scale-100"
          >
            {isCapturing ? (
              <span className="loading loading-spinner loading-md"></span>
            ) : (
              <div className="w-12 h-12 rounded-full border-4 border-red-600 bg-red-600"></div>
            )}
          </button>
        )}
      </div>

      {/* Camera guidelines */}
      <div className="mt-4 bg-dark-50 dark:bg-dark-800/50 rounded-lg p-4">
        <p className="text-sm font-semibold text-dark-700 dark:text-dark-300 mb-2">Camera Guidelines:</p>
        <ul className="text-sm text-dark-600 dark:text-dark-400 space-y-1">
          <li className="flex items-center gap-2">
            <span className="text-green-600 dark:text-green-400">✓</span>
            <span>Ensure good lighting on your face</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="text-green-600 dark:text-green-400">✓</span>
            <span>Position yourself in the center of frame</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="text-green-600 dark:text-green-400">✓</span>
            <span>Remove glasses and accessories if possible</span>
          </li>
        </ul>
      </div>
    </div>
  )
}
