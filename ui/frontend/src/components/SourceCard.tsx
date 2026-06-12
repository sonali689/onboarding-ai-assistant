import { FileText, Globe } from 'lucide-react'
import type { Source } from '../types'

interface Props {
  sources:     Source[]
  source_type: 'company_data' | 'general_knowledge' | null
}

export default function SourceCard({ sources, source_type }: Props) {
  const isGeneral = source_type === 'general_knowledge'

  return (
    <div className="mt-3 space-y-2">

      {/* Badge */}
      <div className={`flex items-center gap-1.5 text-xs font-semibold ${
        isGeneral ? 'text-gray-500' : 'text-[#003DA5]'
      }`}>
        {isGeneral
          ? <><Globe size={11} /> General knowledge | 一般知識</>
          : <><FileText size={11} /> From Autoliv training materials</>
        }
      </div>

      {/* Source list */}
      {!isGeneral && sources.length > 0 && (
        <div className="space-y-1.5">
          {sources.map((s, i) => {
            // 1. Handle the subfolder safely (if it has nested folders, split and encode them)
            const subfolderPath = s.subfolder 
              ? s.subfolder.split('/').map(part => encodeURIComponent(part)).join('/') + '/'
              : ''

            // 2. Combine the base URL + subfolder + filename
            const fileUrl = `http://localhost:8000/materials/${subfolderPath}${encodeURIComponent(s.file)}`

            return (
              <a
                key={i}
                href={fileUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-2.5 bg-white rounded-lg px-3 py-2 
                           border border-gray-200 border-l-[3px] border-l-[#003DA5] 
                           hover:bg-gray-50 hover:shadow-sm transition-all cursor-pointer block"
              >
                <FileText size={12} className="text-[#003DA5] mt-0.5 shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-gray-800 leading-tight truncate max-w-xs">
                    {s.file}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Slide {s.slide_number} · {s.subfolder || 'Root'} · {s.lang_hint.toUpperCase()}
                  </p>
                </div>
              </a>
            )
          })}
        </div>
      )}
    </div>
  )
}