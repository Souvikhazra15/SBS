'use client'

import React, { useState } from 'react'
import { Button } from '@/components/Button'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'
import { useRouter } from 'next/navigation'
import { AuthModal } from '@/components/AuthModal'

function AbstractIllustration() {
  return (
    <div className="relative w-full h-full max-w-md mx-auto">
      {/* Circular Video Container */}
      <div className="relative w-full aspect-square animate-float">
        <svg
          className="absolute inset-0 w-full h-full"
          viewBox="0 0 300 300"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#5b7dff" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#3746e6" stopOpacity="0.1" />
            </linearGradient>
            <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#4361ff" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#5b7dff" stopOpacity="0.2" />
            </linearGradient>
            <clipPath id="circleClip">
              <circle cx="150" cy="150" r="140" />
            </clipPath>
          </defs>

          {/* Background circle with gradient */}
          <circle cx="150" cy="150" r="140" fill="url(#grad1)" />

          {/* Video in circular form */}
          <foreignObject x="10" y="10" width="280" height="280" clipPath="url(#circleClip)">
            <div className="w-full h-full flex items-center justify-center">
              <video
                autoPlay
                loop
                muted
                playsInline
                className="w-full h-full object-cover"
              >
                <source src="/videos/🎥_KYC_Face_Scanning_–_Video_P (2).mp4" type="video/mp4" />
              </video>
            </div>
          </foreignObject>

          {/* Decorative border rings */}
          <circle cx="150" cy="150" r="145" fill="none" stroke="url(#grad2)" strokeWidth="2" opacity="0.5" />
          <circle cx="150" cy="150" r="135" fill="none" stroke="#5b7dff" strokeWidth="1" opacity="0.3" />

          {/* Corner decorative elements */}
          <circle cx="100" cy="100" r="8" fill="#7d9dff" opacity="0.6" />
          <circle cx="200" cy="100" r="8" fill="#7d9dff" opacity="0.6" />
          <circle cx="100" cy="200" r="8" fill="#7d9dff" opacity="0.6" />
          <circle cx="200" cy="200" r="8" fill="#7d9dff" opacity="0.6" />

          {/* Connecting lines */}
          <line x1="100" y1="100" x2="200" y2="100" stroke="#a3baff" strokeWidth="1" opacity="0.4" strokeDasharray="5,5" />
          <line x1="100" y1="100" x2="100" y2="200" stroke="#a3baff" strokeWidth="1" opacity="0.4" strokeDasharray="5,5" />
          <line x1="200" y1="100" x2="200" y2="200" stroke="#a3baff" strokeWidth="1" opacity="0.4" strokeDasharray="5,5" />
          <line x1="100" y1="200" x2="200" y2="200" stroke="#a3baff" strokeWidth="1" opacity="0.4" strokeDasharray="5,5" />
        </svg>
      </div>
    </div>
  )
}

export function HeroSection() {
  const { ref, isVisible } = useScrollAnimation()
  const router = useRouter()
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)
  const [user, setUser] = useState<any>(null)

  const handleAuthSuccess = (userData: any) => {
    setUser(userData)
    setIsAuthModalOpen(false)
  }

  return (
    <section
      ref={ref}
      className={`
        min-h-screen flex items-center justify-center py-20 px-4 sm:px-6 lg:px-8 
        bg-gradient-to-b from-white via-white to-primary-50/30 
        dark:from-dark-900 dark:via-dark-900 dark:to-dark-800/50
        transition-colors duration-300
        ${isVisible ? 'animate-fade-in' : 'opacity-0'}
      `}
    >
      <div className="max-w-7xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left Content */}
          <div className={`order-2 lg:order-1 ${isVisible ? 'animate-slide-up' : ''}`}>
            {/* Badge */}
            <div className="mb-6 inline-block">
              <span className="px-4 py-2 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 text-sm font-medium border border-primary-200 dark:border-primary-800/50 shadow-sm">
                ✨ AI-Powered Identity Verification
              </span>
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-dark-900 dark:text-dark-50 mb-6 leading-tight">
              Secure Onboarding
              <span className="block bg-gradient-to-r from-primary-600 to-primary-700 dark:from-primary-400 dark:to-primary-500 bg-clip-text text-transparent">in Seconds</span>
            </h1>

{/* Subtext */}
<p className="text-lg sm:text-xl text-dark-600 dark:text-dark-400 mb-8 leading-relaxed max-w-lg">
  Enterprise-grade identity verification platform with AI-powered document OCR, real-time fraud detection, and global AML compliance. Reduce onboarding friction while maintaining security.
</p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 mb-10">
            <Button
              variant="primary"
              size="lg"
              className="w-full sm:w-auto text-center"
              onClick={() => setIsAuthModalOpen(true)}
            >
              {user ? 'Start Verification' : 'Start Demo'}
            </Button>

            <Button
              variant="outline"
              size="lg"
              className="w-full sm:w-auto text-center"
              onClick={() => {
                const contactSection = document.getElementById('contact')
                contactSection?.scrollIntoView({ behavior: 'smooth' })
              }}
            >
              Contact Sales
            </Button>
          </div>

            {/* Trust indicators */}
            <div className="flex flex-wrap gap-6 text-sm text-dark-600 dark:text-dark-400">
              <div className="flex items-center gap-2">
                <span className="text-primary-600 dark:text-primary-400 font-bold">98%</span>
                <span>Accuracy Rate</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-primary-600 dark:text-primary-400 font-bold">150+</span>
                <span>Countries</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-primary-600 dark:text-primary-400 font-bold">SOC 2</span>
                <span>Certified</span>
              </div>
            </div>
          </div>

          {/* Right Illustration */}
          <div className={`order-1 lg:order-2 ${isVisible ? 'animate-fade-in' : ''}`}>
            <AbstractIllustration />
          </div>
        </div>
      </div>

      {/* Auth Modal */}
      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} onSuccess={handleAuthSuccess} />
    </section>
  )
}
