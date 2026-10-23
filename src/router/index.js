import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AnalysisView from '../views/AnalysisView.vue'
import RoutesView from '../views/RoutesView.vue'
import AboutView from '../views/AboutView.vue'
import { lastAnalysis } from '../state/lastAnalysis'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: 'Home' },
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: AnalysisView,
    meta: { title: 'Risk Analysis' },
    // Navbar se bina destination aaye to pichhla analysis kholo (agar hai)
    beforeEnter: (to) => {
      if (!to.query.destination && lastAnalysis.destination) {
        return { name: 'analysis', query: { destination: lastAnalysis.destination } }
      }
    },
  },
  {
    path: '/routes',
    name: 'routes',
    component: RoutesView,
    meta: { title: 'Safer Routes' },
  },
  {
    path: '/about',
    name: 'about',
    component: AboutView,
    meta: { title: 'About SafeRoute' },
  },
  // Wireframe: "three screens, no extra pages" -> galat URL Home par bhej do
  {
    path: '/:pathMatch(.*)*',
    redirect: { name: 'home' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // Har navigation par page upar se dikhao
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} | SafeRoute AI` : 'SafeRoute AI'
})

export default router
