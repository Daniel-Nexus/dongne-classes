import {
  AGE_BUCKETS,
  DAYS,
  FACILITY_TYPE_LABEL,
  STATUS_LABEL,
  type AgeBucketId,
  type Day,
  type FacilityType,
  type Status,
} from '../types'
import { CloseIcon } from './icons'

export interface FilterState {
  ageBuckets: Set<AgeBucketId>
  facilityTypes: Set<FacilityType>
  statuses: Set<Status>
  days: Set<Day>
  freeOnly: boolean
}

export function emptyFilters(): FilterState {
  return {
    ageBuckets: new Set(),
    facilityTypes: new Set(),
    statuses: new Set(),
    days: new Set(),
    freeOnly: false,
  }
}

export function activeFilterCount(f: FilterState): number {
  return (
    f.ageBuckets.size +
    f.facilityTypes.size +
    f.statuses.size +
    f.days.size +
    (f.freeOnly ? 1 : 0)
  )
}

const FACILITY_OPTIONS: FacilityType[] = [
  'gu_office',
  'library',
  'kids_culture',
  'youth_center',
  'sports',
]

const STATUS_OPTIONS: Status[] = ['recruiting', 'upcoming', 'waitlist', 'closed']

interface Props {
  open: boolean
  filters: FilterState
  onChange: (f: FilterState) => void
  onClose: () => void
  matchedCount: number
}

export function FilterPanel({ open, filters, onChange, onClose, matchedCount }: Props) {
  if (!open) return null

  const toggle = <T,>(set: Set<T>, value: T): Set<T> => {
    const next = new Set(set)
    if (next.has(value)) next.delete(value)
    else next.add(value)
    return next
  }

  const reset = () => onChange(emptyFilters())
  const count = activeFilterCount(filters)

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/45" onClick={onClose}>
      <div
        className="mt-auto bg-stone-50 rounded-t-3xl max-h-[88vh] flex flex-col shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative px-5 pt-5 pb-3 border-b border-stone-200/70">
          <div className="absolute top-2.5 left-1/2 -translate-x-1/2 w-10 h-1 rounded-full bg-stone-300" />
          <div className="flex items-center justify-between">
            <h2 className="text-[17px] font-bold text-stone-900">필터</h2>
            <div className="flex items-center gap-2">
              <button
                onClick={reset}
                disabled={count === 0}
                className="text-[13px] text-stone-500 disabled:text-stone-300 hover:text-stone-800"
              >
                초기화
              </button>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-full hover:bg-stone-200/70 flex items-center justify-center text-stone-500"
                aria-label="닫기"
              >
                <CloseIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-y-auto px-5 py-5 space-y-6">
          <FilterGroup label="대상 연령">
            {AGE_BUCKETS.map((b) => (
              <Chip
                key={b.id}
                active={filters.ageBuckets.has(b.id)}
                onClick={() =>
                  onChange({ ...filters, ageBuckets: toggle(filters.ageBuckets, b.id) })
                }
              >
                {b.label}
              </Chip>
            ))}
          </FilterGroup>

          <FilterGroup label="시설 유형">
            {FACILITY_OPTIONS.map((t) => (
              <Chip
                key={t}
                active={filters.facilityTypes.has(t)}
                onClick={() =>
                  onChange({ ...filters, facilityTypes: toggle(filters.facilityTypes, t) })
                }
              >
                {FACILITY_TYPE_LABEL[t]}
              </Chip>
            ))}
          </FilterGroup>

          <FilterGroup label="모집 상태">
            {STATUS_OPTIONS.map((s) => (
              <Chip
                key={s}
                active={filters.statuses.has(s)}
                onClick={() => onChange({ ...filters, statuses: toggle(filters.statuses, s) })}
              >
                {STATUS_LABEL[s]}
              </Chip>
            ))}
          </FilterGroup>

          <FilterGroup label="요일">
            {DAYS.map((d) => (
              <Chip
                key={d}
                small
                active={filters.days.has(d)}
                onClick={() => onChange({ ...filters, days: toggle(filters.days, d) })}
              >
                {d}
              </Chip>
            ))}
          </FilterGroup>

          <FilterGroup label="비용">
            <Chip
              active={filters.freeOnly}
              onClick={() => onChange({ ...filters, freeOnly: !filters.freeOnly })}
            >
              무료만 보기
            </Chip>
          </FilterGroup>
        </div>

        <div className="px-5 pt-3 pb-4 border-t border-stone-200/70 bg-white/80 backdrop-blur">
          <button
            onClick={onClose}
            className="w-full rounded-xl bg-stone-900 text-white py-3 text-[14px] font-semibold hover:bg-stone-800 active:bg-stone-700"
          >
            결과 {matchedCount}개 보기
          </button>
        </div>
      </div>
    </div>
  )
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-[12px] font-semibold text-stone-500 uppercase tracking-wide mb-2.5">
        {label}
      </h3>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  )
}

function Chip({
  active,
  onClick,
  children,
  small,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
  small?: boolean
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border transition ${
        small ? 'px-3.5 py-1.5 text-[14px]' : 'px-3.5 py-1.5 text-[13.5px]'
      } ${
        active
          ? 'bg-stone-900 border-stone-900 text-white'
          : 'bg-white border-stone-200 text-stone-700 hover:border-stone-300'
      }`}
    >
      {children}
    </button>
  )
}
