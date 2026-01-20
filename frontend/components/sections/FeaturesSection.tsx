'use client'

import React from 'react'
import { Card } from '@/components/Card'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'
import {
  ShieldVerifyIcon,
  ZapIcon,
  CheckCircleIcon,
  DocumentIcon,
} from '@/components/icons/Icons'

const features = [
  {
    icon: ShieldVerifyIcon,
    title: 'Identity Verification',
    description: 'Verify user identity through government-issued documents with advanced liveness detection and biometric matching.',
    highlights: ['Liveness Detection', 'Facial Recognition', 'Global Documents'],
  },
  {
    icon: ZapIcon,
    title: 'Fraud Prevention',
    description: 'Real-time threat detection using machine learning models to identify suspicious patterns and prevent synthetic fraud.',
    highlights: ['Real-time Analysis', 'Behavioral Detection', 'Risk Scoring'],
  },
  {
    icon: CheckCircleIcon,
    title: 'AML Compliance',
    description: 'Stay compliant with global AML/KYC regulations with automated screening against OFAC and PEP databases.',
    highlights: ['Database Screening', 'Watchlist Matching', 'Compliance Reports'],
  },
  {
    icon: DocumentIcon,
    title: 'Document OCR',
    description: 'Intelligent document capture and extraction with support for 100+ document types across all major countries.',
    highlights: ['Multi-language', 'Automatic Extraction', 'Quality Validation'],
  },
]

export function FeaturesSection() {
  const { ref, isVisible } = useScrollAnimation()

  return (
    <section ref={ref} className="py-20 px-4 sm:px-6 lg:px-8 bg-dark-50">
      <div className="container-wide">
        {/* Header */}
        <div className={`text-center mb-16 ${isVisible ? 'animate-slide-up' : ''}`}>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-dark-900 mb-4">
            Powerful Features for Every Need
          </h2>
          <p className="text-lg text-dark-500 max-w-2xl mx-auto">
            Comprehensive tools designed to streamline your onboarding process while maintaining the highest security standards.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div style={{ '--animation-delay': `${index * 100}ms` } as React.CSSProperties}>
                <Card
                  key={index}
                  className={`flex flex-col h-full ${isVisible ? 'animate-fade-in' : 'opacity-0'}`}
                >
                {/* Icon */}
                <div className="mb-6 inline-flex p-3 rounded-lg bg-primary-100 text-primary-600 w-fit">
                  <Icon className="w-6 h-6" />
                </div>

                {/* Title */}
                <h3 className="text-xl font-semibold text-dark-900 mb-3">
                  {feature.title}
                </h3>

                {/* Description */}
                <p className="text-dark-600 mb-6 flex-grow">
                  {feature.description}
                </p>

                {/* Highlights */}
                <div className="flex flex-wrap gap-2">
                  {feature.highlights.map((highlight, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 text-xs font-medium bg-primary-50 text-primary-700 rounded-full"
                    >
                      {highlight}
                    </span>
                  ))}
                </div>
                </Card>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
