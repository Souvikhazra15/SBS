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
        bg-white rounded-xl border border-dark-100 p-6 sm:p-8
        shadow-sm-soft hover:shadow-md-soft transition-all duration-300
        ${animated ? (isVisible ? 'animate-fade-in' : 'opacity-0') : ''}
        ${className}
      `}
    >
      {children}
    </div>
  )
}
