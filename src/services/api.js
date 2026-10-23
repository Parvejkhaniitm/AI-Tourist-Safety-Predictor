// Centralized API service. Pages sirf yahin se data mangte hain.
// Mock mode: sample data (backend nahi chahiye) | Live mode: Flask backend.
// NOTE: request/response shapes "proposed" hain (API_CONTRACT.md dekho), backend ke saath confirm hone baki hain.
// Format badle to sirf neeche ke adapt* functions badlo, pages nahi.
import { fetchAnalysis as mockFetchAnalysis } from './mockAnalysisService'
import { fetchRoutes as mockFetchRoutes } from './mockRoutesService'
import { destinationSuggestions } from '../data/mockDestinations'

const MODE = import.meta.env.VITE_API_MODE === 'live' ? 'live' : 'mock'
const BASE_URL = String(import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const TIMEOUT_MS = 10000

export const API_MODE = MODE
export const isMockMode = MODE === 'mock'

console.info(`[SafeRoute] API mode: ${MODE}`)

// Error ka 'code' pages me check hota hai: 'NOT_FOUND', 'SERVER_ERROR', 'BAD_REQUEST'
export class ApiError extends Error {
  constructor(code, message) {
    super(message)
    this.code = code
  }
}

// ---------- Common request helper (sirf live mode me) ----------
async function request(path, options = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      signal: controller.signal,
    })
  } catch (err) {
    throw new ApiError(
      'SERVER_ERROR',
      err.name === 'AbortError'
        ? 'The server took too long to respond.'
        : 'Could not reach the server. Please check that the backend is running.',
    )
  } finally {
    clearTimeout(timer)
  }

  if (!response.ok) {
    // Sirf HTTP status dekhte hain, backend ke error body ke fields assume nahi karte.
    if (response.status === 404) throw new ApiError('NOT_FOUND', 'Destination not found.')
    const code = response.status >= 500 ? 'SERVER_ERROR' : 'BAD_REQUEST'
    throw new ApiError(code, `The server responded with an error (status ${response.status}).`)
  }

  try {
    return await response.json()
  } catch {
    throw new ApiError('SERVER_ERROR', 'The server sent a response that is not valid JSON.')
  }
}

// ---------- Adapters: backend response -> wo shape jo pages use karte hain ----------
const badFormat = (endpoint) => new ApiError('SERVER_ERROR', `Unexpected response format from ${endpoint}.`)
const isString = (v) => typeof v === 'string'
const isNumber = (v) => typeof v === 'number' && !Number.isNaN(v)

function adaptDestinations(raw) {
  if (!Array.isArray(raw) || !raw.every(isString)) throw badFormat('GET /api/destinations')
  return raw
}

function adaptAnalysis(raw) {
  const analyzedAt = new Date(raw?.analyzedAt)
  const valid =
    raw &&
    isString(raw.destination) &&
    isString(raw.location) &&
    isNumber(raw.score) &&
    Array.isArray(raw.reasons) &&
    raw.reasons.every(isString) &&
    Array.isArray(raw.factors) &&
    raw.factors.every((f) => f && isString(f.key) && isString(f.title) && typeof f.available === 'boolean') &&
    !Number.isNaN(analyzedAt.getTime())

  if (!valid) throw badFormat('POST /api/analyze')
  return { ...raw, analyzedAt } // analyzedAt string se Date ban jata hai
}

const isRoute = (r) => r && isNumber(r.distanceKm) && isNumber(r.durationMin) && isNumber(r.score)

function adaptRoutes(raw) {
  const valid =
    raw &&
    isString(raw.destination) &&
    isString(raw.start) &&
    isString(raw.destinationLabel) &&
    isRoute(raw.shortest) &&
    (raw.safer === null || isRoute(raw.safer))

  if (!valid) throw badFormat('GET /api/routes')
  return raw
}

// ---------- Public functions ----------

// GET /api/destinations  ->  ["India Gate", "Red Fort", ...]
export async function fetchDestinations() {
  if (isMockMode) return [...destinationSuggestions]
  return adaptDestinations(await request('/api/destinations'))
}

// POST /api/analyze  body: { destination }
export async function fetchAnalysis(destination) {
  if (isMockMode) return mockFetchAnalysis(destination)
  const raw = await request('/api/analyze', {
    method: 'POST',
    body: JSON.stringify({ destination }),
  })
  return adaptAnalysis(raw)
}

// GET /api/routes?destination=India%20Gate&start=Connaught%20Place
export async function fetchRoutes(destination, start = '') {
  if (isMockMode) return mockFetchRoutes(destination)
  const params = new URLSearchParams({ destination })
  if (start) params.set('start', start)
  const raw = await request(`/api/routes?${params}`)
  return adaptRoutes(raw)
}
