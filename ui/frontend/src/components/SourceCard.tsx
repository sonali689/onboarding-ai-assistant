import { useState }         from 'react'
import { FileText, Globe,
         ExternalLink }     from 'lucide-react'
import { useLang }          from '../contexts/LanguageContext'
import SlideModal           from './SlideModal'
import type { Source }      from '../types'

interface Props {
  sources:     Source[]
  source_type: 'company_data' | 'general_knowledge' | null
}

export default function SourceCard({ sources, source_type }: Props) {
  const { t }       = useLang()
  const isGeneral   = source_type === 'general_knowledge'
  const [modalIndex, setModalIndex] = useState<number | null>(null)

  const openModal = (i: number) => setModalIndex(i)
  const closeModal = ()         => setModalIndex(null)
  const goPrev = ()             =>
    setModalIndex(i => i !== null && i > 0 ? i - 1 : i)
  const goNext = ()             =>
    setModalIndex(i =>
      i !== null && i < sources.length - 1 ? i + 1 : i)

  return (
    <>
      <div className="mt-3 space-y-2">

        {/* Badge */}
        <div className="flex items-center gap-1.5 text-xs font-semibold"
             style={{ color: isGeneral ? '#6B7280' : '#003DA5' }}>
          {isGeneral
            ? <><Globe size={11} /> {t.generalKnowledge}</>
            : <><FileText size={11} /> {t.fromMaterials}</>
          }
        </div>

        {/* Clickable source items — deduplicated by file, no slide numbers */}
        {!isGeneral && sources.length > 0 && (
          <div className="space-y-1.5">
            {sources.map((s, i) => (
              <button
                key={i}
                onClick={() => openModal(i)}
                className="w-full flex items-center gap-2.5 bg-white
                           rounded-lg px-3 py-2.5 text-left
                           transition-all duration-150 group
                           active:scale-[0.98]"
                style={{
                  border:     '1px solid #E5E7EB',
                  borderLeft: '3px solid #003DA5',
                  cursor:     'pointer',
                }}
                onMouseEnter={e => {
                  const el = e.currentTarget
                  el.style.borderColor     = '#003DA5'
                  el.style.background      = '#EEF3FC'
                  el.style.borderLeftColor = '#003DA5'
                  el.style.boxShadow       = '0 2px 8px rgba(0,61,165,0.1)'
                }}
                onMouseLeave={e => {
                  const el = e.currentTarget
                  el.style.borderColor     = '#E5E7EB'
                  el.style.background      = '#FFFFFF'
                  el.style.borderLeftColor = '#003DA5'
                  el.style.boxShadow       = 'none'
                }}
              >
                <FileText size={12} style={{ color: '#003DA5' }}
                          className="shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-gray-800
                                 leading-tight truncate">
                    {s.file}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {s.subfolder}{s.lang_hint ? ` · ${s.lang_hint.toUpperCase()}` : ''}
                  </p>
                </div>
                <div className="flex items-center gap-1 shrink-0
                                opacity-0 group-hover:opacity-100
                                transition-opacity"
                     style={{ color: '#003DA5' }}>
                  <span className="text-xs font-medium">View</span>
                  <ExternalLink size={11} />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Modal */}
      {modalIndex !== null && sources[modalIndex] && (
        <SlideModal
          file={sources[modalIndex].file}
          subfolder={sources[modalIndex].subfolder}
          onClose={closeModal}
          onPrev={goPrev}
          onNext={goNext}
          hasPrev={modalIndex > 0}
          hasNext={modalIndex < sources.length - 1}
        />
      )}
    </>
  )
}