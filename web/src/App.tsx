import { useMemo, useState } from 'react'
import { ClassCard } from './components/ClassCard'
import { ClassDetail } from './components/ClassDetail'
import {
  FilterPanel,
  activeFilterCount,
  emptyFilters,
  type FilterState,
} from './components/FilterPanel'
import { Header } from './components/Header'
import { MOCK_CLASSES } from './data/mock'
import { AGE_BUCKETS, type ClassListing } from './types'

function matchesAge(c: ClassListing, filters: FilterState): boolean {
  if (filters.ageBuckets.size === 0) return true
  if (c.target_age_min == null || c.target_age_max == null) return false
  for (const id of filters.ageBuckets) {
    const b = AGE_BUCKETS.find((x) => x.id === id)
    if (!b) continue
    // 강좌의 연령 범위가 버킷과 겹치면 매치.
    if (c.target_age_min <= b.max && c.target_age_max >= b.min) return true
  }
  return false
}

function matches(c: ClassListing, filters: FilterState, q: string): boolean {
  if (filters.facilityTypes.size > 0 && !filters.facilityTypes.has(c.facility_type)) return false
  if (filters.statuses.size > 0 && !filters.statuses.has(c.status)) return false
  if (filters.days.size > 0 && !c.schedule_days.some((d) => filters.days.has(d as never))) return false
  if (filters.freeOnly && c.fee_won !== 0) return false
  if (!matchesAge(c, filters)) return false

  if (q) {
    const hay = `${c.title} ${c.facility_name} ${c.category ?? ''} ${c.target_description ?? ''}`.toLowerCase()
    if (!hay.includes(q.toLowerCase())) return false
  }
  return true
}

export default function App() {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<FilterState>(emptyFilters)
  const [filterOpen, setFilterOpen] = useState(false)
  const [selected, setSelected] = useState<ClassListing | null>(null)

  const visible = useMemo(
    () => MOCK_CLASSES.filter((c) => matches(c, filters, query.trim())),
    [filters, query],
  )

  return (
    <div className="min-h-full pb-12">
      <Header
        total={MOCK_CLASSES.length}
        shown={visible.length}
        query={query}
        onQueryChange={setQuery}
        onOpenFilters={() => setFilterOpen(true)}
        activeFilterCount={activeFilterCount(filters)}
      />

      <main className="max-w-3xl mx-auto px-4 pt-4">
        {visible.length === 0 ? (
          <div className="rounded-xl border border-dashed border-zinc-300 p-10 text-center text-zinc-500 text-sm">
            조건에 맞는 강좌가 없어요.
          </div>
        ) : (
          <ul className="space-y-3">
            {visible.map((c) => (
              <li key={`${c.source_id}:${c.external_id}`}>
                <ClassCard item={c} onClick={() => setSelected(c)} />
              </li>
            ))}
          </ul>
        )}
      </main>

      <FilterPanel
        open={filterOpen}
        filters={filters}
        onChange={setFilters}
        onClose={() => setFilterOpen(false)}
      />
      {selected && <ClassDetail item={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
