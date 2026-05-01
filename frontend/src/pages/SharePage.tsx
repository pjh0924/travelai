import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getSharedCourse } from '../api'
import type { CourseGetResponse } from '../types'
import KakaoMap from '../components/KakaoMap'
import DayScheduleList from '../components/DayScheduleList'

export default function SharePage() {
  const { shareCode } = useParams<{ shareCode: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<CourseGetResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!shareCode) return
    getSharedCourse(shareCode)
      .then(setData)
      .catch(() => setError('공유된 코스를 불러오는 데 실패했습니다.'))
      .finally(() => setLoading(false))
  }, [shareCode])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error ?? '알 수 없는 오류'}</p>
          <button className="btn-primary" onClick={() => void navigate('/')}>직접 만들기</button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 공유 배너 */}
      <div className="bg-primary-600 text-white text-center py-2 px-4 text-sm">
        이 코스가 마음에 드시나요?{' '}
        <button
          className="underline font-semibold hover:text-primary-100"
          onClick={() => void navigate('/')}
        >
          직접 만들어 보세요 →
        </button>
      </div>

      {/* 헤더 */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-2xl mx-auto px-4 py-3">
          <h1 className="font-semibold text-gray-900 text-sm">{data.course.title}</h1>
          <p className="text-xs text-gray-400 mt-0.5">{data.course.region} · {data.course.duration}</p>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-4 space-y-4">
        <div className="card">
          <p className="text-sm text-gray-700">{data.course.summary}</p>
          <p className="text-xs text-gray-400 mt-2">
            <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full text-xs">한국관광공사 공식 데이터</span>
          </p>
        </div>
        <KakaoMap days={data.course.days} />
        <DayScheduleList days={data.course.days} />
      </div>
    </div>
  )
}
