// SAMPLE / MOCK DATA ONLY.
// Ye scores aur texts UI test karne ke liye banaye gaye hain, asli ya verified safety facts nahi hain.
// Phase 7 me ye data backend API se replace hoga.

export const destinationSuggestions = [
  'India Gate',
  'Red Fort',
  'Qutub Minar',
  "Humayun's Tomb",
  'Lotus Temple',
]

// impact: 'lowers' | 'neutral' | 'raises'
// weather: null  ->  weather data missing (missing-data state test karne ke liye, Lotus Temple me)
const mockDestinations = {
  'india gate': {
    name: 'India Gate',
    location: 'New Delhi, Delhi',
    score: 78,
    reasons: [
      'The location sits on a central, open avenue, which the sample dataset rates as low risk.',
      'Weekend crowds and minor sample incident notes raise the risk slightly, so keep belongings secure.',
    ],
    factors: {
      location: { text: 'Central open avenue with main roads nearby.', impact: 'lowers', impactLabel: 'Lowers risk', dataLabel: 'Sample data' },
      crowd: { text: 'Busier than usual on weekends (estimate).', impact: 'raises', impactLabel: 'Raises risk slightly', dataLabel: 'Demo data, not live' },
      weather: { text: 'Warm and mostly clear, around 31°C.', impact: 'neutral', impactLabel: 'Neutral', dataLabel: 'Sample data' },
      incidents: { text: 'Minor petty-theft notes in crowded spots.', impact: 'raises', impactLabel: 'Raises risk slightly', dataLabel: 'Sample data, not verified' },
    },
  },
  'red fort': {
    name: 'Red Fort',
    location: 'Old Delhi, Delhi',
    score: 62,
    reasons: [
      'Dense surroundings and narrow lanes nearby push the sample risk estimate up.',
      'Heavy crowds near entry points raise the risk, so keep belongings close.',
    ],
    factors: {
      location: { text: 'Dense old-city surroundings with narrow lanes.', impact: 'raises', impactLabel: 'Raises risk slightly', dataLabel: 'Sample data' },
      crowd: { text: 'Very busy around entry gates (estimate).', impact: 'raises', impactLabel: 'Raises risk', dataLabel: 'Demo data, not live' },
      weather: { text: 'Hot and hazy, around 33°C.', impact: 'neutral', impactLabel: 'Neutral', dataLabel: 'Sample data' },
      incidents: { text: 'A few illustrative notes near market streets.', impact: 'raises', impactLabel: 'Raises risk slightly', dataLabel: 'Sample data, not verified' },
    },
  },
  'qutub minar': {
    name: 'Qutub Minar',
    location: 'Mehrauli, New Delhi',
    score: 74,
    reasons: [
      'A fenced complex with staffed entry keeps the sample risk estimate low.',
      'Moderate crowds and very few sample incident notes keep the overall estimate in the Safe range.',
    ],
    factors: {
      location: { text: 'Fenced heritage complex with staffed entry.', impact: 'lowers', impactLabel: 'Lowers risk', dataLabel: 'Sample data' },
      crowd: { text: 'Moderate visitor numbers (estimate).', impact: 'neutral', impactLabel: 'Neutral', dataLabel: 'Demo data, not live' },
      weather: { text: 'Mild and clear, around 28°C.', impact: 'neutral', impactLabel: 'Neutral', dataLabel: 'Sample data' },
      incidents: { text: 'Very few illustrative incident notes.', impact: 'lowers', impactLabel: 'Lowers risk', dataLabel: 'Sample data, not verified' },
    },
  },
  "humayun's tomb": {
    name: "Humayun's Tomb",
    location: 'Nizamuddin, New Delhi',
    score: 81,
    reasons: [
      'A large walled garden with controlled entry keeps the sample risk estimate low.',
      'Calmer crowds and few sample incident notes support a Safe rating.',
    ],
    factors: {
      location: { text: 'Large walled garden with controlled entry.', impact: 'lowers', impactLabel: 'Lowers risk', dataLabel: 'Sample data' },
      crowd: { text: 'Usually calmer outside weekends (estimate).', impact: 'lowers', impactLabel: 'Lowers risk', dataLabel: 'Demo data, not live' },
      weather: { text: 'Warm and clear, around 30°C.', impact: 'neutral', impactLabel: 'Neutral', dataLabel: 'Sample data' },
      incidents: { text: 'Few illustrative incident notes nearby.', impact: 'lowers', impactLabel: 'Lowers risk', dataLabel: 'Sample data, not verified' },
    },
  },
  'lotus temple': {
    name: 'Lotus Temple',
    location: 'Kalkaji, New Delhi',
    score: 36,
    reasons: [
      'Busy approach roads and limited lighting near exits push the sample risk estimate up.',
      'Large evening crowds and several sample incident notes raise the risk. Weather data is missing, so confidence is lower.',
    ],
    factors: {
      location: { text: 'Busy approach roads, limited lighting near exits.', impact: 'raises', impactLabel: 'Raises risk', dataLabel: 'Sample data' },
      crowd: { text: 'Large evening crowds (estimate).', impact: 'raises', impactLabel: 'Raises risk', dataLabel: 'Demo data, not live' },
      weather: null,
      incidents: { text: 'Several illustrative incident notes nearby.', impact: 'raises', impactLabel: 'Raises risk', dataLabel: 'Sample data, not verified' },
    },
  },
}

// User ke typed text se record dhoondta hai. Match nahi mila to null.
// Home page bhi isi ko use karta hai (name aur score ke liye).
export function getMockSafetyData(input) {
  const key = String(input ?? '')
    .trim()
    .toLowerCase()
    .replace(/[\u2018\u2019]/g, "'")
  return mockDestinations[key] ?? null
}