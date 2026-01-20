'use client'

import React from 'react'
import { Button } from '@/components/Button'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'

function AbstractIllustration() {
  return (
    <svg
      className="w-full h-full max-w-md mx-auto animate-float"
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
      </defs>

      {/* Background circle */}
      <circle cx="150" cy="150" r="140" fill="url(#grad1)" />

      {/* Abstract shapes - representing verification */}
      <rect x="80" y="80" width="140" height="140" rx="20" fill="none" stroke="#5b7dff" strokeWidth="2" opacity="0.6" />

      {/* Inner shield/checkmark concept */}
      <g opacity="0.8">
        <path
          d="M150 100 L180 130 L160 160 M140 155 L145 160 L155 150"
          stroke="#4361ff"
          strokeWidth="3"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>

      {/* Circular elements - representing flow */}
      <circle cx="100" cy="100" r="8" fill="#7d9dff" opacity="0.6" />
      <circle cx="200" cy="100" r="8" fill="#7d9dff" opacity="0.6" />
      <circle cx="100" cy="200" r="8" fill="#7d9dff" opacity="0.6" />
      <circle cx="200" cy="200" r="8" fill="#7d9dff" opacity="0.6" />

      {/* Connecting lines */}
      <line x1="100" y1="100" x2="200" y2="100" stroke="#a3baff" strokeWidth="1" opacity="0.4" strokeDasharray="5,5" />
      <line x1="100" y1="100" x2="100" y2="200" stroke="#a3baff" strokeWidth="1" opacity="0.4" strokeDasharray="5,5" />
      <line x1="200" y1="100" x2="200" y2="200" stroke="#a3baff" strokeWidth="1" opacity="0.4" strokeDasharray="5,5" />
      <line x1="100" y1="200" x2="200" y2="200" stroke="#a3baff" strokeWidth="1" opacity="0.4" strokeDasharray="5,5" />

      {/* Central decorative element */}
      <g opacity="0.7">
        <circle cx="150" cy="150" r="30" fill="none" stroke="url(#grad2)" strokeWidth="2" />
        <circle cx="150" cy="150" r="20" fill="none" stroke="#5b7dff" strokeWidth="1" opacity="0.5" />
      </g>
    </svg>
  )
}

export function HeroSection() {
  const { ref, isVisible } = useScrollAnimation()

  return (
    <section
      ref={ref}
      className={`
        min-h-screen flex items-center justify-center py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-white to-primary-50/30
        ${isVisible ? 'animate-fade-in' : 'opacity-0'}
      `}
    >
      <div className="max-w-7xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left Content */}
          <div className={`order-2 lg:order-1 ${isVisible ? 'animate-slide-up' : ''}`}>
            {/* Badge */}
            <div className="mb-6 inline-block">
              <span className="px-4 py-2 rounded-full bg-primary-100 text-primary-700 text-sm font-medium">
                ✨ AI-Powered Identity Verification
              </span>
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-dark-900 mb-6 leading-tight">
              Secure Onboarding
              <span className="block gradient-text">in Seconds</span>
            </h1>

            {/* Subtext */}
            <p className="text-lg sm:text-xl text-dark-500 mb-8 leading-relaxed max-w-lg">
              Enterprise-grade identity verification platform with AI-powered document OCR, real-time fraud detection, and global AML compliance. Reduce onboarding friction while maintaining security.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <Button
                variant="primary"
                size="lg"
                className="w-full sm:w-auto text-center"
                onClick={() => {
                  const demoSection = document.getElementById('demo')
                  demoSection?.scrollIntoView({ behavior: 'smooth' })
                }}
              >
                Start Demo
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
            <div className="flex flex-wrap gap-6 text-sm text-dark-600">
              <div className="flex items-center gap-2">
                <span className="text-primary-600 font-bold">98%</span>
                <span>Accuracy Rate</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-primary-600 font-bold">150+</span>
                <span>Countries</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-primary-600 font-bold">SOC 2</span>
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
    </section>
  )
}
