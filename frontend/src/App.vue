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
      <!-- 更新横幅 -->
      <div v-if="updateInfo" style="background: #e6f4ff; padding: 8px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #91caff">
        <span>🎉 发现新版本 <b>v{{ updateInfo.version }}</b>
          <span v-if="updateInfo.description" style="color: #666; margin-left: 8px">{{ updateInfo.description }}</span>
        </span>
        <a-space>
          <a-button v-if="updateInfo.update_type !== 'cold'" type="primary" size="small" @click="onStartUpdate">
            立即更新
          </a-button>
          <template v-else>
            <a-button type="primary" size="small" :href="coldDownloadUrl" target="_blank">下载新版本</a-button>
          </template>
          <a-button size="small" @click="updateInfo = null">忽略</a-button>
        </a-space>
      </div>

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

  <!-- 更新进度弹窗 -->
  <a-modal v-model:open="showUpdateModal" title="版本更新" :footer="null" :closable="updateProgress.status === 'done' || updateProgress.status === 'failed'" :maskClosable="false">
    <div style="padding: 16px 0">
      <p v-if="updateProgress.status === 'done'" style="color: #52c41a; font-size: 16px; text-align: center">
        ✅ {{ updateProgress.message }}
      </p>
      <p v-else-if="updateProgress.status === 'failed'" style="color: #ff4d4f; text-align: center">
        ❌ {{ updateProgress.message }}
      </p>
      <template v-else>
        <p style="margin-bottom: 12px">{{ updateProgress.message || '准备更新...' }}</p>
        <a-progress :percent="updateProgress.percent" :status="updateProgress.status === 'failed' ? 'exception' : 'active'" />
      </template>
      <div v-if="updateProgress.status === 'done'" style="text-align: center; margin-top: 16px">
        <a-button type="primary" @click="onRefreshAfterUpdate">刷新页面</a-button>
        <p style="color: #999; margin-top: 8px; font-size: 12px">{{ countdown }}秒后自动刷新</p>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { DashboardOutlined, SettingOutlined, QuestionCircleOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { triggerCollect, getCollectStatus, checkUpdate, doUpdate, getUpdateProgress } from './api'
import HelpModal from './views/HelpModal.vue'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const collecting = ref(false)
const version = ref('')
const helpRef = ref()

// 更新相关
const updateInfo = ref<any>(null)
const showUpdateModal = ref(false)
const updateProgress = ref({ status: 'idle', percent: 0, message: '' })
const countdown = ref(5)
let progressTimer: any = null
let countdownTimer: any = null

const currentRoute = computed(() => String(route.name || 'dashboard'))
const pageTitle = computed(() => {
  const map: Record<string, string> = { dashboard: '仪表盘', manage: 'ETF管理', detail: 'ETF详情' }
  return map[currentRoute.value] || 'ETF雷达'
})

const coldDownloadUrl = computed(() => {
  if (!updateInfo.value) return ''
  const ua = navigator.userAgent.toLowerCase()
  return ua.includes('mac') ? updateInfo.value.full_url_mac : updateInfo.value.full_url_windows
})

const onMenuClick = ({ key }: { key: string }) => router.push({ name: key })

// 启动时检查版本和更新
onMounted(async () => {
  try {
    const res = await getCollectStatus()
    version.value = res.data.data?.version ? `v${res.data.data.version}` : ''
  } catch { /* empty */ }

  try {
    const res = await checkUpdate()
    const d = res.data.data
    if (d?.has_update) {
      updateInfo.value = d
    }
  } catch { /* empty */ }
})

onUnmounted(() => {
  if (progressTimer) clearInterval(progressTimer)
  if (countdownTimer) clearInterval(countdownTimer)
})

const onStartUpdate = async () => {
  showUpdateModal.value = true
  updateProgress.value = { status: 'downloading', percent: 0, message: '准备更新...' }
  try {
    await doUpdate()
    // 轮询进度
    progressTimer = setInterval(async () => {
      try {
        const res = await getUpdateProgress()
        updateProgress.value = res.data.data
        if (res.data.data.status === 'done') {
          clearInterval(progressTimer)
          startCountdown()
        } else if (res.data.data.status === 'failed') {
          clearInterval(progressTimer)
        }
      } catch { /* empty */ }
    }, 500)
  } catch {
    updateProgress.value = { status: 'failed', percent: 0, message: '更新请求失败' }
  }
}

const startCountdown = () => {
  countdown.value = 5
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      onRefreshAfterUpdate()
    }
  }, 1000)
}

const onRefreshAfterUpdate = () => {
  window.location.reload()
}

const onCollect = async () => {
  collecting.value = true
  try {
    const res = await triggerCollect(true)
    const d = res.data.data
    const count = d.updated || d.fund_count || 0
    if (d.sources && !d.sources.szse) {
      message.warning(`采集完成: ${count} 条数据（深交所连接失败，仅更新上交所）`)
    } else {
      message.success(`采集完成: ${count} 条数据`)
    }
  } catch {
    message.error('采集失败')
  } finally {
    collecting.value = false
  }
}
</script>
