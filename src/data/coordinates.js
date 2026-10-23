// Coordinates for the places shown in the starter destination picker and common
// Delhi/NCR starting points. No address is sent to a geocoder by this lookup.
const knownPlaces = new Map([
  ['india gate', { lat: 28.6129, lng: 77.2295, label: 'India Gate, New Delhi' }],
  ['red fort', { lat: 28.6562, lng: 77.2410, label: 'Red Fort, Old Delhi' }],
  ['qutub minar', { lat: 28.5245, lng: 77.1855, label: 'Qutub Minar, New Delhi' }],
  ["humayun's tomb", { lat: 28.5933, lng: 77.2507, label: "Humayun's Tomb, New Delhi" }],
  ['lotus temple', { lat: 28.5535, lng: 77.2588, label: 'Lotus Temple, New Delhi' }],
  ['connaught place', { lat: 28.6315, lng: 77.2167, label: 'Connaught Place, New Delhi' }],
  ['new delhi', { lat: 28.6139, lng: 77.2090, label: 'New Delhi, India' }],
  ['delhi', { lat: 28.6139, lng: 77.2090, label: 'Delhi, India' }],
  ['ghaziabad', { lat: 28.6692, lng: 77.4538, label: 'Ghaziabad, Uttar Pradesh' }],
  ['noida', { lat: 28.5355, lng: 77.3910, label: 'Noida, Uttar Pradesh' }],
  ['gurugram', { lat: 28.4595, lng: 77.0266, label: 'Gurugram, Haryana' }],
  ['gurgaon', { lat: 28.4595, lng: 77.0266, label: 'Gurugram, Haryana' }],
  ['igi airport', { lat: 28.5562, lng: 77.1000, label: 'Indira Gandhi International Airport' }],
])

export function parseCoordinates(value) {
  const match = String(value ?? '').match(/(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)/)
  if (!match) return null
  const lat = Number(match[1])
  const lng = Number(match[2])
  if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return null
  return { lat, lng, label: `${lat.toFixed(4)}, ${lng.toFixed(4)}` }
}

export function resolveCoordinates(value, explicitCoordinates = null) {
  if (explicitCoordinates && Number.isFinite(explicitCoordinates.lat) && Number.isFinite(explicitCoordinates.lng)) {
    return { lat: explicitCoordinates.lat, lng: explicitCoordinates.lng, label: String(value || 'Selected location') }
  }
  return parseCoordinates(value) ?? knownPlaces.get(String(value ?? '').trim().toLowerCase()) ?? null
}

export const knownDestinationData = [...knownPlaces.values()].slice(0, 5)
