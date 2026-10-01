import React from 'react'

export function PageShell({
  title,
  titleAccent,
  subtitle,
  actions,
  badge,
  children,
  maxWidth = 'max-w-7xl',
  className = '',
}) {
  return (
    <div className={`w-full mx-auto px-4 sm:px-8 py-8 ${maxWidth} ${className}`}>
      {/* Header section if provided */}
      {(title || subtitle || actions || badge) && (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            {badge && <div className="mb-2">{badge}</div>}
            {title && (
              <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight">
                {title} {titleAccent && <span className="text-[#2563EB]">{titleAccent}</span>}
              </h1>
            )}
            {subtitle && (
              <p className="text-sm text-[#64748B] mt-1.5 max-w-2xl leading-relaxed">
                {subtitle}
              </p>
            )}
          </div>

          {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
        </div>
      )}

      {/* Main Content Slot */}
      <main>{children}</main>
    </div>
  )
}

export default PageShell
