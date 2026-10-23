import { fetchAnalysis as mockFetchAnalysis } from './mockAnalysisService'
import { fetchRoutes as mockFetchRoutes } from './mockRoutesService'
import { destinationSuggestions } from '../data/mockDestinations'
import { resolveCoordinates } from '../data/coordinates'

const MODE = import.meta.env.VITE_API_MODE === 'live' ? 'live' : 'mock'
const BASE_URL = String(import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const TIMEOUT_MS = 25000
const ANALYSIS_CACHE_TTL_MS = 5 * 60 * 1000
const ANALYSIS_CACHE_PREFIX = 'saferoute:analysis:v4:'
const ROUTE_CACHE_TTL_MS = 15 * 60 * 1000
const ROUTE_CACHE_PREFIX = 'saferoute:routes:v2:'

export const API_MODE = MODE
export const isMockMode = MODE === 'mock'

console.info(`[SafeRoute] API mode: ${MODE}`)

export class ApiError extends Error {
  constructor(code, message) {
    super(message)
    this.code = code
  }
}

async function request(path, options = {}) {
  const { timeoutMs = TIMEOUT_MS, ...fetchOptions } = options
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...fetchOptions,
      headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...fetchOptions.headers },
      signal: controller.signal,
    })
  } catch (err) {
    throw new ApiError('SERVER_ERROR', err.name === 'AbortError'
      ? 'The server took too long to respond. Live map and model providers can take a few seconds.'
      : 'Could not reach the Flask backend. Start it with “python backend/app.py” and try again.')
  } finally {
    clearTimeout(timer)
  }

  if (!response.ok) {
    let payload = null
    try { payload = await response.json() } catch { /* response may not contain JSON */ }
    if (response.status === 404) throw new ApiError('NOT_FOUND', payload?.error?.message || 'Place not found.')
    throw new ApiError(payload?.error?.code || (response.status >= 500 ? 'SERVER_ERROR' : 'BAD_REQUEST'),
      payload?.error?.message || `The server responded with an error (status ${response.status}).`)
  }

  try { return await response.json() } catch {
    throw new ApiError('SERVER_ERROR', 'The server sent a response that is not valid JSON.')
  }
}

const isString = (value) => typeof value === 'string'
const isNumber = (value) => typeof value === 'number' && Number.isFinite(value)
const badFormat = (endpoint) => new ApiError('SERVER_ERROR', `Unexpected response format from ${endpoint}.`)

function adaptDestinations(raw) {
  if (!Array.isArray(raw)) throw badFormat('GET /api/destinations')
  const names = raw.map((item) => (isString(item) ? item : item?.name)).filter(isString)
  if (!names.length) throw badFormat('GET /api/destinations')
  return names
}

function adaptAnalysis(raw, resolvedPlace) {
  const destination = raw?.destination
  const analyzedAt = new Date(raw?.analyzed_at)
  const valid = destination && isString(destination.name) && isNumber(destination.lat) && isNumber(destination.lng) &&
    isNumber(raw?.score) && Array.isArray(raw?.reasons) && raw.reasons.every(isString) &&
    Array.isArray(raw?.factors) && raw.factors.every((factor) => factor && isString(factor.key) && isString(factor.title) && typeof factor.available === 'boolean') &&
    !Number.isNaN(analyzedAt.getTime())
  if (!valid) throw badFormat('POST /api/analyze')

  return {
    destination: destination.name,
    location: resolvedPlace?.label || `${destination.lat.toFixed(4)}, ${destination.lng.toFixed(4)}`,
    score: raw.score,
    analyzedAt,
    factors: raw.factors.map((factor) => ({
      key: factor.key,
      title: factor.title,
      text: factor.text,
      impact: ['raises', 'lowers', 'neutral'].includes(factor.impact) ? factor.impact : 'neutral',
      impactLabel: factor.impact_label || 'Not included',
      dataLabel: factor.data_label || (factor.available ? 'Source unavailable' : ''),
      available: factor.available,
    })),
    reasons: raw.reasons,
    confidence: raw.confidence?.label || 'Unknown',
    confidenceReasons: raw.confidence?.reasons || [],
    disclaimer: raw.disclaimer || '',
    missingFactors: raw.missing_factors || [],
  }
}

function adaptRoutes(raw) {
  const destination = raw?.destination?.name
  const origin = raw?.origin?.name
  if (!isString(destination) || !isString(origin) || !Array.isArray(raw.routes) || !raw.routes.length) {
    throw badFormat('POST /api/routes')
  }
  const routes = raw.routes.filter((route) => isNumber(route.distance_meters) && isNumber(route.duration_seconds)).map((route) => ({
    id: route.id,
    distanceKm: Math.round((route.distance_meters / 1000) * 10) / 10,
    durationMin: Math.round(route.duration_seconds / 60),
    score: isNumber(route.estimated_risk_score) ? route.estimated_risk_score : null,
    note: route.risk_explanation || route.note || `${route.estimated_risk_level} estimated risk · ${route.confidence} confidence · ${route.sample_count} sampled point(s).`,
    riskReasons: Array.isArray(route.risk_reasons) ? route.risk_reasons : [],
    riskExplanation: route.risk_explanation || '',
    path: route.path,
  }))
  if (!routes.length) throw badFormat('POST /api/routes')
  const shortest = [...routes].sort((a, b) => a.distanceKm - b.distanceKm)[0]
  const options = routes.filter((route) => route.id !== shortest.id)
  const safer = shortest.score === null ? null : options
    .filter((route) => route.score !== null && route.score < shortest.score)
    .sort((a, b) => a.score - b.score)[0] || null
  const alternative = safer || options.sort((a, b) => a.distanceKm - b.distanceKm)[0] || null
  return {
    destination,
    start: origin,
    destinationLabel: destination,
    provider: raw.route_provider || 'Directions provider',
    shortest,
    safer,
    alternative,
    limitations: raw.limitations || [],
    riskMethod: raw.risk_method || '',
    routeCount: routes.length,
  }
}

