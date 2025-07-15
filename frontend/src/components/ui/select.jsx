import React from 'react'
import { cn } from '../../lib/utils'
// Using simple arrow instead of lucide-react
const ChevronDown = () => <span>▼</span>

const SelectContext = React.createContext()

const Select = ({ children, value, onValueChange, defaultValue }) => {
  const [internalValue, setInternalValue] = React.useState(defaultValue || '')
  const [isOpen, setIsOpen] = React.useState(false)
  const currentValue = value !== undefined ? value : internalValue

  const handleValueChange = (newValue) => {
    if (value === undefined) {
      setInternalValue(newValue)
    }
    onValueChange?.(newValue)
    setIsOpen(false)
  }

  return (
    <SelectContext.Provider value={{ 
      value: currentValue, 
      onValueChange: handleValueChange,
      isOpen,
      setIsOpen
    }}>
      <div className="relative">
        {children}
      </div>
    </SelectContext.Provider>
  )
}

const SelectTrigger = React.forwardRef(({ className, children, ...props }, ref) => {
  const context = React.useContext(SelectContext)

  return (
    <button
      ref={ref}
      type="button"
      className={cn(
        "flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-background placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      onClick={() => context?.setIsOpen(!context?.isOpen)}
      {...props}
    >
      {children}
      <ChevronDown />
    </button>
  )
})
SelectTrigger.displayName = "SelectTrigger"

const SelectValue = React.forwardRef(({ className, placeholder, ...props }, ref) => {
  const context = React.useContext(SelectContext)

  return (
    <span
      ref={ref}
      className={cn("block truncate", className)}
      {...props}
    >
      {context?.value || placeholder}
    </span>
  )
})
SelectValue.displayName = "SelectValue"

const SelectContent = React.forwardRef(({ className, children, ...props }, ref) => {
  const context = React.useContext(SelectContext)

  if (!context?.isOpen) return null

  return (
    <div
      ref={ref}
      className={cn(
        "absolute top-full z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
})
SelectContent.displayName = "SelectContent"

const SelectItem = React.forwardRef(({ className, children, value, ...props }, ref) => {
  const context = React.useContext(SelectContext)
  const isSelected = context?.value === value

  return (
    <div
      ref={ref}
      className={cn(
        "relative cursor-pointer select-none py-2 pl-3 pr-9 text-gray-900 hover:bg-primary-50 hover:text-primary-900",
        isSelected && "bg-primary-100 text-primary-900",
        className
      )}
      onClick={() => context?.onValueChange?.(value)}
      {...props}
    >
      {children}
      {isSelected && (
        <span className="absolute inset-y-0 right-0 flex items-center pr-4 text-primary-600">
          ✓
        </span>
      )}
    </div>
  )
})
SelectItem.displayName = "SelectItem"

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem }
