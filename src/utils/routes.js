// Route comparison helpers. Model risk points are lower for lower estimated risk.

const round1 = (n) => Math.round(n * 10) / 10 // 4.1 - 3.4 = 0.7000000000000002 jaisa float error hatata hai

// Safer route shortest se kitna zyada (ya kam) hai.
// scoreDelta negative ho to safer route ka risk kam hai (jaise -27).
export function getTradeOff(shortest, safer) {
  return {
    distanceKm: round1(safer.distanceKm - shortest.distanceKm),
    durationMin: Math.round(safer.durationMin - shortest.durationMin),
    scoreDelta: Math.round(safer.score - shortest.score),
  }
}

// Safer alternative tabhi recommend hota hai jab uska risk score sach me kam ho
export function getRecommendedRoute(shortest, safer) {
  if (!safer) return 'shortest'
  return safer.score < shortest.score ? 'safer' : 'shortest'
}

// +18, -4, 0 jaisa text
export function formatSigned(value) {
  if (value > 0) return `+${value}`
  if (value < 0) return `-${Math.abs(value)}`
  return '0'
}
