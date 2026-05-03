import {
  FACILITY_TYPE_LABEL,
  STATUS_BADGE,
  STATUS_LABEL,
  type ClassListing,
} from '../types'

interface Props {
  item: ClassListing
  onClick: () => void
}

export function ClassCard({ item, onClick }: Props) {
  const fee =
    item.fee_won == null
      ? '비용 미정'
      : item.fee_won === 0
        ? '무료'
        : `${item.fee_won.toLocaleString()}원`

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white border border-zinc-200 rounded-xl p-4
                 hover:border-emerald-300 hover:shadow-sm active:bg-zinc-50 transition"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-[11px] text-zinc-500">
            <span>{FACILITY_TYPE_LABEL[item.facility_type]}</span>
            <span>·</span>
            <span className="truncate">{item.facility_name}</span>
          </div>
          <h2 className="mt-1 font-semibold text-zinc-900 leading-snug break-keep">
            {item.title}
          </h2>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_BADGE[item.status]}`}
        >
          {STATUS_LABEL[item.status]}
        </span>
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5 text-[13px]">
        <div className="contents">
          <dt className="text-zinc-500">대상</dt>
          <dd className="text-zinc-800 truncate">{item.target_description ?? '-'}</dd>
        </div>
        <div className="contents">
          <dt className="text-zinc-500">일정</dt>
          <dd className="text-zinc-800 truncate">
            {item.schedule_days.join('·') || '-'} {item.schedule_time ?? ''}
          </dd>
        </div>
        <div className="contents">
          <dt className="text-zinc-500">기간</dt>
          <dd className="text-zinc-800 truncate">
            {item.period_start ?? '?'} ~ {item.period_end ?? '?'}
          </dd>
        </div>
        <div className="contents">
          <dt className="text-zinc-500">비용</dt>
          <dd className={`truncate ${item.fee_won === 0 ? 'text-emerald-700 font-medium' : 'text-zinc-800'}`}>
            {fee}
          </dd>
        </div>
      </dl>
    </button>
  )
}
