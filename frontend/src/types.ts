// 트레블AI 공통 타입 정의

export interface BarrierFreeInfo {
  certified: boolean
  wheelchair_rental: boolean
  parking_accessible: boolean
  note: string
}

export interface TravelToNext {
  mode: string
  minutes: number
}

export interface PlaceItem {
  order: number
  content_id: string
  name: string
  address: string
  lat: number
  lng: number
  image_url: string
  open_hours: string
  recommendation: string
  barrier_free: BarrierFreeInfo
  travel_to_next: TravelToNext | null
}

export interface DaySchedule {
  day: number
  date_label: string
  places: PlaceItem[]
}

export interface CourseData {
  title: string
  region: string
  duration: string
  summary: string
  days: DaySchedule[]
  /** v2: LLM 생성 성향 반영 코멘트 1줄. 성향 미입력 시 빈 문자열. */
  personality_comment: string
}

export interface GenerateResponse {
  course_id: string
  course: CourseData
  generated_at: string
  cache_hit: boolean
}

export interface CourseGetResponse {
  course_id: string
  query: string
  course: CourseData
  created_at: string
}

// localStorage 저장용 최근 코스 요약
export interface RecentCourse {
  course_id: string
  title: string
  region: string
  duration: string
  created_at: string
}

// v2: 성향 프로파일
export interface PersonalityProfile {
  mbti: string
  blood_type: string
  zodiac: string
  note: string
}
