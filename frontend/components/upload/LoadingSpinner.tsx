/**
 * Loading Spinner and Progress Indicator
 * Professional loading states for analysis operations
 */

'use client'

import React from 'react'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  label?: string
  progress?: number // 0-100
}

export function LoadingSpinner({ size = 'md', label, progress }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  }

  return (
    <div className="flex flex-col items-center justify-center space-y-4 py-8">
      {/* Spinner */}
      <div className="relative">
        <div
          className={`${sizeClasses[size]} border-4 border-dark-200 dark:border-dark-700 border-t-primary-600 dark:border-t-primary-500 rounded-full animate-spin`}
        />
        {progress !== undefined && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-medium text-primary-600 dark:text-primary-400">
              {progress}%
            </span>
          </div>
        )}
      </div>

      {/* Label */}
      {label && (
        <p className="text-sm font-medium text-dark-700 dark:text-dark-300 animate-pulse">
          {label}
        </p>
      )}

      {/* Progress Bar */}
      {progress !== undefined && (
        <div className="w-full max-w-xs">
          <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-2">
            <div
              className="bg-primary-600 dark:bg-primary-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

interface LoadingSkeletonProps {
  lines?: number
  className?: string
}

export function LoadingSkeleton({ lines = 3, className = '' }: LoadingSkeletonProps) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="h-4 bg-dark-200 dark:bg-dark-700 rounded animate-pulse"
          style={{ width: `${100 - index * 10}%` }}
        />
      ))}
    </div>
  )
}

interface AnalysisProgressProps {
  steps: {
    label: string
    status: 'pending' | 'processing' | 'completed' | 'error'
  }[]
}

export function AnalysisProgress({ steps }: AnalysisProgressProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        )
      case 'processing':
        return (
          <div className="w-5 h-5 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
        )
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        )
      default:
        return (
          <div className="w-5 h-5 rounded-full border-2 border-dark-300 dark:border-dark-600" />
        )
    }
  }

  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <div key={index} className="flex items-center gap-4">
          {getStatusIcon(step.status)}
          <div className="flex-1">
            <p
              className={`text-sm font-medium ${
                step.status === 'completed'
                  ? 'text-green-600 dark:text-green-400'
                  : step.status === 'processing'
                  ? 'text-primary-600 dark:text-primary-400'
                  : step.status === 'error'
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-dark-500 dark:text-dark-500'
              }`}
            >
              {step.label}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
