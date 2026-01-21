'use client'

import React from 'react'
import { Button } from '@/components/Button'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'

export function CTASection() {
  const { ref, isVisible } = useScrollAnimation()

  return (
    <section
      ref={ref}
      id="demo"
      className={`py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-primary-600 to-primary-700 dark:from-primary-500 dark:to-primary-600 text-white transition-all ${
        isVisible ? 'animate-fade-in' : 'opacity-0'
      }`}
    >
      <div className="container-wide text-center">
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6">
          Ready to Get Started?
        </h2>
        <p className="text-lg opacity-90 max-w-2xl mx-auto mb-8">
          Join hundreds of companies already using VerifyAI for secure, compliant onboarding.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            variant="primary"
            size="lg"
            className="bg-white dark:bg-dark-900 text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-dark-800 w-full sm:w-auto shadow-lg"
          >
            Start Free Trial
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="border-2 border-white dark:border-dark-100 text-white hover:bg-white/10 dark:hover:bg-dark-900/30 w-full sm:w-auto"
            onClick={() => {
              const contactSection = document.getElementById('contact')
              contactSection?.scrollIntoView({ behavior: 'smooth' })
            }}
          >
            Schedule Demo
          </Button>
        </div>
      </div>
    </section>
  )
}
