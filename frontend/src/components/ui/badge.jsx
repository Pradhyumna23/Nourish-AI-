import React from 'react'
import { cn } from '../../lib/utils'

const badgeVariants = {
  default: "bg-primary-100 text-primary-800 border-primary-200",
  secondary: "bg-gray-100 text-gray-800 border-gray-200",
  destructive: "bg-red-100 text-red-800 border-red-200",
  outline: "text-gray-600 border-gray-300 bg-transparent",
  success: "bg-green-100 text-green-800 border-green-200",
  warning: "bg-yellow-100 text-yellow-800 border-yellow-200",
}

const Badge = React.forwardRef(({ className, variant = "default", ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        badgeVariants[variant],
        className
      )}
      {...props}
    />
  )
})
Badge.displayName = "Badge"

export { Badge, badgeVariants }
