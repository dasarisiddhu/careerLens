import React from 'react'
import Button from './Button'
import { FolderSearch } from 'lucide-react'

export function EmptyState({
  icon: Icon = FolderSearch,
  title = 'No items found',
  description = 'There is nothing here yet.',
  actionLabel,
  onAction,
  className = '',
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-[20px] bg-white/60 border border-slate-200/80 backdrop-blur-sm ${className}`}
    >
      <div className="w-14 h-14 rounded-2xl bg-blue-50 text-[#2563EB] flex items-center justify-center mb-4 border border-blue-100 shadow-sm">
        <Icon size={28} />
      </div>
      <h4 className="text-base font-bold text-[#0B0F19] tracking-tight">{title}</h4>
      <p className="text-sm text-[#64748B] mt-1.5 max-w-sm">{description}</p>
      {actionLabel && onAction && (
        <div className="mt-5">
          <Button variant="primary" size="sm" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  )
}

export default EmptyState
