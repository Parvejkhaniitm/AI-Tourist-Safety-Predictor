// ILLUSTRATIVE / MOCK DATA ONLY.
// Distances, times aur scores UI dikhane ke liye banaye gaye hain, real navigation data nahi hain.
// Phase 7 me ye GET /api/routes se replace hoga.
import { getMockSafetyData } from './mockDestinations'

const START = 'Connaught Place, New Delhi'

// safer: null  ->  "Route alternatives unavailable" state (Lotus Temple me test hota hai)
const routesByName = {
  'India Gate': {
    start: START,
    destinationLabel: 'India Gate, New Delhi',
    shortest: { distanceKm: 3.4, durationMin: 14, score: 64, note: 'Passes two busy junctions (sample data).' },
    safer: { distanceKm: 4.1, durationMin: 18, score: 82, note: 'Stays on wider main roads (sample data).' },
  },
  'Red Fort': {
    start: START,
    destinationLabel: 'Red Fort, Old Delhi',
    shortest: { distanceKm: 3.1, durationMin: 13, score: 55, note: 'Cuts through crowded old-city lanes (sample data).' },
    safer: { distanceKm: 3.9, durationMin: 17, score: 71, note: 'Uses main roads with more lighting (sample data).' },
  },
  'Qutub Minar': {
    start: START,
    destinationLabel: 'Qutub Minar, New Delhi',
    shortest: { distanceKm: 14.2, durationMin: 38, score: 68, note: 'Takes a congested stretch of main road (sample data).' },
    safer: { distanceKm: 15.3, durationMin: 44, score: 79, note: 'Uses a wider arterial road (sample data).' },
  },
  "Humayun's Tomb": {
    start: START,
    destinationLabel: "Humayun's Tomb, New Delhi",
    shortest: { distanceKm: 5.6, durationMin: 19, score: 72, note: 'Passes one busy junction (sample data).' },
    safer: { distanceKm: 6.0, durationMin: 22, score: 84, note: 'Stays on well-lit main roads (sample data).' },
  },
  'Lotus Temple': {
    start: START,
    destinationLabel: 'Lotus Temple, New Delhi',
    shortest: { distanceKm: 11.8, durationMin: 34, score: 41, note: 'Passes several crowded junctions (sample data).' },
    safer: null,
  },
}

// Destination ka naam normalize karna Phase 3 ke helper se hota hai, to code duplicate nahi hota.
export function getMockRoutes(input) {
  const destination = getMockSafetyData(input)
  if (!destination) return null

  const routes = routesByName[destination.name]
  if (!routes) return null

  return { destination: destination.name, ...routes }
}