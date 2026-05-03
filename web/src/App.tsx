import { useMemo, useState } from 'react'
import { CategoryStrip } from './components/CategoryStrip'
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
    if (c.target_age_min <= b.max && c.target_age_max >= b.min) return true
  }
  return false
}

function matches(
  c: ClassListing,
  filters: FilterState,
  q: string,
  category: string | null,
): boolean {
  if (category != null && c.category !== category) return false
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
  const [category, setCategory] = useState<string | null>(null)
  const [selected, setSelected] = useState<ClassListing | null>(null)

  // 카테고리 목록 + 카운트 — 카테고리는 카테고리 필터 자체를 제외한 결과에서 카운트.
  const { categories, categoryCounts } = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const c of MOCK_CLASSES) {
      if (!c.category) continue
      if (!matches(c, filters, query.trim(), null)) continue
      counts[c.category] = (counts[c.category] ?? 0) + 1
    }
    const order = ['미술', '음악', '체육', '코딩', '독서', '외국어', '과학', '요리', '두뇌놀이']
    const cats = order.filter((c) => counts[c])
    return { categories: cats, categoryCounts: counts }
  }, [filters, query])

  const visible = useMemo(
    () => MOCK_CLASSES.filter((c) => matches(c, filters, query.trim(), category)),
    [filters, query, category],
  )

  const totalForCategoryStrip = useMemo(
    () => MOCK_CLASSES.filter((c) => matches(c, filters, query.trim(), null)).length,
    [filters, query],
  )

  return (
    <div className="min-h-full bg-stone-50">
      <Header
        query={query}
        onQueryChange={setQuery}
        onOpenFilters={() => setFilterOpen(true)}
        activeFilterCount={activeFilterCount(filters)}
      />
      <CategoryStrip
        categories={categories}
        counts={categoryCounts}
        total={totalForCategoryStrip}
        selected={category}
        onSelect={setCategory}
      />

      <main className="max-w-3xl mx-auto px-4 pt-4 pb-12">
        <div className="px-1 pb-3 flex items-baseline justify-between">
          <p className="text-[13px] text-stone-500">
            <span className="font-semibold text-stone-700 tabular-nums">{visible.length}</span>개
            강좌
          </p>
          <p className="text-[11.5px] text-stone-400">합성 데이터 · 실제 강좌 아님</p>
        </div>

        {visible.length === 0 ? (
          <EmptyState />
        ) : (
          <ul className="space-y-3">
            {visible.map((c) => (
              <li key={`${c.source_id}:${c.external_id}`}>
                <ClassCard item={c} onClick={() => setSelected(c)} />
              </li>
            ))}
          </ul>
        )}

        <Footer />
      </main>

      <FilterPanel
        open={filterOpen}
        filters={filters}
        onChange={setFilters}
        onClose={() => setFilterOpen(false)}
        matchedCount={visible.length}
      />
      {selected && <ClassDetail item={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="rounded-2xl border border-dashed border-stone-300 bg-white p-10 text-center">
      <div className="mx-auto w-12 h-12 rounded-full bg-stone-100 flex items-center justify-center text-stone-400 text-xl">
        ·
      </div>
      <p className="mt-3 text-[14px] text-stone-700 font-medium">조건에 맞는 강좌가 없어요</p>
      <p className="mt-1 text-[12.5px] text-stone-500">필터를 조정하거나 검색어를 바꿔보세요.</p>
    </div>
  )
}

function Footer() {
  return (
    <footer className="mt-10 pt-6 border-t border-stone-200/70 text-[11.5px] text-stone-400 space-y-1.5">
      <p>송파구 공공시설 어린이 강좌 통합 검색 (MVP)</p>
      <p>현재 표시 데이터는 합성 데이터입니다. 실 데이터 연결은 진행 중.</p>
      <p>
        <a
          href="https://github.com/Daniel-Nexus/dongne-classes"
          target="_blank"
          rel="noopener noreferrer"
          className="underline-offset-2 hover:underline hover:text-stone-600"
        >
          오픈소스 · GitHub
        </a>
      </p>
    </footer>
  )
}
