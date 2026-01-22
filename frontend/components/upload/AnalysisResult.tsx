/**
 * Analysis Result Component
 * Displays verification results with scores, confidence, and status
 */

'use client'

import React from 'react'

export interface AnalysisResult {
  score: number
  confidence: number
  status: 'APPROVED' | 'REJECTED' | 'REVIEW_REQUIRED' | 'PENDING'
  details?: {
    label: string
    value: string | number
    type?: 'success' | 'warning' | 'error' | 'info'
  }[]
  issues?: string[]
  recommendation?: string
}

interface AnalysisResultDisplayProps {
  result: AnalysisResult
  title: string
  scoreLabel?: string
  maxScore?: number
}

export function AnalysisResultDisplay({
  result,
  title,
  scoreLabel = 'Score',
  maxScore = 100,
}: AnalysisResultDisplayProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
      case 'REJECTED':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
      case 'REVIEW_REQUIRED':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
      default:
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 dark:text-green-400'
    if (score >= 60) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getDetailTypeColor = (type?: string) => {
    switch (type) {
      case 'success':
        return 'text-green-600 dark:text-green-400'
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400'
      case 'error':
        return 'text-red-600 dark:text-red-400'
      default:
        return 'text-dark-600 dark:text-dark-400'
    }
  }

  return (
    <div className="bg-white dark:bg-dark-800 rounded-lg border border-dark-200 dark:border-dark-700 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-dark-900 dark:text-white">{title}</h3>
        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(result.status)}`}>
          {result.status.replace('_', ' ')}
        </span>
      </div>

      {/* Score Display */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-dark-50 dark:bg-dark-900/50 rounded-lg p-4">
          <p className="text-sm text-dark-600 dark:text-dark-400 mb-1">{scoreLabel}</p>
          <p className={`text-3xl font-bold ${getScoreColor(result.score)}`}>
            {result.score.toFixed(1)}
            <span className="text-lg text-dark-500 dark:text-dark-500">/{maxScore}</span>
          </p>
        </div>
        
        <div className="bg-dark-50 dark:bg-dark-900/50 rounded-lg p-4">
          <p className="text-sm text-dark-600 dark:text-dark-400 mb-1">Confidence</p>
          <p className={`text-3xl font-bold ${getScoreColor(result.confidence)}`}>
            {result.confidence.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-dark-600 dark:text-dark-400">
          <span>{scoreLabel}</span>
          <span>{result.score.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-dark-200 dark:bg-dark-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${
              result.score >= 80
                ? 'bg-green-500 dark:bg-green-600'
                : result.score >= 60
                ? 'bg-yellow-500 dark:bg-yellow-600'
                : 'bg-red-500 dark:bg-red-600'
            }`}
            style={{ width: `${result.score}%` }}
          />
        </div>
      </div>

      {/* Details */}
      {result.details && result.details.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-dark-900 dark:text-white">Details</p>
          <div className="space-y-2">
            {result.details.map((detail, index) => (
              <div
                key={index}
                className="flex justify-between items-center py-2 border-b border-dark-100 dark:border-dark-700 last:border-0"
              >
                <span className="text-sm text-dark-600 dark:text-dark-400">{detail.label}</span>
                <span className={`text-sm font-medium ${getDetailTypeColor(detail.type)}`}>
                  {detail.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Issues */}
      {result.issues && result.issues.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-red-600 dark:text-red-400">Issues Detected</p>
          <ul className="space-y-1">
            {result.issues.map((issue, index) => (
              <li key={index} className="text-sm text-dark-600 dark:text-dark-400 flex items-start gap-2">
                <span className="text-red-500 dark:text-red-400 mt-0.5">⚠</span>
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendation */}
      {result.recommendation && (
        <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-4">
          <p className="text-sm font-medium text-primary-900 dark:text-primary-300 mb-1">
            Recommendation
          </p>
          <p className="text-sm text-primary-700 dark:text-primary-400">{result.recommendation}</p>
        </div>
      )}
    </div>
  )
}
