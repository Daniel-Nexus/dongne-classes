import {
  FACILITY_TYPE_LABEL,
  STATUS_BADGE,
  STATUS_LABEL,
  categoryStyle,
  type ClassListing,
} from '../types'
import {
  CalendarIcon,
  ClockIcon,
  CloseIcon,
  ExternalLinkIcon,
  MapPinIcon,
  UsersIcon,
} from './icons'

interface Props {
  item: ClassListing
  onClose: () => void
}

const REG_LABEL = {
  online: '온라인 신청',
  phone: '전화 신청',
  visit: '방문 신청',
  mixed: '혼합 신청',
  unknown: '확인 필요',
} as const

export function ClassDetail({ item, onClose }: Props) {
  const cat = categoryStyle(item.category)
  const free = item.fee_won === 0
  const totalFee =
    item.fee_won != null && item.fee_won >= 0
      ? item.fee_won + (item.materials_fee_won ?? 0)
      : null

  return (
    <div className="fixed inset-0 z-50 bg-black/45 flex flex-col" onClick={onClose}>
      <div
        className="mt-auto bg-stone-50 rounded-t-3xl max-h-[94vh] flex flex-col overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={`relative bg-gradient-to-br ${cat.gradient}`}>
          <div className="absolute top-3 left-1/2 -translate-x-1/2 w-10 h-1 rounded-full bg-stone-400/40" />
          <button
            onClick={onClose}
            className="absolute top-3 right-3 w-9 h-9 rounded-full bg-white/70 backdrop-blur flex items-center justify-center text-stone-600 hover:bg-white"
            aria-label="닫기"
          >
            <CloseIcon className="w-5 h-5" />
          </button>
          <div className="px-5 pt-9 pb-5">
            <div className="flex items-center gap-2 text-[12px] text-stone-700">
              <span className={`inline-block px-2 py-0.5 rounded-md font-semibold ${cat.bg} ${cat.text}`}>
                {item.category ?? '강좌'}
              </span>
              <span>·</span>
              <span>{FACILITY_TYPE_LABEL[item.facility_type]}</span>
            </div>
            <h2 className="mt-2 text-[22px] font-bold tracking-tight text-stone-900 break-keep leading-snug">
              {item.title}
            </h2>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11.5px] font-medium ring-1 ring-inset ${STATUS_BADGE[item.status]}`}
              >
                {STATUS_LABEL[item.status]}
              </span>
              {item.target_description && (
                <span className="inline-flex rounded-full px-2.5 py-0.5 text-[11.5px] font-medium bg-white/70 text-stone-700 ring-1 ring-inset ring-stone-200">
                  {item.target_description}
                </span>
              )}
              {free && (
                <span className="inline-flex rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold bg-emerald-600 text-white">
                  무료
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="overflow-y-auto px-5 pt-5 pb-4 space-y-5">
          {item.description && (
            <p className="text-[14px] text-stone-700 leading-relaxed break-keep">
              {item.description}
            </p>
          )}

          <InfoGrid>
            <InfoCell
              icon={<CalendarIcon className="w-4 h-4 text-stone-400" />}
              label="요일·시간"
              value={`${item.schedule_days.join('·') || '-'}${item.schedule_time ? '  ' + item.schedule_time : ''}`}
            />
            <InfoCell
              icon={<ClockIcon className="w-4 h-4 text-stone-400" />}
              label="기간"
              value={`${fmt(item.period_start)} ~ ${fmt(item.period_end)}${
                item.session_count ? `  (총 ${item.session_count}회)` : ''
              }`}
            />
            <InfoCell
              icon={<UsersIcon className="w-4 h-4 text-stone-400" />}
              label="정원"
              value={item.capacity ? `${item.capacity}명` : '-'}
            />
            <InfoCell
              icon={<MapPinIcon className="w-4 h-4 text-stone-400" />}
              label="장소"
              value={
                <>
                  <div className="text-stone-900 font-medium">{item.facility_name}</div>
                  {item.address && (
                    <div className="text-[12.5px] text-stone-500 mt-0.5">{item.address}</div>
                  )}
                  {item.venue_detail && (
                    <div className="text-[12.5px] text-stone-500">{item.venue_detail}</div>
                  )}
                </>
              }
            />
          </InfoGrid>

          <Section title="접수 안내">
            <Row
              k="접수기간"
              v={`${fmt(item.registration_start)} ~ ${fmt(item.registration_end)}`}
            />
            <Row k="접수방법" v={REG_LABEL[item.registration_method]} />
          </Section>

          <Section title="비용">
            <Row k="강좌비" v={item.fee_won == null ? '-' : free ? '무료' : `${item.fee_won.toLocaleString()}원`} />
            {item.materials_fee_won && item.materials_fee_won > 0 && (
              <Row k="재료비" v={`${item.materials_fee_won.toLocaleString()}원`} />
            )}
            {totalFee != null && totalFee > 0 && (
              <Row k="총합" v={`${totalFee.toLocaleString()}원`} bold />
            )}
          </Section>

          {item.instructor && (
            <Section title="강사">
              <Row k="이름" v={item.instructor} />
            </Section>
          )}
        </div>

        <div className="px-5 py-3 border-t border-stone-200 bg-white/80 backdrop-blur flex gap-2">
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-stone-900 text-white py-3 text-[14px] font-semibold hover:bg-stone-800 active:bg-stone-700"
          >
            원본 페이지에서 신청
            <ExternalLinkIcon className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  )
}

function fmt(s?: string): string {
  if (!s) return '?'
  // 2026-06-03 → 6.3
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s)
  if (!m) return s
  return `${Number(m[2])}.${Number(m[3])}`
}

function InfoGrid({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl bg-white ring-1 ring-stone-200 divide-y divide-stone-100">
      {children}
    </div>
  )
}

function InfoCell({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: React.ReactNode
}) {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      <div className="mt-0.5 shrink-0">{icon}</div>
      <div className="min-w-0 flex-1">
        <div className="text-[11.5px] font-medium text-stone-500 uppercase tracking-wide">{label}</div>
        <div className="mt-0.5 text-[13.5px] text-stone-800 break-keep">{value}</div>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-[11.5px] font-semibold text-stone-500 uppercase tracking-wide mb-2 px-1">
        {title}
      </h3>
      <dl className="rounded-2xl bg-white ring-1 ring-stone-200 px-4 py-3 space-y-2 text-[14px]">
        {children}
      </dl>
    </div>
  )
}

function Row({ k, v, bold }: { k: string; v: string; bold?: boolean }) {
  return (
    <div className="flex justify-between items-baseline gap-3">
      <dt className="text-stone-500 shrink-0">{k}</dt>
      <dd className={`text-right break-keep ${bold ? 'text-stone-900 font-semibold' : 'text-stone-800'}`}>
        {v}
      </dd>
    </div>
  )
}
