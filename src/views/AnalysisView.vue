<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseButton from '../components/BaseButton.vue'
import StatusMessage from '../components/StatusMessage.vue'
import RiskBadge from '../components/RiskBadge.vue'
import ScoreGauge from '../components/ScoreGauge.vue'
import FactorCard from '../components/FactorCard.vue'
import AnalysisSkeleton from '../components/AnalysisSkeleton.vue'
import { fetchAnalysis, getCachedAnalysis } from '../services/api'
import { destinationSuggestions } from '../data/mockDestinations'
import { getRiskLevel } from '../utils/risk'
import { saveLastAnalysis } from '../state/lastAnalysis'

const route = useRoute()
const router = useRouter()

// --- State: idle | loading | success | error ---
const status = ref('idle')
const result = ref(null)
const errorInfo = ref(null)
const shouldPlayVideo = ref(false)

onMounted(() => {
  shouldPlayVideo.value = !window.matchMedia('(prefers-reduced-motion: reduce)').matches && !navigator.connection?.saveData
})

// URL se destination aur start: /analysis?destination=India%20Gate&start=...
const destinationName = computed(() => String(route.query.destination ?? '').trim())
const startName = computed(() => String(route.query.start ?? '').trim())
const startLat = computed(() => Number.isFinite(Number(route.query.startLat)) ? Number(route.query.startLat) : null)
const startLng = computed(() => Number.isFinite(Number(route.query.startLng)) ? Number(route.query.startLng) : null)

