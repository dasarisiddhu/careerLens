import React from 'react'
import Button from './Button'
import { AlertTriangle, RefreshCw } from 'lucide-react'

export function ErrorState({
  title = 'Something went wrong',
  message = "That didn't go through. Check your connection and try again.",
  onRetry,
  retryLabel = 'Try Again',
  className = '',
}) {
  return (
    <div
      role="alert"
      className={`flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-[20px] bg-rose-50/40 border border-rose-200/80 backdrop-blur-sm ${className}`}
    >
      <div className="w-14 h-14 rounded-2xl bg-rose-100 text-[#E11D48] flex items-center justify-center mb-4 border border-rose-200 shadow-sm">
        <AlertTriangle size={28} />
      </div>
      <h4 className="text-base font-bold text-[#0B0F19] tracking-tight">{title}</h4>
      <p className="text-sm text-[#64748B] mt-1.5 max-w-md">{message}</p>
      {onRetry && (
        <div className="mt-5">
          <Button
            variant="secondary"
            size="sm"
            icon={RefreshCw}
            onClick={onRetry}
          >
            {retryLabel}
          </Button>
        </div>
      )}
    </div>
  )
}

export default ErrorState
