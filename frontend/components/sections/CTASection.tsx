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
      className={`py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 dark:from-primary-500 dark:via-primary-600 dark:to-primary-700 text-white transition-all duration-700 relative overflow-hidden ${
        isVisible ? 'animate-fade-in' : 'opacity-0'
      }`}
    >
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-500/20 to-transparent"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full blur-3xl -translate-y-48 translate-x-48"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-white/5 rounded-full blur-3xl translate-y-48 -translate-x-48"></div>

      <div className="container-wide text-center relative z-10">
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6 leading-tight">
          Ready to Get Started?
        </h2>
        <p className="text-lg opacity-90 max-w-2xl mx-auto mb-10 leading-relaxed">
          Join hundreds of companies already using Deep Defenders for secure, compliant onboarding.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md mx-auto sm:max-w-none">
          <Button
            variant="primary"
            size="lg"
            className="bg-white dark:bg-dark-900 text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-dark-800 hover:scale-105 w-full sm:w-auto shadow-lg hover:shadow-xl transition-all duration-300 transform"
          >
            Start Free Trial
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="border-2 border-white/80 dark:border-dark-100 text-white dark:text-dark-100 hover:bg-white/10 dark:hover:bg-dark-900/30 hover:border-white hover:scale-105 w-full sm:w-auto transition-all duration-300 transform backdrop-blur-sm"
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
