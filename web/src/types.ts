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

export const STATUS_BADGE: Record<Status, string> = {
  upcoming: 'bg-amber-100 text-amber-800',
  recruiting: 'bg-emerald-100 text-emerald-800',
  waitlist: 'bg-orange-100 text-orange-800',
  closed: 'bg-zinc-200 text-zinc-600',
  in_progress: 'bg-sky-100 text-sky-800',
  ended: 'bg-zinc-200 text-zinc-500',
  unknown: 'bg-zinc-100 text-zinc-500',
}

// 0~12세 → 4개 버킷
export const AGE_BUCKETS = [
  { id: 'infant', label: '영아 (0~2세)', min: 0, max: 2 },
  { id: 'toddler', label: '유아 (3~5세)', min: 3, max: 5 },
  { id: 'lower', label: '초등 저학년 (6~9세)', min: 6, max: 9 },
  { id: 'upper', label: '초등 고학년 (10~12세)', min: 10, max: 12 },
] as const

export type AgeBucketId = (typeof AGE_BUCKETS)[number]['id']

export const DAYS = ['월', '화', '수', '목', '금', '토', '일'] as const
export type Day = (typeof DAYS)[number]
