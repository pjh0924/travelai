import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getCourse } from '../api'
import type { CourseGetResponse } from '../types'
import KakaoMap from '../components/KakaoMap'
import DayScheduleList from '../components/DayScheduleList'

const DISCLAIMER =
  '혈액형/별자리는 재미를 위한 옵션입니다. 비과학적 요소를 포함합니다.'

export default function ResultPage() {
  const { courseId } = useParams<{ courseId: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<CourseGetResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!courseId) return
    getCourse(courseId)
      .then(setData)
      .catch(() => setError('코스를 불러오는 데 실패했습니다.'))
      .finally(() => setLoading(false))
  }, [courseId])

  const handleShare = async () => {
    const url = `${window.location.origin}/share/${courseId ?? ''}`
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      window.prompt('공유 URL 복사:', url)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">코스를 불러오는 중...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error ?? '알 수 없는 오류'}</p>
          <button className="btn-primary" onClick={() => void navigate('/')}>홈으로</button>
        </div>
      </div>
    )
  }

  const personalityComment = data.course.personality_comment

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => void navigate('/')}
            className="text-gray-500 hover:text-gray-800 transition"
            aria-label="홈으로"
          >
            ← 뒤로
          </button>
          <h1 className="flex-1 font-semibold text-gray-900 truncate text-sm">
            {data.course.title}
          </h1>
          <button
            onClick={() => void handleShare()}
            className="text-xs bg-primary-50 text-primary-600 px-3 py-1.5 rounded-full hover:bg-primary-100 transition"
            data-testid="share-btn"
          >
            {copied ? '복사됨!' : '공유 ▶'}
          </button>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-4 space-y-4">
        {/* v2: 성향 코멘트 (personality_comment 존재 시만 렌더링) */}
        {personalityComment && (
          <div
            className="bg-purple-50 border border-purple-100 rounded-2xl px-4 py-3 space-y-1"
            data-testid="personality-comment"
          >
            <p className="text-sm text-purple-800 font-medium">
              {personalityComment}
            </p>
            <p className="text-xs text-gray-400" data-testid="result-disclaimer">
              {DISCLAIMER}
            </p>
          </div>
        )}

        {/* 코스 요약 */}
        <div className="card">
          <p className="text-sm text-gray-500">{data.course.region} · {data.course.duration}</p>
          <p className="text-sm text-gray-700 mt-1">{data.course.summary}</p>
          <p className="text-xs text-gray-400 mt-2">
            <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full text-xs">한국관광공사 공식 데이터</span>
          </p>
        </div>

        {/* 카카오맵 */}
        <KakaoMap days={data.course.days} />

        {/* 일정표 */}
        <DayScheduleList days={data.course.days} />
      </div>
    </div>
  )
}
