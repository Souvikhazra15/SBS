'use client'

import React, { useState, useCallback } from 'react'
import { useToast } from '@/components/Toast'

interface VoiceInputProps {
  onTranscript: (text: string) => void
  language?: string
}

export function VoiceInput({ onTranscript, language = 'en-US' }: VoiceInputProps) {
  const [isListening, setIsListening] = useState(false)
  const { showToast } = useToast()

  const startListening = useCallback(() => {
    if (!('webkitSpeechRecognition' in window)) {
      showToast({
        type: 'error',
        title: 'Not Supported',
        message: 'Speech recognition is not supported in your browser'
      })
      return
    }

    const recognition = new (window as any).webkitSpeechRecognition()
    recognition.lang = language
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onstart = () => {
      setIsListening(true)
      setTimeout(() => {
        recognition.stop()
      }, 10000) // Auto-stop after 10 seconds
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      onTranscript(transcript)
      showToast({
        type: 'success',
        title: 'Voice Captured',
        message: `Heard: "${transcript}"`
      })
    }

    recognition.onerror = (error: any) => {
      console.error('Speech recognition error:', error)
      setIsListening(false)
      showToast({
        type: 'error',
        title: 'Voice Input Failed',
        message: 'Please try again or type your response'
      })
    }

    recognition.start()
  }, [language, onTranscript, showToast])

  return (
    <button
      onClick={startListening}
      disabled={isListening}
      className={`p-3 rounded-full transition-all duration-200 ${
        isListening
          ? 'bg-red-600 animate-pulse'
          : 'bg-primary-600 hover:bg-primary-700'
      } text-white disabled:cursor-not-allowed`}
      title={isListening ? 'Listening...' : 'Click to speak'}
    >
      {isListening ? (
        <svg className="w-6 h-6 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
        </svg>
      ) : (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
        </svg>
      )}
    </button>
  )
}
