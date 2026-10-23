// Risk ranges: High Risk 0-39 | Moderate 40-69 | Safe 70-100
// range text ab Analysis page ki explanation me bhi use hota hai.
export function getRiskLevel(score) {
  if (typeof score !== 'number' || Number.isNaN(score)) {
    return { label: 'No result yet', variant: 'none', range: '' }
  }
  if (score >= 70) return { label: 'Safe', variant: 'safe', range: '70–100' }
  if (score >= 40) return { label: 'Moderate', variant: 'moderate', range: '40–69' }
  return { label: 'High Risk', variant: 'high', range: '0–39' }
}