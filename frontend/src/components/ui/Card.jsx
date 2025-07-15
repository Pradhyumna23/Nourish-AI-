import React from 'react'
import clsx from 'clsx'

const Card = ({
  children,
  className = '',
  padding = 'md',
  shadow = 'sm',
  variant = 'default',
  hover = true,
  ...props
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
    xl: 'shadow-xl',
    '2xl': 'shadow-2xl',
  }

  const variantClasses = {
    default: 'bg-white border border-gray-200',
    gradient: 'bg-gradient-to-br from-white to-blue-50 border-0',
    glass: 'glass-effect',
    enhanced: 'card-enhanced',
  }

  const classes = clsx(
    'rounded-2xl transition-all duration-300',
    variantClasses[variant],
    paddingClasses[padding],
    shadowClasses[shadow],
    hover && 'hover:shadow-xl hover:-translate-y-1',
    className
  )

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  )
}

const CardHeader = ({ children, className = '', gradient = false }) => (
  <div className={clsx(
    'border-b border-gray-100 pb-6 mb-6',
    gradient && 'bg-gradient-to-r from-purple-50 to-blue-50 -m-6 mb-6 p-6 rounded-t-2xl',
    className
  )}>
    {children}
  </div>
)

const CardTitle = ({ children, className = '', gradient = false }) => (
  <h3 className={clsx(
    'text-xl font-bold',
    gradient
      ? 'bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent'
      : 'text-gray-900',
    className
  )}>
    {children}
  </h3>
)

const CardContent = ({ children, className = '' }) => (
  <div className={className}>
    {children}
  </div>
)

const CardFooter = ({ children, className = '' }) => (
  <div className={clsx('border-t border-gray-200 pt-4 mt-4', className)}>
    {children}
  </div>
)

Card.Header = CardHeader
Card.Title = CardTitle
Card.Content = CardContent
Card.Footer = CardFooter

export { Card, CardHeader, CardTitle, CardContent, CardFooter }
export default Card