async function requireCoordinates(place, explicitCoordinates = null, role = 'place') {
  const resolved = resolveCoordinates(place, explicitCoordinates)
  if (resolved) return { ...resolved, name: String(place).trim() }
  const query = String(place ?? '').trim()
  if (query.length < 2) throw new ApiError('BAD_REQUEST', 'Enter a place name or coordinates to continue.')
  let match
  try {
    match = await request(`/api/geocode?q=${encodeURIComponent(query)}`)
  } catch (error) {
    if (error.code === 'NOT_FOUND') {
      throw new ApiError('NOT_FOUND', `Could not find the ${role} “${query}”. Add its city, state, or country and try again.`)
    }
    throw error
  }
  if (!isNumber(match?.lat) || !isNumber(match?.lng)) throw badFormat('GET /api/geocode')
  return { ...match, name: query }
}

export async function fetchDestinations() {
  if (isMockMode) return [...destinationSuggestions]
  return adaptDestinations(await request('/api/destinations'))
}

export function getCachedAnalysis(destination) {
  if (isMockMode) return null
  const cacheKey = `${ANALYSIS_CACHE_PREFIX}${String(destination).trim().toLowerCase()}`
  try {
    const cached = JSON.parse(sessionStorage.getItem(cacheKey) || 'null')
    if (cached && cached.expiresAt > Date.now() && cached.result) {
      return { ...cached.result, analyzedAt: new Date(cached.result.analyzedAt) }
    }
    if (cached) sessionStorage.removeItem(cacheKey)
  } catch { /* Storage can be disabled; network analysis still works. */ }
  return null
}

export async function fetchAnalysis(destination, { forceRefresh = false } = {}) {
  if (isMockMode) return mockFetchAnalysis(destination)
  const cacheKey = `${ANALYSIS_CACHE_PREFIX}${String(destination).trim().toLowerCase()}`
  if (!forceRefresh) {
    const cached = getCachedAnalysis(destination)
    if (cached) return cached
  } else {
    try {
      sessionStorage.removeItem(cacheKey)
    } catch { /* Storage can be disabled; network analysis still works. */ }
  }

  const resolved = await requireCoordinates(destination)
  const raw = await request('/api/analyze', {
    method: 'POST',
    body: JSON.stringify({ ...resolved, force_refresh: forceRefresh }),
  })
  const result = adaptAnalysis(raw, resolved)
  try {
    sessionStorage.setItem(cacheKey, JSON.stringify({
      expiresAt: Date.now() + ANALYSIS_CACHE_TTL_MS,
      result,
    }))
  } catch { /* Storage can be full or disabled; the backend cache remains available. */ }
  return result
}

export async function fetchRoutes(destination, start = '', startCoordinates = null) {
  if (isMockMode) return mockFetchRoutes(destination)
  const cacheKey = routeCacheKey(destination, start, startCoordinates)
  const cached = getCachedRoutes(destination, start, startCoordinates)
  if (cached) return cached

  const [origin, target] = await Promise.all([
    requireCoordinates(start, startCoordinates, 'starting point'),
    requireCoordinates(destination, null, 'destination'),
  ])
  const raw = await request('/api/routes', {
    timeoutMs: 90000,
    method: 'POST',
    body: JSON.stringify({ origin, destination: target }),
  })
  const result = adaptRoutes(raw)
  try {
    localStorage.setItem(cacheKey, JSON.stringify({ expiresAt: Date.now() + ROUTE_CACHE_TTL_MS, result }))
  } catch {
    try {
      sessionStorage.setItem(cacheKey, JSON.stringify({ expiresAt: Date.now() + ROUTE_CACHE_TTL_MS, result }))
    } catch { /* Storage can be full or disabled; backend cache remains available. */ }
  }
  return result
}

function routeCacheKey(destination, start, startCoordinates) {
  return `${ROUTE_CACHE_PREFIX}${JSON.stringify([
    String(start).trim().toLowerCase(),
    startCoordinates ? [Number(startCoordinates.lat).toFixed(5), Number(startCoordinates.lng).toFixed(5)] : null,
    String(destination).trim().toLowerCase(),
  ])}`
}

export function getCachedRoutes(destination, start = '', startCoordinates = null) {
  if (isMockMode) return null
  const cacheKey = routeCacheKey(destination, start, startCoordinates)
  try {
    let cached = JSON.parse(localStorage.getItem(cacheKey) || 'null')
    if (cached && cached.expiresAt > Date.now() && cached.result) return cached.result
    if (cached) {
      localStorage.removeItem(cacheKey)
    }
  } catch { /* Storage can be disabled; route lookup still works. */ }
  try {
    const cached = JSON.parse(sessionStorage.getItem(cacheKey) || 'null')
    if (cached && cached.expiresAt > Date.now() && cached.result) return cached.result
    if (cached) sessionStorage.removeItem(cacheKey)
  } catch { /* Storage can be disabled; route lookup still works. */ }
  return null
}

export async function reverseGeocodeCoordinates({ lat, lng }) {
  if (isMockMode) return null
  const match = await request(`/api/reverse-geocode?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}`)
  return isString(match?.label) && match.label.trim() ? match.label : null
}

export async function fetchHealth() {
  if (isMockMode) return { status: 'mock', models: null }
  return request('/api/health')
}
