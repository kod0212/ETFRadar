<template>
  <div>
    <a-page-header :title="fundName" :sub-title="code" @back="$router.push('/')" />

    <a-card title="趋势图" size="small" style="margin-bottom: 16px">
      <template #extra>
        <a-radio-group v-model:value="metric" size="small" @change="loadTrend">
          <a-radio-button value="market_cap">总市值</a-radio-button>
          <a-radio-button value="shares">份额</a-radio-button>
        </a-radio-group>
      </template>
      <div ref="chartRef" style="height: 360px"></div>
    </a-card>

    <a-card title="历史数据" size="small">
      <a-table :dataSource="shares" :columns="columns" rowKey="trade_date" size="small" :pagination="{ pageSize: 20 }">
        <template #bodyCell="{ column, record }">
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
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { getShares, getSharesTrend } from '../api'

const route = useRoute()
const code = route.params.code as string
const fundName = ref(code)
const shares = ref<any[]>([])
const trendData = ref<any[]>([])
const metric = ref('market_cap')
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const metricLabel = computed(() => metric.value === 'market_cap' ? '总市值(亿元)' : '份额(亿份)')

const columns = [
  { title: '日期', dataIndex: 'trade_date', key: 'trade_date', width: 120 },
  { title: '价格', dataIndex: 'price', key: 'price', width: 100,
    customRender: ({ text }: any) => text?.toFixed(3) },
  { title: '总市值(亿)', dataIndex: 'total_market_cap', key: 'total_market_cap', width: 120,
    customRender: ({ text }: any) => text?.toFixed(2) ?? '-' },
  { title: '份额(亿份)', dataIndex: 'shares', key: 'shares', width: 120,
    customRender: ({ text }: any) => text?.toFixed(2) ?? '-' },
  { title: '份额变化', dataIndex: 'change_shares', key: 'change_shares', width: 100 },
  { title: '数据源', dataIndex: 'source', key: 'source', width: 80 },
]

const renderChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: trendData.value.map(d => d.trade_date) },
    yAxis: { type: 'value', name: metricLabel.value, scale: true },
    series: [{ type: 'line', data: trendData.value.map(d => d.value), smooth: true, areaStyle: { opacity: 0.15 } }],
    grid: { left: 80, right: 20, top: 40, bottom: 30 },
  })
}

const loadTrend = async () => {
  const res = await getSharesTrend({ code, metric: metric.value })
  trendData.value = res.data.data || []
  renderChart()
}

onMounted(async () => {
  const [sharesRes] = await Promise.all([
    getShares({ code, limit: 500 }),
  ])
  shares.value = sharesRes.data.data || []
  await loadTrend()
})
</script>
