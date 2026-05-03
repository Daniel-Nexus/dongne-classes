export type FacilityType =
  | 'gu_office'
  | 'library'
  | 'dong_center'
  | 'kids_culture'
  | 'youth_center'
  | 'sports'
  | 'parenting'
  | 'other'

export type RegistrationMethod =
  | 'online'
  | 'phone'
  | 'visit'
  | 'mixed'
  | 'unknown'

export type Status =
  | 'upcoming'
  | 'recruiting'
  | 'waitlist'
  | 'closed'
  | 'in_progress'
  | 'ended'
  | 'unknown'

export interface ClassListing {
  source_id: string
  external_id: string
  source_url: string
  title: string
  description?: string
  category?: string
  instructor?: string
  facility_name: string
  facility_type: FacilityType
  address?: string
  venue_detail?: string
  target_description?: string
  target_age_min?: number
  target_age_max?: number
  schedule_days: string[]
  schedule_time?: string
  session_count?: number
  period_start?: string
  period_end?: string
  capacity?: number
  registration_start?: string
  registration_end?: string
  registration_method: RegistrationMethod
  status: Status
  fee_won?: number
  materials_fee_won?: number
}

export const FACILITY_TYPE_LABEL: Record<FacilityType, string> = {
  gu_office: '구청',
  library: '도서관',
  dong_center: '동주민센터',
  kids_culture: '어린이문화회관',
  youth_center: '청소년시설',
  sports: '체육시설',
  parenting: '육아종합지원센터',
  other: '기타',
}

export const STATUS_LABEL: Record<Status, string> = {
  upcoming: '접수 예정',
  recruiting: '접수 중',
  waitlist: '대기',
  closed: '마감',
  in_progress: '진행 중',
  ended: '종료',
  unknown: '확인 필요',
}

export const STATUS_DOT: Record<Status, string> = {
  upcoming: 'bg-amber-500',
  recruiting: 'bg-emerald-500',
  waitlist: 'bg-orange-500',
  closed: 'bg-zinc-400',
  in_progress: 'bg-sky-500',
  ended: 'bg-zinc-400',
  unknown: 'bg-zinc-300',
}

export const STATUS_BADGE: Record<Status, string> = {
  upcoming: 'bg-amber-50 text-amber-700 ring-amber-200',
  recruiting: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  waitlist: 'bg-orange-50 text-orange-700 ring-orange-200',
  closed: 'bg-zinc-100 text-zinc-500 ring-zinc-200',
  in_progress: 'bg-sky-50 text-sky-700 ring-sky-200',
  ended: 'bg-zinc-100 text-zinc-500 ring-zinc-200',
  unknown: 'bg-zinc-50 text-zinc-500 ring-zinc-200',
}

export interface CategoryStyle {
  text: string
  bg: string
  ring: string
  stripe: string
  gradient: string
}

export const CATEGORY_FALLBACK: CategoryStyle = {
  text: 'text-stone-700',
  bg: 'bg-stone-100',
  ring: 'ring-stone-200',
  stripe: 'bg-stone-300',
  gradient: 'from-stone-100 to-stone-50',
}

export const CATEGORY_META: Record<string, CategoryStyle> = {
  '미술': {
    text: 'text-rose-700',
    bg: 'bg-rose-100',
    ring: 'ring-rose-200',
    stripe: 'bg-rose-400',
    gradient: 'from-rose-100 to-rose-50',
  },
  '음악': {
    text: 'text-violet-700',
    bg: 'bg-violet-100',
    ring: 'ring-violet-200',
    stripe: 'bg-violet-400',
    gradient: 'from-violet-100 to-violet-50',
  },
  '체육': {
    text: 'text-blue-700',
    bg: 'bg-blue-100',
    ring: 'ring-blue-200',
    stripe: 'bg-blue-400',
    gradient: 'from-blue-100 to-blue-50',
  },
  '코딩': {
    text: 'text-slate-700',
    bg: 'bg-slate-100',
    ring: 'ring-slate-200',
    stripe: 'bg-slate-500',
    gradient: 'from-slate-100 to-slate-50',
  },
  '독서': {
    text: 'text-amber-700',
    bg: 'bg-amber-100',
    ring: 'ring-amber-200',
    stripe: 'bg-amber-400',
    gradient: 'from-amber-100 to-amber-50',
  },
  '외국어': {
    text: 'text-teal-700',
    bg: 'bg-teal-100',
    ring: 'ring-teal-200',
    stripe: 'bg-teal-400',
    gradient: 'from-teal-100 to-teal-50',
  },
  '과학': {
    text: 'text-emerald-700',
    bg: 'bg-emerald-100',
    ring: 'ring-emerald-200',
    stripe: 'bg-emerald-400',
    gradient: 'from-emerald-100 to-emerald-50',
  },
  '요리': {
    text: 'text-orange-700',
    bg: 'bg-orange-100',
    ring: 'ring-orange-200',
    stripe: 'bg-orange-400',
    gradient: 'from-orange-100 to-orange-50',
  },
  '두뇌놀이': {
    text: 'text-fuchsia-700',
    bg: 'bg-fuchsia-100',
    ring: 'ring-fuchsia-200',
    stripe: 'bg-fuchsia-400',
    gradient: 'from-fuchsia-100 to-fuchsia-50',
  },
}

export function categoryStyle(category?: string): CategoryStyle {
  if (!category) return CATEGORY_FALLBACK
  return CATEGORY_META[category] ?? CATEGORY_FALLBACK
}

// 0~12세 → 4개 버킷
export const AGE_BUCKETS = [
  { id: 'infant', label: '영아 (0~2세)', short: '영아', min: 0, max: 2 },
  { id: 'toddler', label: '유아 (3~5세)', short: '유아', min: 3, max: 5 },
  { id: 'lower', label: '초등 저학년 (6~9세)', short: '저학년', min: 6, max: 9 },
  { id: 'upper', label: '초등 고학년 (10~12세)', short: '고학년', min: 10, max: 12 },
] as const

export type AgeBucketId = (typeof AGE_BUCKETS)[number]['id']

export const DAYS = ['월', '화', '수', '목', '금', '토', '일'] as const
export type Day = (typeof DAYS)[number]
