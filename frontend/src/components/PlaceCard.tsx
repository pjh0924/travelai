import type { PlaceItem } from '../types'

interface Props {
  place: PlaceItem
  isLast: boolean
}

export default function PlaceCard({ place, isLast }: Props) {
  return (
    <div className="relative pl-6">
      {/* 타임라인 선 */}
      {!isLast && (
        <div className="absolute left-2 top-8 bottom-0 w-0.5 bg-gray-200" />
      )}
      {/* 타임라인 점 */}
      <div className="absolute left-0 top-4 w-4 h-4 rounded-full bg-primary-500 border-2 border-white shadow-sm" />

      <div className="card mb-3 ml-2">
        <div className="flex gap-3">
          {/* 이미지 */}
          {place.image_url ? (
            <img
              src={place.image_url}
              alt={place.name}
              className="w-20 h-20 rounded-xl object-cover flex-shrink-0"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none'
              }}
            />
          ) : (
            <div className="w-20 h-20 rounded-xl bg-gray-100 flex-shrink-0 flex items-center justify-center text-2xl">
              📍
            </div>
          )}

          {/* 정보 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1 flex-wrap">
              <h3 className="font-semibold text-sm text-gray-900">{place.name}</h3>
              {place.barrier_free.certified && (
                <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">♿ 무장애</span>
              )}
            </div>
            {place.open_hours && (
              <p className="text-xs text-gray-400 mt-0.5">⏱ {place.open_hours}</p>
            )}
            <p className="text-xs text-gray-600 mt-1 line-clamp-2">{place.recommendation}</p>
            {place.barrier_free.note && (
              <p className="text-xs text-green-600 mt-1">{place.barrier_free.note}</p>
            )}
          </div>
        </div>
      </div>

      {/* 이동 정보 */}
      {!isLast && place.travel_to_next && (
        <div className="ml-2 mb-3 text-xs text-gray-400 flex items-center gap-1">
          <span>{place.travel_to_next.mode === '도보' ? '🚶' : '🚗'}</span>
          <span>{place.travel_to_next.mode} {place.travel_to_next.minutes}분</span>
        </div>
      )}
    </div>
  )
}