async function runAnalysis(forceRefresh = false) {
  if (!destinationName.value) {
    status.value = 'idle'
    result.value = null
    return
  }

  const requested = destinationName.value
  if (!forceRefresh) {
    const cached = getCachedAnalysis(requested)
    if (cached) {
      result.value = cached
      status.value = 'success'
      saveLastAnalysis({ destination: cached.destination, score: cached.score, analyzedAt: cached.analyzedAt })
      return
    }
  }
  status.value = 'loading'
  errorInfo.value = null

  try {
    const data = await fetchAnalysis(requested, { forceRefresh })
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
    query: {
      destination: result.value.destination,
      ...(startName.value && { start: startName.value }),
      ...(startLat.value !== null && startLng.value !== null && { startLat: startLat.value, startLng: startLng.value }),
    },
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
const scoreFactors = computed(() => result.value?.factors.filter((factor) => factor.key !== 'crowd') ?? [])
const usedFactorCount = computed(() => scoreFactors.value.filter((factor) => factor.available).length)
const hasMissingFactors = computed(() => !!result.value && usedFactorCount.value < scoreFactors.value.length)
const displayFactors = computed(() => result.value?.factors.map((factor) => {
  if (factor.key === 'crowd') {
    return { ...factor, displayOnly: true }
  }
  if (factor.key === 'location' && !factor.available) {
    return {
      ...factor,
      title: 'Location',
      text: result.value.location || result.value.destination,
      displayOnly: true,
    }
  }
  return factor
}) ?? [])
const errorSuggestions = destinationSuggestions.slice(0, 3)
</script>

<template>
  <div class="container py-4 py-md-5 analysis-page">
    <!-- 1. Idle: koi destination chuna hi nahi -->
    <section v-if="status === 'idle'" class="analysis-state-card">
      <div class="analysis-state-copy">
        <p class="analysis-state-kicker">A CLEARER STARTING POINT</p>
        <h1>Every good plan starts with a place.</h1>
        <p>Choose a destination to see its available context, estimated risk, and the signals behind the score.</p>
        <BaseButton @click="goHome">Choose a destination <span aria-hidden="true">↗</span></BaseButton>
      </div>
      <div class="analysis-state-art" aria-hidden="true"><span>⌖</span><i></i><b>01</b><small>DESTINATION BRIEF</small></div>
    </section>

    <!-- 2. Loading -->
    <AnalysisSkeleton v-else-if="status === 'loading'" :destination="destinationName" />

    <!-- 3. Error -->
    <section v-else-if="status === 'error'" class="analysis-state-card analysis-error-card">
      <div class="analysis-state-copy">
      <p class="analysis-state-kicker">WE COULDN’T FINISH THIS BRIEF</p>
      <h1>Let’s get your destination back on track.</h1>

      <StatusMessage
        v-if="errorInfo.code === 'NOT_FOUND'"
        type="danger"
        :title="`We could not find &quot;${destinationName}&quot;`"
      >
        Check the spelling or add the city and country to help us find the right place. You can also try one of these:
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

      <BaseButton outline class="mt-4" @click="goHome">Choose another destination</BaseButton>
      </div>
      <div class="analysis-state-art" aria-hidden="true"><span>↻</span><i></i><b>!</b><small>LET’S TRY AGAIN</small></div>
    </section>

    <!-- 4. Success -->
    <div v-else-if="status === 'success' && result">
      <header class="analysis-hero d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <video v-if="shouldPlayVideo" class="analysis-hero-video" autoplay muted loop playsinline preload="metadata" aria-hidden="true" tabindex="-1">
          <source src="/cinematic-city.mp4" type="video/mp4" />
        </video>
        <span class="analysis-hero-shade" aria-hidden="true"></span>
        <div>
          <p class="analysis-kicker mb-2"><span class="analysis-kicker-dot"></span> YOUR DESTINATION BRIEF</p>
          <h1 class="fw-bold mb-2">{{ result.destination }}</h1>
          <p class="analysis-location mb-2"><span aria-hidden="true">⌖</span> {{ result.location }}</p>
          <p v-if="startName" class="analysis-origin small mb-1">Starting from {{ startName }}</p>
          <p class="analysis-time small mb-0">
            Analyzed {{ analyzedText }} · {{ result.confidence }} confidence
          </p>
        </div>
        <div class="d-grid d-sm-flex gap-2 align-self-md-start">
          <BaseButton outline @click="runAnalysis(true)">Re-analyze</BaseButton>
          <BaseButton @click="goHome">Analyze Another Destination</BaseButton>
        </div>
      </header>

      <StatusMessage v-if="hasMissingFactors" type="warning" class="mb-4">
        Estimate uses {{ usedFactorCount }} of {{ scoreFactors.length }} score factors. Confidence: {{ result.confidence }}.
        {{ result.confidenceReasons.join(' ') }}
      </StatusMessage>

      <section class="analysis-snapshot mb-4" aria-label="Analysis snapshot">
        <div class="snapshot-heading"><span>AT A GLANCE</span><strong>How to read this estimate</strong></div>
        <div class="snapshot-metrics">
          <div class="snapshot-metric"><span>Signals used</span><strong>{{ usedFactorCount }} <small>/ {{ scoreFactors.length }}</small></strong><em>Scoring factors with available data</em></div>
          <div class="snapshot-metric"><span>Confidence</span><strong>{{ result.confidence }}</strong><em>Based on signal coverage and model context</em></div>
          <div class="snapshot-metric"><span>Estimated range</span><strong>{{ risk.label }}</strong><em>{{ risk.range }} · lower scores mean lower estimated risk</em></div>
        </div>
      </section>

      <div class="row g-3 mb-4">
        <div class="col-lg-5">
          <section class="sr-card p-4 h-100 text-center" aria-labelledby="score-heading">
            <h2 id="score-heading" class="h5 fw-bold mb-3">Risk score</h2>
            <div class="mb-3"><RiskBadge :score="result.score" /></div>
            <ScoreGauge :score="result.score" />
            <p class="text-muted small mt-3 mb-0">
              A lower score means lower estimated risk. {{ result.score }} falls in the
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
              {{ result.disclaimer || 'This is an estimate, not a guarantee of personal safety.' }}
            </p>
          </section>
        </div>
      </div>

      <section class="analysis-details-scene mb-4" aria-label="More destination details">
        <video v-if="shouldPlayVideo" class="details-scene-video" autoplay muted loop playsinline preload="metadata" aria-hidden="true" tabindex="-1">
          <source src="/cinematic-city-dusk.mp4" type="video/mp4" />
        </video>
        <span class="details-scene-shade" aria-hidden="true"></span>
        <section aria-labelledby="factors-heading" class="detail-factors">
          <h2 id="factors-heading" class="h5 fw-bold mb-3">Factors behind the score</h2>
          <div class="row g-3 row-cols-1 row-cols-sm-2 row-cols-lg-5">
            <div v-for="factor in displayFactors" :key="factor.key" class="col">
              <FactorCard
                :title="factor.title"
                :text="factor.text"
                :impact="factor.impact"
                :impact-label="factor.impactLabel"
                :data-label="factor.dataLabel"
                :available="factor.available"
                :display-only="factor.displayOnly"
              />
            </div>
          </div>
        </section>

        <section class="sr-card detail-route-cta p-4 d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3">
          <div>
            <h2 class="h5 fw-bold mb-1">Want to see how to get there?</h2>
            <p class="text-muted mb-0">
              Compare the shortest route with a safer alternative. Route data in this demo is illustrative.
            </p>
          </div>
          <BaseButton @click="goToRoutes">View Safer Routes</BaseButton>
        </section>
      </section>
    </div>
  </div>
</template>

<style scoped>
.analysis-page{--analysis-ink:#18382f;--analysis-muted:#708077;color:var(--analysis-ink)}
.analysis-details-scene{position:relative;isolation:isolate;overflow:hidden;padding:24px;border:1px solid #30494a;border-radius:20px;background:#102124}.details-scene-video,.details-scene-shade{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.details-scene-video{z-index:-2;object-fit:cover;object-position:center 48%;opacity:.62;filter:saturate(.82)}.details-scene-shade{z-index:-1;background:linear-gradient(110deg,rgba(5,17,20,.7),rgba(7,23,25,.54) 50%,rgba(8,24,26,.7)),linear-gradient(0deg,rgba(5,16,19,.7),rgba(5,16,19,.18) 70%)}.detail-factors,.detail-route-cta{position:relative;z-index:1}.detail-factors h2{color:#f0f2e7}.analysis-page .analysis-details-scene .row-cols-lg-5 :deep(.sr-card),.analysis-page .analysis-details-scene .row-cols-lg-5 :deep(.sr-card-dashed){background:rgba(12,28,31,.76)!important;border-color:rgba(181,213,184,.29)!important;backdrop-filter:blur(7px)}.detail-route-cta{background:rgba(13,29,31,.83)!important;border-color:rgba(190,222,181,.35)!important;backdrop-filter:blur(8px)}
.analysis-state-card{position:relative;isolation:isolate;min-height:320px;display:grid;grid-template-columns:1.1fr .9fr;align-items:center;overflow:hidden;padding:36px;border:1px solid #dce6d9;border-radius:18px;background:linear-gradient(145deg,#fff,#f0f4eb);box-shadow:0 18px 40px rgba(26,60,42,.06)}.analysis-state-copy{position:relative;z-index:1;max-width:570px}.analysis-state-kicker{margin:0 0 13px;color:#67816f;font-size:.64rem;font-weight:800;letter-spacing:.15em}.analysis-state-copy h1{max-width:520px;margin:0 0 13px;color:#17392f;font-family:Georgia,'Times New Roman',serif;font-size:clamp(2.1rem,4vw,3.35rem);font-weight:500;letter-spacing:-.045em;line-height:1.02}.analysis-state-copy>p:not(.analysis-state-kicker){max-width:470px;margin:0 0 21px;color:#718078;font-size:.9rem;line-height:1.7}.analysis-state-art{position:relative;justify-self:center;display:grid;place-items:center;width:min(100%,290px);aspect-ratio:1;border:1px solid #dce6d9;border-radius:50%;background:radial-gradient(circle,#fff 0 32%,transparent 33%),radial-gradient(circle at 50% 50%,#e7efdf,#eff3e9 62%,transparent 63%)}.analysis-state-art:before,.analysis-state-art:after{position:absolute;content:'';inset:12%;border:1px solid rgba(86,125,88,.2);border-radius:50%;transform:rotate(-28deg) scaleY(.65)}.analysis-state-art:after{inset:22%;transform:rotate(28deg) scaleY(.62)}.analysis-state-art>span{z-index:1;display:grid;place-items:center;width:64px;height:64px;border-radius:22px;background:#173e35;color:#c4e581;font-size:2rem;box-shadow:0 12px 28px rgba(23,62,53,.2)}.analysis-state-art>i{position:absolute;top:21%;right:23%;width:12px;height:12px;border-radius:50%;background:#d4a05f;box-shadow:0 0 0 7px rgba(212,160,95,.14)}.analysis-state-art>b{position:absolute;bottom:25%;left:20%;display:grid;place-items:center;width:29px;height:29px;border-radius:50%;background:#dcebbf;color:#385d42;font-size:.72rem}.analysis-state-art>small{position:absolute;bottom:11%;color:#738577;font-size:.55rem;font-weight:800;letter-spacing:.14em}.analysis-error-card{background:linear-gradient(145deg,#fff,#f7f1e9)}.analysis-error-card .analysis-state-art{background:radial-gradient(circle,#fff 0 32%,transparent 33%),radial-gradient(circle at 50% 50%,#f0e8dd,#f6f1e9 62%,transparent 63%)}.analysis-error-card .analysis-state-art>span{background:#704d36;color:#f1d7a7}.analysis-error-card .analysis-state-art>i{background:#d46f4b;box-shadow:0 0 0 7px rgba(212,111,75,.12)}.analysis-state-card :deep(.status-message){max-width:540px;margin-top:18px}.analysis-state-card :deep(.status-message .mt-2){gap:8px}
.analysis-hero{position:relative;isolation:isolate;overflow:hidden;align-items:flex-start;padding:30px 34px;border-radius:18px;background:radial-gradient(circle at 82% 8%,rgba(196,229,129,.22),transparent 28%),linear-gradient(118deg,#173e35,#28594a);color:#f6f4e8;box-shadow:0 15px 35px rgba(24,60,50,.12)}.analysis-hero-video,.analysis-hero-shade{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.analysis-hero-video{z-index:-2;object-fit:cover;object-position:center 54%;opacity:.35;filter:saturate(.75)}.analysis-hero-shade{z-index:-1;background:linear-gradient(90deg,rgba(13,39,34,.93),rgba(18,54,44,.78) 52%,rgba(19,54,46,.48)),linear-gradient(0deg,rgba(13,39,34,.37),transparent 60%)}.analysis-hero>div{position:relative;z-index:1}
.analysis-snapshot{display:grid;grid-template-columns:minmax(150px,.68fr) 2fr;gap:24px;align-items:center;padding:19px 23px;border:1px solid #dce6d9;border-radius:15px;background:linear-gradient(105deg,#eaf1e5,#f6f6ed)}.snapshot-heading span,.snapshot-heading strong{display:block}.snapshot-heading span{margin-bottom:7px;color:#668071;font-size:.58rem;font-weight:800;letter-spacing:.15em}.snapshot-heading strong{font:500 1.25rem/1.08 Georgia,'Times New Roman',serif;color:#1d4033;letter-spacing:-.025em}.snapshot-metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.snapshot-metric{min-width:0;padding:4px 14px;border-left:1px solid #d7e1d4}.snapshot-metric>span,.snapshot-metric>em{display:block;color:#748278;font-size:.69rem;font-style:normal}.snapshot-metric>strong{display:block;margin:4px 0;color:#1e4436;font:600 1.16rem/1.15 Georgia,'Times New Roman',serif}.snapshot-metric>strong small{font:500 .84rem Georgia,'Times New Roman',serif;color:#829087}.snapshot-metric>em{font-size:.62rem;line-height:1.4}
.analysis-kicker{display:flex;align-items:center;gap:9px;color:#c5dfaa;font-size:.63rem;letter-spacing:.16em;font-weight:800}.analysis-kicker-dot{width:7px;height:7px;border-radius:50%;background:#c4e581;box-shadow:0 0 0 4px rgba(196,229,129,.14)}.analysis-hero h1{font-family:Georgia,'Times New Roman',serif;font-size:clamp(2.5rem,5vw,4.1rem);font-weight:500!important;letter-spacing:-.05em;line-height:1}.analysis-location{color:rgba(249,247,231,.9);font-size:.95rem}.analysis-location span{color:#c4e581}.analysis-time,.analysis-origin{color:rgba(245,246,232,.65)}.analysis-hero :deep(.btn){border-radius:9px;padding:.68rem .9rem}.analysis-hero :deep(.btn-primary){background:#c4e581;border-color:#c4e581;color:#19392f}.analysis-hero :deep(.btn-outline-primary){color:#f7f4e9;border-color:rgba(246,245,229,.48)}.analysis-hero :deep(.btn:hover){transform:translateY(-2px)}
.analysis-page :deep(.sr-card){border:1px solid #e0e7df;border-radius:16px;box-shadow:0 10px 28px rgba(33,67,47,.045);transition:transform .2s,box-shadow .2s}.analysis-page .row.g-3.mb-4>.col-lg-5 :deep(.sr-card){background:linear-gradient(160deg,#fff,#f1f6ee)}.analysis-page .row.g-3.mb-4>.col-lg-7 :deep(.sr-card){background:#fff}.analysis-page :deep(.sr-card h2){letter-spacing:-.025em}.analysis-page :deep(.step-number){width:30px;height:30px;background:#e5efde;color:#466d4c;border-radius:9px}.analysis-page :deep(.impact-lowers){color:#3b8050}.analysis-page :deep(.impact-raises){color:#b27522}.analysis-page :deep(.gauge-number){font-family:Georgia,'Times New Roman',serif;color:#1c4335}.analysis-page :deep(.gauge-safe){stroke:#77ae75}.analysis-page :deep(.gauge-moderate){stroke:#e2b856}.analysis-page :deep(.gauge-high){stroke:#d77966}.analysis-page :deep(.sr-card-dashed){border:1px solid #e0e8dd;border-radius:13px;box-shadow:0 8px 20px rgba(33,67,47,.04);transition:transform .2s,box-shadow .2s}.analysis-page :deep(.sr-card-dashed:hover){transform:translateY(-3px);box-shadow:0 12px 25px rgba(33,67,47,.09)}.analysis-page :deep(.sr-value){color:#23483a}.analysis-page>div>section.sr-card:last-child{border-color:transparent;background:linear-gradient(110deg,#e6efdf,#f4f3e8)}.analysis-page :deep(.btn){transition:transform .18s,box-shadow .18s}.analysis-page :deep(.btn:hover){transform:translateY(-1px);box-shadow:0 7px 14px rgba(24,55,40,.12)}
.analysis-page>section.sr-card{border:1px solid #dce6d9;border-radius:17px;box-shadow:0 15px 32px rgba(26,60,42,.06)}.analysis-page :deep(.status-message){border-radius:12px}
@media(max-width:767.98px){.analysis-hero{padding:24px 20px;border-radius:15px}.analysis-hero h1{font-size:2.7rem}.analysis-hero>div:last-child{width:100%}.analysis-hero>div:last-child :deep(.d-grid){grid-template-columns:1fr 1fr}.analysis-page :deep(.row.row-cols-lg-5>.col){width:100%}}
@media(max-width:767.98px){.analysis-snapshot{grid-template-columns:1fr;gap:15px;padding:17px}.snapshot-metrics{grid-template-columns:1fr;gap:0}.snapshot-metric{padding:10px 0;border-left:0;border-top:1px solid #d7e1d4}.snapshot-metric>em{font-size:.68rem}}
@media(max-width:767.98px){.analysis-state-card{grid-template-columns:1fr;gap:12px;padding:25px 20px;border-radius:15px}.analysis-state-copy h1{font-size:2.35rem}.analysis-state-art{width:min(64%,220px);min-width:175px;grid-row:1}.analysis-state-card :deep(.status-message){font-size:.85rem}}
</style>
