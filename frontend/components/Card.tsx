'use client'

import React from 'react'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'

interface CardProps {
  className?: string
  children: React.ReactNode
  animated?: boolean
}

export function Card({ className = '', children, animated = true }: CardProps) {
  const { ref, isVisible } = useScrollAnimation()

  return (
    <div
      ref={animated ? ref : undefined}
      className={`
        bg-white dark:bg-dark-800 rounded-xl border border-dark-100 dark:border-dark-700 p-4 sm:p-6 lg:p-8
        shadow-sm-soft hover:shadow-md-soft dark:shadow-lg dark:hover:shadow-xl transition-all duration-300
        ${animated ? (isVisible ? 'animate-fade-in' : 'opacity-0') : ''}
        ${className}
      `}
    >
      {children}
    </div>
  )
}
