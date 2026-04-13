<template>
  <div>
    <!-- 更新状态条 -->
    <a-alert v-if="updateStatus.running" type="info" show-icon style="margin-bottom: 16px"
             :message="`数据更新中: ${updateStatus.step}`"
             :description="updateStatus.progress" />

    <!-- 指标卡片 -->
    <a-row :gutter="16" style="margin-bottom: 24px">
      <a-col :span="8">
        <a-statistic :title="filterLabel ? `筛选ETF数` : '追踪ETF数'"
                     :value="filteredData.length" :suffix="filterLabel ? `/ ${latestData.length}` : ''" :loading="loading" />
      </a-col>
      <a-col :span="8">
        <a-statistic title="数据最新日期" :value="lastCollectTime" :loading="loading" />
      </a-col>
      <a-col :span="8">
        <a-statistic :title="filterLabel ? '筛选合计市值(亿元)' : '全部合计市值(亿元)'"
                     :value="summaryMcap" :precision="2" :loading="loading" />
      </a-col>
    </a-row>

    <!-- 趋势图 -->
    <a-card :title="chartTitle" style="margin-bottom: 24px; position: relative" size="small">
      <template #extra>
        <a-space>
          <a-radio-group v-model:value="metric" size="small" @change="loadTrend">
            <a-radio-button value="market_cap">总市值</a-radio-button>
            <a-radio-button value="shares">份额</a-radio-button>
          </a-radio-group>
          <a-select v-model:value="filterKey" style="width: 200px" size="small" @change="onFilterChange">
            <a-select-option value="__all__">全部追踪ETF</a-select-option>
            <a-select-opt-group label="系统标签">
              <a-select-option v-for="t in allFilterTags.sys" :key="'s:'+t.name" :value="'s:'+t.name">
                {{ t.name }} ({{ t.count }}只)
              </a-select-option>
            </a-select-opt-group>
            <a-select-opt-group v-if="allFilterTags.user.length" label="自定义标签">
              <a-select-option v-for="t in allFilterTags.user" :key="'u:'+t.name" :value="'u:'+t.name">
                {{ t.name }} ({{ t.count }}只)
              </a-select-option>
            </a-select-opt-group>
          </a-select>
        </a-space>
      </template>
      <div ref="chartRef" style="width: 100%; height: 360px"></div>
      <a-empty v-if="!loading && trendData.length === 0" description="暂无趋势数据" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%)" />
    </a-card>

    <!-- 最新数据表格 -->
    <a-card :title="`最新份额数据${filterLabel ? ' — ' + filterLabel : ''}`" size="small">
      <a-table :dataSource="filteredData" :columns="columns" rowKey="fund_code"
               size="small" :loading="loading" :pagination="{ pageSize: 50, showSizeChanger: true, pageSizeOptions: ['20','50','100'], showTotal: (t: number) => `共 ${t} 只` }">
        <template #emptyText>
          <a-empty :description="loading ? '加载中...' : '暂无追踪ETF，请先到ETF管理添加'" />
        </template>
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'fund_code'">
            <a @click="$router.push(`/detail/${record.fund_code}`)">{{ record.fund_code }}</a>
          </template>
          <template v-if="column.key === 'change_shares'">
            <span :style="{ color: record.change_shares > 0 ? '#cf1322' : record.change_shares < 0 ? '#3f8600' : '' }">
              {{ record.change_shares != null ? record.change_shares.toFixed(2) : '-' }}
            </span>
          </template>
          <template v-if="column.key === 'all_tags'">
            <a-space size="small" wrap>
              <a-tag v-for="t in (record.sys_tags||'').split(',').filter(Boolean)" :key="'s'+t" size="small" color="orange">{{ t }}</a-tag>
              <a-tag v-for="t in (record.tags||'').split(',').filter(Boolean)" :key="'u'+t" size="small" color="blue">{{ t }}</a-tag>
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
const metric = ref('market_cap')
const lastCollectTime = ref('-')
const updateStatus = ref({ running: false, step: '', progress: '' })
const filterKey = ref('__all__')
const chartRef = ref<HTMLElement>()
const loading = ref(true)
let chart: echarts.ECharts | null = null
let pollTimer: any = null

