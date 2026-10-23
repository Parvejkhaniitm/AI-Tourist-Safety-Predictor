// MOCK service: backend ki jagah. Phase 7 me ye src/services/api.js (POST /api/analyze) se replace hoga.
// Page ye function aise call karta hai jaise koi asli API ho (async, loading, errors).
import { getMockSafetyData } from '../data/mockDestinations'

export class AnalysisError extends Error {
  constructor(code, message) {
    super(message)
    this.code = code // 'NOT_FOUND' ya 'SERVER_ERROR'
  }
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// Time and Day factor asli current time se banta hai (fake nahi).
function buildTimeFactor(date) {
  const day = date.toLocaleDateString('en-IN', { weekday: 'long' })
  const time = date
    .toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit', hour12: true })
    .toUpperCase()
  const daylight = date.getHours() >= 6 && date.getHours() < 18

  return {
    key: 'time',
    title: 'Time and Day',
    text: `${day}, ${time}. ${daylight ? 'Daylight with good visibility.' : 'After dark, lower visibility.'}`,
    impact: daylight ? 'lowers' : 'raises',
    impactLabel: daylight ? 'Lowers risk' : 'Raises risk slightly',
    dataLabel: 'From analysis time',
    available: true,
    daylight,
  }
}

function buildFactor(key, title, data) {
  if (!data) {
    return {
      key,
      title,
      text: `The ${title.toLowerCase()} service did not respond, so this factor is left out.`,
      impact: 'neutral',
      impactLabel: '',
      dataLabel: 'Not included in the score',
      available: false,
    }
  }
  return { key, title, available: true, ...data }
}

export async function fetchAnalysis(destinationName) {
  await wait(900) // loading state dikhane ke liye nakli delay

  const name = String(destinationName ?? '').trim()

  // Sirf testing ke liye: ye naam "server error" state trigger karta hai
  if (name.toLowerCase() === 'server error') {
    throw new AnalysisError('SERVER_ERROR', 'Analysis failed. The server did not respond.')
  }

  const record = getMockSafetyData(name)
  if (!record) {
    throw new AnalysisError('NOT_FOUND', `We could not find "${name}".`)
  }

  const analyzedAt = new Date()
  const timeFactor = buildTimeFactor(analyzedAt)

  // Wireframe ka order: Location, Time and Day, Crowd Density, Weather, Historical Incidents
  const factors = [
    buildFactor('location', 'Location', record.factors.location),
    timeFactor,
    buildFactor('crowd', 'Crowd Density', record.factors.crowd),
    buildFactor('weather', 'Weather', record.factors.weather),
    buildFactor('incidents', 'Historical Incidents', record.factors.incidents),
  ]

  const timeReason = timeFactor.daylight
    ? 'The analysis time falls in daylight, when visibility is good. This lowers the estimated risk.'
    : 'The analysis time falls after dark, when visibility is lower. This raises the estimated risk.'

  return {
    destination: record.name,
    location: record.location,
    score: record.score,
    analyzedAt,
    factors,
    reasons: [timeReason, ...record.reasons],
  }
}