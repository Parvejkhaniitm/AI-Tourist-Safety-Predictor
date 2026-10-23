// MOCK service. Phase 7 me ye src/services/api.js (GET /api/routes) se replace hoga.
import { getMockRoutes } from '../data/mockRoutes'

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

function makeError(code, message) {
  const error = new Error(message)
  error.code = code // 'NOT_FOUND' ya 'SERVER_ERROR'
  return error
}

export async function fetchRoutes(destinationName) {
  await wait(700) // loading state dikhane ke liye nakli delay

  const name = String(destinationName ?? '').trim()

  // Sirf testing ke liye: ye naam server error state trigger karta hai
  if (name.toLowerCase() === 'server error') {
    throw makeError('SERVER_ERROR', 'Route data could not be loaded. The server did not respond.')
  }

  const record = getMockRoutes(name)
  if (!record) {
    throw makeError('NOT_FOUND', `We could not find routes for "${name}".`)
  }
  return record
}