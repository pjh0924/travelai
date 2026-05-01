import { useEffect, useRef } from 'react'
import type { DaySchedule } from '../types'

// 카카오맵 SDK 타입 선언 (전역 window.kakao)
declare global {
  interface Window {
    kakao: {
      maps: {
        load: (callback: () => void) => void
        Map: new (container: HTMLElement, options: object) => KakaoMap
        Marker: new (options: object) => KakaoMarker
        Polyline: new (options: object) => KakaoPolyline
        LatLng: new (lat: number, lng: number) => KakaoLatLng
        InfoWindow: new (options: object) => KakaoInfoWindow
        MarkerImage: new (src: string, size: object) => object
        Size: new (w: number, h: number) => object
      }
    }
  }
}

interface KakaoMap {
  setCenter: (latlng: KakaoLatLng) => void
  setBounds: (bounds: KakaoBounds) => void
}
interface KakaoMarker {
  setMap: (map: KakaoMap | null) => void
  addListener: (event: string, handler: () => void) => void
}
interface KakaoPolyline {
  setMap: (map: KakaoMap | null) => void
}
interface KakaoLatLng {
  getLat: () => number
  getLng: () => number
}
interface KakaoBounds {
  extend: (latlng: KakaoLatLng) => void
}
interface KakaoInfoWindow {
  open: (map: KakaoMap, marker: KakaoMarker) => void
  close: () => void
}

const DAY_COLORS = ['#3b82f6', '#22c55e', '#f97316', '#a855f7', '#ef4444']

interface Props {
  days: DaySchedule[]
}

export default function KakaoMap({ days }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<KakaoMap | null>(null)

  useEffect(() => {
    const allPlaces = days.flatMap((d) => d.places)
    if (allPlaces.length === 0 || !containerRef.current) return

    const init = () => {
      if (!containerRef.current) return
      const { kakao } = window
      const { maps } = kakao

      const center = new maps.LatLng(allPlaces[0].lat, allPlaces[0].lng)
      const map = new maps.Map(containerRef.current, {
        center,
        level: 8,
      })
      mapRef.current = map

      days.forEach((day, dayIdx) => {
        const color = DAY_COLORS[dayIdx % DAY_COLORS.length]
        const path: KakaoLatLng[] = []

        day.places.forEach((place) => {
          const pos = new maps.LatLng(place.lat, place.lng)
          path.push(pos)

          const marker = new maps.Marker({ position: pos, map })
          const infoContent = `
            <div style="padding:8px;max-width:180px;font-size:12px;">
              <strong>${place.name}</strong>
              ${place.barrier_free.certified ? '<span style="color:#16a34a;margin-left:4px;">♿</span>' : ''}
              <p style="margin:4px 0 0;color:#6b7280;">${place.recommendation}</p>
            </div>`
          const infoWindow = new maps.InfoWindow({ content: infoContent })
          marker.addListener('click', () => {
            infoWindow.open(map, marker)
          })
        })

        if (path.length > 1) {
          new maps.Polyline({
            map,
            path,
            strokeWeight: 3,
            strokeColor: color,
            strokeOpacity: 0.8,
            strokeStyle: 'solid',
          })
        }
      })
    }

    if (window.kakao?.maps) {
      window.kakao.maps.load(init)
    }
  }, [days])

  return (
    <div
      ref={containerRef}
      className="w-full rounded-2xl overflow-hidden border border-gray-100"
      style={{ height: '40vh', minHeight: '240px' }}
      data-testid="kakao-map"
    />
  )
}
