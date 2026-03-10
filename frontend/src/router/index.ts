import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/dashboard' },
    {
      path: '/dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { title: '总览' }
    },
    {
      path: '/energy',
      component: () => import('@/views/EnergyQueryView.vue'),
      meta: { title: '能耗查询' }
    },
    {
      path: '/statistics',
      component: () => import('@/views/StatisticsView.vue'),
      meta: { title: '统计分析' }
    },
    {
      path: '/anomaly',
      component: () => import('@/views/AnomalyView.vue'),
      meta: { title: '异常检测' }
    },
    {
      path: '/equipment',
      component: () => import('@/views/EquipmentView.vue'),
      meta: { title: '设备监控' }
    },
    {
      path: '/import',
      component: () => import('@/views/DataImportView.vue'),
      meta: { title: '数据导入' }
    },
    {
      path: '/qa',
      component: () => import('@/views/QAView.vue'),
      meta: { title: '智能问答' }
    }
  ]
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || 'AERO'} - 建筑能源智能管理`
})

export default router
