'use client'

import React from 'react'
import Link from 'next/link'
import { Card } from '@/components/Card'
import { ShieldVerifyIcon, ArrowLeftIcon } from '@/components/icons/Icons'

export default function DeepfakePage() {
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
              <ShieldVerifyIcon className="w-12 h-12" />
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-dark-900 dark:text-white mb-4">
                Deepfake Detection
              </h1>
              <p className="text-lg text-dark-600 dark:text-dark-400 max-w-3xl">
                Sophisticated AI detects synthetic faces and video manipulations with high precision using advanced neural networks and behavioral analysis.
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
              { step: '1', title: 'Media Upload', description: 'User uploads image or video for analysis' },
              { step: '2', title: 'Frame Analysis', description: 'AI analyzes each frame for manipulation signs' },
              { step: '3', title: 'Pattern Detection', description: 'Identify deepfake artifacts and inconsistencies' },
              { step: '4', title: 'Authenticity Score', description: 'Generate confidence score for media authenticity' }
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
                Images and video files
              </li>
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                Live video streams
              </li>
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                Multiple file formats support
              </li>
              <li className="flex items-center gap-3">
                <span className="text-primary-600 dark:text-primary-400">•</span>
                Real-time camera feed
              </li>
            </ul>
          </Card>

          <Card className="p-6">
            <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4">Outputs</h3>
            <ul className="space-y-2 text-dark-600 dark:text-dark-400">
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Deepfake probability score
              </li>
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Manipulation detection report
              </li>
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Artifact analysis breakdown
              </li>
              <li className="flex items-center gap-3">
                <span className="text-green-600 dark:text-green-400">✓</span>
                Real-time alert system
              </li>
            </ul>
          </Card>
        </div>

        {/* AI Model */}
        <Card className="p-8 mb-16 bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 border-primary-200 dark:border-primary-700">
          <h3 className="text-xl font-semibold text-dark-900 dark:text-white mb-4">AI Technology</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-dark-800 dark:text-dark-200 mb-2">Neural Networks</h4>
              <p className="text-dark-600 dark:text-dark-400 text-sm mb-4">
                Advanced deep learning models trained on millions of synthetic and real media samples.
              </p>
              <ul className="text-sm text-dark-600 dark:text-dark-400 space-y-1">
                <li>• Transformer-based architectures</li>
                <li>• Convolutional neural networks</li>
                <li>• Temporal consistency analysis</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-dark-800 dark:text-dark-200 mb-2">Detection Methods</h4>
              <p className="text-dark-600 dark:text-dark-400 text-sm mb-4">
                Multi-layered approach combining various detection techniques for maximum accuracy.
              </p>
              <ul className="text-sm text-dark-600 dark:text-dark-400 space-y-1">
                <li>• Facial landmark consistency</li>
                <li>• Pixel-level artifact detection</li>
                <li>• Behavioral pattern analysis</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* CTA Section */}
        <div className="text-center">
          <h3 className="text-2xl font-bold text-dark-900 dark:text-white mb-4">
            Ready to Test Deepfake Detection?
          </h3>
          <p className="text-dark-600 dark:text-dark-400 mb-8 max-w-2xl mx-auto">
            Try our cutting-edge synthetic media detection system.
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