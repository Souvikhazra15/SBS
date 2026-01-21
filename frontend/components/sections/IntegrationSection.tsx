'use client'

import React from 'react'
import { Card } from '@/components/Card'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'
import { APIIcon } from '@/components/icons/Icons'

const integrations = [
  {
    label: 'REST API',
    description: 'Standard REST endpoints for complete integration control.',
    example: 'GET /api/verification/{id}',
    color: 'from-blue-400 to-blue-600',
  },
  {
    label: 'Webhooks',
    description: 'Real-time event notifications for verification updates.',
    example: 'POST /webhook/verification',
    color: 'from-indigo-400 to-indigo-600',
  },
  {
    label: 'SDKs',
    description: 'Client libraries for JavaScript, Python, Go, and more.',
    example: 'npm install @verifyai/sdk',
    color: 'from-purple-400 to-purple-600',
  },
  {
    label: 'Dashboard',
    description: 'Beautiful admin panel for monitoring and management.',
    example: 'dashboard.verifyai.io',
    color: 'from-pink-400 to-pink-600',
  },
]

export function IntegrationSection() {
  const { ref, isVisible } = useScrollAnimation()

  return (
    <section ref={ref} id="integration" className="py-20 px-4 sm:px-6 lg:px-8 bg-dark-50 dark:bg-dark-900/50 transition-colors">
      <div className="container-wide">
        {/* Header */}
        <div className={`text-center mb-16 ${isVisible ? 'animate-slide-up' : ''}`}>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-dark-900 dark:text-dark-50 mb-4">
            Easy Integration
          </h2>
          <p className="text-lg text-dark-500 dark:text-dark-400 max-w-2xl mx-auto">
            Multiple integration methods to fit your tech stack. Start building in minutes.
          </p>
        </div>

        {/* Integration Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {integrations.map((integration, index) => (
            <div
              key={index}
              style={{
                animationDelay: isVisible ? `${index * 100}ms` : '0ms',
              }}
            >
              <Card
                className={`relative overflow-hidden h-full flex flex-col ${
                  isVisible ? 'animate-fade-in' : 'opacity-0'
                }`}
              >
              {/* Gradient accent */}
              <div className={`absolute -top-2 -right-2 w-24 h-24 bg-gradient-to-br ${integration.color} opacity-10 rounded-full blur-2xl`} />

              {/* Content */}
              <div className="relative">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
                    <APIIcon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-dark-900 dark:text-dark-50">
                    {integration.label}
                  </h3>
                </div>
                <p className="text-dark-600 dark:text-dark-400 mb-4">
                  {integration.description}
                </p>
                <div className="bg-dark-900 dark:bg-dark-950 text-primary-300 dark:text-primary-400 px-3 py-2 rounded-lg text-xs font-mono mb-4 overflow-x-auto border border-dark-800 dark:border-dark-700">
                  {integration.example}
                </div>
              </div>

              {/* Action link */}
              <div className="mt-auto">
                <a
                  href="#"
                  className="text-primary-600 dark:text-primary-400 font-medium text-sm hover:text-primary-700 dark:hover:text-primary-300 inline-flex items-center gap-2 transition-colors"
                >
                  Learn more →
                </a>
              </div>
              </Card>
            </div>
          ))}
        </div>

        {/* Code example section */}
        <Card className={`bg-dark-900 text-white border-primary-900 ${isVisible ? 'animate-fade-in' : 'opacity-0'}`}>
          <div className="mb-4">
            <h3 className="text-xl font-semibold mb-2">Quick Start Example</h3>
            <p className="text-dark-400 text-sm">Initialize verification with just a few lines of code:</p>
          </div>
          <pre className="bg-dark-800 p-4 rounded-lg overflow-x-auto text-sm font-mono">
            <code>{`import { VerifyAI } from '@verifyai/sdk';

const client = new VerifyAI({
  apiKey: 'sk_live_...'
});

const result = await client.verify({
  document: file,
  liveness: true,
  amlCheck: true
});

console.log(result.status); // 'approved'`}</code>
          </pre>
        </Card>
      </div>
    </section>
  )
}
