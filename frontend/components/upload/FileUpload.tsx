/**
 * File Upload Component with Drag & Drop
 * Professional SaaS-style file uploader with preview and validation
 */

'use client'

import React, { useState, useRef, DragEvent, ChangeEvent } from 'react'

export interface UploadedFile {
  file: File
  preview: string
  name: string
  size: number
  type: string
}

interface FileUploadProps {
  onFileSelect: (file: UploadedFile) => void
  acceptedTypes?: string[]
  maxSize?: number // in MB
  label: string
  description?: string
  icon?: React.ReactNode
  currentFile?: UploadedFile | null
}

export function FileUpload({
  onFileSelect,
  acceptedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'],
  maxSize = 10,
  label,
  description,
  icon,
  currentFile,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    if (!acceptedTypes.includes(file.type)) {
      return `File type not supported. Please upload: ${acceptedTypes.map(t => t.split('/')[1]).join(', ')}`
    }
    
    const fileSizeMB = file.size / (1024 * 1024)
    if (fileSizeMB > maxSize) {
      return `File size must be less than ${maxSize}MB`
    }
    
    return null
  }

  const handleFile = (file: File) => {
    setError(null)
    
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      const uploadedFile: UploadedFile = {
        file,
        preview: e.target?.result as string,
        name: file.name,
        size: file.size,
        type: file.type,
      }
      onFileSelect(uploadedFile)
    }
    reader.readAsDataURL(file)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFile(files[0])
    }
  }

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFile(files[0])
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        {icon && <div className="text-primary-600 dark:text-primary-400">{icon}</div>}
        <h3 className="text-lg font-semibold text-dark-900 dark:text-white">{label}</h3>
      </div>
      
      {description && (
        <p className="text-sm text-dark-600 dark:text-dark-400 mb-4">{description}</p>
      )}

      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-all duration-300 ease-in-out
          ${isDragging 
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' 
            : 'border-dark-300 dark:border-dark-700 hover:border-primary-400 dark:hover:border-primary-600 bg-white dark:bg-dark-800'
          }
          ${currentFile ? 'border-green-500 dark:border-green-600' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept={acceptedTypes.join(',')}
          onChange={handleFileInput}
        />

        {currentFile ? (
          <div className="space-y-3">
            {currentFile.type.startsWith('image/') && (
              <div className="mx-auto w-32 h-32 rounded-lg overflow-hidden border-2 border-dark-200 dark:border-dark-700">
                <img
                  src={currentFile.preview}
                  alt="Preview"
                  className="w-full h-full object-cover"
                />
              </div>
            )}
            <div className="space-y-1">
              <p className="text-sm font-medium text-dark-900 dark:text-white truncate max-w-xs mx-auto">
                {currentFile.name}
              </p>
              <p className="text-xs text-dark-500 dark:text-dark-500">
                {formatFileSize(currentFile.size)}
              </p>
            </div>
            <p className="text-xs text-green-600 dark:text-green-400 font-medium">
              ✓ File uploaded successfully
            </p>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onFileSelect(null as any)
              }}
              className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
            >
              Change file
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <svg
              className="mx-auto h-12 w-12 text-dark-400 dark:text-dark-600"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div>
              <p className="text-sm font-medium text-dark-900 dark:text-white">
                Drag and drop your file here
              </p>
              <p className="text-xs text-dark-500 dark:text-dark-500 mt-1">
                or click to browse
              </p>
            </div>
            <p className="text-xs text-dark-400 dark:text-dark-600">
              Supported: {acceptedTypes.map(t => t.split('/')[1].toUpperCase()).join(', ')} (Max {maxSize}MB)
            </p>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}
    </div>
  )
}
