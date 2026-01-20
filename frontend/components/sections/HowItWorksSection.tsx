'use client'

import React from 'react'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'

const steps = [
  {
    number: '01',
    title: 'Initiate Process',
    description: 'User starts the verification journey with a simple, intuitive interface.',
    details: ['Quick setup', 'Mobile-friendly', 'Multi-language'],
  },
  {
    number: '02',
    title: 'Capture Documents',
    description: 'Upload or scan government-issued documents with our AI-powered camera.',
    details: ['Auto-detection', 'Quality check', 'Multiple formats'],
  },
  {
    number: '03',
    title: 'Verify Identity',
    description: 'Complete liveness check and facial recognition to confirm identity.',
    details: ['3D liveness', 'Face matching', '< 2 seconds'],
  },
  {
    number: '04',
    title: 'Compliance Check',
    description: 'Automated screening against global sanction and PEP databases.',
    details: ['Real-time', 'AML/KYC ready', 'Full audit trail'],
  },
  {
    number: '05',
    title: 'Get Results',
    description: 'Instant verification results with detailed compliance report.',
    details: ['Instant decision', 'API response', 'Full transparency'],
  },
]

export function HowItWorksSection() {
  const { ref, isVisible } = useScrollAnimation()

  return (
    <section ref={ref} className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="container-wide">
        {/* Header */}
        <div className={`text-center mb-16 ${isVisible ? 'animate-slide-up' : ''}`}>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-dark-900 mb-4">
            How It Works
          </h2>
          <p className="text-lg text-dark-500 max-w-2xl mx-auto">
            A seamless verification process from start to finish, optimized for user experience and security.
          </p>
        </div>

        {/* Timeline for desktop */}
        <div className="hidden md:block">
          <div className="relative">
            {/* Connecting line */}
            <div className="absolute top-32 left-0 right-0 h-1 bg-gradient-to-r from-primary-200 via-primary-600 to-primary-200" />

            {/* Steps */}
            <div className="grid md:grid-cols-5 gap-8">
              {steps.map((step, index) => (
                <div
                  key={index}
                  className={`relative ${isVisible ? 'animate-fade-in' : 'opacity-0'}`}
                  style={{
                    animationDelay: isVisible ? `${index * 100}ms` : '0ms',
                  }}
                >
                  {/* Circle node */}
                  <div className="flex justify-center mb-8">
                    <div className="relative">
                      <div className="w-24 h-24 rounded-full bg-white border-4 border-primary-600 flex items-center justify-center shadow-lg">
                        <span className="text-2xl font-bold text-primary-600">{step.number}</span>
                      </div>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="text-center">
                    <h3 className="text-xl font-semibold text-dark-900 mb-2">
                      {step.title}
                    </h3>
                    <p className="text-sm text-dark-600 mb-4">
                      {step.description}
                    </p>
                    <ul className="space-y-1">
                      {step.details.map((detail, i) => (
                        <li key={i} className="text-xs text-primary-600 font-medium">
                          ✓ {detail}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Timeline for mobile */}
        <div className="md:hidden space-y-8">
          {steps.map((step, index) => (
            <div
              key={index}
              className={`flex gap-6 ${isVisible ? 'animate-fade-in' : 'opacity-0'}`}
              style={{
                animationDelay: isVisible ? `${index * 100}ms` : '0ms',
              }}
            >
              {/* Left line and circle */}
              <div className="flex flex-col items-center">
                <div className="w-14 h-14 rounded-full bg-primary-600 text-white flex items-center justify-center font-bold text-lg shrink-0">
                  {index + 1}
                </div>
                {index < steps.length - 1 && (
                  <div className="w-1 h-16 bg-primary-200 mt-2" />
                )}
              </div>

              {/* Right content */}
              <div className="pb-4">
                <h3 className="text-lg font-semibold text-dark-900 mb-2">
                  {step.title}
                </h3>
                <p className="text-dark-600 mb-3">
                  {step.description}
                </p>
                <ul className="space-y-1">
                  {step.details.map((detail, i) => (
                    <li key={i} className="text-xs text-primary-600 font-medium">
                      ✓ {detail}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
