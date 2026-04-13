<template>
  <div>
    <a-page-header :title="`${fundName} (${code})`" :sub-title="latestDate ? `最新数据: ${latestDate}` : ''" @back="$router.push('/')">
      <template #tags>
        <a-tag v-for="t in fundSysTags" :key="'s'+t" color="orange">{{ t }}</a-tag>
        <a-tag v-for="t in fundTags" :key="'u'+t" color="blue">{{ t }}</a-tag>
      </template>
    </a-page-header>

    <a-card title="趋势图" size="small" style="margin-bottom: 16px">
      <template #extra>
        <a-radio-group v-model:value="metric" size="small" @change="loadTrend">
          <a-radio-button value="market_cap">总市值</a-radio-button>
          <a-radio-button value="shares">份额</a-radio-button>
        </a-radio-group>
      </template>
      <div ref="chartRef" style="width: 100%; height: 360px"></div>
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
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { getShares, getSharesTrend, getFunds } from '../api'

const route = useRoute()
const code = route.params.code as string
const fundName = ref(code)
const fundSysTags = ref<string[]>([])
const fundTags = ref<string[]>([])
const shares = ref<any[]>([])
const trendData = ref<any[]>([])
const metric = ref('market_cap')
const latestDate = ref('')
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
  if (!chart) {
    chart = echarts.init(chartRef.value)
    resizeObserver = new ResizeObserver(() => setTimeout(() => chart?.resize(), 100))
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
  const res = await getSharesTrend({ code, metric: metric.value })
  trendData.value = res.data.data || []
  renderChart()
}

let resizeObserver: ResizeObserver | null = null

onMounted(async () => {
  const [sharesRes, fundsRes] = await Promise.all([
    getShares({ code, limit: 500 }),
    getFunds(),
  ])
  shares.value = sharesRes.data.data || []
  const funds = fundsRes.data.data || []
  const fund = funds.find((f: any) => f.code === code)
  if (fund) {
    fundName.value = fund.name
    fundSysTags.value = fund.sys_tags ? fund.sys_tags.split(',').map((t: string) => t.trim()).filter(Boolean) : []
    fundTags.value = fund.tags ? fund.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : []
  }
  if (shares.value.length > 0) latestDate.value = shares.value[0].trade_date
  await loadTrend()
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = null
})
</script>
