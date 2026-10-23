<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseButton from '../components/BaseButton.vue'
import StatusMessage from '../components/StatusMessage.vue'
import RiskBadge from '../components/RiskBadge.vue'
import ScoreGauge from '../components/ScoreGauge.vue'
import FactorCard from '../components/FactorCard.vue'
import AnalysisSkeleton from '../components/AnalysisSkeleton.vue'
import { fetchAnalysis } from '../services/api'
import { destinationSuggestions } from '../data/mockDestinations'
import { getRiskLevel } from '../utils/risk'
import { saveLastAnalysis } from '../state/lastAnalysis'

const route = useRoute()
const router = useRouter()

// --- State: idle | loading | success | error ---
const status = ref('idle')
const result = ref(null)
const errorInfo = ref(null)

// URL se destination aur start: /analysis?destination=India%20Gate&start=...
const destinationName = computed(() => String(route.query.destination ?? '').trim())
const startName = computed(() => String(route.query.start ?? '').trim())

async function runAnalysis() {
  if (!destinationName.value) {
    status.value = 'idle'
    result.value = null
    return
  }

  const requested = destinationName.value
  status.value = 'loading'
  errorInfo.value = null

  try {
    const data = await fetchAnalysis(requested)
    if (requested !== destinationName.value) return // user beech me kisi aur destination par chala gaya
    result.value = data
    status.value = 'success'

    // Home page aur navbar ke liye pichhla result yaad rakho
    saveLastAnalysis({
      destination: data.destination,
      score: data.score,
      analyzedAt: data.analyzedAt,
    })
  } catch (err) {
    if (requested !== destinationName.value) return
    result.value = null
    errorInfo.value = { code: err.code ?? 'UNKNOWN', message: err.message || 'Something went wrong.' }
    status.value = 'error'
  }
}

// URL ka destination badle (ya page pehli baar khule) to analysis chalao
watch(destinationName, runAnalysis, { immediate: true })

// --- Navigation ---
function goHome() {
  router.push({ name: 'home' })
}
function goToRoutes() {
  router.push({
    name: 'routes',
    query: { destination: result.value.destination, ...(startName.value && { start: startName.value }) },
  })
}
function analyzeSuggestion(place) {
  router.push({
    name: 'analysis',
    query: { destination: place, ...(startName.value && { start: startName.value }) },
  })
}

// --- Derived values ---
const risk = computed(() => getRiskLevel(result.value?.score))
const analyzedText = computed(() =>
  result.value
    ? result.value.analyzedAt.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
    : '',
)
const usedFactorCount = computed(() => result.value?.factors.filter((f) => f.available).length ?? 0)
const hasMissingFactors = computed(() => !!result.value && usedFactorCount.value < result.value.factors.length)
const errorSuggestions = destinationSuggestions.slice(0, 3)
</script>