// 解析筛选key
const filterType = computed(() => {
  if (filterKey.value === '__all__') return 'all'
  return 'tag'
})
const filterValue = computed(() => filterKey.value.replace(/^[su]:/, ''))
const filterLabel = computed(() => {
  if (filterType.value === 'all') return ''
  return filterValue.value
})

// 合并标签（系统+用户）
const getAllTagsForItem = (d: any): string[] => {
  const tags: string[] = []
  if (d.sys_tags) d.sys_tags.split(',').forEach((t: string) => { if (t.trim()) tags.push(t.trim()) })
  if (d.tags) d.tags.split(',').forEach((t: string) => { if (t.trim()) tags.push(t.trim()) })
  return tags
}

// 所有标签列表（系统橙色+用户蓝色）
const allFilterTags = computed(() => {
  const sysMap: Record<string, number> = {}
  const userMap: Record<string, number> = {}
  latestData.value.forEach(d => {
    if (d.sys_tags) d.sys_tags.split(',').forEach((t: string) => {
      const tag = t.trim(); if (tag) sysMap[tag] = (sysMap[tag] || 0) + 1
    })
    if (d.tags) d.tags.split(',').forEach((t: string) => {
      const tag = t.trim(); if (tag && !sysMap[tag]) userMap[tag] = (userMap[tag] || 0) + 1
    })
  })
  return {
    sys: Object.entries(sysMap).sort((a,b) => b[1]-a[1]).map(([name, count]) => ({ name, count })),
    user: Object.entries(userMap).sort().map(([name, count]) => ({ name, count })),
  }
})

// 筛选后的数据
const filteredData = computed(() => {
  if (filterType.value === 'all') return latestData.value
  return latestData.value.filter(d => getAllTagsForItem(d).includes(filterValue.value))
})

const summaryMcap = computed(() =>
  filteredData.value.reduce((s, d) => s + (d.total_market_cap || 0), 0)
)

const chartTitle = computed(() => {
  if (filterLabel.value) return `「${filterLabel.value}」趋势图`
  return '全部追踪ETF趋势图'
})

const columns = [
  { title: '代码', dataIndex: 'fund_code', key: 'fund_code', width: 100 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '最新价', dataIndex: 'price', key: 'price', width: 100,
    sorter: (a: any, b: any) => (a.price || 0) - (b.price || 0) },
  { title: '总市值(亿)', dataIndex: 'total_market_cap', key: 'total_market_cap', width: 120,
    customRender: ({ text }: any) => text?.toFixed(2),
    sorter: (a: any, b: any) => (a.total_market_cap || 0) - (b.total_market_cap || 0),
    defaultSortOrder: 'descend' as const },
  { title: '份额(亿份)', dataIndex: 'shares', key: 'shares', width: 120,
    customRender: ({ text }: any) => text?.toFixed(2),
    sorter: (a: any, b: any) => (a.shares || 0) - (b.shares || 0) },
  { title: '份额变化', dataIndex: 'change_shares', key: 'change_shares', width: 100,
    sorter: (a: any, b: any) => (a.change_shares || 0) - (b.change_shares || 0) },
  { title: '标签', key: 'all_tags', width: 200 },
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
    const params: any = { metric: metric.value }
    const codes = filteredData.value.map(d => d.fund_code).join(',')
    if (!codes) return
    params.codes = codes
    const res = await getSharesTrend(params)
    trendData.value = res.data.data || []
    renderChart()
  } catch { /* empty */ }
}

const onFilterChange = () => loadTrend()

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
    updateStatus.value = status?.update || { running: false, step: '', progress: '' }

    if (status && !status.is_up_to_date) {
      triggerCollect(false).then(res => {
        const d = res.data.data
        if (d.status === 'cooldown' || d.status === 'up_to_date') return
        updateStatus.value = { running: true, step: '准备更新...', progress: '' }
        pollTimer = setInterval(pollStatus, 2000)
      }).catch(() => {})
    }
  } catch { /* empty */ }
  await loadTrend()
  loading.value = false
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  resizeObserver?.disconnect()
  if (pollTimer) clearInterval(pollTimer)
  chart?.dispose()
  chart = null
})
</script>
