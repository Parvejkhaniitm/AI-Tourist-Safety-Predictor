// The model emits risk points: a lower score means a lower estimated risk.
export function getRiskLevel(score) {
  if (typeof score !== 'number' || Number.isNaN(score)) {
    return { label: 'No result yet', variant: 'none', range: '' }
  }
  if (score < 40) return { label: 'Safe', variant: 'safe', range: '0–39' }
  if (score < 70) return { label: 'Moderate', variant: 'moderate', range: '40–69' }
  return { label: 'High Risk', variant: 'high', range: '70–100' }
}
