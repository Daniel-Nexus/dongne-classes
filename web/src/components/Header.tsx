import { FilterIcon, SearchIcon } from './icons'

interface Props {
  query: string
  onQueryChange: (q: string) => void
  onOpenFilters: () => void
  activeFilterCount: number
}

export function Header({ query, onQueryChange, onOpenFilters, activeFilterCount }: Props) {
  return (
    <header className="sticky top-0 z-30 bg-stone-50/85 backdrop-blur-md border-b border-stone-200/70">
      <div className="max-w-3xl mx-auto px-4 pt-4 pb-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-baseline gap-1.5">
              <h1 className="text-[19px] font-bold tracking-tight text-stone-900">
                송파 어린이 클래스
              </h1>
            </div>
            <p className="text-[12px] text-stone-500 mt-0.5">
              송파구 공공시설 강좌를 한 번에
            </p>
          </div>
        </div>

        <div className="mt-3 flex gap-2">
          <label className="relative flex-1 min-w-0">
            <span className="absolute inset-y-0 left-3 flex items-center text-stone-400">
              <SearchIcon className="w-4.5 h-4.5" />
            </span>
            <input
              type="search"
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              placeholder="강좌·시설·주제 검색"
              className="w-full rounded-xl bg-white border border-stone-200 pl-10 pr-3 py-2.5 text-[14px]
                         placeholder:text-stone-400
                         focus:outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
            />
          </label>
          <button
            onClick={onOpenFilters}
            className="relative shrink-0 rounded-xl bg-white border border-stone-200 px-3.5 py-2.5
                       text-stone-700 hover:bg-stone-50 active:bg-stone-100 transition"
            aria-label="필터"
          >
            <FilterIcon className="w-5 h-5" />
            {activeFilterCount > 0 && (
              <span className="absolute -top-1 -right-1 inline-flex h-5 min-w-5 items-center justify-center
                               rounded-full bg-orange-500 px-1 text-[10px] font-bold text-white ring-2 ring-stone-50">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  )
}
