<template>
  <div>
    <a-button type="primary" style="margin-bottom: 16px" @click="showAdd = true">添加ETF</a-button>
    <a-table :dataSource="funds" :columns="columns" rowKey="code" size="small">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'is_active'">
          <a-switch :checked="record.is_active" @change="(v: boolean) => onToggle(record.code, v)" />
        </template>
        <template v-if="column.key === 'action'">
          <a-popconfirm title="确认删除?" @confirm="onDelete(record.code)">
            <a-button type="link" danger size="small">删除</a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <a-modal v-model:open="showAdd" title="添加ETF" @ok="onAdd" :confirmLoading="adding"
             :okButtonProps="{ disabled: !lookupResult }">
      <a-form :labelCol="{ span: 6 }">
        <a-form-item label="基金代码">
          <a-input-search v-model:value="inputCode" placeholder="输入6位代码后回车"
                          :loading="looking" @search="onLookup" enter-button="查询" />
        </a-form-item>
        <template v-if="lookupResult">
          <a-form-item label="名称">
            <span>{{ lookupResult.name }}</span>
          </a-form-item>
          <a-form-item label="市场">
            <a-tag :color="lookupResult.market === 'sh' ? 'blue' : 'green'">
              {{ lookupResult.market === 'sh' ? '上海' : '深圳' }}
            </a-tag>
          </a-form-item>
          <a-form-item label="历史数据">
            <span v-if="lookupResult.has_history" style="color: #3f8600">
              ✓ 有 {{ lookupResult.history_count }} 天历史份额
            </span>
            <span v-else style="color: #999">暂无历史数据</span>
          </a-form-item>
          <a-form-item label="分组">
            <a-input v-model:value="groupTag" placeholder="可选，如：沪深300" />
          </a-form-item>
        </template>
        <a-alert v-if="lookupError" :message="lookupError" type="error" show-icon style="margin-top: 8px" />
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getFunds, lookupFund, createFund, updateFund, deleteFund } from '../api'

const funds = ref<any[]>([])
const showAdd = ref(false)
const adding = ref(false)
const inputCode = ref('')
const looking = ref(false)
const lookupResult = ref<any>(null)
const lookupError = ref('')
const groupTag = ref('')

const columns = [
  { title: '代码', dataIndex: 'code', key: 'code', width: 100 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '市场', dataIndex: 'market', key: 'market', width: 80 },
  { title: '分组', dataIndex: 'group_tag', key: 'group_tag', width: 100 },
  { title: '启用', key: 'is_active', width: 80 },
  { title: '操作', key: 'action', width: 80 },
]

const load = async () => {
  const res = await getFunds()
  funds.value = res.data.data || []
}

const onLookup = async () => {
  const code = inputCode.value.trim()
  if (!code || code.length !== 6) {
    lookupError.value = '请输入6位基金代码'
    lookupResult.value = null
    return
  }
  looking.value = true
  lookupError.value = ''
  lookupResult.value = null
  try {
    const res = await lookupFund(code)
    if (res.data.code === 0) {
      lookupResult.value = res.data.data
    } else {
      lookupError.value = res.data.message
    }
  } catch (e: any) {
    lookupError.value = e.response?.data?.detail || '查询失败'
  } finally { looking.value = false }
}

const onAdd = async () => {
  if (!lookupResult.value) return
  adding.value = true
  try {
    await createFund({
      code: lookupResult.value.code,
      name: lookupResult.value.name,
      market: lookupResult.value.market,
      group_tag: groupTag.value || null,
    })
    message.success(`已添加 ${lookupResult.value.name}`)
    showAdd.value = false
    inputCode.value = ''
    lookupResult.value = null
    groupTag.value = ''
    await load()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '添加失败')
  } finally { adding.value = false }
}

const onToggle = async (code: string, active: boolean) => {
  await updateFund(code, { is_active: active })
  await load()
}

const onDelete = async (code: string) => {
  await deleteFund(code)
  message.success('已删除')
  await load()
}

onMounted(load)
</script>
