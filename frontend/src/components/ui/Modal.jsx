import React, { useEffect } from 'react'
import { createPortal } from 'react-dom'
import clsx from 'clsx'

const Modal = ({ 
  isOpen, 
  onClose, 
  children, 
  size = 'md',
  className = '',
  closeOnOverlayClick = true,
  showCloseButton = true,
}) => {
  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4',
  }

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const modalContent = (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Overlay */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={closeOnOverlayClick ? onClose : undefined}
        />
        
        {/* Modal */}
        <div className={clsx(
          'relative bg-white rounded-lg shadow-xl w-full',
          sizes[size],
          className
        )}>
          {showCloseButton && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
          {children}
        </div>
      </div>
    </div>
  )

  return createPortal(modalContent, document.body)
}

const ModalHeader = ({ children, className = '' }) => (
  <div className={clsx('px-6 py-4 border-b border-gray-200', className)}>
    {children}
  </div>
)

const ModalTitle = ({ children, className = '' }) => (
  <h2 className={clsx('text-xl font-semibold text-gray-900', className)}>
    {children}
  </h2>
)

const ModalContent = ({ children, className = '' }) => (
  <div className={clsx('px-6 py-4', className)}>
    {children}
  </div>
)

const ModalFooter = ({ children, className = '' }) => (
  <div className={clsx('px-6 py-4 border-t border-gray-200 flex justify-end space-x-3', className)}>
    {children}
  </div>
)

Modal.Header = ModalHeader
Modal.Title = ModalTitle
Modal.Content = ModalContent
Modal.Footer = ModalFooter

export default Modal
