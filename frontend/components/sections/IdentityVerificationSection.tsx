'use client'

import React from 'react'
import { Card } from '@/components/Card'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'
import {
  ShieldVerifyIcon,
  CheckCircleIcon,
} from '@/components/icons/Icons'

const verificationFeatures = [
  {
    icon: ShieldVerifyIcon,
    title: 'Fake Document Detection',
    description: 'Advanced algorithms detect fraudulent, expired, or altered government-issued documents in real-time.',
    features: [
      'Hologram & Security Feature Detection',
      'Document Tampering Detection',
      'Geolocation Verification',
      'Multi-Document Cross-Reference',
    ],
  },
  {
    icon: CheckCircleIcon,
    title: 'Face Matching',
    description: 'Cutting-edge facial recognition technology matches faces with government documents.',
    features: [
      'Liveness Detection',
      '3D Face Recognition',
      'Anti-Spoofing Technology',
      'High Accuracy Matching',
    ],
  },
  {
    icon: ShieldVerifyIcon,
    title: 'Deepfake Detection',
    description: 'Sophisticated AI detects synthetic faces and video manipulations with high precision.',
    features: [
      'Video Fraud Detection',
      'Synthetic Media Detection',
      'Behavioral Analysis',
      'Real-time Alert System',
    ],
  },
  {
    icon: CheckCircleIcon,
    title: 'Risk Scoring',
    description: 'Intelligent risk assessment algorithm evaluates verification confidence and fraud likelihood.',
    features: [
      'ML-Based Risk Calculation',
      'Customizable Thresholds',
      'Historical Data Analysis',
      'Continuous Learning',
    ],
  },
]

export function IdentityVerificationSection() {
  const { ref, isVisible } = useScrollAnimation()

  return (
    <section ref={ref} id="identity-verification" className="py-20 px-4 sm:px-6 lg:px-8 bg-white dark:bg-dark-900 transition-colors">
      <div className="container-wide">
        {/* Header */}
        <div className={`text-center mb-16 ${isVisible ? 'animate-slide-up' : ''}`}>
          <div className="inline-flex p-4 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 mb-6">
            <ShieldVerifyIcon className="w-12 h-12" />
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-dark-900 dark:text-white mb-4">
            Identity Verification Platform
          </h2>
          <p className="text-lg text-dark-600 dark:text-dark-400 max-w-3xl mx-auto">
            Our comprehensive identity verification solution combines multiple verification methods to ensure user authenticity while maintaining a seamless onboarding experience. Powered by advanced AI and machine learning.
          </p>
        </div>

        {/* Key Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-16">
          {[
            { label: 'Verification Accuracy', value: '99.8%' },
            { label: 'Processing Time', value: '<5s' },
            { label: 'Document Types', value: '150+' },
            { label: 'Countries Supported', value: '195+' },
          ].map((stat, index) => (
            <div
              key={index}
              className={`text-center p-6 rounded-lg bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800/30 transition-all duration-300 ${
                isVisible ? 'animate-fade-in' : 'opacity-0'
              }`}
              style={{ '--animation-delay': `${index * 100}ms` } as React.CSSProperties}
            >
              <p className="text-3xl font-bold text-primary-600 dark:text-primary-400 mb-2">{stat.value}</p>
              <p className="text-sm font-medium text-dark-600 dark:text-dark-400">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Verification Methods Grid */}
        <div className="mb-16">
          <h3 className="text-2xl font-bold text-dark-900 dark:text-white mb-8 text-center">Verification Methods</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {verificationFeatures.map((feature, index) => {
              const Icon = feature.icon
              return (
                <div
                  key={index}
                  className={`transition-all duration-300 ${
                    isVisible ? 'animate-fade-in' : 'opacity-0'
                  }`}
                  style={{ '--animation-delay': `${index * 150}ms` } as React.CSSProperties}
                >
                  <Card className="h-full flex flex-col hover:shadow-xl hover:scale-105 transition-all duration-300">
                    {/* Icon */}
                    <div className="mb-6 inline-flex p-4 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 w-fit">
                      <Icon className="w-8 h-8" />
                    </div>

                    {/* Title */}
                    <h4 className="text-xl font-semibold text-dark-900 dark:text-white mb-3">
                      {feature.title}
                    </h4>

                    {/* Description */}
                    <p className="text-dark-600 dark:text-dark-400 mb-6 flex-grow">
                      {feature.description}
                    </p>

                    {/* Features List */}
                    <div className="space-y-2">
                      {feature.features.map((item, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <span className="text-primary-600 dark:text-primary-400 font-bold mt-1">✓</span>
                          <span className="text-sm text-dark-700 dark:text-dark-300">{item}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>
              )
            })}
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-dark-50 dark:bg-dark-800/50 rounded-xl p-8 md:p-12">
          <h3 className="text-2xl font-bold text-dark-900 dark:text-white mb-8 text-center">How Our Verification Works</h3>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              {
                step: '1',
                title: 'Document Upload',
                description: 'User uploads government-issued ID or passport',
              },
              {
                step: '2',
                title: 'Document Analysis',
                description: 'AI analyzes authenticity and extracts information',
              },
              {
                step: '3',
                title: 'Liveness Check',
                description: 'User performs face matching and liveness detection',
              },
              {
                step: '4',
                title: 'Risk Assessment',
                description: 'System calculates risk score and renders decision',
              },
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-600 dark:bg-primary-500 text-white font-bold text-xl mb-4 mx-auto">
                  {item.step}
                </div>
                <h4 className="font-semibold text-dark-900 dark:text-white mb-2">{item.title}</h4>
                <p className="text-sm text-dark-600 dark:text-dark-400">{item.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Benefits Section */}
        <div className="mt-16">
          <h3 className="text-2xl font-bold text-dark-900 dark:text-white mb-8 text-center">Key Benefits</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                title: 'Global Compliance',
                description: 'Meets KYC, AML, and GDPR requirements across 195+ countries',
              },
              {
                title: 'Instant Verification',
                description: 'Results delivered in under 5 seconds with 99.8% accuracy',
              },
              {
                title: 'Fraud Prevention',
                description: 'Advanced AI detects deepfakes, synthetic identities, and forged documents',
              },
              {
                title: 'User Experience',
                description: 'Seamless mobile-first interface maximizes completion rates',
              },
              {
                title: 'Scalability',
                description: 'Handle millions of verifications with enterprise-grade infrastructure',
              },
              {
                title: 'Support',
                description: '24/7 customer support with dedicated account management',
              },
            ].map((benefit, index) => (
              <Card key={index} className="p-6 hover:shadow-lg transition-shadow duration-300">
                <h4 className="text-lg font-semibold text-dark-900 dark:text-white mb-3">{benefit.title}</h4>
                <p className="text-dark-600 dark:text-dark-400 text-sm">{benefit.description}</p>
              </Card>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-16 text-center">
          <p className="text-dark-600 dark:text-dark-400 mb-6">
            Ready to implement our identity verification platform?
          </p>
          <button className="px-8 py-3 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white font-semibold rounded-lg transition-colors duration-300">
            Get Started Today
          </button>
        </div>
      </div>
    </section>
  )
}
