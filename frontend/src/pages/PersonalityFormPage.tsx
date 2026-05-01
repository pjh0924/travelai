import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { generateCourseWithPersonality } from '../api'
import { saveRecentCourse } from '../storage'

const MBTI_LIST = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP',
] as const

const BLOOD_TYPES = ['A', 'B', 'AB', 'O', '모름'] as const

const ZODIAC_LIST = [
  '양자리', '황소자리', '쌍둥이자리', '게자리',
  '사자자리', '처녀자리', '천칭자리', '전갈자리',
  '사수자리', '염소자리', '물병자리', '물고기자리',
] as const

const LOADING_STEPS = [
  '성향 분석 중...',
  '관광지 탐색 중...',
  '코스 구성 중...',
  '마무리 중...',
]

const DISCLAIMER =
  '혈액형/별자리는 재미를 위한 옵션입니다. 비과학적 요소를 포함합니다.'

export default function PersonalityFormPage() {
  const navigate = useNavigate()
  const [selectedMbti, setSelectedMbti] = useState<string>('')
  const [bloodType, setBloodType] = useState<string>('')
  const [zodiac, setZodiac] = useState<string>('')
  const [note, setNote] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!selectedMbti) return
    setLoading(true)
    setError(null)

    // 로딩 스텝 인터벌
    const stepTimer = setInterval(() => {
      setLoadingStep((s) => Math.min(s + 1, LOADING_STEPS.length - 1))
    }, 2000)

    try {
      // personality 전용 자연어 쿼리를 자동 생성
      const autoQuery = note.trim()
        ? note.trim()
        : `${selectedMbti} 성향에 맞는 국내 여행 코스 추천해줘`

      const result = await generateCourseWithPersonality(autoQuery, {
        mbti: selectedMbti,
        blood_type: bloodType,
        zodiac,
        note: note.trim(),
      })
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
      clearInterval(stepTimer)
      setLoading(false)
      setLoadingStep(0)
    }
  }

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
          <h1 className="flex-1 font-semibold text-gray-900 text-sm">
            성향으로 코스 받기
          </h1>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* MBTI 칩 그리드 */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">
            MBTI <span className="text-red-400">*</span>
          </h2>
          <div className="grid grid-cols-4 gap-2" data-testid="mbti-grid">
            {MBTI_LIST.map((mbti) => (
              <button
                key={mbti}
                onClick={() => setSelectedMbti(selectedMbti === mbti ? '' : mbti)}
                className={[
                  'py-2 px-1 rounded-xl text-sm font-medium border transition',
                  selectedMbti === mbti
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-white text-gray-700 border-gray-200 hover:border-primary-300',
                ].join(' ')}
                data-testid={`mbti-chip-${mbti}`}
              >
                {mbti}
              </button>
            ))}
          </div>
        </section>

        {/* 혈액형 */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">혈액형 (선택)</h2>
          <select
            value={bloodType}
            onChange={(e) => setBloodType(e.target.value)}
            className="w-full border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            data-testid="blood-type-select"
          >
            <option value="">선택 안 함</option>
            {BLOOD_TYPES.map((bt) => (
              <option key={bt} value={bt}>{bt}형</option>
            ))}
          </select>
        </section>

        {/* 별자리 */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">별자리 (선택)</h2>
          <select
            value={zodiac}
            onChange={(e) => setZodiac(e.target.value)}
            className="w-full border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            data-testid="zodiac-select"
          >
            <option value="">선택 안 함</option>
            {ZODIAC_LIST.map((z) => (
              <option key={z} value={z}>{z}</option>
            ))}
          </select>
        </section>

        {/* 여행 메모 */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">여행 메모 (선택)</h2>
          <input
            type="text"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={100}
            placeholder="혼자 조용한 곳 좋아함, 맛집 위주 등"
            className="w-full border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition"
            data-testid="note-input"
          />
          <p className="text-xs text-gray-400 mt-1 text-right">{note.length}/100</p>
        </section>

        {/* 면책 문구 */}
        <p
          className="text-xs text-gray-400 bg-yellow-50 border border-yellow-100 rounded-xl px-4 py-2"
          data-testid="disclaimer"
        >
          {DISCLAIMER}
        </p>

        {/* 에러 메시지 */}
        {error && (
          <p className="text-sm text-red-500 text-center">{error}</p>
        )}

        {/* 코스 만들기 버튼 */}
        <button
          className="btn-primary w-full flex items-center justify-center gap-2"
          onClick={() => void handleGenerate()}
          disabled={loading || !selectedMbti}
          data-testid="personality-generate-btn"
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
    </div>
  )
}
