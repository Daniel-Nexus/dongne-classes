import { categoryStyle } from '../types'

interface Props {
  categories: string[]
  counts: Record<string, number>
  total: number
  selected: string | null
  onSelect: (category: string | null) => void
}

export function CategoryStrip({ categories, counts, total, selected, onSelect }: Props) {
  return (
    <div className="bg-stone-50 border-b border-stone-200/70">
      <div className="max-w-3xl mx-auto">
        <div className="flex gap-2 overflow-x-auto no-scrollbar px-4 py-3">
          <Chip
            active={selected === null}
            onClick={() => onSelect(null)}
            label="전체"
            count={total}
          />
          {categories.map((c) => (
            <Chip
              key={c}
              active={selected === c}
              onClick={() => onSelect(selected === c ? null : c)}
              label={c}
              count={counts[c] ?? 0}
              style={categoryStyle(c)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

interface ChipProps {
  active: boolean
  onClick: () => void
  label: string
  count: number
  style?: ReturnType<typeof categoryStyle>
}

function Chip({ active, onClick, label, count, style }: ChipProps) {
  return (
    <button
      onClick={onClick}
      className={`shrink-0 inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13px] font-medium border transition ${
        active
          ? 'bg-stone-900 text-white border-stone-900'
          : 'bg-white text-stone-700 border-stone-200 hover:border-stone-300 active:bg-stone-50'
      }`}
    >
      {style && !active && (
        <span className={`w-1.5 h-1.5 rounded-full ${style.stripe}`} aria-hidden />
      )}
      <span>{label}</span>
      <span
        className={`text-[11px] tabular-nums ${
          active ? 'text-white/70' : 'text-stone-400'
        }`}
      >
        {count}
      </span>
    </button>
  )
}