<template>
  <div class="container py-4 py-md-5 analysis-page">
    <!-- 1. Idle: koi destination chuna hi nahi -->
    <section v-if="status === 'idle'" class="sr-card p-4 p-md-5">
      <h1 class="h3 fw-bold mb-3">Destination analysis</h1>
      <StatusMessage type="info" title="No destination selected">
        Pick a destination on the Home page to see its risk analysis here.
      </StatusMessage>
      <BaseButton class="mt-4" @click="goHome">Go to Home</BaseButton>
    </section>

    <!-- 2. Loading -->
    <AnalysisSkeleton v-else-if="status === 'loading'" :destination="destinationName" />

    <!-- 3. Error -->
    <section v-else-if="status === 'error'" class="sr-card p-4 p-md-5">
      <h1 class="h3 fw-bold mb-3">Destination analysis</h1>

      <StatusMessage
        v-if="errorInfo.code === 'NOT_FOUND'"
        type="danger"
        :title="`We could not find &quot;${destinationName}&quot;`"
      >
        The demo covers a small list of Delhi destinations. Try one of these:
        <div class="d-flex flex-wrap gap-2 mt-2">
          <button
            v-for="place in errorSuggestions"
            :key="place"
            type="button"
            class="chip chip-danger"
            @click="analyzeSuggestion(place)"
          >
            {{ place }}
          </button>
        </div>
      </StatusMessage>

      <StatusMessage v-else type="danger">
        <div class="d-flex flex-wrap justify-content-between align-items-center gap-2">
          <span>{{ errorInfo.message }}</span>
          <BaseButton @click="runAnalysis">Try again</BaseButton>
        </div>
      </StatusMessage>

      <BaseButton outline class="mt-4" @click="goHome">Analyze Another Destination</BaseButton>
    </section>

    <!-- 4. Success -->
    <div v-else-if="status === 'success' && result">
      <header class="analysis-hero d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <p class="analysis-kicker mb-2"><span class="analysis-kicker-dot"></span> YOUR DESTINATION BRIEF</p>
          <h1 class="fw-bold mb-2">{{ result.destination }}</h1>
          <p class="analysis-location mb-2"><span aria-hidden="true">⌖</span> {{ result.location }}</p>
          <p v-if="startName" class="analysis-origin small mb-1">Starting from {{ startName }}</p>
          <p class="analysis-time small mb-0">
            Analyzed {{ analyzedText }} · Sample data shown for this demo
          </p>
        </div>
        <div class="d-grid d-sm-flex gap-2 align-self-md-start">
          <BaseButton outline @click="runAnalysis">Re-analyze</BaseButton>
          <BaseButton @click="goHome">Analyze Another Destination</BaseButton>
        </div>
      </header>

      <StatusMessage v-if="hasMissingFactors" type="warning" class="mb-4">
        Risk score based on {{ usedFactorCount }} of {{ result.factors.length }} factors. Confidence is lower than usual.
      </StatusMessage>

      <div class="row g-3 mb-4">
        <div class="col-lg-5">
          <section class="sr-card p-4 h-100 text-center" aria-labelledby="score-heading">
            <h2 id="score-heading" class="h5 fw-bold mb-3">Risk score</h2>
            <div class="mb-3"><RiskBadge :score="result.score" /></div>
            <ScoreGauge :score="result.score" />
            <p class="text-muted small mt-3 mb-0">
              A higher score means higher estimated risk. {{ result.score }} falls in the
              {{ risk.label }} range ({{ risk.range }}).
            </p>
          </section>
        </div>

        <div class="col-lg-7">
          <section class="sr-card p-4 h-100" aria-labelledby="why-heading">
            <h2 id="why-heading" class="h5 fw-bold mb-3">Why this risk level?</h2>
            <ol class="list-unstyled d-flex flex-column gap-3 mb-3">
              <li v-for="(reason, index) in result.reasons" :key="index" class="d-flex gap-3">
                <span class="step-number d-inline-flex align-items-center justify-content-center">
                  {{ index + 1 }}
                </span>
                <span>{{ reason }}</span>
              </li>
            </ol>
            <p class="text-muted small mb-0">
              Reasons are generated from the demo data of the selected destination. This score is an
              estimate, not a guarantee of personal safety.
            </p>
          </section>
        </div>
      </div>

      <section aria-labelledby="factors-heading" class="mb-4">
        <h2 id="factors-heading" class="h5 fw-bold mb-3">Factors behind the score</h2>
        <div class="row g-3 row-cols-1 row-cols-sm-2 row-cols-lg-5">
          <div v-for="factor in result.factors" :key="factor.key" class="col">
            <FactorCard
              :title="factor.title"
              :text="factor.text"
              :impact="factor.impact"
              :impact-label="factor.impactLabel"
              :data-label="factor.dataLabel"
              :available="factor.available"
            />
          </div>
        </div>
      </section>

      <section
        class="sr-card p-4 d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3"
      >
        <div>
          <h2 class="h5 fw-bold mb-1">Want to see how to get there?</h2>
          <p class="text-muted mb-0">
            Compare the shortest route with a safer alternative. Route data in this demo is illustrative.
          </p>
        </div>
        <BaseButton @click="goToRoutes">View Safer Routes</BaseButton>
      </section>
    </div>
  </div>
</template>

