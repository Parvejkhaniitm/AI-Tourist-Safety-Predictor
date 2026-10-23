// Shared frontend state (Pinia/Vuex ke bina).
// Analysis page jo result nikalta hai, uska chhota summary yahan save hota hai,
// taaki Home page (overview cards) aur router use dikha sakein.
import { reactive } from 'vue'

export const lastAnalysis = reactive({
  destination: '', // khali = abhi tak koi analysis nahi hua
  score: null,
  analyzedAt: null,
})

export function saveLastAnalysis({ destination, score, analyzedAt }) {
  lastAnalysis.destination = destination
  lastAnalysis.score = score
  lastAnalysis.analyzedAt = analyzedAt
}