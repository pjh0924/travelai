// API 클라이언트
import axios from 'axios'
import type { CourseGetResponse, GenerateResponse, PersonalityProfile } from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
})

export async function generateCourse(query: string): Promise<GenerateResponse> {
  const resp = await client.post<GenerateResponse>('/api/v1/course/generate', { query })
  return resp.data
}

/** v2: personality_profile 포함 코스 생성 */
export async function generateCourseWithPersonality(
  query: string,
  personality_profile: PersonalityProfile,
): Promise<GenerateResponse> {
  const resp = await client.post<GenerateResponse>('/api/v1/course/generate', {
    query,
    personality_profile,
  })
  return resp.data
}

export async function getCourse(courseId: string): Promise<CourseGetResponse> {
  const resp = await client.get<CourseGetResponse>(`/api/v1/course/${courseId}`)
  return resp.data
}

export async function getSharedCourse(shareCode: string): Promise<CourseGetResponse> {
  const resp = await client.get<CourseGetResponse>(`/api/v1/share/${shareCode}`)
  return resp.data
}