<style scoped>
.analysis-page{--analysis-ink:#18382f;--analysis-muted:#708077;color:var(--analysis-ink)}
.analysis-hero{align-items:flex-start;padding:30px 34px;border-radius:18px;background:radial-gradient(circle at 82% 8%,rgba(196,229,129,.22),transparent 28%),linear-gradient(118deg,#173e35,#28594a);color:#f6f4e8;box-shadow:0 15px 35px rgba(24,60,50,.12)}
.analysis-kicker{display:flex;align-items:center;gap:9px;color:#c5dfaa;font-size:.63rem;letter-spacing:.16em;font-weight:800}.analysis-kicker-dot{width:7px;height:7px;border-radius:50%;background:#c4e581;box-shadow:0 0 0 4px rgba(196,229,129,.14)}.analysis-hero h1{font-family:Georgia,'Times New Roman',serif;font-size:clamp(2.5rem,5vw,4.1rem);font-weight:500!important;letter-spacing:-.05em;line-height:1}.analysis-location{color:rgba(249,247,231,.9);font-size:.95rem}.analysis-location span{color:#c4e581}.analysis-time,.analysis-origin{color:rgba(245,246,232,.65)}.analysis-hero :deep(.btn){border-radius:9px;padding:.68rem .9rem}.analysis-hero :deep(.btn-primary){background:#c4e581;border-color:#c4e581;color:#19392f}.analysis-hero :deep(.btn-outline-primary){color:#f7f4e9;border-color:rgba(246,245,229,.48)}.analysis-hero :deep(.btn:hover){transform:translateY(-2px)}
.analysis-page :deep(.sr-card){border:1px solid #e0e7df;border-radius:16px;box-shadow:0 10px 28px rgba(33,67,47,.045);transition:transform .2s,box-shadow .2s}.analysis-page .row.g-3.mb-4>.col-lg-5 :deep(.sr-card){background:linear-gradient(160deg,#fff,#f1f6ee)}.analysis-page .row.g-3.mb-4>.col-lg-7 :deep(.sr-card){background:#fff}.analysis-page :deep(.sr-card h2){letter-spacing:-.025em}.analysis-page :deep(.step-number){width:30px;height:30px;background:#e5efde;color:#466d4c;border-radius:9px}.analysis-page :deep(.impact-lowers){color:#3b8050}.analysis-page :deep(.impact-raises){color:#b27522}.analysis-page :deep(.gauge-number){font-family:Georgia,'Times New Roman',serif;color:#1c4335}.analysis-page :deep(.gauge-safe){stroke:#77ae75}.analysis-page :deep(.gauge-moderate){stroke:#e2b856}.analysis-page :deep(.gauge-high){stroke:#d77966}.analysis-page :deep(.sr-card-dashed){border:1px solid #e0e8dd;border-radius:13px;box-shadow:0 8px 20px rgba(33,67,47,.04);transition:transform .2s,box-shadow .2s}.analysis-page :deep(.sr-card-dashed:hover){transform:translateY(-3px);box-shadow:0 12px 25px rgba(33,67,47,.09)}.analysis-page :deep(.sr-value){color:#23483a}.analysis-page>div>section.sr-card:last-child{border-color:transparent;background:linear-gradient(110deg,#e6efdf,#f4f3e8)}.analysis-page :deep(.btn){transition:transform .18s,box-shadow .18s}.analysis-page :deep(.btn:hover){transform:translateY(-1px);box-shadow:0 7px 14px rgba(24,55,40,.12)}
.analysis-page>section.sr-card{border:1px solid #dce6d9;border-radius:17px;box-shadow:0 15px 32px rgba(26,60,42,.06)}.analysis-page :deep(.status-message){border-radius:12px}
@media(max-width:767.98px){.analysis-hero{padding:24px 20px;border-radius:15px}.analysis-hero h1{font-size:2.7rem}.analysis-hero>div:last-child{width:100%}.analysis-hero>div:last-child :deep(.d-grid){grid-template-columns:1fr 1fr}.analysis-page :deep(.row.row-cols-lg-5>.col){width:100%}}
</style>
