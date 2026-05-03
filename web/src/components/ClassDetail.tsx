import {
  FACILITY_TYPE_LABEL,
  STATUS_BADGE,
  STATUS_LABEL,
  type ClassListing,
} from '../types'

interface Props {
  item: ClassListing
  onClose: () => void
}

export function ClassDetail({ item, onClose }: Props) {
  const fee = item.fee_won == null ? null : item.fee_won === 0 ? '무료' : `${item.fee_won.toLocaleString()}원`
  const matFee =
    item.materials_fee_won && item.materials_fee_won > 0
      ? `재료비 ${item.materials_fee_won.toLocaleString()}원`
      : null

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex flex-col" onClick={onClose}>
      <div
        className="mt-auto bg-white rounded-t-2xl max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-5 pt-4 pb-3 border-b border-zinc-200">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="text-xs text-zinc-500">
                {FACILITY_TYPE_LABEL[item.facility_type]} · {item.facility_name}
              </div>
              <h2 className="mt-1 text-lg font-bold leading-snug break-keep">{item.title}</h2>
              {item.category && (
                <div className="mt-1 text-xs text-zinc-500">{item.category}</div>
              )}
            </div>
            <button
              onClick={onClose}
              className="shrink-0 rounded-full bg-zinc-100 hover:bg-zinc-200 w-9 h-9 flex items-center justify-center text-zinc-600"
              aria-label="닫기"
            >
              ✕
            </button>
          </div>
          <span
            className={`mt-3 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE[item.status]}`}
          >
            {STATUS_LABEL[item.status]}
          </span>
        </div>

        <div className="overflow-y-auto px-5 py-4 space-y-5">
          {item.description && (
            <p className="text-sm text-zinc-700 leading-relaxed break-keep">{item.description}</p>
          )}

          <Section title="대상 / 정원">
            <Row k="대상" v={item.target_description ?? '-'} />
            <Row k="정원" v={item.capacity ? `${item.capacity}명` : '-'} />
          </Section>

          <Section title="일정">
            <Row k="요일·시간" v={`${item.schedule_days.join('·') || '-'} ${item.schedule_time ?? ''}`} />
            <Row k="기간" v={`${item.period_start ?? '?'} ~ ${item.period_end ?? '?'}`} />
            <Row k="회차" v={item.session_count ? `총 ${item.session_count}회` : '-'} />
          </Section>

          <Section title="장소">
            <Row k="시설" v={item.facility_name} />
            <Row k="주소" v={item.address ?? '-'} />
            {item.venue_detail && <Row k="강의실" v={item.venue_detail} />}
          </Section>

          <Section title="접수">
            <Row
              k="접수기간"
              v={`${item.registration_start ?? '?'} ~ ${item.registration_end ?? '?'}`}
            />
            <Row k="접수방법" v={REG_LABEL[item.registration_method]} />
          </Section>

          <Section title="비용">
            <Row k="강좌비" v={fee ?? '-'} />
            {matFee && <Row k="재료비" v={matFee} />}
          </Section>

          {item.instructor && (
            <Section title="강사">
              <Row k="강사" v={item.instructor} />
            </Section>
          )}
        </div>

        <div className="px-5 py-3 border-t border-zinc-200 bg-white flex gap-2">
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 text-center rounded-lg bg-emerald-600 text-white py-2.5 text-sm font-semibold hover:bg-emerald-700"
          >
            원본 페이지에서 신청
          </a>
        </div>
      </div>
    </div>
  )
}

const REG_LABEL = {
  online: '온라인',
  phone: '전화',
  visit: '방문',
  mixed: '혼합',
  unknown: '확인 필요',
} as const

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wide mb-2">
        {title}
      </h3>
      <dl className="space-y-1.5 text-sm">{children}</dl>
    </div>
  )
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex gap-3">
      <dt className="w-20 shrink-0 text-zinc-500">{k}</dt>
      <dd className="flex-1 text-zinc-800 break-keep">{v}</dd>
    </div>
  )
}
