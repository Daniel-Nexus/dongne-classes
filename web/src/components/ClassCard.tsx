import {
  AGE_BUCKETS,
  FACILITY_TYPE_LABEL,
  STATUS_DOT,
  STATUS_LABEL,
  categoryStyle,
  type ClassListing,
} from '../types'
import { CalendarIcon, MapPinIcon } from './icons'

interface Props {
  item: ClassListing
  onClick: () => void
}

export function ClassCard({ item, onClick }: Props) {
  const cat = categoryStyle(item.category)
  const free = item.fee_won === 0
  const ageLabel = ageShortLabel(item)

  return (
    <button
      onClick={onClick}
      className="group relative w-full text-left bg-white rounded-2xl border border-stone-200/80
                 hover:border-stone-300 hover:shadow-[0_2px_12px_-4px_rgb(0_0_0_/_0.08)]
                 active:scale-[0.995] transition overflow-hidden"
    >
      <div className={`absolute inset-y-0 left-0 w-1 ${cat.stripe}`} aria-hidden />
      <div className="pl-5 pr-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            {item.category && (
              <span
                className={`inline-block text-[11px] font-semibold px-2 py-0.5 rounded-md ${cat.bg} ${cat.text}`}
              >
                {item.category}
              </span>
            )}
            <h2 className="mt-1.5 font-semibold text-[16px] text-stone-900 leading-snug break-keep line-clamp-2">
              {item.title}
            </h2>
          </div>
          <span className="shrink-0 inline-flex items-center gap-1 text-[11px] text-stone-600">
            <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[item.status]}`} aria-hidden />
            {STATUS_LABEL[item.status]}
          </span>
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5">
          {ageLabel && <Tag>{ageLabel}</Tag>}
          {free ? <Tag accent>무료</Tag> : item.fee_won != null && <Tag>{item.fee_won.toLocaleString()}원</Tag>}
          {item.session_count && <Tag>{item.session_count}회</Tag>}
        </div>

        <dl className="mt-3 space-y-1.5 text-[13px] text-stone-600">
          <Row icon={<MapPinIcon className="w-4 h-4 text-stone-400" />}>
            <span className="text-stone-700">{item.facility_name}</span>
            <span className="text-stone-400 mx-1.5">·</span>
            <span>{FACILITY_TYPE_LABEL[item.facility_type]}</span>
          </Row>
          <Row icon={<CalendarIcon className="w-4 h-4 text-stone-400" />}>
            <span className="text-stone-700">{item.schedule_days.join('·') || '-'}</span>
            {item.schedule_time && <>
              <span className="text-stone-400 mx-1.5">·</span>
              <span>{item.schedule_time}</span>
            </>}
          </Row>
        </dl>
      </div>
    </button>
  )
}

function Tag({ children, accent }: { children: React.ReactNode; accent?: boolean }) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11.5px] font-medium ring-1 ring-inset ${
        accent
          ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
          : 'bg-stone-50 text-stone-600 ring-stone-200'
      }`}
    >
      {children}
    </span>
  )
}

function Row({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 truncate">
      {icon}
      <span className="truncate">{children}</span>
    </div>
  )
}

function ageShortLabel(c: ClassListing): string | null {
  if (c.target_age_min == null || c.target_age_max == null) {
    return c.target_description ?? null
  }
  // 가장 가까운 버킷으로 라벨링.
  const buckets = AGE_BUCKETS.filter(
    (b) => c.target_age_min! <= b.max && c.target_age_max! >= b.min,
  )
  if (buckets.length === 0) return `${c.target_age_min}~${c.target_age_max}세`
  if (buckets.length === 1) return buckets[0].label.replace(/\s\(.+\)/, ` ${c.target_age_min}~${c.target_age_max}세`)
  return `${c.target_age_min}~${c.target_age_max}세`
}
