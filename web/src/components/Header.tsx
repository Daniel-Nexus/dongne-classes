interface Props {
  total: number
  shown: number
  query: string
  onQueryChange: (q: string) => void
  onOpenFilters: () => void
  activeFilterCount: number
}

export function Header({
  total,
  shown,
  query,
  onQueryChange,
  onOpenFilters,
  activeFilterCount,
}: Props) {
  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur border-b border-zinc-200">
      <div className="max-w-3xl mx-auto px-4 pt-3 pb-2">
        <div className="flex items-baseline gap-2">
          <h1 className="text-lg font-bold tracking-tight">송파구 어린이 강좌</h1>
          <span className="text-xs text-zinc-500">{shown}/{total}</span>
        </div>
        <p className="text-[11px] text-zinc-500 mt-0.5">
          MVP · 합성 데이터 기반 · 실제 강좌 정보 아님
        </p>
        <div className="mt-3 flex gap-2">
          <input
            type="search"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="강좌명·시설·카테고리 검색"
            className="flex-1 min-w-0 rounded-lg border border-zinc-300 px-3 py-2 text-sm
                       focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          />
          <button
            onClick={onOpenFilters}
            className="relative shrink-0 rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium
                       hover:bg-zinc-50 active:bg-zinc-100"
          >
            필터
            {activeFilterCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 inline-flex h-5 min-w-5 items-center justify-center
                               rounded-full bg-emerald-600 px-1 text-[10px] font-bold text-white">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  )
}
