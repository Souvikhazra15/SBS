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

const allDetailedSections = [
  {
    id: 'identity-verification',
    title: 'Identity Verification',
    icon: ShieldVerifyIcon,
    description: 'Complete identity verification solution with multi-layer authentication',
    methods: [
      {
        title: 'Fake Document Detection',
        description: 'Advanced AI algorithms analyze government-issued documents for authenticity.',
        features: ['Hologram & Security Features', 'Document Tampering Detection', 'Expiry Date Validation', 'Cross-Reference Verification'],
      },
      {
        title: 'Face Matching',
        description: 'Cutting-edge facial recognition matches user selfies with ID documents.',
        features: ['3D Liveness Detection', 'Facial Recognition AI', 'Anti-Spoofing Technology', 'High Accuracy Matching'],
      },
      {
        title: 'Deepfake Detection',
        description: 'Sophisticated AI detects synthetic faces and video manipulations.',
        features: ['Video Fraud Detection', 'Synthetic Media Analysis', 'Real-time Behavioral Analysis', 'AI-Powered Alerts'],
      },
      {
        title: 'Risk Scoring',
        description: 'Intelligent risk assessment evaluates verification confidence levels.',
        features: ['ML-Based Risk Calculation', 'Customizable Thresholds', 'Historical Pattern Analysis', 'Continuous Learning Model'],
      },
    ],
  },
  {
    id: 'fraud-prevention',
    title: 'Fraud Prevention',
    icon: ZapIcon,
    description: 'Real-time fraud detection and prevention with advanced ML models',
    methods: [
      {
        title: 'Real-time Analysis',
        description: 'Instant threat detection analyzing patterns and anomalies as they occur.',
        features: ['Pattern Recognition', 'Anomaly Detection', 'Behavioral Analysis', 'Instant Alerts'],
      },
      {
        title: 'Synthetic Identity Detection',
        description: 'Identify artificially created identities using stolen or fabricated information.',
        features: ['Cross-Database Verification', 'Identity Graph Analysis', 'Stolen Data Detection', 'Fabrication Patterns'],
      },
      {
        title: 'Device Intelligence',
        description: 'Track and analyze device fingerprints to detect suspicious behavior.',
        features: ['Device Fingerprinting', 'Location Analysis', 'Velocity Checks', 'Bot Detection'],
      },
      {
        title: 'Transaction Monitoring',
        description: 'Monitor user transactions for suspicious patterns and fraud indicators.',
        features: ['Real-time Monitoring', 'Pattern Analysis', 'Fraud Scoring', 'Automated Blocking'],
      },
    ],
  },
  {
    id: 'aml-compliance',
    title: 'AML Compliance',
    icon: CheckCircleIcon,
    description: 'Comprehensive AML/KYC compliance screening and monitoring',
    methods: [
      {
        title: 'Watchlist Screening',
        description: 'Screen against global sanctions, PEP, and watchlist databases.',
        features: ['OFAC Screening', 'PEP Database', 'Sanctions Lists', 'Adverse Media Check'],
      },
      {
        title: 'Ongoing Monitoring',
        description: 'Continuous monitoring of customer profiles against updated watchlists.',
        features: ['Daily Updates', 'Profile Monitoring', 'Alert Management', 'Case Management'],
      },
      {
        title: 'Risk Assessment',
        description: 'Automated risk scoring based on customer profile and behavior.',
        features: ['Customer Risk Profiling', 'Transaction Analysis', 'Geographic Risk', 'Industry Risk Factors'],
      },
      {
        title: 'Compliance Reporting',
        description: 'Generate comprehensive reports for regulatory compliance requirements.',
        features: ['Audit Trail', 'SAR Generation', 'Regulatory Reports', 'Documentation Management'],
      },
    ],
  },
  {
    id: 'document-ocr',
    title: 'Document OCR',
    icon: DocumentIcon,
    description: 'Intelligent document capture and data extraction technology',
    methods: [
      {
        title: 'Multi-Language Support',
        description: 'Extract data from documents in 100+ languages with high accuracy.',
        features: ['100+ Languages', 'Character Recognition', 'Script Detection', 'Translation Support'],
      },
      {
        title: 'Automatic Extraction',
        description: 'AI-powered extraction of structured data from various document types.',
        features: ['Field Detection', 'Data Parsing', 'Format Recognition', 'Auto-Categorization'],
      },
      {
        title: 'Quality Validation',
        description: 'Ensure document quality and readability before processing.',
        features: ['Image Quality Check', 'Blur Detection', 'Glare Detection', 'Completeness Verification'],
      },
      {
        title: 'Document Classification',
        description: 'Automatically classify and categorize document types.',
        features: ['AI Classification', '150+ Document Types', 'Custom Categories', 'Version Detection'],
      },
    ],
  },
  {
    id: 'manual-review',
    title: 'Manual Review',
    icon: CheckCircleIcon,
    description: 'Expert human review for complex cases and edge scenarios',
    methods: [
      {
        title: 'Expert Review Queue',
        description: 'Dedicated team of verification experts for manual case review.',
        features: ['24/7 Review Team', 'Priority Queuing', 'Quality Assurance', 'Fast Turnaround'],
      },
      {
        title: 'Case Management',
        description: 'Comprehensive case management system for tracking and resolution.',
        features: ['Case Dashboard', 'Status Tracking', 'Note Documentation', 'History Timeline'],
      },
      {
        title: 'Decision Support',
        description: 'AI-assisted tools to help reviewers make informed decisions.',
        features: ['AI Recommendations', 'Risk Indicators', 'Similar Cases', 'Decision Templates'],
      },
      {
        title: 'Quality Control',
        description: 'Multi-layer quality control process ensuring accuracy.',
        features: ['Dual Review', 'Quality Metrics', 'Reviewer Training', 'Audit Process'],
      },
    ],
  },
  {
    id: 'explainable-results',
    title: 'Explainable Results',
    icon: DocumentIcon,
    description: 'Transparent AI decisions with detailed explanations and reasoning',
    methods: [
      {
        title: 'Decision Transparency',
        description: 'Clear explanations for every verification decision made by the system.',
        features: ['Decision Breakdown', 'Confidence Scores', 'Factor Analysis', 'Visual Explanations'],
      },
      {
        title: 'Audit Trail',
        description: 'Complete audit trail of all verification steps and decisions.',
        features: ['Step-by-Step Logs', 'Timestamp Records', 'User Actions', 'System Events'],
      },
      {
        title: 'Compliance Documentation',
        description: 'Detailed documentation for regulatory compliance and audits.',
        features: ['Regulatory Reports', 'Evidence Collection', 'Compliance Proof', 'Export Options'],
      },
      {
        title: 'User Communication',
        description: 'Clear communication to users about verification status and requirements.',
        features: ['Status Updates', 'Action Items', 'Rejection Reasons', 'Appeal Process'],
      },
    ],
  },
  {
    id: 'secure-scalable-system',
    title: 'Secure & Scalable System',
    icon: ShieldVerifyIcon,
    description: 'Enterprise-grade security and unlimited scalability',
    methods: [
      {
        title: 'Data Encryption',
        description: 'Military-grade encryption for data at rest and in transit.',
        features: ['AES-256 Encryption', 'TLS 1.3', 'Key Management', 'Zero-Knowledge Architecture'],
      },
      {
        title: 'Infrastructure Security',
        description: 'Robust infrastructure with multiple layers of security protection.',
        features: ['DDoS Protection', 'Firewall Rules', 'Network Isolation', 'Intrusion Detection'],
      },
      {
        title: 'Scalability',
        description: 'Auto-scaling infrastructure handling millions of verifications.',
        features: ['Auto-Scaling', 'Load Balancing', 'Global CDN', '99.99% Uptime SLA'],
      },
      {
        title: 'Compliance Certifications',
        description: 'Industry-leading security and compliance certifications.',
        features: ['SOC 2 Type II', 'ISO 27001', 'GDPR Compliant', 'PCI DSS'],
      },
    ],
  },
  {
    id: 'integration-api',
    title: 'Integration & API',
    icon: ZapIcon,
    description: 'Developer-friendly APIs and seamless integration options',
    methods: [
      {
        title: 'RESTful API',
        description: 'Well-documented RESTful API for easy integration.',
        features: ['REST Endpoints', 'JSON Responses', 'Webhook Support', 'Rate Limiting'],
      },
      {
        title: 'SDK Support',
        description: 'Native SDKs for popular programming languages and platforms.',
        features: ['JavaScript SDK', 'Python SDK', 'iOS SDK', 'Android SDK'],
      },
      {
        title: 'No-Code Integration',
        description: 'Easy integration options without writing any code.',
        features: ['Web Widget', 'iFrame Embed', 'QR Code Link', 'Email Link'],
      },
      {
        title: 'Testing Tools',
        description: 'Comprehensive testing environment and developer tools.',
        features: ['Sandbox Environment', 'Test Data', 'API Playground', 'Debug Console'],
      },
    ],
  },
]

