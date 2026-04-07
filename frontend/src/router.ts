import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'dashboard', component: () => import('./views/Dashboard.vue') },
  { path: '/manage', name: 'manage', component: () => import('./views/Manage.vue') },
  { path: '/detail/:code', name: 'detail', component: () => import('./views/Detail.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
