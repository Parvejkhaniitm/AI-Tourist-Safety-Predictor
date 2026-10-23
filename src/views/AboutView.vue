<script setup>
import { useRouter } from 'vue-router'
import BaseButton from '../components/BaseButton.vue'

const router = useRouter()

const benefits = [
  { number: '01', icon: '◉', title: 'A little more context', text: 'See the factors behind an estimate—like time, weather, crowd levels, or local incident information when those signals are available.' },
  { number: '02', icon: '↗', title: 'Compare your options', text: 'Understand the distance and time trade-offs between route choices, then open live directions in Google Maps to continue planning.' },
  { number: '03', icon: '◎', title: 'Make your own call', text: 'Clear explanations help you decide what matters for your trip. SafeRoute is a planning aid, not a substitute for local guidance.' },
]

const principles = [
  { title: 'Show what is known', text: 'Factors are presented with their availability and source context, so missing information is easier to spot.' },
  { title: 'Be honest about limits', text: 'A safety estimate cannot predict what will happen to an individual. Conditions can change quickly.' },
  { title: 'Keep you in control', text: 'Use the details as one input in your own planning, alongside official advisories and local knowledge.' },
]

function startPlanning() {
  router.push({ name: 'home' })
}
</script>

<template>
  <div class="about-page">
    <div class="container about-container">
      <section class="about-hero">
        <div class="about-hero-copy">
          <p class="about-eyebrow"><span></span> A MORE THOUGHTFUL WAY TO EXPLORE</p>
          <h1>Travel curious.<br /><em>Plan with context.</em></h1>
          <p class="about-lede">SafeRoute AI helps you look at a destination and its journey with a little more information before you head out.</p>
          <BaseButton @click="startPlanning">Plan a trip <span aria-hidden="true">↗</span></BaseButton>
        </div>
        <div class="about-hero-art" aria-hidden="true">
          <div class="about-sun"></div><div class="about-circle circle-a"></div><div class="about-circle circle-b"></div>
          <div class="about-land land-a"></div><div class="about-land land-b"></div>
          <div class="about-location-pin"><span></span></div>
          <div class="about-art-note"><b>THE JOURNEY</b><span>starts with a question</span></div>
          <span class="about-coord">28° 36′ N&nbsp; · &nbsp;77° 13′ E</span>
        </div>
        <span class="about-hero-index">ABOUT / 01</span>
      </section>

      <section class="about-intro" aria-labelledby="about-intro-heading">
        <div class="about-section-tag">WHY SAFEROUTE EXISTS</div>
        <div><h2 id="about-intro-heading">Good travel decisions start with better questions.</h2><p>When you are visiting somewhere new, it helps to know more than just how to get there. SafeRoute brings destination context, a transparent risk estimate, and route comparisons into one simple planning flow.</p><p>We want to make it easier to notice what information is available, what is missing, and what you may want to check before setting off.</p></div>
      </section>

      <section class="benefit-section" aria-labelledby="benefit-heading">
        <div class="about-section-heading"><div><div class="about-section-tag">A USEFUL TRAVEL COMPANION</div><h2 id="benefit-heading">More context for the journey.</h2></div><p>Small details can make planning feel clearer. Here are a few ways SafeRoute can help.</p></div>
        <div class="benefit-grid">
          <article v-for="benefit in benefits" :key="benefit.number" class="benefit-card">
            <div class="benefit-top"><span class="benefit-number">{{ benefit.number }}</span><span class="benefit-icon" aria-hidden="true">{{ benefit.icon }}</span></div>
            <h3>{{ benefit.title }}</h3><p>{{ benefit.text }}</p><span class="benefit-rule"></span>
          </article>
        </div>
      </section>

      <section class="about-process" aria-labelledby="process-heading">
        <div class="process-heading"><div class="about-section-tag">HOW IT WORKS</div><h2 id="process-heading">A simple flow.<br /><em>A clearer starting point.</em></h2></div>
        <div class="process-list">
          <article><span>01</span><div><h3>Choose your destination</h3><p>Search for a place and add a starting point to begin planning.</p></div><b aria-hidden="true">⌕</b></article>
          <article><span>02</span><div><h3>Review available context</h3><p>See the estimated risk score, its contributing factors, and any data gaps.</p></div><b aria-hidden="true">◎</b></article>
          <article><span>03</span><div><h3>Explore route options</h3><p>Compare the available route estimates or continue with Google Maps directions.</p></div><b aria-hidden="true">↗</b></article>
        </div>
      </section>

      <section class="trust-section" aria-labelledby="trust-heading">
        <div class="trust-copy"><div class="about-section-tag">A NOTE ON RESPONSIBLE USE</div><h2 id="trust-heading">Helpful context.<br /><em>Never a guarantee.</em></h2><p>Safety is personal and circumstances change. A score cannot account for every situation or replace official travel advisories, emergency services, or your own judgment.</p></div>
        <div class="principle-list"><article v-for="(principle, index) in principles" :key="principle.title"><span>0{{ index + 1 }}</span><div><h3>{{ principle.title }}</h3><p>{{ principle.text }}</p></div></article></div>
      </section>

      <section class="about-cta"><div><div class="about-section-tag">READY WHEN YOU ARE</div><h2>Make your next plan<br />a little more informed.</h2></div><BaseButton @click="startPlanning">Explore a destination <span aria-hidden="true">↗</span></BaseButton></section>
      <footer class="about-foot"><span>SAFEROUTE AI · FIELD NOTES</span><span>PLAN WITH CONTEXT. TRAVEL WITH CARE.</span></footer>
    </div>
  </div>
