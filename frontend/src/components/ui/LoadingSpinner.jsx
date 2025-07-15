import React from 'react'
import clsx from 'clsx'

const LoadingSpinner = ({ 
  size = 'md', 
  className = '',
  text = '',
  center = false 
}) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  }

  const containerClasses = clsx(
    'flex items-center',
    {
      'justify-center': center,
      'flex-col space-y-2': text,
      'space-x-2': text && !center,
    },
    className
  )

  return (
    <div className={containerClasses}>
      <svg
        className={clsx('animate-spin text-primary-600', sizes[size])}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        ></circle>
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
      {text && (
        <span className="text-sm text-gray-600">{text}</span>
      )}
    </div>
  )
}

export default LoadingSpinner
