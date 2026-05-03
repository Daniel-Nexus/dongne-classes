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
}

export function FilterPanel({ open, filters, onChange, onClose }: Props) {
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
    <div className="fixed inset-0 z-50 flex flex-col bg-black/40" onClick={onClose}>
      <div className="mt-auto bg-white rounded-t-2xl max-h-[88vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-4 pb-2 border-b border-zinc-200">
          <h2 className="text-base font-semibold">필터</h2>
          <button onClick={reset} className="text-sm text-zinc-500 hover:text-zinc-800" disabled={count === 0}>
            초기화
          </button>
        </div>

        <div className="overflow-y-auto px-5 py-4 space-y-5">
          <FilterGroup label="대상 연령">
            {AGE_BUCKETS.map((b) => (
              <Chip
                key={b.id}
                active={filters.ageBuckets.has(b.id)}
                onClick={() => onChange({ ...filters, ageBuckets: toggle(filters.ageBuckets, b.id) })}
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
                onClick={() => onChange({ ...filters, facilityTypes: toggle(filters.facilityTypes, t) })}
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
              무료만
            </Chip>
          </FilterGroup>
        </div>

        <div className="px-5 py-3 border-t border-zinc-200 bg-white">
          <button
            onClick={onClose}
            className="w-full rounded-lg bg-zinc-900 text-white py-2.5 text-sm font-semibold hover:bg-zinc-800"
          >
            적용
          </button>
        </div>
      </div>
    </div>
  )
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-[12px] font-semibold text-zinc-500 uppercase tracking-wide mb-2">
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
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-3 py-1.5 text-sm border transition ${
        active
          ? 'bg-emerald-600 border-emerald-600 text-white'
          : 'bg-white border-zinc-300 text-zinc-700 hover:border-zinc-400'
      }`}
    >
      {children}
    </button>
  )
}