</template>

<style scoped>
.about-page{--a-ink:#17392f;--a-muted:#718078;--a-green:#c4e581;background:#f6f7f1;color:var(--a-ink);padding:28px 0 0;overflow:hidden}.about-container{max-width:1190px}.about-hero{position:relative;min-height:400px;display:grid;grid-template-columns:1.02fr .98fr;align-items:center;overflow:hidden;border-radius:21px;background:radial-gradient(ellipse at 76% 8%,rgba(196,229,129,.22),transparent 28%),linear-gradient(118deg,#132f2b,#28584b);color:#f7f5ea;padding:55px 60px 60px;box-shadow:0 22px 52px rgba(21,54,46,.12)}.about-hero-copy{position:relative;z-index:2;max-width:500px}.about-eyebrow,.about-section-tag{font-size:.64rem;font-weight:800;letter-spacing:.16em}.about-eyebrow{display:flex;align-items:center;gap:9px;color:#c4d9b6}.about-eyebrow span{width:7px;height:7px;border-radius:50%;background:#c4e581;box-shadow:0 0 0 4px rgba(196,229,129,.14)}.about-hero h1{font-family:Georgia,'Times New Roman',serif;font-size:clamp(3.1rem,5.5vw,5.1rem);line-height:.97;letter-spacing:-.055em;font-weight:500;margin:24px 0 18px}.about-hero h1 em,.process-heading h2 em,.trust-copy h2 em{color:#c4e581;font-weight:400}.about-lede{max-width:440px;color:rgba(247,245,234,.75);line-height:1.7;font-size:.95rem;margin-bottom:24px}.about-hero-copy :deep(.btn){background:#c4e581;border-color:#c4e581;color:#1c3d31;border-radius:10px;font-size:.82rem;font-weight:800;padding:11px 16px;transition:transform .2s,box-shadow .2s}.about-hero-copy :deep(.btn:hover){transform:translateY(-2px);box-shadow:0 8px 18px rgba(0,0,0,.18)}.about-hero-art{position:relative;min-height:305px;display:grid;place-items:center}.about-sun{position:absolute;width:105px;height:105px;right:20%;top:0;border-radius:50%;background:linear-gradient(140deg,#dfe6ae,#ddb991);box-shadow:0 0 65px rgba(222,211,159,.15)}.about-circle{position:absolute;border:1px solid rgba(236,243,216,.16);border-radius:50%;transform:rotate(-30deg)}.circle-a{width:420px;height:190px}.circle-b{width:340px;height:145px;transform:rotate(34deg)}.about-land{position:absolute;bottom:18px;left:0;width:100%;height:125px;clip-path:polygon(0 64%,17% 34%,30% 60%,48% 17%,64% 54%,78% 28%,100% 58%,100% 100%,0 100%);background:#94a27a;opacity:.55}.land-b{bottom:0;height:96px;clip-path:polygon(0 44%,18% 72%,40% 30%,61% 63%,77% 38%,100% 66%,100% 100%,0 100%);background:#b0ae7c;opacity:.43}.about-location-pin{position:absolute;left:49%;top:35%;width:32px;height:32px;border:4px solid #f7f2dd;border-radius:50% 50% 50% 0;background:#c4e581;transform:rotate(-45deg);box-shadow:0 7px 20px rgba(5,28,21,.2)}.about-location-pin span{position:absolute;inset:7px;border-radius:50%;background:#305d48}.about-art-note{position:absolute;right:3%;bottom:23%;display:flex;flex-direction:column;gap:4px;padding:12px 15px;border:1px solid rgba(243,245,227,.24);border-radius:11px;background:rgba(17,48,40,.78);backdrop-filter:blur(8px)}.about-art-note b{font-size:.58rem;letter-spacing:.14em;color:#c4e581}.about-art-note span{font-family:Georgia,serif;font-size:.95rem}.about-coord{position:absolute;left:4%;bottom:8%;color:rgba(237,242,222,.67);font-size:.58rem;letter-spacing:.13em}.about-hero-index{position:absolute;bottom:20px;left:60px;color:#d7e2c9;font-size:.59rem;font-weight:800;letter-spacing:.15em}
.about-intro{display:grid;grid-template-columns:.67fr 1.33fr;gap:60px;padding:78px 55px 73px}.about-section-tag{color:#67816f}.about-intro h2,.about-section-heading h2,.trust-copy h2{max-width:670px;font-family:Georgia,'Times New Roman',serif;font-size:clamp(2rem,4vw,3.25rem);line-height:1.05;letter-spacing:-.045em;font-weight:500;margin:0 0 19px}.about-intro p,.about-section-heading>p,.trust-copy>p{max-width:670px;color:#718078;line-height:1.75;font-size:.92rem;margin:0 0 12px}
.benefit-section{padding:43px 35px 72px;border-top:1px solid #dfe5da}.about-section-heading{display:flex;justify-content:space-between;align-items:end;gap:30px;margin-bottom:23px}.about-section-heading h2{font-size:2.55rem;margin:8px 0 0}.about-section-heading>p{max-width:360px;font-size:.82rem;margin:0 0 4px}.benefit-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}.benefit-card{position:relative;min-height:218px;display:flex;flex-direction:column;align-items:flex-start;padding:22px;border:1px solid #dce5d9;border-radius:15px;background:linear-gradient(145deg,#fff,#f2f5ed);transition:transform .22s,box-shadow .22s,border-color .22s}.benefit-card:hover{transform:translateY(-5px);box-shadow:0 14px 30px rgba(31,68,43,.09);border-color:#b8cdb2}.benefit-top{width:100%;display:flex;justify-content:space-between;align-items:center;margin-bottom:25px}.benefit-number{color:#748678;font-size:.6rem;font-weight:800;letter-spacing:.13em}.benefit-icon{display:grid;place-items:center;width:37px;height:37px;border-radius:11px;background:#e5efdf;color:#4c774e;font-size:1.1rem}.benefit-card h3{font-family:Georgia,'Times New Roman',serif;font-size:1.25rem;font-weight:500;margin-bottom:8px}.benefit-card p{color:#708076;font-size:.78rem;line-height:1.65;margin:0}.benefit-rule{width:34px;height:2px;background:#b8d28c;margin-top:auto;padding-top:0}
.about-process{display:grid;grid-template-columns:.8fr 1.2fr;gap:65px;padding:63px 42px 73px;background:#e9eee5;border-radius:18px}.process-heading h2{font-family:Georgia,'Times New Roman',serif;font-size:2.45rem;line-height:1.08;letter-spacing:-.045em;font-weight:500;margin:11px 0}.process-list article{display:grid;grid-template-columns:42px 1fr 25px;gap:13px;align-items:start;padding:15px 0;border-bottom:1px solid #d5dfd2}.process-list article:first-child{padding-top:0}.process-list article:last-child{border-bottom:0;padding-bottom:0}.process-list article>span{display:grid;place-items:center;width:30px;height:30px;border-radius:9px;background:#fff;color:#527451;font-size:.64rem;font-weight:800}.process-list h3,.principle-list h3{font-size:.9rem;font-weight:800;margin:2px 0 5px}.process-list p,.principle-list p{font-size:.76rem;line-height:1.6;color:#748178;margin:0}.process-list article>b{color:#6b9363;font-size:1.1rem;text-align:right}
.trust-section{display:grid;grid-template-columns:.9fr 1.1fr;gap:70px;padding:78px 55px}.trust-copy h2{font-size:2.6rem;margin:10px 0 15px}.trust-copy h2 em{color:#63845c}.principle-list article{display:grid;grid-template-columns:37px 1fr;gap:13px;padding:14px 0;border-bottom:1px solid #dfe5da}.principle-list article:first-child{padding-top:0}.principle-list article:last-child{border-bottom:0}.principle-list article>span{font-size:.62rem;color:#789178;letter-spacing:.1em;font-weight:800;padding-top:2px}
.about-cta{display:flex;align-items:center;justify-content:space-between;gap:25px;padding:35px 42px;border-radius:17px;background:linear-gradient(115deg,#173e35,#28594a);color:#f7f5e9}.about-cta .about-section-tag{color:#c4d9b6}.about-cta h2{font-family:Georgia,'Times New Roman',serif;font-size:2rem;font-weight:500;letter-spacing:-.035em;line-height:1.08;margin:8px 0 0}.about-cta :deep(.btn){background:#c4e581;border-color:#c4e581;color:#19392f;border-radius:10px;font-weight:800;font-size:.8rem;padding:12px 16px;white-space:nowrap;transition:transform .2s}.about-cta :deep(.btn:hover){transform:translateY(-2px)}.about-foot{display:flex;justify-content:space-between;gap:14px;padding:18px 35px 20px;color:#829085;font-size:.56rem;font-weight:800;letter-spacing:.13em}
@media(max-width:767.98px){.about-page{padding-top:14px}.about-hero{grid-template-columns:1fr;min-height:0;padding:34px 24px 46px;border-radius:16px}.about-hero h1{font-size:3.35rem;margin:20px 0 14px}.about-lede{font-size:.87rem}.about-hero-art{min-height:215px;margin:8px -7px -6px}.about-sun{width:75px;height:75px;right:18%}.circle-a{width:90%;height:150px}.circle-b{width:74%;height:120px}.about-hero-index{left:24px;bottom:16px}.about-art-note{right:0;bottom:20%}.about-coord{bottom:0}.about-intro{grid-template-columns:1fr;gap:17px;padding:49px 10px}.about-intro h2{font-size:2.4rem}.benefit-section{padding:36px 10px 50px}.about-section-heading{align-items:flex-start;flex-direction:column;gap:10px}.about-section-heading h2{font-size:2.25rem}.benefit-grid{grid-template-columns:1fr}.benefit-card{min-height:190px}.about-process{grid-template-columns:1fr;gap:18px;padding:31px 20px;border-radius:15px}.process-heading h2{font-size:2.15rem}.trust-section{grid-template-columns:1fr;gap:20px;padding:48px 10px}.trust-copy h2{font-size:2.3rem}.about-cta{align-items:flex-start;flex-direction:column;padding:28px 23px}.about-cta h2{font-size:1.8rem}.about-foot{padding:15px 8px 18px;font-size:.47rem;letter-spacing:.07em}}
@media(prefers-reduced-motion:reduce){.about-page *, .about-page *:before,.about-page *:after{transition-duration:.01ms!important;animation-duration:.01ms!important;animation-iteration-count:1!important}}
</style>
