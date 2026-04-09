<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible theme="light" :width="200">
      <div style="height: 48px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; color: #1677ff">
        📡 ETF雷达
        <span style="font-size: 11px; font-weight: normal; color: #999; margin-left: 4px">{{ version }}</span>
      </div>
      <a-menu mode="inline" :selectedKeys="[currentRoute]" @click="onMenuClick">
        <a-menu-item key="dashboard">
          <template #icon><DashboardOutlined /></template>
          仪表盘
        </a-menu-item>
        <a-menu-item key="manage">
          <template #icon><SettingOutlined /></template>
          ETF管理
        </a-menu-item>
        <a-menu-item key="help" @click="helpRef?.show()">
          <template #icon><QuestionCircleOutlined /></template>
          使用说明
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #f0f0f0">
        <span style="font-size: 16px; font-weight: 500">{{ pageTitle }}</span>
        <a-button type="primary" :loading="collecting" @click="onCollect">
          手动采集
        </a-button>
      </a-layout-header>
      <a-layout-content style="margin: 16px; padding: 24px; background: #fff; border-radius: 8px">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
  <HelpModal ref="helpRef" />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { DashboardOutlined, SettingOutlined, QuestionCircleOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { triggerCollect } from './api'
import HelpModal from './views/HelpModal.vue'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const collecting = ref(false)
const version = ref('')
const helpRef = ref()

const currentRoute = computed(() => String(route.name || 'dashboard'))
const pageTitle = computed(() => {
  const map: Record<string, string> = { dashboard: '仪表盘', manage: 'ETF管理', detail: 'ETF详情' }
  return map[currentRoute.value] || 'ETF雷达'
})

const onMenuClick = ({ key }: { key: string }) => router.push({ name: key })

// 获取版本号
import { onMounted } from 'vue'
import { getCollectStatus } from './api'
onMounted(async () => {
  try {
    const res = await getCollectStatus()
    version.value = res.data.data?.version ? `v${res.data.data.version}` : ''
  } catch { /* empty */ }
})

const onCollect = async () => {
  collecting.value = true
  try {
    const res = await triggerCollect(true)
    const d = res.data.data
    message.success(`采集完成: ${d.updated || d.fund_count || 0} 条数据`)
  } catch {
    message.error('采集失败')
  } finally {
    collecting.value = false
  }
}
</script>
