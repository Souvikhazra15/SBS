'use client'

import React, { useState } from 'react'
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
    sections: ['Fake Document Detection', 'Face Matching', 'Deepfake Detection', 'Risk Scoring'],
  },
  {
    icon: ZapIcon,
    title: 'Fraud Prevention',
    description: 'Real-time threat detection using machine learning models to identify suspicious patterns and prevent synthetic fraud.',
    highlights: ['Real-time Analysis', 'Behavioral Detection', 'Risk Scoring'],
    sections: ['Risk Scoring', 'Manual Review', 'Explainable Results', 'Secure & Scalable System'],
  },
  {
    icon: CheckCircleIcon,
    title: 'AML Compliance',
    description: 'Stay compliant with global AML/KYC regulations with automated screening against OFAC and PEP databases.',
    highlights: ['Database Screening', 'Watchlist Matching', 'Compliance Reports'],
    sections: ['Manual Review', 'Explainable Results', 'Secure & Scalable System', 'Face Matching'],
  },
  {
    icon: DocumentIcon,
    title: 'Document OCR',
    description: 'Intelligent document capture and extraction with support for 100+ document types across all major countries.',
    highlights: ['Multi-language', 'Automatic Extraction', 'Quality Validation'],
    sections: ['Fake Document Detection', 'Risk Scoring', 'Explainable Results', 'Secure & Scalable System'],
  },
]

const verificationMethods = [
  {
    title: 'Fake Document Detection',
    description: 'Advanced algorithms detect fraudulent, expired, or altered government-issued documents.',
    features: ['Hologram Detection', 'Tampering Detection', 'Geolocation Verification'],
  },
  {
    title: 'Face Matching',
    description: 'Cutting-edge facial recognition technology matches faces with government documents.',
    features: ['Liveness Detection', '3D Recognition', 'Anti-Spoofing'],
  },
  {
    title: 'Deepfake Detection',
    description: 'Sophisticated AI detects synthetic faces and video manipulations with precision.',
    features: ['Video Detection', 'Synthetic Media', 'Behavioral Analysis'],
  },
  {
    title: 'Risk Scoring',
    description: 'Intelligent risk assessment evaluates verification confidence and fraud likelihood.',
    features: ['ML-Based Calculation', 'Customizable Thresholds', 'Continuous Learning'],
  },
]

export function FeaturesSection() {
  const { ref, isVisible } = useScrollAnimation()
  const [selectedFeature, setSelectedFeature] = useState<number | null>(null)
  const [hoveredFeature, setHoveredFeature] = useState<number | null>(null)

  const handleFeatureClick = (index: number) => {
    setSelectedFeature(selectedFeature === index ? null : index)
  }

  return (
    <section ref={ref} id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-dark-50">
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
            const isActive = selectedFeature === index || hoveredFeature === index
            return (
              <div 
                key={index}
                style={{ '--animation-delay': `${index * 100}ms` } as React.CSSProperties}
                onMouseEnter={() => setHoveredFeature(index)}
                onMouseLeave={() => setHoveredFeature(null)}
                onClick={() => handleFeatureClick(index)}
                className="cursor-pointer"
              >
                <Card
                  className={`flex flex-col h-full transition-all duration-300 ${
                    isVisible ? 'animate-fade-in' : 'opacity-0'
                  } ${
                    isActive ? 'ring-2 ring-primary-500 shadow-lg scale-105' : ''
                  }`}
                >
                  {!isActive ? (
                    <>
                      {/* Icon */}
                      <div className="mb-6 inline-flex p-3 rounded-lg bg-primary-100 text-primary-600 w-fit transition-transform duration-300 group-hover:scale-110">
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
                    </>
                  ) : (
                    <>
                      {/* Active State - Show Sections */}
                      <div className="mb-6">
                        <div className="inline-flex p-3 rounded-lg bg-primary-100 text-primary-600 w-fit mb-4">
                          <Icon className="w-6 h-6" />
                        </div>
                        <h3 className="text-lg font-semibold text-dark-900">
                          {feature.title}
                        </h3>
                      </div>

                      {/* Detailed Sections */}
                      <div className="space-y-2 flex-grow">
                        {feature.sections.map((section, i) => (
                          <button
                            key={i}
                            className="w-full text-left px-3 py-2 rounded-md bg-primary-50 hover:bg-primary-100 text-primary-700 font-medium text-sm transition-colors duration-200 flex items-center gap-2"
                          >
                            <span className="text-primary-500">•</span>
                            {section}
                          </button>
                        ))}
                      </div>

                      {/* Click to Close Hint */}
                      <div className="mt-4 pt-3 border-t border-dark-200">
                        <p className="text-xs text-dark-500 italic">Click to close</p>
                      </div>
                    </>
                  )}
                </Card>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
