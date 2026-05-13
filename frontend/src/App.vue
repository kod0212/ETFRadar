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
      <div v-if="updateInfo && !dismissed" style="background: #e6f4ff; padding: 10px 24px; border-bottom: 1px solid #91caff">
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>
            🆕 新版本 <b>v{{ updateInfo.version }}</b> 可用
            <span v-if="updateInfo.download_size" style="color: #666; margin-left: 6px">({{ updateInfo.download_size }})</span>
            <a v-if="updateInfo.changelog" style="margin-left: 10px; font-size: 12px" @click="showChangelog = !showChangelog">
              {{ showChangelog ? '收起' : '更新内容 ▾' }}
            </a>
          </span>
          <a-space>
            <template v-if="updateInfo.update_type !== 'cold'">
              <a-button type="primary" size="small" @click="onStartUpdate">立即更新</a-button>
            </template>
            <template v-else>
              <a-button type="primary" size="small" :href="coldDownloadUrl" target="_blank">下载完整包 ↗</a-button>
            </template>
            <a-button size="small" @click="dismissed = true">忽略</a-button>
          </a-space>
        </div>
        <div v-if="showChangelog && updateInfo.changelog" style="margin-top: 8px; padding: 8px 12px; background: #f6f8fa; border-radius: 4px; font-size: 13px; white-space: pre-wrap; color: #333">{{ updateInfo.changelog }}</div>
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
        <a-space>
          <a-button type="primary" @click="onRefreshAfterUpdate">立即刷新</a-button>
          <a-button @click="showUpdateModal = false">稍后</a-button>
        </a-space>
      </div>
      <div v-if="updateProgress.status === 'failed'" style="text-align: center; margin-top: 16px">
        <a-space>
          <a-button type="primary" @click="onStartUpdate">重试</a-button>
          <a-button @click="showUpdateModal = false">关闭</a-button>
        </a-space>
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
const dismissed = ref(false)
const showChangelog = ref(false)
const showUpdateModal = ref(false)
const updateProgress = ref({ status: 'idle', percent: 0, message: '' })
let progressTimer: ReturnType<typeof setInterval> | null = null

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
})

const onStartUpdate = async () => {
  showUpdateModal.value = true
  updateProgress.value = { status: 'downloading', percent: 0, message: '准备更新...' }
  try {
    const res = await doUpdate()
    const status = res.data.data?.status
    if (status === 'up_to_date') {
      updateProgress.value = { status: 'done', percent: 100, message: '已是最新版本' }
      updateInfo.value = null
      return
    }
    if (status !== 'started') {
      updateProgress.value = { status: 'failed', percent: 0, message: res.data.data?.message || '更新启动失败' }
      return
    }
    progressTimer = setInterval(async () => {
      try {
        const res = await getUpdateProgress()
        updateProgress.value = res.data.data
        if (res.data.data.status === 'done' || res.data.data.status === 'failed') {
          if (progressTimer) clearInterval(progressTimer)
          progressTimer = null
        }
      } catch { /* empty */ }
    }, 500)
  } catch {
    updateProgress.value = { status: 'failed', percent: 0, message: '更新请求失败' }
  }
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
