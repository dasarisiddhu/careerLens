import React, { forwardRef } from 'react'

export const Input = forwardRef(function Input(
  {
    className = '',
    type = 'text',
    label,
    error,
    id,
    leadingIcon: LeadingIcon,
    trailingIcon: TrailingIcon,
    onTrailingIconClick,
    ...props
  },
  ref
) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined)

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-semibold text-[#1E293B] mb-1.5 ml-1"
        >
          {label}
        </label>
      )}

      <div className="relative flex items-center">
        {LeadingIcon && (
          <div className="absolute left-3.5 text-[#94A3B8] pointer-events-none">
            <LeadingIcon size={18} />
          </div>
        )}

        <input
          id={inputId}
          ref={ref}
          type={type}
          aria-invalid={Boolean(error)}
          aria-describedby={error && inputId ? `${inputId}-error` : undefined}
          className={`w-full h-11 px-4 text-sm text-[#0B0F19] placeholder:text-[#94A3B8] bg-white/90 border rounded-xl backdrop-blur-sm transition-all duration-200 focus-ring disabled:opacity-50 disabled:bg-slate-50 disabled:pointer-events-none ${
            LeadingIcon ? 'pl-10' : ''
          } ${TrailingIcon ? 'pr-10' : ''} ${
            error
              ? 'border-rose-400 bg-rose-50/20 focus:border-rose-500'
              : 'border-slate-200 hover:border-slate-300 focus:border-[#2563EB] focus:bg-white shadow-[0_2px_6px_rgba(0,0,0,0.02)]'
          } ${className}`}
          {...props}
        />

        {TrailingIcon && (
          <button
            type="button"
            tabIndex={onTrailingIconClick ? 0 : -1}
            onClick={onTrailingIconClick}
            className={`absolute right-3.5 text-[#94A3B8] hover:text-[#0B0F19] transition-colors ${
              !onTrailingIconClick ? 'pointer-events-none' : 'cursor-pointer p-0.5'
            }`}
          >
            <TrailingIcon size={18} />
          </button>
        )}
      </div>

      {error && (
        <p id={inputId ? `${inputId}-error` : undefined} className="text-xs text-[#E11D48] mt-1 ml-1 font-medium">
          {error}
        </p>
      )}
    </div>
  )
})

Input.displayName = 'Input'
export default Input
