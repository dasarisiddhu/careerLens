import React, { useCallback, useState } from 'react'
import { UploadCloud, FileText, CheckCircle2, AlertCircle } from 'lucide-react'

export function FileDropzone({
  onFileSelect,
  selectedFile,
  accept = '.pdf',
  maxSizeMB = 10,
  error,
  className = '',
}) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [internalError, setInternalError] = useState('')

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragOver(true)
    } else if (e.type === 'dragleave') {
      setIsDragOver(false)
    }
  }, [])

  const validateAndSelect = (file) => {
    setInternalError('')
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setInternalError('Please select a valid PDF file.')
      return
    }

    if (file.size > maxSizeMB * 1024 * 1024) {
      setInternalError(`File size exceeds maximum allowed size of ${maxSizeMB}MB.`)
      return
    }

    onFileSelect?.(file)
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelect(e.dataTransfer.files[0])
    }
  }, [])

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSelect(e.target.files[0])
    }
  }

  const displayError = error || internalError

  return (
    <div className={`w-full ${className}`}>
      <label
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-[20px] transition-all duration-200 cursor-pointer text-center backdrop-blur-sm ${
          isDragOver
            ? 'border-[#2563EB] bg-blue-50/50 scale-[1.01]'
            : selectedFile
            ? 'border-emerald-300 bg-emerald-50/30'
            : 'border-slate-300/80 bg-white/70 hover:border-slate-400 hover:bg-white/90'
        }`}
      >
        <input
          type="file"
          accept={accept}
          onChange={handleChange}
          className="sr-only"
        />

        {selectedFile ? (
          <div className="flex flex-col items-center">
            <div className="w-14 h-14 rounded-2xl bg-emerald-100/80 text-[#16A34A] flex items-center justify-center mb-3 shadow-sm">
              <FileText size={28} />
            </div>
            <p className="text-sm font-bold text-[#0B0F19] max-w-xs truncate">{selectedFile.name}</p>
            <p className="text-xs text-[#64748B] mt-1">
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready to analyze
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-xs text-[#16A34A] font-semibold bg-emerald-100/60 px-2.5 py-1 rounded-full">
              <CheckCircle2 size={13} />
              <span>Selected successfully</span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-14 h-14 rounded-2xl bg-blue-50 text-[#2563EB] flex items-center justify-center mb-3 shadow-sm border border-blue-100">
              <UploadCloud size={28} />
            </div>
            <p className="text-sm font-bold text-[#0B0F19]">
              Drop your resume here, or <span className="text-[#2563EB]">browse</span>
            </p>
            <p className="text-xs text-[#64748B] mt-1">
              Supports PDF documents up to {maxSizeMB}MB
            </p>
          </div>
        )}
      </label>

      {displayError && (
        <div className="flex items-center gap-1.5 text-xs text-[#E11D48] font-medium mt-2 ml-1">
          <AlertCircle size={14} className="shrink-0" />
          <span>{displayError}</span>
        </div>
      )}
    </div>
  )
}

export default FileDropzone
