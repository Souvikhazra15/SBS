'use client'

import React from 'react'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  children: React.ReactNode
}

const sizeClasses = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-6 py-3 text-base',
  lg: 'px-8 py-4 text-lg',
}

const variantClasses = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 active:scale-95',
  secondary: 'bg-primary-100 text-primary-700 hover:bg-primary-200 active:scale-95',
  outline: 'border-2 border-primary-600 text-primary-600 hover:bg-primary-50 active:scale-95',
}

export function Button({ 
  variant = 'primary', 
  size = 'md', 
  className = '',
  ...props 
}: ButtonProps) {
  return (
    <button
      className={`
        rounded-lg font-medium transition-all duration-200
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${className}
      `}
      {...props}
    />
  )
}
