import { useEffect, useRef, useState } from 'react'
import { X, FileText, Download,
         ChevronLeft, ChevronRight,
         AlertCircle, ExternalLink }   from 'lucide-react'

interface Props {
  file:        string
  slideNumber: number
  subfolder:   string
  onClose:     () => void
  onPrev?:     () => void
  onNext?:     () => void
  hasPrev?:    boolean
  hasNext?:    boolean
}

function isPDF(filename: string) {
  return filename.toLowerCase().endsWith('.pdf')
}

export default function SlideModal({
  file, slideNumber, subfolder,
  onClose, onPrev, onNext, hasPrev, hasNext,
}: Props) {
  const overlayRef         = useRef<HTMLDivElement>(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(false)

  const fileUrl    = `/api/file/${encodeURIComponent(file)}`
  const pdfWithPage = `${fileUrl}#page=${slideNumber}`
  const isFileAPDF  = isPDF(file)

  // Reset loading state when slide changes
  useEffect(() => {
    setLoading(true)
    setError(false)
  }, [file, slideNumber])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape')                         onClose()
      if (e.key === 'ArrowLeft'  && hasPrev && onPrev) onPrev()
      if (e.key === 'ArrowRight' && hasNext && onNext) onNext()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose, onPrev, onNext, hasPrev, hasNext])

  // Click backdrop to close
  const handleBackdrop = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose()
  }

  return (
    <div
      ref={overlayRef}
      onClick={handleBackdrop}
      className="fixed inset-0 z-50 flex items-center justify-center px-4 py-6"
      style={{ background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(4px)' }}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden"
        style={{ width: '92vw', maxWidth: '1100px', height: '88vh' }}
      >

        {/* ── Header ──────────────────────────────────────────── */}
        <div
          className="flex items-center justify-between px-5 py-3.5 shrink-0"
          style={{ borderBottom: '1px solid #E5E7EB' }}
        >
          <div className="flex items-center gap-3 min-w-0">
            {/* File icon */}
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: '#EEF3FC' }}
            >
              <FileText size={15} style={{ color: '#003DA5' }} />
            </div>

            {/* File info */}
            <div className="min-w-0">
              <p className="text-sm font-semibold text-gray-800 truncate leading-tight">
                {file}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">
                {isFileAPDF ? 'Page' : 'Slide'} {slideNumber} · {subfolder}
              </p>
            </div>

            {/* File type badge */}
            <span
              className="text-xs font-bold px-2 py-0.5 rounded-md shrink-0"
              style={{
                background: isFileAPDF ? '#FEF3C7' : '#EEF3FC',
                color:      isFileAPDF ? '#92400E' : '#003DA5',
              }}
            >
              {isFileAPDF ? 'PDF' : 'PPTX'}
            </span>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-1.5 shrink-0 ml-4">

            {/* Prev / Next — only for multiple sources */}
            {(hasPrev || hasNext) && (
              <>
                <button
                  onClick={onPrev}
                  disabled={!hasPrev}
                  title="Previous source"
                  className="p-1.5 rounded-lg transition-all
                             disabled:opacity-30 disabled:cursor-not-allowed"
                  style={{ color: '#003DA5' }}
                  onMouseEnter={e => {
                    if (hasPrev)
                      (e.currentTarget as HTMLButtonElement).style.background = '#EEF3FC'
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                  }}
                >
                  <ChevronLeft size={18} />
                </button>
                <button
                  onClick={onNext}
                  disabled={!hasNext}
                  title="Next source"
                  className="p-1.5 rounded-lg transition-all
                             disabled:opacity-30 disabled:cursor-not-allowed"
                  style={{ color: '#003DA5' }}
                  onMouseEnter={e => {
                    if (hasNext)
                      (e.currentTarget as HTMLButtonElement).style.background = '#EEF3FC'
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                  }}
                >
                  <ChevronRight size={18} />
                </button>
              </>
            )}

            {/* Open in new tab */}
            <a
              href={isFileAPDF ? pdfWithPage : fileUrl}
              target="_blank"
              rel="noreferrer"
              title="Open in new tab"
              className="p-1.5 rounded-lg transition-all flex items-center"
              style={{ color: '#6B7280' }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLAnchorElement).style.background = '#F3F4F6'
                ;(e.currentTarget as HTMLAnchorElement).style.color = '#111827'
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLAnchorElement).style.background = 'transparent'
                ;(e.currentTarget as HTMLAnchorElement).style.color = '#6B7280'
              }}
            >
              <ExternalLink size={16} />
            </a>

            {/* Close */}
            <button
              onClick={onClose}
              title="Close"
              className="p-1.5 rounded-lg transition-all"
              style={{ color: '#6B7280' }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLButtonElement).style.background = '#F3F4F6'
                ;(e.currentTarget as HTMLButtonElement).style.color = '#111827'
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                ;(e.currentTarget as HTMLButtonElement).style.color = '#6B7280'
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* ── Content ─────────────────────────────────────────── */}
        <div
          className="flex-1 min-h-0 flex items-center justify-center"
          style={{ background: '#F8F9FB' }}
        >

          {/* ── PDF → embed directly in browser ─────────────── */}
          {isFileAPDF && (
            <div className="w-full h-full relative">
              {loading && (
                <div className="absolute inset-0 flex items-center
                                justify-center z-10 bg-gray-50">
                  <div className="flex flex-col items-center gap-3">
                    <div
                      className="w-8 h-8 rounded-full border-2 animate-spin"
                      style={{
                        borderColor:      '#003DA5',
                        borderTopColor:   'transparent',
                      }}
                    />
                    <p className="text-sm text-gray-500">Loading PDF...</p>
                  </div>
                </div>
              )}

              {error ? (
                <div className="flex flex-col items-center justify-center
                                h-full gap-3 p-8 text-center">
                  <AlertCircle size={36} style={{ color: '#D1D5DB' }} />
                  <p className="text-sm font-medium text-gray-500">
                    Could not load the PDF
                  </p>
                  <a
                    href={pdfWithPage}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-2 px-4 py-2 rounded-xl
                               text-sm font-medium text-white transition-all"
                    style={{ background: '#003DA5' }}
                  >
                    <ExternalLink size={14} />
                    Open in new tab
                  </a>
                </div>
              ) : (
                <embed
                  src={pdfWithPage}
                  type="application/pdf"
                  className="w-full h-full"
                  onLoad={() => setLoading(false)}
                  onError={() => { setLoading(false); setError(true) }}
                />
              )}
            </div>
          )}

          {/* ── PPTX → download prompt ────────────────────────── */}
          {!isFileAPDF && (
            <div className="flex flex-col items-center justify-center
                            h-full gap-6 p-8 text-center max-w-md mx-auto">

              {/* Icon */}
              <div
                className="w-20 h-20 rounded-2xl flex items-center
                           justify-center shadow-md"
                style={{ background: '#EEF3FC' }}
              >
                <FileText size={36} style={{ color: '#003DA5' }} />
              </div>

              {/* Info */}
              <div>
                <h3 className="text-base font-bold text-gray-800 leading-tight">
                  {file}
                </h3>
                <p className="text-sm text-gray-500 mt-2 leading-relaxed">
                  PowerPoint files open in Microsoft PowerPoint.
                  After opening, navigate to{' '}
                  <span
                    className="font-bold px-2 py-0.5 rounded-lg"
                    style={{ background: '#003DA5', color: 'white' }}
                  >
                    Slide {slideNumber}
                  </span>
                  {' '}for the referenced content.
                </p>
              </div>

              {/* Slide number callout */}
              <div
                className="flex items-center gap-3 px-6 py-4 rounded-2xl w-full"
                style={{ background: '#EEF3FC', border: '1px solid #C7D7F5' }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center
                             justify-center shrink-0 text-white font-black text-sm"
                  style={{ background: '#003DA5' }}
                >
                  {slideNumber}
                </div>
                <div className="text-left">
                  <p className="text-xs font-semibold"
                     style={{ color: '#003DA5' }}>
                    Navigate to this slide
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Press <kbd className="px-1.5 py-0.5 rounded text-xs
                                         font-mono bg-white border border-gray-200
                                         text-gray-600">Ctrl+G</kbd> in PowerPoint
                    and enter {slideNumber}
                  </p>
                </div>
              </div>

              {/* Download button */}
              <a
                href={fileUrl}
                download={file}
                className="flex items-center gap-2.5 px-6 py-3 rounded-xl
                           text-sm font-semibold text-white transition-all
                           active:scale-95 shadow-sm hover:shadow-md w-full
                           justify-center"
                style={{ background: '#003DA5' }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLAnchorElement).style.background = '#002D7A'
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLAnchorElement).style.background = '#003DA5'
                }}
              >
                <Download size={16} />
                Open in PowerPoint
              </a>

              <p className="text-xs" style={{ color: '#9CA3AF' }}>
                The file will download and open automatically
                if PowerPoint is installed.
              </p>
            </div>
          )}
        </div>

        {/* ── Footer ──────────────────────────────────────────── */}
        <div
          className="px-5 py-2.5 shrink-0 flex items-center justify-between"
          style={{ borderTop: '1px solid #E5E7EB' }}
        >
          <p className="text-xs" style={{ color: '#9CA3AF' }}>
            Press{' '}
            <kbd className="px-1.5 py-0.5 rounded text-xs font-mono
                            bg-gray-100 text-gray-500 border border-gray-200">
              Esc
            </kbd>{' '}
            to close
            {(hasPrev || hasNext) && (
              <span>
                {' · '}
                <kbd className="px-1.5 py-0.5 rounded text-xs font-mono
                                bg-gray-100 text-gray-500 border border-gray-200">
                  ←
                </kbd>{' '}
                <kbd className="px-1.5 py-0.5 rounded text-xs font-mono
                                bg-gray-100 text-gray-500 border border-gray-200">
                  →
                </kbd>{' '}
                to switch sources
              </span>
            )}
          </p>
          <p className="text-xs font-semibold" style={{ color: '#003DA5' }}>
            {isFileAPDF ? 'Page' : 'Slide'} {slideNumber} of {file}
          </p>
        </div>
      </div>
    </div>
  )
}