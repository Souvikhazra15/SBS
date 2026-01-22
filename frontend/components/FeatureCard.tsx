'use client'

import React from 'react'
import Link from 'next/link'
import { Card } from '@/components/Card'

interface FeatureCardProps {
  icon: React.ComponentType<{ className?: string }>
  title: string
  description: string
  features: string[]
  href: string
  index?: number
  isVisible?: boolean
}

export function FeatureCard({ 
  icon: Icon, 
  title, 
  description, 
  features, 
  href, 
  index = 0,
  isVisible = true 
}: FeatureCardProps) {
  return (
    <div
      className={`transition-all duration-300 ${
        isVisible ? 'animate-fade-in' : 'opacity-0'
      }`}
      style={{ '--animation-delay': `${index * 150}ms` } as React.CSSProperties}
    >
      <Link href={href} className="block h-full">
        <Card className="h-full flex flex-col hover:shadow-xl hover:scale-105 transition-all duration-300 cursor-pointer group">
          {/* Icon */}
          <div className="mb-6 inline-flex p-4 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 w-fit group-hover:bg-primary-200 dark:group-hover:bg-primary-800/50 transition-colors duration-300">
            <Icon className="w-8 h-8" />
          </div>

          {/* Title */}
          <h4 className="text-xl font-semibold text-dark-900 dark:text-white mb-3 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors duration-300">
            {title}
          </h4>

          {/* Description */}
          <p className="text-dark-600 dark:text-dark-400 mb-6 flex-grow">
            {description}
          </p>

          {/* Features List */}
          <div className="space-y-2">
            {features.map((item, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="text-primary-600 dark:text-primary-400 font-bold mt-1">✓</span>
                <span className="text-sm text-dark-700 dark:text-dark-300">{item}</span>
              </div>
            ))}
          </div>

          {/* View Details Indicator */}
          <div className="mt-4 pt-4 border-t border-dark-200 dark:border-dark-700">
            <span className="text-xs text-primary-600 dark:text-primary-400 font-medium group-hover:text-primary-700 dark:group-hover:text-primary-300 transition-colors duration-300">
              Click to view details →
            </span>
          </div>
        </Card>
      </Link>
    </div>
  )
}