'use client'

import React from 'react'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'

interface SectionProps {
  className?: string
  children: React.ReactNode
  animated?: boolean
}

export function Section({ className = '', children, animated = true }: SectionProps) {
  const { ref, isVisible } = useScrollAnimation()

  return (
    <section
      ref={animated ? ref : undefined}
      className={`
        ${animated ? (isVisible ? 'animate-fade-in' : 'opacity-0') : ''}
        ${className}
      `}
    >
      {children}
    </section>
  )
}
