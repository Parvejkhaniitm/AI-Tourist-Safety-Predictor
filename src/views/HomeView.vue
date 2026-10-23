<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SearchBar from '../components/SearchBar.vue'
import OverviewCard from '../components/OverviewCard.vue'
import RiskBadge from '../components/RiskBadge.vue'
import BaseButton from '../components/BaseButton.vue'
import HowItWorks from '../components/HowItWorks.vue'
import { destinationSuggestions } from '../data/mockDestinations'
import { fetchDestinations } from '../services/api'
import { lastAnalysis } from '../state/lastAnalysis'


const router = useRouter()

// --- State ---
const destination = ref('')
const errorMessage = ref('')
const start = ref('')
const startError = ref('')
const selectedSpot = ref(destinationSuggestions[0])

// Suggestions: pehle local list, backend se list aa jaye to wo
const suggestions = ref(destinationSuggestions)

onMounted(async () => {
  try {
    const list = await fetchDestinations()
    if (list.length > 0) suggestions.value = list
  } catch (err) {
    // Suggestions zaroori nahi, fail hone par local list chalti rahe
    console.warn('[SafeRoute] Could not load destinations, using the local list.', err.message)
  }
})

// Type karte hi purana error hata do
watch(destination, (value) => {
  errorMessage.value = ''
  const match = suggestions.value.find((place) => place.toLowerCase() === value.trim().toLowerCase())
  if (match) selectedSpot.value = match
})


watch(start, () => {
  startError.value = ''
})

// --- Actions ---
// Home -> Analysis. Destination dhoondna aur not-found sambhalna Analysis page ka kaam hai.
function handleAnalyze() {
  const startName = start.value.trim()
  const name = destination.value.trim()
  let hasError = false

  if (startName.length < 2) {
    startError.value = 'Please enter your starting point.'
    hasError = true
  }
  if (name.length < 2) {
    errorMessage.value = 'Please enter or pick a destination to continue.'
    hasError = true
  }
  if (hasError) return

  router.push({ name: 'analysis', query: { destination: name, start: startName } })
}


function viewLastAnalysis() {
  router.push({ name: 'analysis', query: { destination: lastAnalysis.destination } })
}

function chooseDestination(place) {
  destination.value = place
  selectedSpot.value = place
  document.getElementById('destination-input')?.focus()
}

// --- Derived values (shared state se) ---
const hasResult = computed(() => lastAnalysis.destination !== '')
const scoreText = computed(() => (hasResult.value ? `${lastAnalysis.score} / 100` : '-- / 100'))
const lastUpdatedText = computed(() =>
  hasResult.value
    ? lastAnalysis.analyzedAt.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
    : '--',
)
</script>

