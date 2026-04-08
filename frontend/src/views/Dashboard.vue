<template>
  <div>
    <!-- 更新状态条 -->
    <a-alert v-if="updateStatus.running" type="info" show-icon style="margin-bottom: 16px"
             :message="`数据更新中: ${updateStatus.step}`"
             :description="updateStatus.progress" />
    <a-alert v-else-if="updateStatus.step === '更新完成'" type="success" show-icon closable
             style="margin-bottom: 16px"
             :message="`数据已更新: ${updateStatus.progress}`" />

    <!-- 指标卡片 -->
    <a-row :gutter="16" style="margin-bottom: 24px">
      <a-col :span="8">
        <a-statistic title="追踪ETF数" :value="latestData.length" />
      </a-col>
      <a-col :span="8">
        <a-statistic title="数据最新日期" :value="lastCollectTime" />
      </a-col>
      <a-col :span="8">
        <a-statistic title="沪深300合计市值(亿元)" :value="hs300TotalMcap" :precision="2" />
      </a-col>
    </a-row>

    <!-- 趋势图 -->
    <a-card title="趋势图" style="margin-bottom: 24px" size="small">
      <template #extra>
        <a-space>
          <a-radio-group v-model:value="metric" size="small" @change="loadTrend">
            <a-radio-button value="market_cap">总市值</a-radio-button>
            <a-radio-button value="shares">份额</a-radio-button>
          </a-radio-group>
          <a-radio-group v-model:value="selectedGroup" size="small" @change="loadTrend">
            <a-radio-button value="沪深300">沪深300</a-radio-button>
            <a-radio-button value="中证500">中证500</a-radio-button>
            <a-radio-button value="上证50">上证50</a-radio-button>
            <a-radio-button value="创业板">创业板</a-radio-button>
          </a-radio-group>
        </a-space>
      </template>
      <div ref="chartRef" style="height: 360px"></div>
    </a-card>

    <!-- 最新数据表格 -->
    <a-card title="最新份额数据" size="small">
      <a-table :dataSource="latestData" :columns="columns" rowKey="fund_code"
               size="small" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'fund_code'">
            <a @click="$router.push(`/detail/${record.fund_code}`)">{{ record.fund_code }}</a>
          </template>
          <template v-if="column.key === 'change_shares'">
            <span :style="{ color: record.change_shares > 0 ? '#cf1322' : record.change_shares < 0 ? '#3f8600' : '' }">
              {{ record.change_shares != null ? record.change_shares.toFixed(2) : '-' }}
            </span>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'
import { getLatestShares, getSharesTrend, getCollectStatus, triggerCollect } from '../api'

const latestData = ref<any[]>([])
const trendData = ref<any[]>([])
const selectedGroup = ref('沪深300')
const metric = ref('market_cap')
const lastCollectTime = ref('-')
const updateStatus = ref({ running: false, step: '', progress: '' })
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
let pollTimer: any = null

const hs300TotalMcap = computed(() =>
  latestData.value.filter(d => d.group_tag === '沪深300').reduce((s, d) => s + (d.total_market_cap || 0), 0)
)

const columns = [
  { title: '代码', dataIndex: 'fund_code', key: 'fund_code', width: 100 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '分组', dataIndex: 'group_tag', key: 'group_tag', width: 100 },
  { title: '最新价', dataIndex: 'price', key: 'price', width: 100 },
  { title: '总市值(亿)', dataIndex: 'total_market_cap', key: 'total_market_cap', width: 120,
    customRender: ({ text }: any) => text?.toFixed(2) },
  { title: '份额(亿份)', dataIndex: 'shares', key: 'shares', width: 120,
    customRender: ({ text }: any) => text?.toFixed(2) },
  { title: '份额变化', dataIndex: 'change_shares', key: 'change_shares', width: 100 },
]

const metricLabel = computed(() => metric.value === 'market_cap' ? '总市值(亿元)' : '份额(亿份)')

const renderChart = () => {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
    // 窗口大小变化时自动resize
    window.addEventListener('resize', () => chart?.resize())
  }
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: trendData.value.map(d => d.trade_date) },
    yAxis: { type: 'value', name: metricLabel.value, scale: true },
    series: [{ type: 'line', data: trendData.value.map(d => d.value), smooth: true, areaStyle: { opacity: 0.15 } }],
    grid: { left: 80, right: 20, top: 40, bottom: 30 },
  })
}

const loadTrend = async () => {
  try {
    const res = await getSharesTrend({ group: selectedGroup.value, metric: metric.value })
    trendData.value = res.data.data || []
    renderChart()
  } catch { /* empty */ }
}

const pollStatus = async () => {
  try {
    const res = await getCollectStatus()
    const s = res.data.data
    updateStatus.value = s.update || { running: false, step: '', progress: '' }
    if (!updateStatus.value.running && pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
      // 更新完成，刷新数据
      const latestRes = await getLatestShares()
      latestData.value = latestRes.data.data || []
      lastCollectTime.value = s.latest_date || '-'
      await loadTrend()
    }
  } catch { /* empty */ }
}

onMounted(async () => {
  try {
    const [latestRes, statusRes] = await Promise.all([getLatestShares(), getCollectStatus()])
    latestData.value = latestRes.data.data || []
    const status = statusRes.data.data
    lastCollectTime.value = status?.latest_date || '-'
    updateStatus.value = status?.update || { running: false, step: '', progress: '' }

    if (status && !status.is_up_to_date) {
      // 6小时内只自动触发一次
      const COOLDOWN = 6 * 60 * 60 * 1000
      const lastAuto = Number(localStorage.getItem('etf_last_auto_update') || '0')
      if (Date.now() - lastAuto > COOLDOWN) {
        localStorage.setItem('etf_last_auto_update', String(Date.now()))
        triggerCollect().catch(() => {})
        pollTimer = setInterval(pollStatus, 2000)
      }
    }
  } catch { /* empty */ }
  await loadTrend()
})
</script>
