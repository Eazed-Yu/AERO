import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/statistics' },
    {
      path: '/statistics',
      component: () => import('@/views/StatisticsView.vue'),
      meta: { title: '统计分析' }
    },
    {
      path: '/regions',
      component: () => import('@/views/RegionManageView.vue'),
      meta: { title: '区域管理' }
    },
    {
      path: '/buildings',
      component: () => import('@/views/BuildingManageView.vue'),
      meta: { title: '建筑管理' }
    },
    {
      path: '/equipment',
      component: () => import('@/views/EquipmentView.vue'),
      meta: { title: '设备管理' }
    },
    {
      path: '/data',
      component: () => import('@/views/DataImportView.vue'),
      meta: { title: '数据管理' }
    },
    {
      path: '/anomaly',
      component: () => import('@/views/AnomalyView.vue'),
      meta: { title: '异常检测' }
    },
    {
      path: '/qa',
      component: () => import('@/views/QAView.vue'),
      meta: { title: '智能问答' }
    },
    {
      path: '/mcp',
      component: () => import('@/views/MCPView.vue'),
      meta: { title: 'MCP 服务' }
    }
  ]
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || 'AERO'} - 建筑能源智能管理`
})

export default router
