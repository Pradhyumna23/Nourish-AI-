import React from 'react'
import clsx from 'clsx'

const Input = ({
  label,
  error,
  helperText,
  className = '',
  required = false,
  ...props
}) => {
  const inputClasses = clsx(
    'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200',
    {
      'border-gray-300': !error,
      'border-danger-500 focus:ring-danger-500 focus:border-danger-500': error,
    },
    className
  )

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-danger-500 ml-1">*</span>}
        </label>
      )}
      <input className={inputClasses} {...props} />
      {error && (
        <p className="text-sm text-danger-600">{error}</p>
      )}
      {helperText && !error && (
        <p className="text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  )
}

export { Input }
export default Input
