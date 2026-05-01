import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { generateCourse } from '../api'
import { getRecentCourses, saveRecentCourse } from '../storage'
import type { RecentCourse } from '../types'

const PLACEHOLDERS = [
  '2박3일 강원도 부모님 모시고 갈 건데 무릎 안 좋으세요',
  '유모차 끌고 제주도 1박2일 가고 싶어요',
  '혼자 경주 당일치기 역사 탐방 코스 추천해줘',
]

const LOADING_STEPS = [
  '여행 조건 분석 중...',
  '관광지 탐색 중...',
  '코스 구성 중...',
  '마무리 중...',
]

export default function HomePage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [recentCourses, setRecentCourses] = useState<RecentCourse[]>([])
  const [placeholderIdx, setPlaceholderIdx] = useState(0)

  useEffect(() => {
    setRecentCourses(getRecentCourses())
    const timer = setInterval(() => {
      setPlaceholderIdx((i) => (i + 1) % PLACEHOLDERS.length)
    }, 3000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    if (!loading) {
      setLoadingStep(0)
      return
    }
    const timer = setInterval(() => {
      setLoadingStep((s) => Math.min(s + 1, LOADING_STEPS.length - 1))
    }, 2000)
    return () => clearInterval(timer)
  }, [loading])

  const handleGenerate = async () => {
    const trimmed = query.trim()
    if (!trimmed) return
    setLoading(true)
    setError(null)
    try {
      const result = await generateCourse(trimmed)
      saveRecentCourse({
        course_id: result.course_id,
        title: result.course.title,
        region: result.course.region,
        duration: result.course.duration,
        created_at: result.generated_at,
      })
      void navigate(`/result/${result.course_id}`)
    } catch (err) {
      setError('코스 생성에 실패했습니다. 잠시 후 다시 시도해주세요.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleGenerate()
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      {/* 로고 */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-primary-600 mb-2">트레블AI</h1>
        <p className="text-gray-500 text-sm">TourAPI 공식 데이터 기반 맞춤 여행 코스 생성</p>
      </div>

      {/* 입력 카드 */}
      <div className="w-full max-w-xl card">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          어떤 여행을 원하시나요?
        </label>
        <textarea
          className="w-full border border-gray-200 rounded-xl p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 transition"
          rows={3}
          maxLength={200}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={PLACEHOLDERS[placeholderIdx]}
          disabled={loading}
          data-testid="query-input"
        />
        <div className="flex items-center justify-between mt-1 mb-3">
          <span className="text-xs text-gray-400">{query.length}/200</span>
          {error && <span className="text-xs text-red-500">{error}</span>}
        </div>
        <button
          className="btn-primary w-full flex items-center justify-center gap-2"
          onClick={() => void handleGenerate()}
          disabled={loading || query.trim().length === 0}
          data-testid="generate-btn"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>{LOADING_STEPS[loadingStep]}</span>
            </>
          ) : (
            '코스 만들기'
          )}
        </button>
      </div>

      {/* v2: 성향 기반 추천 진입점 카드 */}
      <div className="w-full max-w-xl mt-4">
        <button
          className="w-full text-left bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-100 rounded-2xl p-4 hover:border-purple-300 hover:shadow-md transition cursor-pointer"
          onClick={() => void navigate('/personality')}
          data-testid="personality-entry-btn"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-gray-800 text-sm">성향으로 코스 받기</p>
              <p className="text-xs text-gray-500 mt-0.5">
                MBTI · 혈액형 · 별자리로 나만의 여행 코스를 받아보세요
              </p>
            </div>
            <span className="text-purple-400 text-sm font-medium">시작하기 →</span>
          </div>
        </button>
      </div>

      {/* 최근 코스 */}
      {recentCourses.length > 0 && (
        <div className="w-full max-w-xl mt-8">
          <h2 className="text-sm font-semibold text-gray-500 mb-3">최근 코스</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {recentCourses.map((c) => (
              <button
                key={c.course_id}
                className="card text-left hover:border-primary-300 hover:shadow-md transition cursor-pointer"
                onClick={() => void navigate(`/result/${c.course_id}`)}
              >
                <p className="font-medium text-sm text-gray-800 truncate">{c.title}</p>
                <p className="text-xs text-gray-400 mt-1">{c.region} · {c.duration}</p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
