import { FileText, Globe } from 'lucide-react'
import type { Source } from '../types'

interface Props {
  sources:     Source[]
  source_type: 'company_data' | 'general_knowledge' | null
}

export default function SourceCard({ sources, source_type }: Props) {
  const isGeneral = source_type === 'general_knowledge'

  return (
    <div className="mt-2 space-y-2">
      <div className={`flex items-center gap-1.5 text-xs font-semibold
        ${isGeneral ? 'text-sky-500' : 'text-autoliv-blue'}`}>
        {isGeneral
          ? <><Globe size={12} /> General knowledge | 一般知識</>
          : <><FileText size={12} /> From Autoliv training materials</>
        }
      </div>

      {!isGeneral && sources.length > 0 && (
        <div className="space-y-1.5">
          {sources.map((s, i) => (
            <div key={i}
              className="flex items-start gap-2 bg-autoliv-grey-light
                         border border-autoliv-border rounded-lg
                         px-3 py-2 border-l-[3px] border-l-autoliv-blue">
              <FileText size={13}
                className="text-autoliv-blue mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs font-semibold text-autoliv-charcoal
                               leading-tight">
                  {s.file}
                </p>
                <p className="text-xs text-autoliv-grey mt-0.5">
                  Slide {s.slide_number} · {s.subfolder} ·{' '}
                  {s.lang_hint.toUpperCase()}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}