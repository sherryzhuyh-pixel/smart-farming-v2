import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true, title: '登录' }
  },
  {
    path: '/',
    component: AppLayout,
    redirect: '/growth-curve',
    children: [
      {
        path: 'growth-curve',
        name: 'GrowthCurve',
        component: () => import('@/views/GrowthCurve.vue'),
        meta: { title: '个体生长曲线', icon: 'TrendCharts' }
      },
      {
        path: 'batch-lifecycle',
        name: 'BatchLifecycle',
        component: () => import('@/views/BatchLifecycle.vue'),
        meta: { title: '批次全生命周期', icon: 'Calendar' }
      },
      {
        path: 'performance-deviation',
        name: 'PerformanceDeviation',
        component: () => import('@/views/PerformanceDeviation.vue'),
        meta: { title: '性能偏差看板', icon: 'DataLine' }
      },
      {
        path: 'pilot-comparison',
        name: 'PilotComparison',
        component: () => import('@/views/PilotComparison.vue'),
        meta: { title: '中试效果对比', icon: 'Experiment' }
      },
      {
        path: 'financial-management',
        name: 'FinancialManagement',
        component: () => import('@/views/FinancialManagement.vue'),
        meta: { title: '财务收支管理', icon: 'Money' }
      },
      {
        path: 'profit-analysis',
        name: 'ProfitAnalysis',
        component: () => import('@/views/ProfitAnalysis.vue'),
        meta: { title: '批次利润分析', icon: 'PieChart' }
      },
      {
        path: 'traceability-query',
        name: 'TraceabilityQuery',
        component: () => import('@/views/TraceabilityQuery.vue'),
        meta: { title: '溯源查询', icon: 'Search' }
      },
      {
        path: 'inventory-management',
        name: 'InventoryManagement',
        component: () => import('@/views/InventoryManagement.vue'),
        meta: { title: '库存管理', icon: 'Box' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (!to.meta.public && !authStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && authStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
