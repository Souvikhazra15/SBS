'use client'

import React from 'react'
import Link from 'next/link'
import { Card } from '@/components/Card'
import { CheckCircleIcon, ArrowLeftIcon } from '@/components/icons/Icons'

export default function RiskScoringPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-dark-900 transition-colors">
      {/* Header */}
      <div className="bg-primary-50 dark:bg-primary-900/20 border-b border-primary-200 dark:border-primary-800/30">
        <div className="container-wide py-8">
          <Link 
            href="/" 
            className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 mb-6 transition-colors"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            Back to Home
          </Link>
          
          <div className="flex items-start gap-6">
            <div className="inline-flex p-4 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400">
              <CheckCircleIcon className="w-12 h-12" />
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-dark-900 dark:text-white mb-4">
                Risk Scoring
              </h1>
              <p className="text-lg text-dark-600 dark:text-dark-400 max-w-3xl">
                Intelligent risk assessment algorithm evaluates verification confidence and fraud likelihood using machine learning and historical data analysis.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container-wide py-16">
        {/* Process Flow */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-dark-900 dark:text-white mb-8 text-center">Process Flow</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: '1', title: 'Data Collection', description: 'Gather all verification results and metadata' },
              { step: '2', title: 'Feature Analysis', description: 'Analyze patterns and extract risk indicators' },
              { step: '3', title: 'ML Processing', description: 'Apply machine learning models for risk calculation' },
              { step: '4', title: 'Risk Decision', description: 'Generate final risk score and decision recommendation' }
            ].map((item, index) => (
              <Card key={index} className="text-center p-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-600 dark:bg-primary-500 text-white font-bold text-xl mb-4 mx-auto">
                  {item.step}
                </div>
                <h3 className="font-semibold text-dark-900 dark:text-white mb-2">{item.title}</h3>
                <p className="text-sm text-dark-600 dark:text-dark-400">{item.description}</p>
              </Card>
            ))}
          </div>
        </div>

        {/* Inputs & Outputs */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          <Card className="p-6">
            <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4">Inputs</h3>
            <ul className="space-y-2 text-dark-600 dark:text-dark-400">
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                Document verification results
              </li>
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                Face matching scores
              </li>
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                Deepfake detection results
              </li>
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                Historical user data
              </li>
            </ul>
          </Card>

          <Card className="p-6">
            <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4">Outputs</h3>
            <ul className="space-y-2 text-dark-600 dark:text-dark-400">
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Overall risk score (0-1000)
              </li>
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Risk category classification
              </li>
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Decision recommendation
              </li>
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Detailed risk breakdown
              </li>
            </ul>
          </Card>
        </div>

        {/* AI Model */}
        <Card className="p-8 mb-16 bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 border-primary-200 dark:border-primary-700">
          <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4">AI Technology</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-dark-800 dark:text-dark-200 mb-2">Machine Learning Models</h4>
              <p className="text-dark-600 dark:text-dark-400 text-sm mb-4">
                Ensemble of ML models trained on millions of verification sessions and fraud cases.
              </p>
              <ul className="text-sm text-dark-600 dark:text-dark-400 space-y-1">
                <li>• Gradient boosting algorithms</li>
                <li>• Random forest classifiers</li>
                <li>• Neural network ensembles</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-dark-800 dark:text-dark-200 mb-2">Risk Factors</h4>
              <p className="text-dark-600 dark:text-dark-400 text-sm mb-4">
                Comprehensive analysis of multiple risk indicators and behavioral patterns.
              </p>
              <ul className="text-sm text-dark-600 dark:text-dark-400 space-y-1">
                <li>• Verification consistency scores</li>
                <li>• Geolocation anomalies</li>
                <li>• Device fingerprinting</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* CTA Section */}
        <div className="text-center">
          <h3 className="text-2xl font-bold text-dark-900 dark:text-white mb-4">
            Ready to Test Risk Scoring?
          </h3>
          <p className="text-dark-600 dark:text-dark-400 mb-8 max-w-2xl mx-auto">
            Experience our intelligent risk assessment and decision engine.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="px-8 py-3 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white font-semibold rounded-lg transition-colors duration-300">
              Start Demo
            </button>
            <Link 
              href="/"
              className="px-8 py-3 border border-primary-600 dark:border-primary-500 text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 font-semibold rounded-lg transition-colors duration-300 inline-block"
            >
              View All Features
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}