export function FeaturesSection() {
  const { ref, isVisible } = useScrollAnimation()
  const [selectedFeature, setSelectedFeature] = useState<number | null>(null)
  const [hoveredFeature, setHoveredFeature] = useState<number | null>(null)
  const [currentSlide, setCurrentSlide] = useState(0)

  const handleFeatureClick = (index: number) => {
    setSelectedFeature(selectedFeature === index ? null : index)
    if (selectedFeature !== index) {
      setCurrentSlide(0) // Reset slide when opening a new feature
    }
  }

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % allDetailedSections.length)
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + allDetailedSections.length) % allDetailedSections.length)
  }

  return (
    <section ref={ref} id="features" className="py-12 sm:py-16 lg:py-20 px-4 sm:px-6 lg:px-8 bg-dark-50 dark:bg-dark-900/50 transition-colors">
      <div className="container-wide">
        {/* Header */}
        <div className={`text-center mb-12 sm:mb-16 ${isVisible ? 'animate-slide-up' : ''}`}>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl xl:text-5xl font-bold text-dark-900 dark:text-dark-50 mb-4">
            Powerful Features for Every Need
          </h2>
          <p className="text-base sm:text-lg text-dark-500 dark:text-dark-400 max-w-2xl mx-auto px-4">
            Comprehensive tools designed to streamline your onboarding process while maintaining the highest security standards.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
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
                    isActive ? 'ring-2 ring-primary-500 dark:ring-primary-400 shadow-lg scale-105' : ''
                  }`}
                >
                  {!isActive ? (
                    <>
                      {/* Icon */}
                      <div className="mb-4 sm:mb-6 inline-flex p-2 sm:p-3 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 w-fit transition-transform duration-300 hover:scale-110">
                        <Icon className="w-5 h-5 sm:w-6 sm:h-6" />
                      </div>

                      {/* Title */}
                      <h3 className="text-lg sm:text-xl font-semibold text-dark-900 dark:text-dark-50 mb-2 sm:mb-3">
                        {feature.title}
                      </h3>

                      {/* Description */}
                      <p className="text-sm sm:text-base text-dark-600 dark:text-dark-400 mb-4 sm:mb-6 flex-grow leading-relaxed">
                        {feature.description}
                      </p>

                      {/* Highlights */}
                      <div className="flex flex-wrap gap-2">
                        {feature.highlights.map((highlight, i) => (
                          <span
                            key={i}
                            className="px-2 sm:px-3 py-1 text-xs font-medium bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 rounded-full"
                          >
                            {highlight}
                          </span>
                        ))}
                      </div>
                    </>
                  ) : (
                    <>
                      {/* Active State - Show Sections */}
                      <div className="mb-4 sm:mb-6">
                        <div className="inline-flex p-2 sm:p-3 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 w-fit mb-3 sm:mb-4">
                          <Icon className="w-5 h-5 sm:w-6 sm:h-6" />
                        </div>
                        <h3 className="text-base sm:text-lg font-semibold text-dark-900 dark:text-dark-50">
                          {feature.title}
                        </h3>
                      </div>

                      {/* Detailed Sections */}
                      <div className="space-y-2 flex-grow">
                        {feature.sections.map((section, i) => (
                          <a
                            key={i}
                            href={`#${section.toLowerCase().replace(/\s+/g, '-')}`}
                            className="bliock px-2 sm:px-3 py-2 rounded-md bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-800/30 text-primary-700 dark:text-primary-400 font-medium text-xs sm:text-sm transition-colors duration-200 items-center gap-2"
                          >
                            <span className="text-primary-500 dark:text-primary-400">•</span>
                            {section}
                          </a>
                        ))}
                      </div>

                      {/* Click to Close Hint */}
                      <div className="mt-3 sm:mt-4 pt-3 border-t border-dark-200 dark:border-dark-700">
                        <p className="text-xs text-dark-500 dark:text-dark-400 italic">Click to close</p>
                      </div>
                    </>
                  )}
                </Card>
              </div>
            )
          })}
        </div>

        {/* Identity Verification Detailed Section */}
        {selectedFeature === 0 && (
          <div className="mt-12 sm:mt-16 animate-fade-in">
            <div className="text-center mb-8 sm:mb-12">
              <h3 className="text-xl sm:text-2xl font-bold text-dark-900 dark:text-dark-50 mb-2 sm:mb-3">Verification Methods</h3>
              <p className="text-sm sm:text-base text-dark-600 dark:text-dark-400 px-4">Explore our comprehensive identity verification capabilities</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              {verificationMethods.map((method, index) => (
                <div
                  key={index}
                  style={{ '--animation-delay': `${index * 100}ms` } as React.CSSProperties}
                >
                  <Card
                    className="flex flex-col h-full hover:shadow-lg transition-all duration-300"
                  >
                  <div className="inline-flex p-2 sm:p-3 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 w-fit mb-3 sm:mb-4">
                    <CheckCircleIcon className="w-5 h-5 sm:w-6 sm:h-6" />
                  </div>
                  <h4 className="text-base sm:text-lg font-semibold text-dark-900 dark:text-dark-50 mb-2">
                    {method.title}
                  </h4>
                  <p className="text-dark-600 dark:text-dark-400 text-xs sm:text-sm mb-3 sm:mb-4 flex-grow leading-relaxed">
                    {method.description}
                  </p>
                  <div className="space-y-2">
                    {method.features.map((feature, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary-600 dark:bg-primary-400 flex-shrink-0"></span>
                        <span className="text-xs text-dark-700 dark:text-dark-300">{feature}</span>
                      </div>
                    ))}
                  </div>
                </Card>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All 8 Sections Carousel */}
        {selectedFeature !== null && (
          <div className="mt-12 sm:mt-16 animate-fade-in">
            <div className="text-center mb-8 sm:mb-12">
              <h3 className="text-xl sm:text-2xl font-bold text-dark-900 dark:text-dark-50 mb-2 sm:mb-3">
                All Feature Details
              </h3>
              <p className="text-sm sm:text-base text-dark-600 dark:text-dark-400 px-4">
                Explore all 8 comprehensive features
              </p>
            </div>

            {/* Carousel Container */}
            <div className="relative">
              {/* Current Slide */}
              <div className="overflow-hidden">
                <div className="px-2">
                  {allDetailedSections.map((section, sectionIndex) => {
                    const SectionIcon = section.icon
                    return (
                      <div 
                        key={section.id}
                        className={`${currentSlide === sectionIndex ? 'block' : 'hidden'} transition-opacity duration-500`}
                      >
                        {/* Section Header */}
                        <div className="text-center mb-8">
                          <div className="inline-flex p-4 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 mb-4">
                            <SectionIcon className="w-10 h-10" />
                          </div>
                          <h4 className="text-xl sm:text-2xl font-bold text-dark-900 dark:text-dark-50 mb-2">
                            {section.title}
                          </h4>
                          <p className="text-sm sm:text-base text-dark-600 dark:text-dark-400 max-w-2xl mx-auto">
                            {section.description}
                          </p>
                        </div>

                        {/* Methods Grid */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
                          {section.methods.map((method, methodIndex) => (
                            <Card
                              key={methodIndex}
                              className="flex flex-col h-full hover:shadow-lg transition-all duration-300"
                            >
                              <div className="inline-flex p-2 sm:p-3 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 w-fit mb-3 sm:mb-4">
                                <CheckCircleIcon className="w-5 h-5 sm:w-6 sm:h-6" />
                              </div>
                              <h5 className="text-base sm:text-lg font-semibold text-dark-900 dark:text-dark-50 mb-2">
                                {method.title}
                              </h5>
                              <p className="text-dark-600 dark:text-dark-400 text-xs sm:text-sm mb-3 sm:mb-4 flex-grow leading-relaxed">
                                {method.description}
                              </p>
                              <div className="space-y-2">
                                {method.features.map((feature, i) => (
                                  <div key={i} className="flex items-start gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-primary-600 dark:bg-primary-400 flex-shrink-0 mt-1.5"></span>
                                    <span className="text-xs text-dark-700 dark:text-dark-300">{feature}</span>
                                  </div>
                                ))}
                              </div>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Navigation Arrows */}
              <div className="flex items-center justify-center gap-4 mt-8 sm:mt-12">
                <button
                  onClick={prevSlide}
                  className="p-3 rounded-full bg-primary-600 dark:bg-primary-500 text-white hover:bg-primary-700 dark:hover:bg-primary-600 transition-all duration-200 shadow-md hover:shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Previous section"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>

                {/* Slide Indicators */}
                <div className="flex gap-2">
                  {allDetailedSections.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentSlide(index)}
                      className={`transition-all duration-300 ${
                        currentSlide === index
                          ? 'w-8 h-2 bg-primary-600 dark:bg-primary-400'
                          : 'w-2 h-2 bg-dark-300 dark:bg-dark-600 hover:bg-dark-400 dark:hover:bg-dark-500'
                      } rounded-full`}
                      aria-label={`Go to ${allDetailedSections[index].title}`}
                    />
                  ))}
                </div>

                <button
                  onClick={nextSlide}
                  className="p-3 rounded-full bg-primary-600 dark:bg-primary-500 text-white hover:bg-primary-700 dark:hover:bg-primary-600 transition-all duration-200 shadow-md hover:shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Next section"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>

              {/* Section Counter */}
              <div className="text-center mt-4">
                <p className="text-sm text-dark-500 dark:text-dark-400">
                  {currentSlide + 1} / {allDetailedSections.length}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
