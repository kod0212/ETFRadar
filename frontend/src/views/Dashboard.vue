<template>
  <div>
    <!-- 更新状态条 -->
    <a-alert v-if="updateStatus.running" type="info" show-icon style="margin-bottom: 16px"
             :message="`数据更新中: ${updateStatus.step}`"
             :description="updateStatus.progress" />

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
      <div ref="chartRef" style="width: 100%; height: 360px"></div>
    </a-card>

    <!-- 最新数据表格 -->
    <a-card title="最新份额数据" size="small">
      <template #extra>
        <a-select v-model:value="filterTag" style="width: 140px" size="small" allowClear placeholder="按标签筛选"
                  @change="() => {}">
          <a-select-option v-for="t in allTags" :key="t" :value="t">{{ t }}</a-select-option>
        </a-select>
      </template>
      <a-table :dataSource="filteredData" :columns="columns" rowKey="fund_code"
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
          <template v-if="column.key === 'tags'">
            <a-space size="small" v-if="record.tags">
              <a-tag v-for="t in record.tags.split(',')" :key="t" size="small" color="blue">{{ t }}</a-tag>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts'
import { getLatestShares, getSharesTrend, getCollectStatus, triggerCollect } from '../api'

const latestData = ref<any[]>([])
const trendData = ref<any[]>([])
const selectedGroup = ref('沪深300')
const metric = ref('market_cap')
const lastCollectTime = ref('-')
const updateStatus = ref({ running: false, step: '', progress: '' })
const filterTag = ref<string | undefined>(undefined)
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
let pollTimer: any = null

const hs300TotalMcap = computed(() =>
  latestData.value.filter(d => d.group_tag === '沪深300').reduce((s, d) => s + (d.total_market_cap || 0), 0)
)

const allTags = computed(() => {
  const tags = new Set<string>()
  latestData.value.forEach(d => {
    if (d.tags) d.tags.split(',').forEach((t: string) => tags.add(t.trim()))
  })
  return Array.from(tags).sort()
})

const filteredData = computed(() => {
  if (!filterTag.value) return latestData.value
  return latestData.value.filter(d => d.tags && d.tags.split(',').map((t: string) => t.trim()).includes(filterTag.value!))
})

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
  { title: '标签', dataIndex: 'tags', key: 'tags', width: 120 },
]

const metricLabel = computed(() => metric.value === 'market_cap' ? '总市值(亿元)' : '份额(亿份)')

const onResize = () => setTimeout(() => chart?.resize(), 100)
let resizeObserver: ResizeObserver | null = null

const renderChart = () => {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
    resizeObserver = new ResizeObserver(onResize)
    resizeObserver.observe(chartRef.value)
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
      const latestRes = await getLatestShares()
      latestData.value = latestRes.data.data || []
      lastCollectTime.value = s.latest_date || '-'
      await loadTrend()
    }
  } catch { /* empty */ }
}

onMounted(async () => {
  window.addEventListener('resize', onResize)

  try {
    const [latestRes, statusRes] = await Promise.all([getLatestShares(), getCollectStatus()])
    latestData.value = latestRes.data.data || []
    const status = statusRes.data.data
    lastCollectTime.value = status?.latest_date || '-'

    // 自动更新（后端控制6小时冷却）
    if (status && !status.is_up_to_date) {
      triggerCollect(false).then(res => {
        const d = res.data.data
        if (d.status === 'cooldown' || d.status === 'up_to_date') return
        // 真正开始更新了，轮询状态
        updateStatus.value = { running: true, step: '准备更新...', progress: '' }
        pollTimer = setInterval(pollStatus, 2000)
      }).catch(() => {})
    }
  } catch { /* empty */ }
  await loadTrend()
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  resizeObserver?.disconnect()
  if (pollTimer) clearInterval(pollTimer)
  chart?.dispose()
  chart = null
})
</script>
