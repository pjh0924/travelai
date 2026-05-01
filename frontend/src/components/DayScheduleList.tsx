import { useState } from 'react'
import type { DaySchedule } from '../types'
import PlaceCard from './PlaceCard'

const DAY_COLORS = [
  'bg-blue-500',
  'bg-green-500',
  'bg-orange-500',
  'bg-purple-500',
  'bg-red-500',
]

interface Props {
  days: DaySchedule[]
}

export default function DayScheduleList({ days }: Props) {
  const [openDay, setOpenDay] = useState<number>(1)

  return (
    <div className="space-y-3">
      {days.map((day, idx) => (
        <div key={day.day} className="card overflow-hidden p-0">
          {/* Day 헤더 */}
          <button
            className="w-full flex items-center gap-3 p-4 text-left hover:bg-gray-50 transition"
            onClick={() => setOpenDay(openDay === day.day ? -1 : day.day)}
            data-testid={`day-header-${day.day}`}
          >
            <span className={`w-8 h-8 rounded-full ${DAY_COLORS[idx % DAY_COLORS.length]} text-white text-sm font-bold flex items-center justify-center`}>
              {day.day}
            </span>
            <span className="font-semibold text-gray-800">{day.date_label}</span>
            <span className="text-xs text-gray-400 ml-auto">{day.places.length}곳</span>
            <span className="text-gray-400">{openDay === day.day ? '▲' : '▼'}</span>
          </button>

          {/* 장소 목록 */}
          {openDay === day.day && (
            <div className="px-4 pb-4 pt-2">
              {day.places.map((place, placeIdx) => (
                <PlaceCard
                  key={place.content_id}
                  place={place}
                  isLast={placeIdx === day.places.length - 1}
                />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