<template>
  <div class="home-page">
    <div class="container home-container">
      <section class="home-hero" aria-labelledby="home-title">
        <div class="hero-copy">
          <div class="eyebrow"><span class="eyebrow-dot"></span> TRAVEL WITH A LITTLE MORE CLARITY</div>
          <h1 id="home-title">The best trips<br />start with <em>feeling ready.</em></h1>
          <p class="hero-description">A thoughtful look at the place, the time, and the way there — so you can plan your next stop with more context.</p>
          <div class="hero-proof">
            <span class="proof-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none"><path d="M12 3 19 6v5c0 4.6-2.8 8-7 10-4.2-2-7-5.4-7-10V6l7-3Z"/><path d="m9 12 2 2 4-4"/></svg>
            </span>
            <span><strong>More informed decisions</strong><small>Know what the estimate can — and can’t — tell you.</small></span>
          </div>
        </div>

        <div class="hero-art" aria-label="Illustrated route winding through a landscape" role="img">
          <div class="art-orbit orbit-one"></div><div class="art-orbit orbit-two"></div>
          <div class="art-sun"></div>
          <svg class="route-art" viewBox="0 0 520 410" fill="none" aria-hidden="true">
            <path class="terrain terrain-back" d="M0 275 82 198l46 38 92-112 55 69 79-91 63 82 103-75v301H0V275Z"/>
            <path class="terrain terrain-front" d="m0 306 91-70 63 51 85-94 66 70 81-56 56 33 78-72v222H0V306Z"/>
            <path class="route-shadow" d="M70 330c65-11 56-93 131-83 76 10 39 100 121 77 55-16 52-95 119-101"/>
            <path class="route-stroke" d="M70 330c65-11 56-93 131-83 76 10 39 100 121 77 55-16 52-95 119-101"/>
            <circle cx="70" cy="330" r="12" class="pin-start"/><circle cx="70" cy="330" r="4" class="pin-center"/>
            <circle cx="441" cy="223" r="17" class="pin-end"/><path d="M441 215v9l6 4" class="pin-clock"/>
            <rect x="28" y="351" width="104" height="33" rx="16.5" class="map-label"/><text x="80" y="372" text-anchor="middle" class="map-label-text">YOUR START</text>
            <rect x="385" y="184" width="108" height="33" rx="16.5" class="map-label"/><text x="439" y="205" text-anchor="middle" class="map-label-text">{{ selectedSpot.split(' ')[0].toUpperCase() }}</text>
            <circle cx="339" cy="78" r="3" class="sparkle"/><circle cx="385" cy="111" r="2" class="sparkle"/><circle cx="150" cy="118" r="2.5" class="sparkle"/>
          </svg>
          <div class="art-caption"><span class="caption-line"></span> EVERY JOURNEY HAS A STORY</div>
        </div>
        <div class="hero-index" aria-hidden="true">01 <span>/ 03</span></div>
      </section>

      <section class="search-panel" aria-labelledby="search-heading">
        <div class="search-heading-row">
          <div><div class="section-kicker">YOUR NEXT ADVENTURE</div><h2 id="search-heading">Where are you headed?</h2></div>
          <span class="search-step"><span>01</span> PLAN YOUR ROUTE</span>
        </div>
        <SearchBar v-model="destination" v-model:start="start" :suggestions="suggestions" :error="errorMessage" :start-error="startError" @submit="handleAnalyze" />
      </section>

      <section class="discover-section" aria-labelledby="discover-heading">
        <div class="section-head">
          <div><div class="section-kicker">A GOOD PLACE TO BEGIN</div><h2 id="discover-heading">On the map right now</h2></div>
          <span class="section-aside">A few places to get you going <span aria-hidden="true">↗</span></span>
        </div>
        <div class="destination-grid">
          <button v-for="(place, index) in suggestions.slice(0, 4)" :key="place" type="button" class="destination-tile" :class="[`destination-tile-${index + 1}`, { 'is-selected': selectedSpot === place }]" :aria-pressed="selectedSpot === place" @click="chooseDestination(place)">
            <span class="tile-number">0{{ index + 1 }} / DELHI</span>
            <span class="tile-name">{{ place }}</span>
            <span class="tile-action" aria-hidden="true">↗</span>
            <span class="tile-texture" aria-hidden="true"></span>
          </button>
        </div>
      </section>

      <section class="overview-section" aria-labelledby="overview-heading">
        <div class="overview-topline"><div class="section-kicker">YOUR TRAVEL DASHBOARD</div><span class="live-dot"></span><span class="overview-label">PERSONAL OVERVIEW</span></div>
        <h2 id="overview-heading" class="overview-title">{{ hasResult ? `Your latest look at ${lastAnalysis.destination}` : 'A clearer picture, before you go.' }}</h2>
        <div class="overview-grid">
          <div class="overview-item"><span class="overview-index">01</span><OverviewCard label="Safety Score" :value="scoreText" :muted="!hasResult" hint="Your latest estimated risk score." /></div>
          <div class="overview-item"><span class="overview-index">02</span><OverviewCard label="Current Risk Level" hint="Risk estimate based on available factors."><RiskBadge :score="hasResult ? lastAnalysis.score : null" /></OverviewCard></div>
          <div class="overview-item"><span class="overview-index">03</span><OverviewCard label="Last Updated" :value="lastUpdatedText" :muted="!hasResult" compact hint="Time your latest analysis ran." /></div>
        </div>
        <div class="overview-bottom">
          <p>{{ hasResult ? 'Your most recent analysis. Sample data for demo only, not verified.' : 'Choose a destination to see your latest analysis here.' }}</p>
          <BaseButton v-if="hasResult" @click="viewLastAnalysis">View full analysis <span aria-hidden="true">↗</span></BaseButton>
          <span v-else class="overview-note">NO ANALYSIS YET</span>
        </div>
      </section>

      <section class="steps-section" aria-labelledby="steps-heading">
        <div class="steps-intro"><div class="section-kicker">A SIMPLE WAY TO START</div><h2 id="steps-heading">Three steps.<br /><em>More informed travel.</em></h2></div>
        <HowItWorks />
      </section>
      <RouterLink class="about-teaser" :to="{ name: 'about' }">
        <span class="about-teaser-mark" aria-hidden="true">S<span>R</span></span>
        <span class="about-teaser-copy"><span class="section-kicker">A LITTLE MORE ABOUT US</span><strong>Travel planning with context, transparency, and you in control.</strong><small>See what SafeRoute can help with — and where its limits are.</small></span>
        <span class="about-teaser-action" aria-hidden="true">↗</span>
      </RouterLink>
      <div class="home-footnote"><span>SAFEROUTE / FIELD NOTES 001</span><span>PLAN WITH CONTEXT. TRAVEL WITH CARE.</span></div>
    </div>
  </div>
