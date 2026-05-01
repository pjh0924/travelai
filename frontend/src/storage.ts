// localStorage 기반 게스트 모드 코스 저장
import type { RecentCourse } from './types'

const STORAGE_KEY = 'travelai_recent_courses'
const MAX_COURSES = 3

export function getRecentCourses(): RecentCourse[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw) as RecentCourse[]
  } catch {
    return []
  }
}

export function saveRecentCourse(course: RecentCourse): void {
  const courses = getRecentCourses().filter((c) => c.course_id !== course.course_id)
  courses.unshift(course)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(courses.slice(0, MAX_COURSES)))
}

export function removeRecentCourse(courseId: string): void {
  const courses = getRecentCourses().filter((c) => c.course_id !== courseId)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(courses))
}
