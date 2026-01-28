'use client'

import React from 'react'
import { Card } from '@/components/Card'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'
import { StarIcon } from '@/components/icons/Icons'

const testimonials = [
  {
    content: 'Deep Defenders reduced our onboarding time by 70% while maintaining excellent security standards. The API integration was seamless.',
    author: 'Sarah Chen',
    title: 'Head of Compliance',
    company: 'FinTech Innovations',
    rating: 5,
  },
  {
    content: 'The fraud detection accuracy is outstanding. We\'ve seen a significant reduction in synthetic fraud attempts since implementation.',
    author: 'Michael Roberts',
    title: 'CTO',
    company: 'Digital Lending Co',
    rating: 5,
  },
  {
    content: 'Best-in-class customer support and comprehensive documentation. The team was incredibly helpful during our integration process.',
    author: 'Emma Williams',
    title: 'Product Manager',
    company: 'Crypto Exchange Pro',
    rating: 5,
  },
  {
    content: 'The global AML compliance features have simplified our regulatory requirements across multiple jurisdictions.',
    author: 'James Kumar',
    title: 'Risk Officer',
    company: 'Banking Solutions Inc',
    rating: 5,
  },
]

export function TestimonialsSection() {
  const { ref, isVisible } = useScrollAnimation()

  return (
    <section ref={ref} className="py-20 px-4 sm:px-6 lg:px-8 bg-white dark:bg-dark-900 transition-colors">
      <div className="container-wide">
        {/* Header */}
        <div className={`text-center mb-16 ${isVisible ? 'animate-slide-up' : ''}`}>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-dark-900 dark:text-dark-50 mb-4">
            Trusted by Industry Leaders
          </h2>
          <p className="text-lg text-dark-500 dark:text-dark-400 max-w-2xl mx-auto">
            See what companies are saying about their experience with Deep Defenders.
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 gap-6 lg:gap-8">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              style={{
                animationDelay: isVisible ? `${index * 100}ms` : '0ms',
              }}
            >
              <Card
                className={`flex flex-col ${isVisible ? 'animate-fade-in' : 'opacity-0'}`}
              >
              {/* Rating stars */}
              <div className="flex gap-1 mb-4">
                {Array.from({ length: testimonial.rating }).map((_, i) => (
                  <StarIcon key={i} className="w-4 h-4 text-yellow-400" />
                ))}
              </div>

              {/* Quote */}
              <p className="text-dark-700 dark:text-dark-300 mb-6 flex-grow leading-relaxed">
                "{testimonial.content}"
              </p>

              {/* Author info */}
              <div>
                <p className="font-semibold text-dark-900 dark:text-dark-50">{testimonial.author}</p>
                <p className="text-sm text-dark-600 dark:text-dark-400">
                  {testimonial.title} · {testimonial.company}
                </p>
              </div>
              </Card>
            </div>
          ))}
        </div>

        {/* Stats */}
        <div className={`mt-16 grid md:grid-cols-3 gap-8 text-center ${isVisible ? 'animate-fade-in' : 'opacity-0'}`}>
          <div>
            <p className="text-4xl font-bold text-primary-600 dark:text-primary-400 mb-2">500+</p>
            <p className="text-dark-600 dark:text-dark-400">Active Customers</p>
          </div>
          <div>
            <p className="text-4xl font-bold text-primary-600 dark:text-primary-400 mb-2">50M+</p>
            <p className="text-dark-600 dark:text-dark-400">Verifications Processed</p>
          </div>
          <div>
            <p className="text-4xl font-bold text-primary-600 dark:text-primary-400 mb-2">150+</p>
            <p className="text-dark-600 dark:text-dark-400">Countries Supported</p>
          </div>
        </div>
      </div>
    </section>
  )
}