</template>

<style scoped>
.home-page{--ink:#132e2a;--muted:#62766e;--pine:#163e37;--mint:#dce9de;--lime:#c4e581;--paper:#f6f7f1;background:#f6f7f1;color:var(--ink);padding:28px 0 0;overflow:hidden}
.home-container{max-width:1190px}
.home-hero{min-height:442px;position:relative;display:grid;grid-template-columns:1fr .92fr;align-items:center;overflow:hidden;border-radius:22px;background:radial-gradient(ellipse at 78% 16%,rgba(99,151,110,.34),transparent 29%),linear-gradient(116deg,#102d2b 0%,#17443b 57%,#285a4d 100%);color:#f6f5e9;padding:58px 62px 66px;box-shadow:0 22px 55px rgba(21,54,46,.13)}
.hero-copy{position:relative;z-index:2;max-width:510px}.eyebrow,.section-kicker{font-size:.68rem;letter-spacing:.16em;font-weight:800}.eyebrow{display:flex;align-items:center;gap:10px;color:#c8dbbe}.eyebrow-dot,.live-dot{width:7px;height:7px;background:#c4e581;border-radius:50%;box-shadow:0 0 0 4px rgba(196,229,129,.13)}
.hero-copy h1{font-family:Georgia,'Times New Roman',serif;font-size:clamp(3.1rem,5.2vw,5rem);line-height:.98;letter-spacing:-.055em;font-weight:500;margin:25px 0 20px}.hero-copy h1 em,.steps-intro h2 em{color:#c4e581;font-weight:400}.hero-description{max-width:410px;color:rgba(245,247,235,.76);font-size:1rem;line-height:1.7;margin:0}.hero-proof{display:flex;align-items:center;gap:13px;margin-top:29px}.proof-icon{width:37px;height:37px;border-radius:12px;background:rgba(255,255,255,.1);display:grid;place-items:center}.proof-icon svg{width:20px;stroke:#c4e581;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.hero-proof strong,.hero-proof small{display:block}.hero-proof strong{font-size:.79rem;font-weight:700}.hero-proof small{font-size:.7rem;color:rgba(245,247,235,.62);margin-top:3px}
.hero-art{position:relative;min-height:335px;display:grid;place-items:center}.art-orbit{position:absolute;border:1px solid rgba(236,243,216,.13);border-radius:50%;transform:rotate(-23deg)}.orbit-one{width:440px;height:210px}.orbit-two{width:360px;height:170px;transform:rotate(29deg)}.art-sun{position:absolute;width:104px;height:104px;border-radius:50%;background:linear-gradient(140deg,#d9e3a3,#e3b887);right:22%;top:6%;box-shadow:0 0 65px rgba(225,202,142,.18)}.route-art{width:min(100%,500px);position:relative;z-index:1;overflow:visible}.terrain-back{fill:#749278;opacity:.34}.terrain-front{fill:#92a87e;opacity:.35}.route-shadow{stroke:rgba(12,35,33,.5);stroke-width:11;stroke-linecap:round;stroke-dasharray:5 12}.route-stroke{stroke:#e7e9c8;stroke-width:4;stroke-linecap:round;stroke-dasharray:1 0;animation:route-draw 1.4s ease-out both}.pin-start{fill:#c4e581;stroke:#f1f3dc;stroke-width:4}.pin-center{fill:#193f39}.pin-end{fill:#e9dfb4;stroke:#f9f5e6;stroke-width:4}.pin-clock{stroke:#34564a;stroke-width:2;stroke-linecap:round}.map-label{fill:rgba(14,40,37,.86);stroke:rgba(235,240,217,.25)}.map-label-text{fill:#eef0dc;font:700 9px Inter,Arial,sans-serif;letter-spacing:1.1px}.sparkle{fill:#dfe8bf;animation:sparkle 3s ease-in-out infinite alternate}.art-caption{position:absolute;bottom:0;right:5%;display:flex;align-items:center;gap:9px;color:rgba(237,242,222,.61);font-size:.57rem;letter-spacing:.16em;font-weight:700}.caption-line{width:24px;height:1px;background:#c4e581}.hero-index{position:absolute;bottom:22px;left:62px;color:#d6e1c9;font-family:Georgia,serif;font-size:.95rem;letter-spacing:.08em}.hero-index span{color:rgba(232,239,221,.44);font:600 .66rem Inter,Arial,sans-serif}
.search-panel{position:relative;z-index:3;margin:-30px 35px 0;background:#fff;border:1px solid rgba(20,58,48,.08);border-radius:18px;padding:27px 32px 24px;box-shadow:0 16px 44px rgba(27,55,43,.09)}.search-heading-row,.section-head{display:flex;justify-content:space-between;align-items:end;gap:18px}.section-kicker{color:#668071}.search-heading-row h2,.section-head h2{font-family:Georgia,'Times New Roman',serif;font-size:1.78rem;letter-spacing:-.04em;margin:6px 0 18px;font-weight:500}.search-step{font-size:.65rem;font-weight:800;letter-spacing:.12em;color:#6d8076;margin-bottom:22px}.search-step span{display:inline-grid;place-items:center;background:#e8f0e5;color:#295545;border-radius:50%;width:24px;height:24px;margin-right:7px;letter-spacing:0}
.search-panel :deep(.form-label){color:#53685f}.search-panel :deep(.form-control){border:1px solid #d7e0d6;border-radius:10px;background:#fbfcf8;color:#19362f;min-height:48px;font-size:.94rem}.search-panel :deep(.form-control:focus){border-color:#56816b;box-shadow:0 0 0 4px rgba(83,128,104,.13);background:#fff}.search-panel :deep(.search-grid){gap:9px 12px}.search-panel :deep(.search-input){padding-left:2.7rem}.search-panel :deep(.search-icon){top:15px;color:#71877a}.search-panel :deep(.sg-submit){border:0;border-radius:10px;background:#c4e581;color:#19392f;font-size:.9rem;font-weight:800;transition:transform .2s ease,background .2s ease,box-shadow .2s ease}.search-panel :deep(.sg-submit:hover){background:#b7dc6f;transform:translateY(-2px);box-shadow:0 8px 18px rgba(90,125,54,.2)}.search-panel :deep(.chip){border-color:#d8e4d4;background:#f4f7ef;color:#476353;transition:all .18s ease}.search-panel :deep(.chip:hover){background:#e4eddb;border-color:#a6c08f;transform:translateY(-1px)}.search-panel :deep(.sg-chips){justify-content:flex-start!important}.search-panel :deep(.text-muted){color:#74847b!important}
.discover-section{padding:59px 35px 61px}.section-head{margin-bottom:20px}.section-head h2{margin-bottom:0}.section-aside{font-size:.76rem;color:#738178}.section-aside span{color:#497256;margin-left:6px}.destination-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.destination-tile{position:relative;isolation:isolate;min-height:146px;overflow:hidden;display:flex;flex-direction:column;align-items:flex-start;justify-content:space-between;text-align:left;border:1px solid rgba(31,66,51,.1);border-radius:14px;padding:17px 18px;background:#e8ecdf;color:#1e392f;transition:transform .24s ease,box-shadow .24s ease,border-color .24s ease}.destination-tile:hover{transform:translateY(-5px);box-shadow:0 13px 25px rgba(27,54,40,.12);border-color:rgba(50,91,59,.28)}.destination-tile:focus-visible{outline:3px solid #518267;outline-offset:3px}.destination-tile-2{background:#e7e8d9}.destination-tile-3{background:#e1e9e2}.destination-tile-4{background:#e8e4d8}.tile-number{font-size:.59rem;letter-spacing:.13em;font-weight:800;color:#718171}.tile-name{position:relative;z-index:1;font-family:Georgia,'Times New Roman',serif;font-size:1.14rem;line-height:1.1;max-width:85%}.tile-action{position:absolute;right:16px;bottom:16px;z-index:1;display:grid;place-items:center;width:27px;height:27px;border-radius:50%;background:rgba(255,255,255,.72);color:#325a43;transition:transform .2s}.destination-tile:hover .tile-action{transform:rotate(45deg)}.tile-texture{position:absolute;z-index:-1;right:-22px;top:20px;width:106px;height:106px;border:1px solid rgba(61,92,63,.13);border-radius:50%}.tile-texture:before,.tile-texture:after{content:'';position:absolute;inset:13px;border:inherit;border-radius:50%}.tile-texture:after{inset:27px}
.overview-section{position:relative;background:#e9eee5;border:1px solid #dce4d9;border-radius:18px;padding:27px 30px 22px}.overview-topline{display:flex;align-items:center;gap:9px}.overview-topline .section-kicker{margin-right:auto}.overview-label{font-size:.61rem;font-weight:800;letter-spacing:.13em;color:#758479}.overview-title{font-family:Georgia,'Times New Roman',serif;font-size:1.66rem;font-weight:500;letter-spacing:-.035em;margin:13px 0 20px}.overview-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px}.overview-item{position:relative}.overview-index{position:absolute;right:13px;top:13px;z-index:1;font-size:.57rem;font-weight:800;letter-spacing:.1em;color:#95a397}.overview-item :deep(.sr-card){min-height:116px;border:1px solid rgba(61,90,67,.11);border-radius:12px;background:rgba(255,255,255,.72);padding:17px!important}.overview-item :deep(.text-muted){color:#718176!important}.overview-item :deep(.sr-value){color:#183b30;font-family:Georgia,serif;font-size:1.38rem}.overview-bottom{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-top:17px}.overview-bottom p{margin:0;color:#6c7b70;font-size:.73rem}.overview-note{font-size:.62rem;font-weight:800;letter-spacing:.12em;color:#87958a}.overview-bottom :deep(.btn){border-radius:9px;background:#183e35;border-color:#183e35;font-size:.76rem;padding:.58rem .9rem}.overview-bottom :deep(.btn:hover){background:#285a4c;border-color:#285a4c;transform:translateY(-1px)}
.steps-section{display:grid;grid-template-columns:.7fr 1.3fr;gap:45px;align-items:center;padding:65px 35px 42px}.steps-intro h2{font-family:Georgia,'Times New Roman',serif;font-weight:500;font-size:2.18rem;line-height:1.08;letter-spacing:-.05em;margin:11px 0}.steps-intro h2 em{color:#527c58}.steps-section :deep(h2#how-it-works-heading){display:none}.steps-section :deep(.d-flex.flex-column.flex-md-row){gap:10px!important}.steps-section :deep(.sr-step){position:relative;min-height:98px;align-items:flex-start!important;flex-direction:column;border:1px solid #dfe6dc;border-radius:12px;background:#fff;padding:15px!important;transition:transform .2s,border-color .2s,box-shadow .2s}.steps-section :deep(.sr-step:hover){transform:translateY(-3px);border-color:#b9ccaf;box-shadow:0 8px 18px rgba(35,68,44,.07)}.steps-section :deep(.step-number){width:25px;height:25px;border-radius:8px;background:#e9f0e3;color:#41644b;font-size:.7rem}.steps-section :deep(.sr-step span:last-child){font-size:.75rem;font-weight:700;color:#274238}.steps-section :deep(.d-none.d-md-flex){display:none!important}.home-footnote{display:flex;justify-content:space-between;border-top:1px solid #dce4d9;padding:17px 35px 20px;color:#829085;font-size:.57rem;font-weight:800;letter-spacing:.13em}
.destination-tile.is-selected{border-color:#557d5a;box-shadow:inset 0 0 0 1px #557d5a,0 8px 20px rgba(27,54,40,.08)}.destination-tile.is-selected .tile-number{color:#477348}.destination-tile.is-selected .tile-action{transform:rotate(45deg);background:#c4e581}
.about-teaser{display:grid;grid-template-columns:56px 1fr 40px;align-items:center;gap:17px;margin:0 35px 28px;padding:19px 22px;border:1px solid #d7e2d3;border-radius:14px;background:linear-gradient(105deg,#e7eee1,#f3f4e9);color:#214235;text-decoration:none;transition:transform .2s,border-color .2s,box-shadow .2s}.about-teaser:hover{transform:translateY(-3px);border-color:#aec4a7;box-shadow:0 12px 23px rgba(29,64,42,.08);color:#214235}.about-teaser-mark{display:grid;place-items:center;width:50px;height:50px;border-radius:14px;background:#21473a;color:#c4e581;font-family:Georgia,serif;font-size:1.4rem}.about-teaser-mark span{font-style:italic;color:#f4f2e5}.about-teaser-copy{display:flex;flex-direction:column;gap:4px}.about-teaser-copy .section-kicker{font-size:.57rem}.about-teaser-copy strong{font-family:Georgia,'Times New Roman',serif;font-size:1.14rem;font-weight:500}.about-teaser-copy small{color:#738177;font-size:.72rem}.about-teaser-action{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:#fff;color:#456d4c;font-size:1.15rem;transition:transform .2s}.about-teaser:hover .about-teaser-action{transform:rotate(45deg);background:#c4e581}
@media(max-width:767.98px){.about-teaser{grid-template-columns:42px 1fr 32px;gap:11px;margin:0 7px 21px;padding:14px}.about-teaser-mark{width:40px;height:40px;border-radius:11px;font-size:1.15rem}.about-teaser-copy strong{font-size:.96rem}.about-teaser-copy small{font-size:.66rem}.about-teaser-action{width:29px;height:29px}}
@keyframes route-draw{from{stroke-dasharray:0 600;opacity:.2}to{stroke-dasharray:600 0;opacity:1}}@keyframes sparkle{from{opacity:.35;transform:scale(.8)}to{opacity:1;transform:scale(1.35)}}
@media(max-width:991.98px){.home-hero{padding:47px 40px 58px;min-height:400px}.hero-art{min-height:280px}.search-panel{margin-left:16px;margin-right:16px}.discover-section{padding-left:16px;padding-right:16px}.steps-section{padding-left:16px;padding-right:16px;gap:25px}.destination-tile{min-height:130px}.overview-section{padding:23px}}
@media(max-width:767.98px){.home-page{padding-top:14px}.home-hero{grid-template-columns:1fr;min-height:auto;padding:37px 27px 34px;border-radius:17px}.hero-copy h1{font-size:clamp(3rem,11vw,4.2rem);margin:21px 0 15px}.hero-description{font-size:.91rem;max-width:480px}.hero-proof{margin-top:20px}.hero-art{min-height:230px;margin:2px -7px -5px}.route-art{max-width:430px}.art-orbit.orbit-one{width:90%;height:170px}.art-orbit.orbit-two{width:75%;height:140px}.art-sun{width:75px;height:75px;right:18%;top:4%}.art-caption{right:4%;bottom:0}.hero-index{left:27px;bottom:14px}.search-panel{margin:-15px 7px 0;padding:21px 19px 18px;border-radius:14px}.search-heading-row h2{font-size:1.5rem;margin-bottom:15px}.search-step{display:none}.search-panel :deep(.search-grid){grid-template-columns:minmax(0,1fr);grid-template-areas:'label' 'field' 'chips' 'submit'}.search-panel :deep(.sg-submit){width:100%;min-height:48px}.search-panel :deep(.sg-chips){justify-content:flex-start!important}.search-panel :deep(.d-flex.align-items-center.gap-2.mt-2){flex-wrap:wrap}.discover-section{padding:43px 7px 41px}.section-head{align-items:flex-start;flex-direction:column;gap:8px}.section-head h2{font-size:1.55rem}.destination-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.destination-tile{min-height:123px;padding:14px}.tile-name{font-size:1.04rem}.overview-section{padding:20px 16px;border-radius:15px}.overview-title{font-size:1.42rem}.overview-grid{grid-template-columns:1fr;gap:8px}.overview-item :deep(.sr-card){min-height:unset!important;padding:14px!important}.overview-index{top:12px;right:12px}.overview-bottom{align-items:flex-start;flex-direction:column}.steps-section{grid-template-columns:1fr;gap:7px;padding:44px 7px 30px}.steps-intro h2{font-size:1.9rem}.steps-section :deep(.d-flex.flex-column.flex-md-row){display:grid!important;grid-template-columns:1fr;gap:8px!important}.steps-section :deep(.sr-step){min-height:64px;flex-direction:row!important;align-items:center!important}.home-footnote{padding:15px 7px 19px;gap:12px;font-size:.48rem}}
@media(max-width:380px){.home-container{padding-left:12px;padding-right:12px}.destination-tile{min-height:112px;padding:12px}.tile-name{font-size:.96rem}.home-footnote{letter-spacing:.07em}}
@media(prefers-reduced-motion:reduce){.home-page *, .home-page *:before,.home-page *:after{animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.01ms!important}}
</style>
