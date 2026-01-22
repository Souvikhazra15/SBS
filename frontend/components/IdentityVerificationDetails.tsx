'use client'

import React from 'react'

interface IdentityVerificationDetailsProps {
  onClose?: () => void
}

export function IdentityVerificationDetails({ onClose }: IdentityVerificationDetailsProps) {
  const verificationFeatures = [
    { id: 'fake-document-detection', label: 'Fake Document Detection' },
    { id: 'face-matching', label: 'Face Matching' },
    { id: 'deepfake-detection', label: 'Deepfake Detection' },
    { id: 'risk-scoring', label: 'Risk Scoring' },
  ]

  return (
    <div className="bg-white dark:bg-dark-800 rounded-lg border border-dark-200 dark:border-dark-700 p-4 sm:p-6 shadow-lg">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <div className="inline-flex p-2 sm:p-3 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 w-fit mb-3 sm:mb-4">
          <svg 
            className="w-5 h-5 sm:w-6 sm:h-6" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth="1.5" 
              d="M12 8.25c.75 0 1.5.225 2.25.675m-2.25-.675V6c0-1.5 1.5-3 3-3s3 1.5 3 3v.925M12 8.25c-.75 0-1.5.225-2.25.675m0 0V6c0-1.5-1.5-3-3-3s-3 1.5-3 3v.925m9.75 8.175v3.225c0 1.5-1.5 3-3 3h-6c-1.5 0-3-1.5-3-3v-3.225m12 0l.75-4.5h-12.75l.75 4.5m0 0l-.075.45c0 1.5.75 3 2.25 3h6c1.5 0 2.25-1.5 2.25-3l-.075-.45"
            />
          </svg>
        </div>
        <h3 className="text-base sm:text-lg font-semibold text-dark-900 dark:text-dark-50">
          Identity Verification
        </h3>
      </div>

      {/* Features List */}
      <div className="space-y-2 flex-grow">
        {verificationFeatures.map((feature) => (
          <a
            key={feature.id}
            href={`#${feature.id}`}
            className="block px-2 sm:px-3 py-2 rounded-md bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-800/30 text-primary-700 dark:text-primary-400 font-medium text-xs sm:text-sm transition-colors duration-200 flex items-center gap-2"
          >
            <span className="text-primary-500 dark:text-primary-400">•</span>
            {feature.label}
          </a>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-3 sm:mt-4 pt-3 border-t border-dark-200 dark:border-dark-700">
        <button
          onClick={onClose}
          className="text-xs text-dark-500 dark:text-dark-400 italic hover:text-dark-700 dark:hover:text-dark-300 transition-colors duration-200"
        >
          Click to close
        </button>
      </div>
    </div>
  )
}